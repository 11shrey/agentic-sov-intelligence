import os
import pytest
from fastapi.testclient import TestClient
import openpyxl

from main import app
from agents.sheet_intelligence import run_sheet_intelligence
from utils.excel_utils import load_workbook_from_path

client = TestClient(app)

SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")

def test_health_endpoint():
    """Test GET /health returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_excel_reading_and_sheet_detection():
    """Test loading messy_sov.xlsx and Agent 1 sheet selection."""
    assert os.path.exists(SAMPLE_EXCEL_PATH), f"Sample Excel file not found at {SAMPLE_EXCEL_PATH}"
    
    wb = load_workbook_from_path(SAMPLE_EXCEL_PATH)
    assert len(wb.sheetnames) >= 2
    assert "Property Data" in wb.sheetnames
    assert "Instructions" in wb.sheetnames

    result = run_sheet_intelligence(wb)
    assert result.selected_sheet == "Property Data"
    assert result.header_row == 3
    assert result.confidence >= 0.70
    assert "Property Data" in result.reasoning

def test_analyze_endpoint_with_valid_file():
    """Test POST /analyze endpoint with messy_sov.xlsx upload."""
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/analyze", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["selected_sheet"] == "Property Data"
    assert data["header_row"] == 3
    assert data["confidence"] > 0.70
    assert isinstance(data["reasoning"], str)
    assert len(data["all_sheets"]) >= 2

def test_analyze_endpoint_invalid_file():
    """Test POST /analyze endpoint with non-excel file returns 400."""
    files = {"file": ("test.txt", b"Hello World", "text/plain")}
    response = client.post("/analyze", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
