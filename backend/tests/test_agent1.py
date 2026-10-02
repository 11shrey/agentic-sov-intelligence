import os
import io
import pytest
from fastapi.testclient import TestClient
import openpyxl

from main import app
from agents.sheet_intelligence import run_sheet_intelligence, analyze_workbook
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


def test_analyze_workbook_interface():
    """Test analyze_workbook interface with file path."""
    result = analyze_workbook(SAMPLE_EXCEL_PATH)
    assert result.selected_sheet == "Property Data"
    assert result.header_row == 3


def test_analyze_endpoint_with_valid_file():
    """Test POST /analyze endpoint with messy_sov.xlsx upload."""
    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        files = {"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/analyze", files=files)

    assert response.status_code == 200
    data = response.json()
    sheet_data = data.get("sheet_analysis", data)
    assert sheet_data["selected_sheet"] == "Property Data"
    assert sheet_data["header_row"] == 3
    assert sheet_data["confidence"] > 0.70
    assert isinstance(sheet_data["reasoning"], str)
    assert len(sheet_data["sheets"]) >= 2


def test_analyze_endpoint_invalid_file():
    """Test POST /analyze endpoint with non-excel file returns 400."""
    files = {"file": ("test.txt", b"Hello World", "text/plain")}
    response = client.post("/analyze", files=files)
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


# Scenario 1: Normal SOV workbook
def test_normal_sov_workbook():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SOV Data"
    ws.append(["Location ID", "Address", "City", "State", "Zip", "Building Value", "Contents Value", "Year Built"])
    ws.append([1, "123 Main St", "Dallas", "TX", 75001, 1000000, 500000, 2010])
    ws.append([2, "456 Oak Ave", "Austin", "TX", 78701, 2000000, 750000, 2018])

    result = analyze_workbook(wb)
    assert result.selected_sheet == "SOV Data"
    assert result.header_row == 1
    assert result.confidence >= 0.70


# Scenario 2: Multiple sheets with one relevant SOV sheet
def test_multiple_sheets_one_sov():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Cover"
    ws1.append(["SOV Submission Form 2024"])
    ws1.append(["Client Name", "Acme Inc"])

    ws2 = wb.create_sheet(title="SOV Data")
    ws2.append(["Building ID", "Address", "City", "State", "Replacement Cost", "Contents Value"])
    ws2.append(["B1", "100 Industry Way", "Houston", "TX", 5000000, 2000000])

    ws3 = wb.create_sheet(title="Summary")
    ws3.append(["Total Buildings", 1])
    ws3.append(["Total Value", 7000000])

    result = analyze_workbook(wb)
    assert result.selected_sheet == "SOV Data"
    assert result.header_row == 1


# Scenario 3: Irrelevant sheets before the SOV sheet
def test_irrelevant_sheets_before_sov():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Instructions"
    ws1.append(["Please read carefully before filing values."])

    ws2 = wb.create_sheet(title="Readme")
    ws2.append(["System configuration details and contact info."])

    ws3 = wb.create_sheet(title="Property Schedule")
    ws3.append(["Loc #", "Street Address", "City", "State", "Building Value", "Contents Value"])
    ws3.append([101, "789 Pine Rd", "Chicago", "IL", 1500000, 300000])

    result = analyze_workbook(wb)
    assert result.selected_sheet == "Property Schedule"
    assert result.header_row == 1


# Scenario 4: Header beginning several rows down (Row 5)
def test_header_several_rows_down():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Locations"
    ws.append(["ACME INSURANCE CORP SOV REPORT"])
    ws.append(["Policy Number: POL-12345"])
    ws.append(["Effective Date: 2024-01-01"])
    ws.append([])  # Blank row 4
    ws.append(["Loc No", "Street Address", "City", "State", "Building Value", "Square Feet"])  # Row 5
    ws.append([1, "100 Industrial Pkwy", "Houston", "TX", 5000000, 50000])  # Row 6

    result = analyze_workbook(wb)
    assert result.selected_sheet == "Locations"
    assert result.header_row == 5


# Scenario 5: Blank rows before headers
def test_blank_rows_before_header():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Schedule"
    ws.append([])
    ws.append([])
    ws.append([])
    ws.append(["Location ID", "Address", "City", "State", "Building Value", "Contents Value"])  # Row 4
    ws.append([101, "789 Pine Rd", "Chicago", "IL", 1500000, 300000])

    result = analyze_workbook(wb)
    assert result.selected_sheet == "Schedule"
    assert result.header_row == 4


# Scenario 6: Metadata/title rows before headers
def test_metadata_rows_before_header():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Properties"
    ws.append(["CONFIDENTIAL PROPERTY REPORT 2024"])
    ws.append(["Prepared by: Underwriting Team"])
    ws.append([])
    ws.append(["Building ID", "Street Address", "City", "State", "Zip Code", "Replacement Cost"])  # Row 4
    ws.append(["B001", "123 Commercial Way", "Miami", "FL", "33101", 3500000])

    result = analyze_workbook(wb)
    assert result.selected_sheet == "Properties"
    assert result.header_row == 4


# Scenario 7: No valid SOV sheet (raises ValueError)
def test_no_valid_sov_sheet():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Help"
    ws.append(["Frequently Asked Questions"])
    ws.append(["Q: How do I submit? A: Email us."])

    ws2 = wb.create_sheet(title="Notes")
    ws2.append(["Contact support@example.com"])

    with pytest.raises(ValueError, match="No valid Statement of Values"):
        analyze_workbook(wb)


# Scenario 8: Invalid/corrupt workbook input
def test_invalid_corrupt_workbook_input():
    # Corrupt bytes
    with pytest.raises(ValueError, match="Corrupted or invalid Excel file"):
        analyze_workbook(b"corrupted binary file content")

    # Non-existent file path
    with pytest.raises(FileNotFoundError):
        analyze_workbook("non_existent_file_12345.xlsx")

    # Invalid object type
    with pytest.raises(ValueError, match="Unsupported file_input type"):
        analyze_workbook(123456)


# Scenario 9: Original workbook remains unmodified
def test_workbook_unmodified():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Property Data"
    ws.append(["Location ID", "Address", "City", "State", "Building Value"])
    ws.append([1, "123 Main St", "Dallas", "TX", 1000000])

    # Snapshot cell values before analysis
    cells_before = [[cell.value for cell in row] for row in ws.iter_rows()]
    sheet_names_before = list(wb.sheetnames)

    result = analyze_workbook(wb)

    cells_after = [[cell.value for cell in row] for row in ws.iter_rows()]
    sheet_names_after = list(wb.sheetnames)

    assert result.selected_sheet == "Property Data"
    assert sheet_names_before == sheet_names_after
    assert cells_before == cells_after


# Scenario 10: Confidence and reasoning populated correctly
def test_confidence_and_reasoning_populated():
    result = analyze_workbook(SAMPLE_EXCEL_PATH)
    assert isinstance(result.confidence, float)
    assert 0.50 <= result.confidence <= 0.98
    assert isinstance(result.reasoning, str)
    assert len(result.reasoning) > 10
    assert "Property Data" in result.reasoning
    assert len(result.sheets) >= 2

