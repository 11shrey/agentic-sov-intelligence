import os
import io
import re
import pytest
import pandas as pd
import openpyxl
from fastapi.testclient import TestClient

from main import app
from pipeline.sov_pipeline import SOVPipelineResult
from agents.sheet_intelligence import analyze_workbook
from models.schemas import TransformationResponse

client = TestClient(app)
SAMPLE_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "sample_data", "messy_sov.xlsx")


# Helper: Generate a minimal valid text-based PDF in memory
def create_text_pdf_bytes() -> bytes:
    # A standard minimal 1-page PDF stream containing text table
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


# Helper: Generate a scanned/image-only PDF (no text stream)
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


# Helper: Generate an ODS file in memory
def create_ods_bytes() -> bytes:
    buf = io.BytesIO()
    df = pd.DataFrame([
        ["Location ID", "Address", "City", "State", "Zip", "Building Value", "Contents Value", "Year Built"],
        [1, "123 Main St", "Dallas", "TX", "75001", 1500000, 500000, 2010],
        [2, "456 Oak Ave", "Austin", "TX", "78701", 2500000, 800000, 2016]
    ])
    with pd.ExcelWriter(buf, engine="odf") as writer:
        df.to_excel(writer, sheet_name="SOV Properties", index=False, header=False)
    return buf.getvalue()


# Helper: Generate an XLSM file in memory
def create_xlsm_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Macro Properties"
    ws.append(["Building ID", "Address", "City", "State", "Replacement Cost", "Contents Value"])
    ws.append(["B-01", "100 Industry Way", "Houston", "TX", 5000000, 2000000])
    ws.append(["B-02", "200 Commerce St", "Dallas", "TX", 3500000, 1200000])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# 1. Existing XLSX Still Works
def test_existing_xlsx_still_works():
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


# 2. Existing CSV Still Works
def test_existing_csv_still_works():
    csv_content = (
        "Location ID,Address,City,State,Building Value\n"
        "1,123 Main St,Dallas,TX,1000000\n"
    ).encode("utf-8")
    response = client.post(
        "/analyze",
        files={"file": ("sov_data.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    assert response.json()["sheet_analysis"]["selected_sheet"] == "sov_data"
    assert response.json()["sheet_analysis"]["header_row"] == 1


# 3. TSV Support
def test_tsv_format_support():
    tsv_content = (
        "Location ID\tAddress\tCity\tState\tBuilding Value\tContents Value\n"
        "101\t500 Pine St\tChicago\tIL\t2500000\t800000\n"
        "102\t600 Lake Dr\tChicago\tIL\t3500000\t1200000\n"
    ).encode("utf-8")

    response = client.post(
        "/analyze",
        files={"file": ("property_schedule.tsv", tsv_content, "text/tab-separated-values")}
    )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert result.sheet_analysis.selected_sheet == "property_schedule"
    assert result.sheet_analysis.header_row == 1
    assert result.sheet_analysis.confidence >= 0.70


# 4. XLSM Support (Macro-enabled Excel without executing macros)
def test_xlsm_format_support():
    xlsm_bytes = create_xlsm_bytes()
    response = client.post(
        "/analyze",
        files={"file": ("macro_sov.xlsm", xlsm_bytes, "application/vnd.ms-excel.sheet.macroEnabled.12")}
    )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert result.sheet_analysis.selected_sheet == "Macro Properties"
    assert result.sheet_analysis.header_row == 1
    assert len(result.mappings) > 0


# 5. ODS Support (OpenDocument Spreadsheet)
def test_ods_format_support():
    ods_bytes = create_ods_bytes()
    response = client.post(
        "/analyze",
        files={"file": ("sov_portfolio.ods", ods_bytes, "application/vnd.oasis.opendocument.spreadsheet")}
    )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert result.sheet_analysis.selected_sheet == "SOV Properties"
    assert result.sheet_analysis.header_row == 1
    assert len(result.mappings) > 0


# 6. Text-based PDF Support
def test_text_pdf_support():
    pdf_bytes = create_text_pdf_bytes()
    response = client.post(
        "/analyze",
        files={"file": ("property_sov.pdf", pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    result = SOVPipelineResult(**data)
    assert "Page" in result.sheet_analysis.selected_sheet
    assert result.sheet_analysis.header_row == 1
    assert result.sheet_analysis.confidence >= 0.70


# 7. Scanned / Image-only PDF returns controlled OCR requirement error
def test_scanned_pdf_returns_ocr_required_error():
    scanned_pdf_bytes = create_scanned_pdf_bytes()
    response = client.post(
        "/analyze",
        files={"file": ("scanned_document.pdf", scanned_pdf_bytes, "application/pdf")}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Scanned or image-only PDF detected" in data["detail"]
    assert "OCR is required" in data["detail"]


# 8. Empty File (0 bytes) for TSV, ODS, XLSM, PDF
def test_empty_files_for_new_formats():
    for ext, mime in [
        (".tsv", "text/tab-separated-values"),
        (".ods", "application/vnd.oasis.opendocument.spreadsheet"),
        (".xlsm", "application/vnd.ms-excel.sheet.macroEnabled.12"),
        (".pdf", "application/pdf")
    ]:
        response = client.post(
            "/analyze",
            files={"file": (f"empty{ext}", b"", mime)}
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()


# 9. Unsupported File Extension (e.g. .docx)
def test_unsupported_extension():
    response = client.post(
        "/analyze",
        files={"file": ("document.docx", b"PK\x03\x04 fake docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]


# 10. End-to-end full pipeline lifecycle for TSV and ODS
def test_new_formats_transform_lifecycle():
    # Test ODS -> Analyze -> Transform
    ods_bytes = create_ods_bytes()
    res_an = client.post(
        "/analyze",
        files={"file": ("portfolio.ods", ods_bytes, "application/vnd.oasis.opendocument.spreadsheet")}
    )
    assert res_an.status_code == 200

    res_tr = client.post("/transform", json={"session_id": "default"})
    assert res_tr.status_code == 200
    tr_data = res_tr.json()
    TransformationResponse(**tr_data)
    assert tr_data["status"] == "success"
    assert tr_data["metrics"]["total_records"] == 2
