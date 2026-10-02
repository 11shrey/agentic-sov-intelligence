import io
import os
import sys
import time

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import openpyxl
from fastapi.testclient import TestClient

from main import app
from agents.sheet_intelligence import analyze_workbook, run_sheet_intelligence
from models.schemas import SheetIntelligenceResult

client = TestClient(app)

# ==============================================================================
# DETERMINISTIC FIXTURE GENERATORS
# ==============================================================================

def create_normal_sov_bytes() -> bytes:
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
    ws.append([2, 1, "200 Elm St", "Houston", "TX", "77001", "Harris", 8000000, 2500000, 1000000, 11500000, 2018, "Warehouse", "Joisted Masonry", 2, 85000, "Yes"])
    ws.append([3, 1, "300 Pine Rd", "Austin", "TX", "78701", "Travis", 3500000, 750000, 250000, 4500000, 2005, "Retail", "Frame", 1, 15000, "No"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_multisheet_sov_bytes() -> bytes:
    wb = openpyxl.Workbook()
    
    # Sheet 1: Instructions (Irrelevant)
    ws1 = wb.active
    ws1.title = "Instructions & Guidelines"
    ws1.append(["SOV Intake Guidelines for Underwriting"])
    ws1.append(["Please submit all properties on the 'Locations SOV' tab."])
    ws1.append(["For assistance, email sov-intake@marsh-broker.com"])

    # Sheet 2: Executive Summary (Irrelevant aggregated)
    ws2 = wb.create_sheet(title="Summary")
    ws2.append(["Executive Portfolio Summary"])
    ws2.append(["Total Locations", 2])
    ws2.append(["Total Portfolio TIV", 18000000])

    # Sheet 3: Real SOV Data
    ws3 = wb.create_sheet(title="Locations SOV")
    ws3.append(["Location Ref", "Street Address", "City", "State", "Zip", "Replacement Cost", "Contents Value", "Year Built", "Construction Type"])
    ws3.append(["LOC-001", "500 Tech Blvd", "San Jose", "CA", "95110", 12000000, 4000000, 2015, "Fire Resistive"])
    ws3.append(["LOC-002", "600 Silicon Ave", "Santa Clara", "CA", "95050", 6000000, 2000000, 2010, "Non-Combustible"])

    # Sheet 4: Sign-off
    ws4 = wb.create_sheet(title="Sign-off")
    ws4.append(["Approval Status", "Approved"])
    ws4.append(["Underwriter", "John Doe"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_title_metadata_block_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Portfolio SOV"
    
    # Title & Metadata block in rows 1-5
    ws.append(["ACME GLOBAL HOLDINGS - PROPERTY SCHEDULE"]) # Row 1
    ws.append(["Policy Period: 2026-2027 | Broker: Aon Risk Services | Date: 2026-01-15"]) # Row 2
    ws.append([]) # Row 3 (blank)
    ws.append(["CONFIDENTIAL UNDERWRITING SUBMISSION - STATEMENT OF VALUES"]) # Row 4
    ws.append([]) # Row 5 (blank)
    # Header row at Row 6
    ws.append(["Location ID", "Address", "City", "State", "Zip Code", "Building Replacement Cost", "Contents Limit", "Year Built", "Occupancy"])
    ws.append(["L-101", "777 Market St", "Philadelphia", "PA", "19106", 4500000, 1200000, 2008, "Commercial Office"])
    ws.append(["L-102", "888 Broad St", "Newark", "NJ", "07102", 9200000, 3100000, 2016, "Data Center"])
    
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_header_far_down_bytes() -> bytes:
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
    ws.append(["Loc Number", "Property Address", "City", "State", "Zip", "Building Value", "BI Value", "Year Built", "Sq Ft", "Sprinklered"])
    ws.append(["001", "10 Harbor Way", "Miami", "FL", "33101", 15000000, 3000000, 2020, 120000, "Yes"])
    ws.append(["002", "20 Bayfront Dr", "Tampa", "FL", "33602", 8500000, 1500000, 2014, 65000, "Yes"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_multiple_plausible_headers_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Complex Hierarchy SOV"
    
    # Row 1: Section Banner
    ws.append(["PORTFOLIO STATEMENT OF VALUES", ""])
    # Row 2: Category grouping
    ws.append(["Primary Property Schedule", ""])
    # Row 3: Comprehensive tabular SOV header
    ws.append(["Location ID", "Address", "City", "State", "Zip", "County", "Building Replacement Cost", "Contents Value", "Business Income", "Total Insured Value", "Year Built", "Occupancy Class", "Construction Type"])
    # Rows 4+: Data
    ws.append(["LOC-1", "1000 Park Ave", "New York", "NY", "10028", "New York", 25000000, 5000000, 2500000, 32500000, 1998, "Residential / Retail", "Fire Resistive"])
    ws.append(["LOC-2", "2000 Madison Ave", "New York", "NY", "10016", "New York", 18000000, 3500000, 1800000, 23300000, 2004, "Commercial Office", "Non-Combustible"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_irrelevant_workbook_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Employee Directory"
    ws1.append(["Employee ID", "First Name", "Last Name", "Department", "Salary", "Hire Date"])
    ws1.append(["EMP-01", "Alice", "Smith", "Engineering", 125000, "2021-04-15"])
    ws1.append(["EMP-02", "Bob", "Johnson", "Marketing", 95000, "2022-08-01"])

    ws2 = wb.create_sheet(title="Office Supplies")
    ws2.append(["Item SKU", "Description", "Unit Cost", "Stock Quantity", "Reorder Level"])
    ws2.append(["SKU-101", "Ergonomic Chair", 250, 45, 10])
    ws2.append(["SKU-102", "Standing Desk", 450, 20, 5])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_messy_sov_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Messy Property SOV"
    
    # Title row
    ws.append(["PROPERTY VALUES SCHEDULE - 2026", None, None, None])
    ws.append([]) # Blank
    # Dirty Header row at Row 3
    ws.append(["Loc #", "Premises Address", "City", "St.", "Postal", "Bldg Repl Cost ($)", "Contents ($)", "Occupancy Desc", "Yr Blt", "Sprinklers?", "Internal Underwriting Notes"])
    # Messy data rows
    ws.append([1, "123 Industrial Way", "Chicago", "IL", "60601", "$4,500,000", 1200000, "Light Mfg", 1995, "Y", "Inspected 2025"])
    ws.append([2, "456 Commerce Blvd", "Peoria", "IL", "61602", None, 450000, "Warehouse", "2001", "N", "Pending appraisal"])
    ws.append([3, "789 Logistics Ct", "Rockford", "IL", "61101", 3200000, "$800,000", "Distribution", 2012, "Yes", None])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_wide_workbook_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Wide Property Schedule"
    
    # 40 columns total: 10 SOV columns + 30 auxiliary columns
    headers = [
        "Loc ID", "Street Address", "City", "State", "Zip", "Building Value", "Contents", "BI", "TIV", "Year Built"
    ] + [f"Aux_Field_{i}" for i in range(1, 31)]
    ws.append(headers)

    for r in range(1, 11):
        row = [
            f"LOC-{r:03d}", f"{r*100} Enterprise Way", "Columbus", "OH", "43215",
            2000000 * r, 500000 * r, 250000 * r, 2750000 * r, 2000 + (r % 20)
        ] + [f"Val_{r}_{i}" for i in range(1, 31)]
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_large_workbook_bytes(num_rows: int = 3500) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Large Property Schedule"
    
    headers = [
        "Location Number", "Building ID", "Street Address", "City", "State", "Zip Code",
        "County", "Building Value", "Contents Value", "Business Income", "Total Insured Value",
        "Year Built", "Occupancy Description", "Construction Class", "Sprinklered"
    ]
    ws.append(headers)

    cities = ["Atlanta", "Charlotte", "Nashville", "Orlando", "Savannah", "Raleigh"]
    states = ["GA", "NC", "TN", "FL", "GA", "NC"]

    for i in range(1, num_rows + 1):
        idx = i % len(cities)
        bldg_val = 1000000 + (i * 1500)
        cont_val = 250000 + (i * 500)
        bi_val = 100000 + (i * 200)
        tiv = bldg_val + cont_val + bi_val
        ws.append([
            f"L-{i:05d}", f"B-{i:05d}", f"{i*10} Commercial Parkway",
            cities[idx], states[idx], f"300{idx:02d}", "County",
            bldg_val, cont_val, bi_val, tiv,
            1980 + (i % 44), "Commercial Office", "Masonry Non-Combustible", "Yes" if i % 2 == 0 else "No"
        ])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_csv_sov_bytes() -> bytes:
    content = (
        "ACME LOGISTICS SOV SUBMISSION\n"
        "Date: 2026-02-01 | Version: 2.1\n"
        "Location ID,Street Address,City,State,Zip Code,Building Value,Contents Value,Year Built,Occupancy\n"
        'LOC-101,"100 Main St, Suite 400",Dallas,TX,75001,5000000,1000000,2012,Office\n'
        'LOC-102,"200 Elm St, Building B",Houston,TX,77001,8000000,2500000,2018,Warehouse\n'
        'LOC-103,"300 Pine Rd",Austin,TX,78701,3500000,750000,2005,Retail\n'
    )
    return content.encode("utf-8")


def create_tsv_sov_bytes() -> bytes:
    content = (
        "Location ID\tStreet Address\tCity\tState\tZip Code\tBuilding Value\tContents Value\tYear Built\n"
        "1\t100 Industrial Pkwy\tHouston\tTX\t77001\t5000000\t1000000\t2014\n"
        "2\t200 Commercial Way\tAustin\tTX\t78701\t3500000\t750000\t2019\n"
    )
    return content.encode("utf-8")


def create_ods_sov_bytes() -> bytes:
    buf = io.BytesIO()
    df = pd.DataFrame([
        ["Location ID", "Address", "City", "State", "Zip", "Building Value", "Contents Value", "Year Built"],
        [1, "123 Main St", "Dallas", "TX", "75001", 1500000, 500000, 2010],
        [2, "456 Oak Ave", "Austin", "TX", "78701", 2500000, 800000, 2016]
    ])
    with pd.ExcelWriter(buf, engine="odf") as writer:
        df.to_excel(writer, sheet_name="ODS SOV Properties", index=False, header=False)
    return buf.getvalue()


def create_xlsm_sov_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Macro Properties"
    ws.append(["Building ID", "Address", "City", "State", "Replacement Cost", "Contents Value", "Year Built"])
    ws.append(["B-01", "100 Industry Way", "Houston", "TX", 5000000, 2000000, 2015])
    ws.append(["B-02", "200 Harbor Blvd", "Galveston", "TX", 3500000, 1200000, 2018])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_text_pdf_sov_bytes() -> bytes:
    pdf_template = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 160 >> stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"50 700 Td\n"
        b"(Location ID  Address  City  State  Building Value  Contents Value) Tj\n"
        b"0 -25 Td\n"
        b"(1  100 Industrial Pkwy  Houston  TX  5000000  1000000) Tj\n"
        b"0 -25 Td\n"
        b"(2  200 Commercial Way  Austin  TX  3500000  750000) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000244 00000 n \n"
        b"0000000456 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"535\n"
        b"%%EOF\n"
    )
    return pdf_template


def create_scanned_pdf_bytes() -> bytes:
    pdf_template = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length 2 >> stream\n"
        b" \n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000222 00000 n \n"
        b"trailer << /Size 5 /Root 1 0 R >>\n"
        b"startxref\n"
        b"276\n"
        b"%%EOF\n"
    )
    return pdf_template


# ==============================================================================
# AGENT 1 VALIDATION TEST BENCH
# ==============================================================================

class TestAgent1ValidationSuite:
    """
    Repeatable Agent 1 validation test bench verifying 12 key scenarios across
    supported formats and realistic insurance Statement of Values structures.
    """

    # Scenario 1: Normal SOV workbook
    def test_01_normal_sov_workbook(self):
        file_bytes = create_normal_sov_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="normal_sov.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Property Schedule"
        assert result.header_row == 1
        assert result.confidence >= 0.85
        assert "Property Schedule" in result.reasoning
        assert len(result.sheets) == 1
        assert result.sheets[0].row_count == 4
        assert result.sheets[0].column_count == 17
        assert duration < 0.5

    # Scenario 2: Multi-sheet workbook (SOV selection & irrelevant sheet filtering)
    def test_02_multisheet_sov_workbook(self):
        file_bytes = create_multisheet_sov_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="multisheet_sov.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Locations SOV"
        assert result.header_row == 1
        assert result.confidence >= 0.85
        assert len(result.sheets) == 4
        assert duration < 0.5

    # Scenario 3: Title & metadata block (header at row 6)
    def test_03_title_metadata_block(self):
        file_bytes = create_title_metadata_block_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="title_metadata_sov.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Portfolio SOV"
        assert result.header_row == 6
        assert result.confidence >= 0.80
        assert duration < 0.5

    # Scenario 4: Header far down (header at row 10)
    def test_04_header_far_down(self):
        file_bytes = create_header_far_down_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="deep_header_sov.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Deep Header SOV"
        assert result.header_row == 10
        assert result.confidence >= 0.80
        assert duration < 0.5

    # Scenario 5: Multiple plausible header rows / banner hierarchy
    def test_05_multiple_plausible_header_rows(self):
        file_bytes = create_multiple_plausible_headers_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="complex_hierarchy.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Complex Hierarchy SOV"
        assert result.header_row == 3
        assert result.confidence >= 0.85
        assert duration < 0.5

    # Scenario 6: Irrelevant workbook rejection (No SOV content)
    def test_06_irrelevant_workbook_rejection(self):
        file_bytes = create_irrelevant_workbook_bytes()
        
        # Test direct Agent 1 engine rejection
        with pytest.raises(ValueError) as exc_info:
            analyze_workbook(file_bytes, filename="employee_roster.xlsx")
        assert "No valid Statement of Values (SOV) sheet detected" in str(exc_info.value)

        # Test API HTTP 400 rejection without traceback leakage
        response = client.post(
            "/analyze",
            files={"file": ("employee_roster.xlsx", file_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 400
        assert "no valid statement of values (sov) sheet detected" in response.json()["detail"].lower()
        assert "traceback" not in response.text.lower()

    # Scenario 7: Messy SOV (mixed types, dirty headers, blanks)
    def test_07_messy_sov_robustness(self):
        file_bytes = create_messy_sov_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="messy_sample.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Messy Property SOV"
        assert result.header_row == 3
        assert result.confidence >= 0.75
        assert duration < 0.5

    # Scenario 8: Wide workbook (40 columns with 30 auxiliary fields)
    def test_08_wide_workbook(self):
        file_bytes = create_wide_workbook_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="wide_sov.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Wide Property Schedule"
        assert result.header_row == 1
        assert result.confidence >= 0.85
        assert result.sheets[0].column_count == 40
        assert duration < 0.5

    # Scenario 9: Large-ish workbook (3,500 deterministic synthetic rows)
    def test_09_large_workbook_throughput(self):
        file_bytes = create_large_workbook_bytes(num_rows=3500)
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="large_sov.xlsx")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "Large Property Schedule"
        assert result.header_row == 1
        assert result.confidence >= 0.85
        assert result.sheets[0].row_count >= 1000
        assert duration < 2.0  # Must be sub-2-second evaluation

    # Scenario 10: CSV SOV input
    def test_10_csv_sov_ingestion(self):
        file_bytes = create_csv_sov_bytes()
        t0 = time.perf_counter()
        result = analyze_workbook(file_bytes, filename="commercial_sov.csv")
        duration = time.perf_counter() - t0

        assert result.selected_sheet == "commercial_sov"
        assert result.header_row == 3
        assert result.confidence >= 0.75
        assert duration < 0.5

    # Scenario 11: Other supported formats (TSV, XLSM, ODS, PDF)
    def test_11a_tsv_format(self):
        file_bytes = create_tsv_sov_bytes()
        result = analyze_workbook(file_bytes, filename="tab_sov.tsv")
        assert result.selected_sheet == "tab_sov"
        assert result.header_row == 1
        assert result.confidence >= 0.75

    def test_11b_xlsm_format_safe_read(self):
        file_bytes = create_xlsm_sov_bytes()
        result = analyze_workbook(file_bytes, filename="macro_sov.xlsm")
        assert result.selected_sheet == "Macro Properties"
        assert result.header_row == 1
        assert result.confidence >= 0.80

    def test_11c_ods_format(self):
        file_bytes = create_ods_sov_bytes()
        result = analyze_workbook(file_bytes, filename="odf_sov.ods")
        assert result.selected_sheet == "ODS SOV Properties"
        assert result.header_row == 1
        assert result.confidence >= 0.80

    def test_11d_pdf_text_table_format(self):
        file_bytes = create_text_pdf_sov_bytes()
        result = analyze_workbook(file_bytes, filename="printed_sov.pdf")
        assert result.selected_sheet == "Page 1"
        assert result.header_row == 1
        assert result.confidence >= 0.75

    def test_11e_pdf_scanned_rejection(self):
        file_bytes = create_scanned_pdf_bytes()
        with pytest.raises(ValueError) as exc:
            analyze_workbook(file_bytes, filename="scanned_sov.pdf")
        assert "OCR is required" in str(exc.value)

        response = client.post(
            "/analyze",
            files={"file": ("scanned_sov.pdf", file_bytes, "application/pdf")}
        )
        assert response.status_code == 400
        assert "ocr is required" in response.json()["detail"].lower()

    # Scenario 12: Invalid input handlings & error control
    def test_12a_empty_file_controlled_failure(self):
        for ext, mime in [("empty.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                          ("empty.csv", "text/csv"),
                          ("empty.tsv", "text/tab-separated-values"),
                          ("empty.pdf", "application/pdf")]:
            response = client.post("/analyze", files={"file": (ext, b"", mime)})
            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()
            assert "traceback" not in response.text.lower()

    def test_12b_corrupt_file_controlled_failure(self):
        corrupted_bytes = b"CORRUPTED_BINARY_STREAM_DATA_XXXX"
        response = client.post(
            "/analyze",
            files={"file": ("corrupt.xlsx", corrupted_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert response.status_code == 400
        assert "corrupted" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()
        assert "traceback" not in response.text.lower()

    def test_12c_unsupported_extension_controlled_failure(self):
        for ext, mime in [("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                          ("graphic.png", "image/png"),
                          ("binary.exe", "application/octet-stream")]:
            response = client.post("/analyze", files={"file": (ext, b"dummy data", mime)})
            assert response.status_code == 400
            assert "invalid file extension" in response.json()["detail"].lower()
            assert "traceback" not in response.text.lower()
