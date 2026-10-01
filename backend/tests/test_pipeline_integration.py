import os
import hashlib
import pytest
from fastapi.testclient import TestClient
import openpyxl

from main import app
from pipeline.sov_pipeline import run_sov_pipeline
from utils.excel_utils import load_workbook_from_path

client = TestClient(app)

SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")

def get_file_md5(file_path: str) -> str:
    """Helper to compute MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def test_end_to_end_pipeline_integration():
    """
    End-to-End Integration Test for Integrated SOV Analysis Pipeline (Agents 1 -> 2 -> 3).
    """
    assert os.path.exists(SAMPLE_EXCEL_PATH), f"Sample Excel file not found at {SAMPLE_EXCEL_PATH}"
    initial_file_hash = get_file_md5(SAMPLE_EXCEL_PATH)

    # 1. Test Excel Upload via POST /analyze
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/analyze", files=files)

    # Verify endpoint returns 200 OK
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    # 2. Verify Agent 1: Sheet Intelligence results
    assert "sheet_analysis" in data
    sheet_info = data["sheet_analysis"]
    assert sheet_info["selected_sheet"] == "Property Data"
    
    # 3. Verify header row detection
    assert sheet_info["header_row"] == 3
    assert sheet_info["confidence"] > 0.70
    assert isinstance(sheet_info["reasoning"], str) and len(sheet_info["reasoning"]) > 0

    # 4. Verify Agent 2: Schema Mappings
    assert "mappings" in data
    mappings = data["mappings"]
    assert len(mappings) >= 10

    target_fields = [m["target_field"] for m in mappings]
    assert "Reference" in target_fields      # Loc #
    assert "Address" in target_fields        # Premises Address
    assert "City" in target_fields           # Town
    assert "State" in target_fields          # St
    assert "Zip" in target_fields            # ZIP Code
    assert "Building Value" in target_fields # Bldg Repl Cost
    assert "Year Built" in target_fields     # Yr Built

    # 5. Verify mapping confidence and reasoning
    for m in mappings:
        assert "source_column" in m
        assert "target_field" in m
        assert "confidence" in m and 0.0 <= m["confidence"] <= 1.0
        assert "matching_method" in m and m["matching_method"] in ("exact", "normalized", "alias", "fuzzy", "default")
        assert "reasoning" in m and isinstance(m["reasoning"], str) and len(m["reasoning"]) > 0
        assert "status" in m and m["status"] in ("approved", "rejected", "needs_review")

    # 6. Verify Agent 3: Data Quality Issues
    assert "quality_issues" in data
    quality_issues = data["quality_issues"]
    assert len(quality_issues) > 0

    # Verify detection of invalid year "189" in row 6 (or row offset)
    invalid_years = [q for q in quality_issues if q["issue_type"] == "invalid_year"]
    assert len(invalid_years) > 0
    assert any(q["field"] == "Year Built" and q["value"] == "189" for q in invalid_years)

    # 7. Verify combined pipeline completes without errors
    assert "sheet_analysis" in data and "mappings" in data and "quality_issues" in data

    # 8. Verify original source Excel file was NOT modified
    post_file_hash = get_file_md5(SAMPLE_EXCEL_PATH)
    assert initial_file_hash == post_file_hash, "Original Excel file was modified during pipeline execution!"


def test_individual_agent_endpoints():
    """Verify GET /schema, POST /map, and POST /quality endpoints."""
    # GET /schema
    res_schema = client.get("/schema")
    assert res_schema.status_code == 200
    assert "standard_fields" in res_schema.json()
    assert len(res_schema.json()["standard_fields"]) == 17

    # POST /map
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res_map = client.post("/map", files=files)
    assert res_map.status_code == 200
    assert "mappings" in res_map.json()

    # POST /quality
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res_quality = client.post("/quality", files=files)
    assert res_quality.status_code == 200
    assert "issues" in res_quality.json()
