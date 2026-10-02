import os
import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
import openpyxl

from main import app
from pipeline.sov_pipeline import SOVPipelineResult
from agents.sheet_intelligence import analyze_workbook
from utils.excel_utils import load_workbook_from_bytes, extract_sheet_rows

client = TestClient(app)
SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")


# 1. Valid /analyze request
def test_valid_analyze_request():
    assert os.path.exists(SAMPLE_EXCEL_PATH)
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        response = client.post(
            "/analyze",
            files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert result.sheet_analysis.selected_sheet == "Property Data"
    assert result.sheet_analysis.header_row == 3
    assert len(result.mappings) > 0
    assert len(result.quality_issues) > 0


# 2. Empty file (0 bytes)
def test_empty_file_upload():
    empty_bytes = b""
    response = client.post(
        "/analyze",
        files={"file": ("empty.xlsx", empty_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# 3. Invalid/corrupt Excel
def test_corrupt_excel_upload():
    corrupt_bytes = b"PK\x03\x04\x00\x00corrupted_zip_stream_data_here"
    response = client.post(
        "/analyze",
        files={"file": ("corrupted.xlsx", corrupt_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


# 4. Non-Excel content
def test_non_excel_extension_upload():
    response = client.post(
        "/analyze",
        files={"file": ("document.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


# 5. Workbook with no sheets
def test_workbook_with_no_sheets():
    wb = openpyxl.Workbook()
    # Remove all sheets
    for sheetname in list(wb.sheetnames):
        wb.remove(wb[sheetname])
    
    buf = io.BytesIO()
    # openpyxl requires at least one sheet to save, so mock load_workbook_from_bytes
    with patch("pipeline.sov_pipeline.load_workbook_from_bytes", return_value=wb):
        response = client.post(
            "/analyze",
            files={"file": ("no_sheets.xlsx", b"dummy_content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert response.status_code == 400
    assert "no sheets" in response.json()["detail"].lower()


# 6. Workbook with no valid SOV sheet
def test_workbook_with_no_valid_sov_sheet():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "General Info"
    ws.append(["Welcome to our service"])
    ws.append(["For inquiries, please contact admin@company.com"])

    buf = io.BytesIO()
    wb.save(buf)
    file_bytes = buf.getvalue()

    response = client.post(
        "/analyze",
        files={"file": ("no_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 400
    assert "No valid Statement of Values (SOV) sheet detected" in response.json()["detail"]


# 7. Agent 1 validation error reaching the API
def test_agent1_validation_error_propagates_to_api():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Instructions"
    ws.append(["Instructions sheet with no property headers"])

    buf = io.BytesIO()
    wb.save(buf)
    file_bytes = buf.getvalue()

    response = client.post(
        "/analyze",
        files={"file": ("only_instructions.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    assert response.status_code == 400
    assert "No valid Statement of Values" in response.json()["detail"]


# 8. Unexpected internal error handling
def test_unexpected_internal_error_handling():
    with patch("main.run_sov_pipeline", side_effect=RuntimeError("Simulated unexpected internal crash")):
        with open(SAMPLE_EXCEL_PATH, "rb") as f:
            response = client.post(
                "/analyze",
                files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Simulated unexpected internal crash" in data["detail"]
    # Verify no traceback is leaked
    assert "Traceback" not in data["detail"]


# 9. Existing valid /analyze response remains compatible
def test_analyze_response_compatibility():
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        response = client.post(
            "/analyze",
            files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert response.status_code == 200
    data = response.json()
    
    # Check top-level keys
    assert "sheet_analysis" in data
    assert "mappings" in data
    assert "quality_issues" in data

    # Check sheet_analysis fields
    sheet_info = data["sheet_analysis"]
    assert "selected_sheet" in sheet_info
    assert "header_row" in sheet_info
    assert "confidence" in sheet_info
    assert "reasoning" in sheet_info
    assert "sheets" in sheet_info
    assert "all_sheets" in sheet_info
    assert isinstance(sheet_info["confidence"], (int, float))
    assert 0.0 <= sheet_info["confidence"] <= 1.0


# 10. Existing Agent 1 behavior remains unchanged
def test_agent1_behavior_unchanged():
    result = analyze_workbook(SAMPLE_EXCEL_PATH)
    assert result.selected_sheet == "Property Data"
    assert result.header_row == 3
    assert result.confidence >= 0.70
    assert "Property Data" in result.reasoning
    assert len(result.sheets) >= 2
    assert len(result.all_sheets) >= 2
