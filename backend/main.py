import os
import io
from typing import Union
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Path
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    HealthResponse,
    NotImplementedResponse,
    SheetIntelligenceResult,
    SchemaMappingResponse,
    DataQualityResponse,
    HumanReviewRequest,
    HumanReviewResponse,
    TransformationResponse,
)
from models.state import pipeline_store, PipelineState
from agents.sheet_intelligence import analyze_workbook
from utils.excel_utils import save_uploaded_file, load_workbook_from_bytes, validate_excel_filename

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
    """Health check endpoint to verify backend status."""
    return HealthResponse(status="ok")


@app.post("/analyze", response_model=SheetIntelligenceResult, tags=["Agent 1 - Sheet Intelligence"])
async def analyze_sov_file(file: UploadFile = File(...)):
    """
    Accepts an Excel (.xlsx) file upload, executes Agent 1 (Sheet Intelligence),
    and initializes the pipeline state.
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
        saved_filename, saved_filepath = save_uploaded_file(contents, file.filename, UPLOADS_DIR)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    try:
        result = analyze_workbook(contents)
        
        # Update pipeline state
        state = pipeline_store.get_state("default")
        state.uploaded_filename = file.filename
        state.saved_file_path = saved_filepath
        state.selected_sheet = result.selected_sheet
        state.header_row = result.header_row
        state.sheet_analysis = result
        pipeline_store.set_state(state)

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sheet Intelligence analysis failed: {str(e)}"
        )


@app.post("/map", response_model=NotImplementedResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED, tags=["Agent 2 - Schema Mapping"])
async def map_schema_endpoint():
    """
    API contract endpoint for Agent 2 (Schema Mapping).
    Returns status 501 Not Implemented until Agent 2 logic is built.
    """
    return NotImplementedResponse(
        status="not_implemented",
        message="Schema Mapping agent (Agent 2) is not implemented yet."
    )


@app.post("/quality", response_model=NotImplementedResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED, tags=["Agent 3 - Data Quality"])
async def data_quality_endpoint():
    """
    API contract endpoint for Agent 3 (Data Quality & Reasoning).
    Returns status 501 Not Implemented until Agent 3 logic is built.
    """
    return NotImplementedResponse(
        status="not_implemented",
        message="Data Quality & Reasoning agent (Agent 3) is not implemented yet."
    )


@app.post("/review", response_model=NotImplementedResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED, tags=["Human Approval"])
async def human_review_endpoint(request: HumanReviewRequest):
    """
    API contract endpoint for Human Review Decisions.
    Validates decision input and updates state once Agent 4 is ready.
    """
    return NotImplementedResponse(
        status="not_implemented",
        message="Human Review processing is ready for Agent 4 integration."
    )


@app.post("/transform", response_model=NotImplementedResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED, tags=["Agent 4 - Controlled Transformation"])
async def transform_endpoint():
    """
    API contract endpoint for Agent 4 (Controlled Transformation).
    Returns status 501 Not Implemented until Agent 4 logic is built.
    """
    return NotImplementedResponse(
        status="not_implemented",
        message="Controlled Transformation agent (Agent 4) is not implemented yet."
    )


@app.get("/download/{filename}", tags=["Downloads"])
async def download_file(filename: str = Path(..., description="Target output filename")):
    """
    Downloads generated output files (Cleaned_SOV.xlsx or Audit_Log.xlsx) from backend/outputs.
    """
    # Sanitize filename to prevent directory traversal
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
