import io
import os
import sys
import pytest
from typing import List, Any
import pandas as pd
import openpyxl
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from pipeline.sov_pipeline import run_agent1_agent2, run_sov_pipeline
from models.schemas import SheetIntelligenceResult, SchemaMappingResponse, SchemaMappingRecommendation

client = TestClient(app)

# ==============================================================================
# DETERMINISTIC TEST FIXTURES
# ==============================================================================

def make_normal_sov_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Property Schedule"
    headers = [
        "Loc #", "Building #", "Street Address", "City", "State", "Zip Code", 
        "County", "Building Value", "Contents Value", "Business Income", 
        "Total Insured Value", "Year Built", "Occupancy Type", "Construction Class", 
        "Stories", "Square Feet", "Sprinklered"
    ]
    ws.append(headers)
    ws.append([1, 1, "100 Main St", "Dallas", "TX", "75001", "Dallas", 5000000, 1000000, 500000, 6500000, 2012, "Office", "MNC", 5, 50000, "Yes"])
    ws.append([2, 1, "200 Elm St", "Houston", "TX", "77001", "Harris", 8000000, 2500000, 1000000, 11500000, 2018, "Warehouse", "JM", 2, 85000, "Yes"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def make_csv_sov() -> bytes:
    content = (
        "ACME LOGISTICS SOV SUBMISSION\n"
        "Date: 2026-02-01 | Version: 2.1\n"
        "Location ID,Street Address,City,State,Zip Code,Building Value,Contents Value,Year Built,Occupancy\n"
        'LOC-101,"100 Main St, Suite 400",Dallas,TX,75001,5000000,1000000,2012,Office\n'
        'LOC-102,"200 Elm St, Building B",Houston,TX,77001,8000000,2500000,2018,Warehouse\n'
    )
    return content.encode("utf-8")


def make_header_row_gt_5_xlsx() -> bytes:
    """Creates a workbook where header is at row 10 (well beyond the 5-row sample)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Deep Header SOV"
    
    # Rows 1-9: Extensive disclaimers and multi-row notices
    ws.append(["PORTFOLIO PROPERTY STATEMENT"]) # Row 1
    ws.append(["Prepared for: Zurich North America"]) # Row 2
    ws.append(["Valuation Basis: 100% Replacement Cost"]) # Row 3
    ws.append([]) # Row 4
    ws.append(["Notice: All values subject to physical engineering survey verification."]) # Row 5
    ws.append(["Currency: USD ($)"]) # Row 6
    ws.append([]) # Row 7
    ws.append(["Primary Schedule of Properties:"]) # Row 8
    ws.append([]) # Row 9
    # Row 10: Actual Header
    ws.append(["Location ID", "Property Address", "City", "State", "Zip", "Building Value", "BI Value", "Year Built", "Sq Ft", "Sprinklered"])
    # Rows 11-15: Data
    for i in range(1, 6):
        ws.append([f"LOC-{i:03d}", f"{i*100} Harbor Way", "Miami", "FL", "33101", 5000000*i, 1000000*i, 2015, 50000, "Yes"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def make_multisheet_sov_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    
    # Sheet 1: Instructions (Irrelevant)
    ws1 = wb.active
    ws1.title = "Instructions & Guidelines"
    ws1.append(["SOV Intake Guidelines for Underwriting"])
    ws1.append(["Please submit all properties on the 'Locations SOV' tab."])

    # Sheet 2: Executive Summary (Irrelevant aggregated)
    ws2 = wb.create_sheet(title="Summary")
    ws2.append(["Executive Portfolio Summary"])
    ws2.append(["Total Locations", 2])

    # Sheet 3: Real SOV Data
    ws3 = wb.create_sheet(title="Locations SOV")
    ws3.append(["Location Ref", "Street Address", "City", "State", "Zip", "Replacement Cost", "Contents Value", "Year Built"])
    ws3.append(["LOC-001", "500 Tech Blvd", "San Jose", "CA", "95110", 12000000, 4000000, 2015])
    ws3.append(["LOC-002", "600 Silicon Ave", "Santa Clara", "CA", "95050", 6000000, 2000000, 2010])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def make_irrelevant_workbook_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Employee Directory"
    ws.append(["Employee ID", "First Name", "Last Name", "Department", "Salary", "Hire Date"])
    ws.append(["EMP-01", "Alice", "Smith", "Engineering", 125000, "2021-04-15"])
    ws.append(["EMP-02", "Bob", "Johnson", "Marketing", 95000, "2022-08-01"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ==============================================================================
# INTEGRATION TESTS: AGENT 1 -> AGENT 2
# ==============================================================================

class TestAgent1ToAgent2Integration:
    """
    Validates end-to-end integration of Agent 1 (Sheet Intelligence) and
    Agent 2 (Schema Mapping) through the backend orchestration adapter.
    """

    # 1. XLSX -> Agent 1 -> Agent 2
    def test_01_xlsx_agent1_to_agent2(self):
        file_bytes = make_normal_sov_xlsx()
        agent1_res, agent2_res = run_agent1_agent2(file_bytes, filename="normal_sov.xlsx")

        assert isinstance(agent1_res, SheetIntelligenceResult)
        assert isinstance(agent2_res, SchemaMappingResponse)
        assert agent1_res.selected_sheet == "Property Schedule"
        assert agent1_res.header_row == 1
        assert agent2_res.selected_sheet == "Property Schedule"
        assert len(agent2_res.mappings) >= 15

        target_map = {m.source_column: m.target_field for m in agent2_res.mappings}
        assert target_map.get("Street Address") == "Address"
        assert target_map.get("City") == "City"
        assert target_map.get("Building Value") == "Building Value"
        assert target_map.get("Contents Value") == "Contents"

    # 2. CSV -> Agent 1 -> Agent 2
    def test_02_csv_agent1_to_agent2(self):
        file_bytes = make_csv_sov()
        agent1_res, agent2_res = run_agent1_agent2(file_bytes, filename="logistics_sov.csv")

        assert agent1_res.selected_sheet == "logistics_sov"
        assert agent1_res.header_row == 3
        assert agent2_res.selected_sheet == "logistics_sov"
        assert len(agent2_res.mappings) == 9

        target_map = {m.source_column: m.target_field for m in agent2_res.mappings}
        assert target_map.get("Location ID") == "Reference"
        assert target_map.get("Street Address") == "Address"
        assert target_map.get("Building Value") == "Building Value"

    # 3. SOV with header_row <= 5
    def test_03_header_row_lte_5(self):
        file_bytes = make_normal_sov_xlsx()
        agent1_res, agent2_res = run_agent1_agent2(file_bytes, filename="sov_row1.xlsx")
        assert agent1_res.header_row <= 5
        assert len(agent2_res.mappings) > 0

    # 4. SOV with header_row > 5 (Crucial: complete sheet data passed, not just 5-row sample)
    def test_04_header_row_gt_5_passes_complete_rows(self):
        file_bytes = make_header_row_gt_5_xlsx()
        agent1_res, agent2_res = run_agent1_agent2(file_bytes, filename="deep_header.xlsx")

        # Verify Agent 1 identified row 10
        assert agent1_res.header_row == 10
        assert agent1_res.selected_sheet == "Deep Header SOV"
        
        # Verify Agent 1's sample_rows only has top 5 rows (metadata/disclaimers)
        assert len(agent1_res.sheets[0].sample_rows) <= 5

        # Verify Agent 2 successfully mapped the columns located on row 10!
        assert len(agent2_res.mappings) == 10
        target_map = {m.source_column: m.target_field for m in agent2_res.mappings}
        assert target_map.get("Location ID") == "Reference"
        assert target_map.get("Property Address") == "Address"
        assert target_map.get("Building Value") == "Building Value"
        assert target_map.get("BI Value") == "BI"
        assert target_map.get("Year Built") == "Year Built"

    # 5. Multiple sheets where Agent 1 selects the correct SOV sheet
    def test_05_multisheet_selects_correct_sov_sheet(self):
        file_bytes = make_multisheet_sov_xlsx()
        agent1_res, agent2_res = run_agent1_agent2(file_bytes, filename="portfolio.xlsx")

        assert agent1_res.selected_sheet == "Locations SOV"
        assert agent2_res.selected_sheet == "Locations SOV"

        # Verify mappings are strictly from "Locations SOV"
        source_cols = [m.source_column for m in agent2_res.mappings]
        assert "Location Ref" in source_cols
        assert "Replacement Cost" in source_cols
        assert "SOV Intake Guidelines for Underwriting" not in source_cols
        assert "Executive Portfolio Summary" not in source_cols

    # 6. Irrelevant workbook rejection
    def test_06_irrelevant_workbook_rejection(self):
        file_bytes = make_irrelevant_workbook_xlsx()
        with pytest.raises(ValueError) as exc:
            run_agent1_agent2(file_bytes, filename="employee_roster.xlsx")
        assert "No valid Statement of Values (SOV) sheet detected" in str(exc.value)

    # 7. Agent 2 receives complete selected-sheet rows
    def test_07_agent2_receives_complete_rows(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Large Set"
        ws.append(["Location ID", "Address", "City", "State", "Building Value"])
        for i in range(1, 30):
            ws.append([f"LOC-{i}", f"{i*10} Main St", "Dallas", "TX", 1000000*i])
        buf = io.BytesIO()
        wb.save(buf)

        agent1_res, agent2_res = run_agent1_agent2(buf.getvalue(), filename="large_set.xlsx")
        assert len(agent2_res.mappings) == 5

    # 8. Agent 2 receives correct 1-indexed header_row
    def test_08_agent2_receives_correct_header_row_indexing(self):
        file_bytes = make_header_row_gt_5_xlsx()
        agent1_res, agent2_res = run_agent1_agent2(file_bytes, filename="deep.xlsx")
        assert agent1_res.header_row == 10
        # Check that mappings correspond to row 10 headers
        headers_found = [m.source_column for m in agent2_res.mappings]
        assert "Property Address" in headers_found
        assert "PORTFOLIO PROPERTY STATEMENT" not in headers_found

    # 9. Agent 2 produces recommendations conforming to schema contract
    def test_09_mapping_recommendations_contract(self):
        file_bytes = make_normal_sov_xlsx()
        _, agent2_res = run_agent1_agent2(file_bytes, filename="normal.xlsx")

        for rec in agent2_res.mappings:
            assert isinstance(rec, SchemaMappingRecommendation)
            assert rec.source_column
            assert rec.target_field
            assert 0.0 <= rec.confidence <= 1.0
            assert rec.matching_method in ("exact", "alias", "normalized", "fuzzy", "default")
            assert isinstance(rec.reasoning, str)
            assert rec.status in ("approved", "rejected", "needs_review")

    # 10. API endpoint POST /map uses Agent 1 -> Agent 2 orchestration
    def test_10_post_map_api_endpoint(self):
        file_bytes = make_normal_sov_xlsx()
        response = client.post(
            "/map",
            files={"file": ("normal_sov.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["selected_sheet"] == "Property Schedule"
        assert len(data["mappings"]) >= 15

    # 11. Full pipeline SOVPipelineResult uses Agent 1 -> Agent 2 orchestration
    def test_11_full_pipeline_orchestration(self):
        file_bytes = make_normal_sov_xlsx()
        pipeline_result = run_sov_pipeline(file_bytes, filename="normal_sov.xlsx")

        assert pipeline_result.sheet_analysis.selected_sheet == "Property Schedule"
        assert pipeline_result.sheet_analysis.header_row == 1
        assert len(pipeline_result.mappings) >= 15
        assert isinstance(pipeline_result.quality_issues, list)
