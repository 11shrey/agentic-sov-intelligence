import os
import openpyxl
import pytest
from fastapi.testclient import TestClient

from main import app
from models.schemas import HumanReviewDecision, HumanReviewRequest
from models.sov_schema import STANDARD_SOV_FIELDS
from agents.controlled_transformation import transform_data, apply_field_standardization
from utils.excel_utils import load_workbook_from_path

client = TestClient(app)
SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")


def test_standardization_rules():
    """Verify deterministic field standardization helper logic."""
    # Fire Sprinklers
    val, desc = apply_field_standardization("Fire Sprinklers (Y/N)", "YES")
    assert val == "Y"
    val, desc = apply_field_standardization("Fire Sprinklers (Y/N)", "NO")
    assert val == "N"

    # Numeric formatting ($1,500,000 -> 1500000)
    val, desc = apply_field_standardization("Building Value", "$1,500,000")
    assert val == 1500000

    # Year Built validation
    val, desc = apply_field_standardization("Year Built", "1998")
    assert val == 1998
    val, desc = apply_field_standardization("Year Built", "189")  # Invalid year
    assert val is None


def test_human_review_and_agent4_transformation():
    """Verify human review decisions and Agent 4 controlled transformation."""
    # 1. Analyze sample file first
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        res_analyze = client.post("/analyze", files=files)
    assert res_analyze.status_code == 200

    # 2. Submit Human Review Decisions (accept, reject, edit)
    decisions = [
        HumanReviewDecision(recommendation_id="Loc #", decision="accept"),
        HumanReviewDecision(recommendation_id="Premises Address", decision="accept"),
        HumanReviewDecision(recommendation_id="Yr Built", decision="edit", edited_value="2024"),
        HumanReviewDecision(recommendation_id="Stories", decision="reject")
    ]
    req = HumanReviewRequest(session_id="default", approver="Senior Risk Analyst", decisions=decisions)
    res_review = client.post("/review", json=req.model_dump())
    assert res_review.status_code == 200
    assert res_review.json()["processed_decisions"] == 4
    assert res_review.json()["accepted"] == 2
    assert res_review.json()["rejected"] == 1
    assert res_review.json()["edited"] == 1

    # 3. Trigger Agent 4 Transformation
    res_transform = client.post("/transform", json={"session_id": "default"})
    assert res_transform.status_code == 200
    data = res_transform.json()

    assert data["status"] == "success"
    assert "cleaned_sov_filename" in data
    assert "audit_log_filename" in data
    assert data["metrics"]["total_records"] >= 10
    assert data["metrics"]["output_records"] >= 10

    # 4. Verify Cleaned_SOV.xlsx output format and EXACT 17 fields
    cleaned_path = os.path.join(OUTPUTS_DIR, data["cleaned_sov_filename"])
    assert os.path.exists(cleaned_path)
    wb_cleaned = openpyxl.load_workbook(cleaned_path)
    sheet = wb_cleaned.active

    headers = [cell.value for cell in sheet[1]]
    assert len(headers) == 17
    assert headers == STANDARD_SOV_FIELDS

    # 5. Verify Audit_Log.xlsx generated
    audit_path = os.path.join(OUTPUTS_DIR, data["audit_log_filename"])
    assert os.path.exists(audit_path)
    wb_audit = openpyxl.load_workbook(audit_path)
    assert "Audit Log" in wb_audit.sheetnames

    # 6. Verify file downloads work
    res_dl1 = client.get(data["cleaned_sov_download_url"])
    assert res_dl1.status_code == 200

    res_dl2 = client.get(data["audit_log_download_url"])
    assert res_dl2.status_code == 200
