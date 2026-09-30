import os
import io
import openpyxl
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import HealthResponse, SheetIntelligenceResult
from agents.sheet_intelligence import run_sheet_intelligence
from utils.excel_utils import load_workbook_from_bytes

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

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend status."""
    return HealthResponse(status="ok")

@app.post("/analyze", response_model=SheetIntelligenceResult, tags=["Agent 1 - Sheet Intelligence"])
async def analyze_sov_file(file: UploadFile = File(...)):
    """
    Accepts an Excel (.xlsx) file upload and executes Agent 1 (Sheet Intelligence).
    Detects sheet names, row/column counts, the primary SOV sheet, and header row.
    """
    if not file.filename or not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an Excel workbook (.xlsx)."
        )

    try:
        contents = await file.read()
        wb = load_workbook_from_bytes(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read Excel workbook. File may be corrupt or invalid: {str(e)}"
        )

    try:
        result = run_sheet_intelligence(wb)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sheet Intelligence analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
