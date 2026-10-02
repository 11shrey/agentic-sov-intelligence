import os
import io
import pytest
from fastapi.testclient import TestClient

from main import app
from pipeline.sov_pipeline import SOVPipelineResult
from agents.sheet_intelligence import analyze_workbook
from models.schemas import TransformationResponse

client = TestClient(app)
SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")


# 1. Valid SOV CSV
def test_valid_sov_csv_pipeline():
    csv_content = (
        "Location ID,Address,City,State,Zip Code,Building Value,Contents Value,Year Built\n"
        "1,123 Main St,Dallas,TX,75001,1500000,500000,2015\n"
        "2,456 Oak Ave,Austin,TX,78701,2500000,800000,2018\n"
    ).encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("commercial_sov.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert result.sheet_analysis.selected_sheet == "commercial_sov"
    assert result.sheet_analysis.header_row == 1
    assert result.sheet_analysis.confidence >= 0.70
    assert len(result.mappings) >= 5
    assert isinstance(result.quality_issues, list)


# 2. CSV with title / metadata rows before header
def test_csv_with_title_and_metadata_rows():
    csv_content = (
        "ACME PROPERTY SCHEDULE 2024\n"
        "Prepared by: Underwriting Risk Team\n"
        "\n"
        "Loc #,Street Address,Town,St,Replacement Cost,Contents Value,Square Feet\n"
        "101,100 Industrial Blvd,Houston,TX,5000000,1000000,50000\n"
        "102,200 Commerce Way,Dallas,TX,3000000,750000,25000\n"
    ).encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("property_schedule.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert result.sheet_analysis.selected_sheet == "property_schedule"
    assert result.sheet_analysis.header_row == 4
    assert result.sheet_analysis.confidence >= 0.70


# 3. CSV with UTF-8 BOM
def test_csv_with_utf8_bom():
    csv_text = (
        "\ufeffLocation ID,Address,City,State,Building Value\n"
        "1,789 Pine Rd,Miami,FL,2000000\n"
    )
    csv_bytes = csv_text.encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("bom_data.csv", csv_bytes, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sheet_analysis"]["header_row"] == 1
    assert data["sheet_analysis"]["selected_sheet"] == "bom_data"


# 4. CSV with quoted fields and embedded commas
def test_csv_with_quoted_fields_and_commas():
    csv_content = (
        '"Loc #","Premises Address, Suite 100","City","State","Building Value"\n'
        '1,"123 Elm St, Building B",Chicago,IL,4000000\n'
    ).encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("quoted_sov.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sheet_analysis"]["header_row"] == 1


# 5. Empty CSV (0 bytes)
def test_empty_csv_upload():
    response = client.post(
        "/analyze",
        files={"file": ("empty.csv", b"", "text/csv")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# 6. CSV with only whitespace / commas
def test_csv_with_only_empty_cells():
    csv_content = b",,,\n,,,\n,,,\n"
    response = client.post(
        "/analyze",
        files={"file": ("all_commas.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# 7. CSV with no valid SOV data
def test_csv_with_no_valid_sov_data():
    csv_content = (
        "Welcome to our service\n"
        "For help contact support@company.com\n"
        "Version 2.0\n"
    ).encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("readme.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 400
    assert "No valid Statement of Values" in response.json()["detail"]


# 8. Unsupported file extension
def test_unsupported_file_extension():
    response = client.post(
        "/analyze",
        files={"file": ("data.json", b'{"key": "value"}', "application/json")}
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


# 9. Existing Excel upload still works flawlessly
def test_existing_excel_upload_still_works():
    assert os.path.exists(SAMPLE_EXCEL_PATH)
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        response = client.post(
            "/analyze",
            files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["sheet_analysis"]["selected_sheet"] == "Property Data"
    assert data["sheet_analysis"]["header_row"] == 3


# 10. End-to-end CSV lifecycle (Analyze -> Map -> Quality -> Transform)
def test_csv_full_pipeline_lifecycle():
    csv_content = (
        "Loc #,Address,Town,St,ZIP Code,Building Value,Contents Value,Yr Built\n"
        "1,100 Industrial Pkwy,Houston,TX,77001,$5,000,000,$1,500,000,1995\n"
        "2,200 Tech Way,Austin,TX,78701,$3,200,000,$800,000,2012\n"
    ).encode("utf-8")

    # 1. Analyze
    res_analyze = client.post(
        "/analyze",
        files={"file": ("sov_test.csv", csv_content, "text/csv")}
    )
    assert res_analyze.status_code == 200
    assert res_analyze.json()["sheet_analysis"]["selected_sheet"] == "sov_test"

    # 2. Map
    res_map = client.post(
        "/map",
        files={"file": ("sov_test.csv", csv_content, "text/csv")}
    )
    assert res_map.status_code == 200
    assert len(res_map.json()["mappings"]) >= 5

    # 3. Quality
    res_quality = client.post(
        "/quality",
        files={"file": ("sov_test.csv", csv_content, "text/csv")}
    )
    assert res_quality.status_code == 200

    # 4. Transform
    res_transform = client.post("/transform", json={"session_id": "default"})
    assert res_transform.status_code == 200
    tr_data = res_transform.json()
    TransformationResponse(**tr_data)
    assert tr_data["status"] == "success"
    assert tr_data["metrics"]["total_records"] == 2
