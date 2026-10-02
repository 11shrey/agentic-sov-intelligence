import io
import os
import sys
import time
import json
from typing import Dict, List, Any

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import openpyxl
from fastapi.testclient import TestClient

from main import app
from agents.sheet_intelligence import analyze_workbook
from tests.test_agent1_testbench import (
    create_normal_sov_bytes,
    create_multisheet_sov_bytes,
    create_title_metadata_block_bytes,
    create_header_far_down_bytes,
    create_multiple_plausible_headers_bytes,
    create_irrelevant_workbook_bytes,
    create_messy_sov_bytes,
    create_wide_workbook_bytes,
    create_large_workbook_bytes,
    create_csv_sov_bytes,
    create_tsv_sov_bytes,
    create_ods_sov_bytes,
    create_xlsm_sov_bytes,
    create_text_pdf_sov_bytes,
    create_scanned_pdf_bytes,
)

client = TestClient(app)

def run_benchmarks():
    test_results = []
    
    # Track classifications
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    false_positives = 0  # Selected an SOV sheet when none existed (irrelevant inputs)
    false_negatives = 0  # Failed to select an SOV sheet when one did exist

    # --- Scenario 1: Normal SOV ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_normal_sov_bytes()
        res = analyze_workbook(data, filename="normal_sov.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Property Schedule" and res.header_row == 1 and res.confidence >= 0.85)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 1: Normal SOV Workbook",
            "format": ".xlsx",
            "expected": "Sheet='Property Schedule', Header=1, Conf>=0.85",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}, Rows={res.sheets[0].row_count}, Cols={res.sheets[0].column_count}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 1: Normal SOV Workbook", "format": ".xlsx",
            "expected": "Sheet='Property Schedule', Header=1", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 2: Multi-sheet workbook ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_multisheet_sov_bytes()
        res = analyze_workbook(data, filename="multisheet_sov.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Locations SOV" and res.header_row == 1 and res.confidence >= 0.85 and len(res.sheets) == 4)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 2: Multi-sheet SOV Selection",
            "format": ".xlsx",
            "expected": "Sheet='Locations SOV', Header=1, 4 Sheets",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}, Total Sheets={len(res.sheets)}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 2: Multi-sheet SOV Selection", "format": ".xlsx",
            "expected": "Sheet='Locations SOV'", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 3: Title & metadata block ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_title_metadata_block_bytes()
        res = analyze_workbook(data, filename="title_metadata_sov.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Portfolio SOV" and res.header_row == 6 and res.confidence >= 0.80)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 3: Title/Metadata Block Detection",
            "format": ".xlsx",
            "expected": "Sheet='Portfolio SOV', Header=6",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 3: Title/Metadata Block Detection", "format": ".xlsx",
            "expected": "Header=6", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 4: Header far down (Row 10) ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_header_far_down_bytes()
        res = analyze_workbook(data, filename="deep_header_sov.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Deep Header SOV" and res.header_row == 10 and res.confidence >= 0.80)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 4: Header Far Down (Row 10)",
            "format": ".xlsx",
            "expected": "Sheet='Deep Header SOV', Header=10",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 4: Header Far Down (Row 10)", "format": ".xlsx",
            "expected": "Header=10", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 5: Multiple plausible header rows ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_multiple_plausible_headers_bytes()
        res = analyze_workbook(data, filename="complex_hierarchy.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Complex Hierarchy SOV" and res.header_row == 3 and res.confidence >= 0.85)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 5: Multiple Plausible Header Hierarchy",
            "format": ".xlsx",
            "expected": "Sheet='Complex Hierarchy SOV', Header=3",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 5: Multiple Plausible Header Hierarchy", "format": ".xlsx",
            "expected": "Header=3", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 6: Irrelevant workbook rejection ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_irrelevant_workbook_bytes()
        dur = 0.0
        try:
            res = analyze_workbook(data, filename="employee_roster.xlsx")
            # If it didn't raise, it's a false positive!
            failed_tests += 1
            false_positives += 1
            test_results.append({
                "name": "Scenario 6: Irrelevant Workbook Rejection",
                "format": ".xlsx",
                "expected": "Controlled rejection (ValueError)",
                "actual": f"False positive selection of sheet '{res.selected_sheet}'",
                "status": "FAIL",
                "time_ms": (time.perf_counter() - t0) * 1000
            })
        except ValueError as val_err:
            dur = (time.perf_counter() - t0) * 1000
            resp = client.post("/analyze", files={"file": ("employee_roster.xlsx", data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
            passed = (resp.status_code == 400 and "no valid statement of values" in resp.json()["detail"].lower())
            if passed: passed_tests += 1
            else: failed_tests += 1
            test_results.append({
                "name": "Scenario 6: Irrelevant Workbook Rejection",
                "format": ".xlsx",
                "expected": "Rejection ValueError -> HTTP 400",
                "actual": f"Controlled rejection (400 Bad Request: {resp.json()['detail'][:45]}...)",
                "status": "PASS" if passed else "FAIL",
                "time_ms": dur
            })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1
        test_results.append({
            "name": "Scenario 6: Irrelevant Workbook Rejection", "format": ".xlsx",
            "expected": "Rejection ValueError", "actual": f"Unexpected exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 7: Messy SOV ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_messy_sov_bytes()
        res = analyze_workbook(data, filename="messy_sample.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Messy Property SOV" and res.header_row == 3 and res.confidence >= 0.75)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 7: Messy SOV Robustness",
            "format": ".xlsx",
            "expected": "Sheet='Messy Property SOV', Header=3",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 7: Messy SOV Robustness", "format": ".xlsx",
            "expected": "Header=3", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 8: Wide workbook (40 cols) ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_wide_workbook_bytes()
        res = analyze_workbook(data, filename="wide_sov.xlsx")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Wide Property Schedule" and res.header_row == 1 and res.sheets[0].column_count == 40)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 8: Wide Workbook (40 Columns)",
            "format": ".xlsx",
            "expected": "Sheet='Wide Property Schedule', Header=1, Cols=40",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Cols={res.sheets[0].column_count}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 8: Wide Workbook (40 Columns)", "format": ".xlsx",
            "expected": "Cols=40", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 9: Large-ish workbook (3500 rows) ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_large_workbook_bytes(3500)
        t_proc0 = time.perf_counter()
        res = analyze_workbook(data, filename="large_sov.xlsx")
        dur = (time.perf_counter() - t_proc0) * 1000
        passed = (res.selected_sheet == "Large Property Schedule" and res.header_row == 1 and res.sheets[0].row_count >= 1000 and dur < 2000.0)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 9: Large Workbook (3,500 Rows)",
            "format": ".xlsx",
            "expected": "Sampled Rows >= 1000, Header=1, Time < 2000ms",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Sampled Rows={res.sheets[0].row_count}, ProcTime={dur:.1f}ms",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 9: Large Workbook (3,500 Rows)", "format": ".xlsx",
            "expected": "Time < 2000ms", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 10: CSV SOV ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_csv_sov_bytes()
        res = analyze_workbook(data, filename="commercial_sov.csv")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "commercial_sov" and res.header_row == 3 and res.confidence >= 0.75)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 10: CSV Delimited SOV",
            "format": ".csv",
            "expected": "Sheet='commercial_sov', Header=3",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 10: CSV Delimited SOV", "format": ".csv",
            "expected": "Header=3", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 11a: TSV ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_tsv_sov_bytes()
        res = analyze_workbook(data, filename="tab_sov.tsv")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "tab_sov" and res.header_row == 1 and res.confidence >= 0.75)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11a: TSV Tab-Delimited SOV",
            "format": ".tsv",
            "expected": "Sheet='tab_sov', Header=1",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11a: TSV Tab-Delimited SOV", "format": ".tsv",
            "expected": "Header=1", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 11b: XLSM ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_xlsm_sov_bytes()
        res = analyze_workbook(data, filename="macro_sov.xlsm")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Macro Properties" and res.header_row == 1 and res.confidence >= 0.80)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11b: XLSM Macro-Enabled SOV",
            "format": ".xlsm",
            "expected": "Sheet='Macro Properties', Header=1",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11b: XLSM Macro-Enabled SOV", "format": ".xlsm",
            "expected": "Header=1", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 11c: ODS ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_ods_sov_bytes()
        res = analyze_workbook(data, filename="odf_sov.ods")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "ODS SOV Properties" and res.header_row == 1 and res.confidence >= 0.80)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11c: ODS OpenDocument SOV",
            "format": ".ods",
            "expected": "Sheet='ODS SOV Properties', Header=1",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11c: ODS OpenDocument SOV", "format": ".ods",
            "expected": "Header=1", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 11d: PDF (Text Table) ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_text_pdf_sov_bytes()
        res = analyze_workbook(data, filename="printed_sov.pdf")
        dur = (time.perf_counter() - t0) * 1000
        passed = (res.selected_sheet == "Page 1" and res.header_row == 1 and res.confidence >= 0.75)
        if passed: passed_tests += 1
        else: failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11d: PDF (Text-based Table)",
            "format": ".pdf",
            "expected": "Sheet='Page 1', Header=1",
            "actual": f"Sheet='{res.selected_sheet}', Header={res.header_row}, Conf={res.confidence:.2f}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur,
            "reasoning": res.reasoning
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1; false_negatives += 1
        test_results.append({
            "name": "Scenario 11d: PDF (Text-based Table)", "format": ".pdf",
            "expected": "Header=1", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 11e: PDF (Scanned / Image-only) ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        data = create_scanned_pdf_bytes()
        resp = client.post("/analyze", files={"file": ("scanned_sov.pdf", data, "application/pdf")})
        dur = (time.perf_counter() - t0) * 1000
        passed = (resp.status_code == 400 and "ocr is required" in resp.json()["detail"].lower())
        if passed: passed_tests += 1
        else: failed_tests += 1
        test_results.append({
            "name": "Scenario 11e: PDF Scanned Rejection",
            "format": ".pdf",
            "expected": "HTTP 400 with 'OCR is required'",
            "actual": f"HTTP {resp.status_code}: {resp.json()['detail']}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1
        test_results.append({
            "name": "Scenario 11e: PDF Scanned Rejection", "format": ".pdf",
            "expected": "HTTP 400 with 'OCR is required'", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 12a: Invalid Empty File ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        resp = client.post("/analyze", files={"file": ("empty.xlsx", b"", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        dur = (time.perf_counter() - t0) * 1000
        passed = (resp.status_code == 400 and "empty" in resp.json()["detail"].lower())
        if passed: passed_tests += 1
        else: failed_tests += 1
        test_results.append({
            "name": "Scenario 12a: Empty File (0 Bytes)",
            "format": ".xlsx",
            "expected": "HTTP 400 with 'empty'",
            "actual": f"HTTP {resp.status_code}: {resp.json()['detail']}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1
        test_results.append({
            "name": "Scenario 12a: Empty File (0 Bytes)", "format": ".xlsx",
            "expected": "HTTP 400", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 12b: Invalid Corrupted File ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        resp = client.post("/analyze", files={"file": ("corrupt.xlsx", b"CORRUPTED_STREAM", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        dur = (time.perf_counter() - t0) * 1000
        passed = (resp.status_code == 400 and ("corrupted" in resp.json()["detail"].lower() or "invalid" in resp.json()["detail"].lower()))
        if passed: passed_tests += 1
        else: failed_tests += 1
        test_results.append({
            "name": "Scenario 12b: Corrupt File Stream",
            "format": ".xlsx",
            "expected": "HTTP 400 with 'corrupted/invalid'",
            "actual": f"HTTP {resp.status_code}: {resp.json()['detail']}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1
        test_results.append({
            "name": "Scenario 12b: Corrupt File Stream", "format": ".xlsx",
            "expected": "HTTP 400", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 12c: Unsupported Extension ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        resp = client.post("/analyze", files={"file": ("unsupported.docx", b"PK...", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
        dur = (time.perf_counter() - t0) * 1000
        passed = (resp.status_code == 400 and "invalid file extension" in resp.json()["detail"].lower())
        if passed: passed_tests += 1
        else: failed_tests += 1
        test_results.append({
            "name": "Scenario 12c: Unsupported Extension (.docx)",
            "format": ".docx",
            "expected": "HTTP 400 with 'Invalid file extension'",
            "actual": f"HTTP {resp.status_code}: {resp.json()['detail']}",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1
        test_results.append({
            "name": "Scenario 12c: Unsupported Extension (.docx)", "format": ".docx",
            "expected": "HTTP 400", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # --- Scenario 12d: No Stack Trace Leakage ---
    total_tests += 1
    t0 = time.perf_counter()
    try:
        resp = client.post("/analyze", files={"file": ("malformed.csv", b"\x00\x00\x00\x00\xff\xfe", "text/csv")})
        dur = (time.perf_counter() - t0) * 1000
        # Either 400 or handled without traceback leakage
        has_no_traceback = "traceback" not in resp.text.lower() and "file \"/" not in resp.text.lower()
        passed = (resp.status_code in (400, 422) and has_no_traceback)
        if passed: passed_tests += 1
        else: failed_tests += 1
        test_results.append({
            "name": "Scenario 12d: API Error Traceback Guard",
            "format": ".csv",
            "expected": "No python stack trace leaked in response body",
            "actual": f"HTTP {resp.status_code}, Clean JSON Response (No tracebacks)",
            "status": "PASS" if passed else "FAIL",
            "time_ms": dur
        })
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000
        failed_tests += 1
        test_results.append({
            "name": "Scenario 12d: API Error Traceback Guard", "format": ".csv",
            "expected": "No traceback", "actual": f"Exception: {str(e)}",
            "status": "FAIL", "time_ms": dur
        })

    # Summary dictionary
    summary = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "results": test_results
    }
    
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    run_benchmarks()
