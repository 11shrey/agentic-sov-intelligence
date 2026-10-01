import os
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from main import app
from models.sov_schema import STANDARD_SOV_FIELDS, is_valid_sov_field, validate_sov_field
from models.schemas import (
    SchemaMappingRecommendation,
    DataQualityIssue,
    HumanReviewDecision,
    HumanReviewRequest,
    AuditRecord,
)
from models.state import pipeline_store, PipelineState

client = TestClient(app)
SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")


def test_17_field_schema_validation():
    """Verify standard 17 SOV fields schema definition and helper validators."""
    assert len(STANDARD_SOV_FIELDS) == 17
    expected_fields = [
        "Reference", "Address", "City", "State", "Zip", "County", "Country",
        "Building Value", "Contents", "BI", "Occupancy", "Construction",
        "Storeys", "Number of Buildings", "Year Built", "Fire Sprinklers (Y/N)", "Other"
    ]
    assert STANDARD_SOV_FIELDS == expected_fields

    assert is_valid_sov_field("Building Value") is True
    assert is_valid_sov_field("Invalid Field Name") is False

    assert validate_sov_field("Zip") == "Zip"
    with pytest.raises(ValueError, match="is not a valid 17-field standard SOV field"):
        validate_sov_field("Random Header")


def test_schema_mapping_recommendation_model():
    """Verify SchemaMappingRecommendation Pydantic model validation."""
    rec = SchemaMappingRecommendation(
        source_column="Loc #",
        target_field="Reference",
        confidence=0.95,
        matching_method="alias",
        reasoning="Loc # is standard alias for Reference",
        status="approved"
    )
    assert rec.source_column == "Loc #"
    assert rec.target_field == "Reference"
    assert rec.confidence == 0.95
    assert rec.status == "approved"

    with pytest.raises(ValidationError):
        SchemaMappingRecommendation(
            source_column="Loc #",
            target_field="Reference",
            confidence=1.5,
            matching_method="alias",
            reasoning="test",
            status="approved"
        )


def test_data_quality_issue_model():
    """Verify DataQualityIssue Pydantic model validation."""
    issue = DataQualityIssue(
        row=12,
        field="Year Built",
        value="189",
        issue_type="invalid_year",
        severity="high",
        reasoning="Year Built should be a valid 4-digit year.",
        recommendation="Review and correct year built value."
    )
    assert issue.row == 12
    assert issue.severity == "high"
    assert issue.issue_type == "invalid_year"


def test_human_review_decision_validation():
    """Verify HumanReviewDecision validation rules."""
    d1 = HumanReviewDecision(recommendation_id="rec_1", decision="accept")
    assert d1.decision == "accept"

    d2 = HumanReviewDecision(recommendation_id="rec_2", decision="edit", edited_value="Y")
    assert d2.decision == "edit"
    assert d2.edited_value == "Y"

    with pytest.raises(ValidationError, match="edited_value is required when decision is 'edit'"):
        HumanReviewDecision(recommendation_id="rec_3", decision="edit", edited_value=None)

    with pytest.raises(ValidationError, match="edited_value is required when decision is 'edit'"):
        HumanReviewDecision(recommendation_id="rec_4", decision="edit", edited_value="   ")


def test_audit_record_validation():
    """Verify AuditRecord model creation and default values."""
    audit = AuditRecord(
        source_field="Fire Prot.",
        target_field="Fire Sprinklers (Y/N)",
        before_value="YES",
        after_value="Y",
        transformation="YES -> Y",
        confidence=0.98,
        approval_status="approved",
        approver="human"
    )
    assert audit.source_field == "Fire Prot."
    assert audit.target_field == "Fire Sprinklers (Y/N)"
    assert audit.before_value == "YES"
    assert audit.after_value == "Y"
    assert audit.approver == "human"
    assert isinstance(audit.timestamp, str)


def test_pipeline_state_store():
    """Verify in-memory pipeline state manager operations."""
    state = pipeline_store.get_state("test_session")
    state.uploaded_filename = "test.xlsx"
    state.selected_sheet = "Sheet1"
    pipeline_store.set_state(state)

    retrieved = pipeline_store.get_state("test_session")
    assert retrieved.uploaded_filename == "test.xlsx"
    assert retrieved.selected_sheet == "Sheet1"

    pipeline_store.reset("test_session")
    reset_state = pipeline_store.get_state("test_session")
    assert reset_state.uploaded_filename is None


def test_api_routes_availability():
    """Verify availability of all API endpoints and 501 Not Implemented stubs."""
    # /health
    res_health = client.get("/health")
    assert res_health.status_code == 200

    # /map
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res_map = client.post("/map", files=files)
    assert res_map.status_code == 200

    # /quality
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res_quality = client.post("/quality", files=files)
    assert res_quality.status_code == 200

    # /review (Stub 501)
    res_review = client.post("/review", json={"decisions": [{"recommendation_id": "r1", "decision": "accept"}]})
    assert res_review.status_code == 501
    assert res_review.json()["status"] == "not_implemented"

    # /transform (Stub 501)
    res_transform = client.post("/transform")
    assert res_transform.status_code == 501
    assert res_transform.json()["status"] == "not_implemented"

    # /download/nonexistent.xlsx
    res_download = client.get("/download/nonexistent.xlsx")
    assert res_download.status_code == 404
