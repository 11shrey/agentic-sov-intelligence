import os
import pytest
from fastapi.testclient import TestClient

from main import app
from pipeline.sov_pipeline import SOVPipelineResult
from models.schemas import (
    HealthResponse,
    SchemaDefinitionResponse,
    SchemaMappingResponse,
    DataQualityResponse,
    HumanReviewResponse,
    TransformationResponse,
)

client = TestClient(app)
SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")


def test_1_get_health():
    """Audit GET /health endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data == {"status": "ok"}
    HealthResponse(**data)


def test_2_get_schema():
    """Audit GET /schema endpoint."""
    res = client.get("/schema")
    assert res.status_code == 200
    data = res.json()
    assert "standard_fields" in data
    assert len(data["standard_fields"]) == 17
    assert data["total_fields"] == 17
    SchemaDefinitionResponse(**data)


def test_3_post_analyze():
    """Audit POST /analyze endpoint with valid and invalid files."""
    # Invalid extension -> 400 Bad Request
    res_inv = client.post("/analyze", files={"file": ("test.txt", b"dummy content", "text/plain")})
    assert res_inv.status_code == 400
    assert "Invalid file extension" in res_inv.json()["detail"]

    # Valid upload -> 200 OK
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        res = client.post("/analyze", files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    assert res.status_code == 200
    data = res.json()
    SOVPipelineResult(**data)
    assert data["sheet_analysis"]["selected_sheet"] == "Property Data"
    assert data["sheet_analysis"]["header_row"] == 3


def test_4_post_map():
    """Audit POST /map endpoint."""
    # Invalid file -> 400
    res_inv = client.post("/map", files={"file": ("test.txt", b"dummy", "text/plain")})
    assert res_inv.status_code == 400

    # Valid upload -> 200 OK
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        res = client.post("/map", files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    assert res.status_code == 200
    data = res.json()
    SchemaMappingResponse(**data)
    assert len(data["mappings"]) >= 10


def test_5_post_quality():
    """Audit POST /quality endpoint."""
    # Invalid file -> 400
    res_inv = client.post("/quality", files={"file": ("test.txt", b"dummy", "text/plain")})
    assert res_inv.status_code == 400

    # Valid upload -> 200 OK
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        res = client.post("/quality", files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    assert res.status_code == 200
    data = res.json()
    DataQualityResponse(**data)
    assert data["total_issues"] > 0


def test_6_post_review():
    """Audit POST /review endpoint and decision validation."""
    # Missing edited_value for edit -> 422 Unprocessable Entity
    invalid_req = {
        "session_id": "default",
        "approver": "Tester",
        "decisions": [{"recommendation_id": "Yr Built", "decision": "edit"}]
    }
    res_inv = client.post("/review", json=invalid_req)
    assert res_inv.status_code == 422

    # Valid review decisions -> 200 OK
    valid_req = {
        "session_id": "default",
        "approver": "Senior Risk Analyst",
        "decisions": [
            {"recommendation_id": "Loc #", "decision": "accept"},
            {"recommendation_id": "Yr Built", "decision": "edit", "edited_value": "2024"},
            {"recommendation_id": "Stories", "decision": "reject"}
        ]
    }
    res = client.post("/review", json=valid_req)
    assert res.status_code == 200
    data = res.json()
    HumanReviewResponse(**data)
    assert data["processed_decisions"] == 3
    assert data["accepted"] == 1
    assert data["edited"] == 1
    assert data["rejected"] == 1


def test_7_post_transform():
    """Audit POST /transform endpoint."""
    res = client.post("/transform", json={"session_id": "default"})
    assert res.status_code == 200
    data = res.json()
    TransformationResponse(**data)
    assert data["status"] == "success"
    assert data["metrics"]["total_records"] >= 10


def test_8_get_download():
    """Audit GET /download/{filename} endpoint."""
    # First get valid filename from transform
    res_tr = client.post("/transform", json={"session_id": "default"})
    filename = res_tr.json()["cleaned_sov_filename"]

    # Valid download -> 200 OK
    res_dl = client.get(f"/download/{filename}")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Nonexistent file -> 404 Not Found
    res_404 = client.get("/download/nonexistent.xlsx")
    assert res_404.status_code == 404


def test_openapi_and_swagger_docs():
    """Verify OpenAPI JSON spec generation and Swagger UI availability."""
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200
    assert "<title>" in res_docs.text or "swagger" in res_docs.text.lower()

    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    openapi_spec = res_openapi.json()
    assert "paths" in openapi_spec
    assert "/health" in openapi_spec["paths"]
    assert "/analyze" in openapi_spec["paths"]
    assert "/transform" in openapi_spec["paths"]
