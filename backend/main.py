import os
import io
from typing import Union, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Path, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.schemas import (
    HealthResponse,
    SchemaDefinitionResponse,
    SheetIntelligenceResult,
    SchemaMappingRecommendation,
    SchemaMappingResponse,
    DataQualityResponse,
    HumanReviewRequest,
    HumanReviewResponse,
    TransformRequest,
    TransformationResponse,
    DashboardMetrics,
)
from models.sov_schema import STANDARD_SOV_FIELDS
from models.state import pipeline_store, PipelineState
from agents.sheet_intelligence import analyze_workbook
from agents.schema_mapping import map_schema
from agents.data_quality import analyze_quality
from agents.controlled_transformation import transform_data
from pipeline.sov_pipeline import run_sov_pipeline, SOVPipelineResult
from utils.excel_utils import save_uploaded_file, load_workbook_from_bytes, validate_excel_filename, extract_sheet_rows

app = FastAPI(
    title="Agentic SOV Intelligence System API",
    description="Backend pipeline for automated, human-approved SOV processing and data transformation.",
    version="1.0.0"
)

# Enable CORS for local development & frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend API status."""
    return HealthResponse(status="ok")


@app.get("/schema", response_model=SchemaDefinitionResponse, tags=["Schema"])
async def get_standard_schema():
    """Returns the central 17 Standard SOV Fields schema definition."""
    return SchemaDefinitionResponse(
        standard_fields=STANDARD_SOV_FIELDS,
        total_fields=len(STANDARD_SOV_FIELDS)
    )


@app.post("/analyze", response_model=SOVPipelineResult, tags=["Pipeline - Full Analysis"])
async def analyze_sov_file(file: UploadFile = File(...)):
    """
    Accepts an Excel (.xlsx) file upload and runs the integrated Agents 1 -> 2 -> 3 pipeline.
    Returns combined sheet_analysis, mappings, and quality_issues.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty."
        )

    try:
        validate_excel_filename(file.filename)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )

    try:
        contents = await file.read()
        save_uploaded_file(contents, file.filename, UPLOADS_DIR)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file upload: {str(e)}"
        )

    try:
        pipeline_result = run_sov_pipeline(contents, filename=file.filename)
        
        # Store raw file bytes in session state for downstream Agent 4 transformation
        state = pipeline_store.get_state("default")
        state.file_bytes = contents
        pipeline_store.set_state(state)

        return pipeline_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SOV Pipeline analysis failed: {str(e)}"
        )


@app.post("/map", response_model=SchemaMappingResponse, tags=["Agent 2 - Schema Mapping"])
async def map_schema_endpoint(file: UploadFile = File(...)):
    """
    Accepts an Excel file upload and executes Agent 2 (Schema Mapping).
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename cannot be empty.")
    
    try:
        validate_excel_filename(file.filename)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    try:
        contents = await file.read()
        sheet_analysis = analyze_workbook(contents)
        wb = load_workbook_from_bytes(contents)
        rows = extract_sheet_rows(wb[sheet_analysis.selected_sheet], max_rows=100)
        res = map_schema(rows, header_row=sheet_analysis.header_row)
        res.selected_sheet = sheet_analysis.selected_sheet
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Schema mapping failed: {str(e)}")


@app.post("/quality", response_model=DataQualityResponse, tags=["Agent 3 - Data Quality"])
async def data_quality_endpoint(file: UploadFile = File(...)):
    """
    Accepts an Excel file upload and executes Agent 3 (Data Quality & Reasoning).
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename cannot be empty.")

    try:
        validate_excel_filename(file.filename)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    try:
        contents = await file.read()
        sheet_analysis = analyze_workbook(contents)
        wb = load_workbook_from_bytes(contents)
        rows = extract_sheet_rows(wb[sheet_analysis.selected_sheet], max_rows=1000)
        mapping_res = map_schema(rows, header_row=sheet_analysis.header_row)
        quality_res = analyze_quality(rows, header_row=sheet_analysis.header_row, approved_mappings=mapping_res.mappings)
        return quality_res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Data quality analysis failed: {str(e)}")


@app.post("/review", response_model=HumanReviewResponse, tags=["Human Approval"])
async def human_review_endpoint(request: HumanReviewRequest):
    """
    Accepts human review decisions (accept, reject, edit) and stores them in pipeline state.
    """
    state = pipeline_store.get_state(request.session_id)
    if not state.sheet_analysis:
        sample_path = os.path.join(BASE_DIR, "sample_data", "messy_sov.xlsx")
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                run_sov_pipeline(f.read(), filename="messy_sov.xlsx", session_id=request.session_id)
            state = pipeline_store.get_state(request.session_id)

    state.human_decisions = request.decisions
    if request.approver:
        state.approver = request.approver
    pipeline_store.set_state(state)

    accepted_cnt = len([d for d in request.decisions if d.decision == "accept"])
    rejected_cnt = len([d for d in request.decisions if d.decision == "reject"])
    edited_cnt = len([d for d in request.decisions if d.decision == "edit"])

    return HumanReviewResponse(
        status="success",
        processed_decisions=len(request.decisions),
        accepted=accepted_cnt,
        rejected=rejected_cnt,
        edited=edited_cnt,
        approver=request.approver or state.approver
    )


@app.post("/transform", response_model=TransformationResponse, tags=["Agent 4 - Controlled Transformation"])
async def transform_endpoint(request: TransformRequest = Body(default_factory=TransformRequest)):
    """
    Executes Agent 4 (Controlled Transformation).
    Applies ONLY approved human decisions and deterministic standardization rules.
    Produces Cleaned_SOV.xlsx and Audit_Log.xlsx.
    """
    session_id = request.session_id
    state = pipeline_store.get_state(session_id)

    if not state.sheet_analysis or not state.file_bytes:
        sample_path = os.path.join(BASE_DIR, "sample_data", "messy_sov.xlsx")
        if os.path.exists(sample_path):
            with open(sample_path, "rb") as f:
                contents = f.read()
                run_sov_pipeline(contents, filename="messy_sov.xlsx", session_id=session_id)
                state = pipeline_store.get_state(session_id)
                state.file_bytes = contents

    if not state.file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No workbook data found in session state. Please analyze an Excel file first."
        )

    try:
        wb = load_workbook_from_bytes(state.file_bytes)
        raw_rows = extract_sheet_rows(wb[state.selected_sheet], max_rows=1000)

        response = transform_data(
            raw_sheet_rows=raw_rows,
            header_row=state.header_row,
            mappings=state.schema_mappings,
            quality_issues=state.quality_issues,
            human_decisions=state.human_decisions,
            approver=state.approver,
            output_dir=OUTPUTS_DIR
        )

        state.cleaned_sov_filename = response.cleaned_sov_filename
        state.audit_log_filename = response.audit_log_filename
        pipeline_store.set_state(state)

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Controlled Transformation failed: {str(e)}"
        )


@app.get("/download/{filename}", tags=["Downloads"])
async def download_file(filename: str = Path(..., description="Target output filename")):
    """
    Downloads generated output files (Cleaned_SOV.xlsx or Audit_Log.xlsx) from backend/outputs.
    """
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(OUTPUTS_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requested output file '{safe_filename}' not found."
        )

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Mount frontend dist static files if available
FRONTEND_DIST_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")
if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
