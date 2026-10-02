from typing import Dict, List, Any, Tuple, Union, Optional
import os
import re
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from models.schemas import SheetIntelligenceResult, SheetSummary
from utils.excel_utils import (
    extract_sheet_rows,
    get_sheet_dimensions,
    load_workbook_from_bytes,
    load_workbook_from_path,
    load_csv_rows_from_bytes,
    load_csv_rows_from_path
)

SOV_HEADER_KEYWORDS = [
    "loc", "location", "ref", "reference", "address", "premises", "street", 
    "city", "town", "state", "st", "zip", "zip code", "postal", "county", 
    "country", "bldg", "building", "value", "repl cost", "replacement cost", 
    "contents", "bi", "business income", "occupancy", "use", "construction", 
    "const", "stories", "storeys", "year built", "yr built", "fire", 
    "sprinkler", "fire prot", "protection", "limit", "premium", "tiv",
    "total insured value", "square feet", "sqft", "sq ft"
]

POSITIVE_SHEET_KEYWORDS = ["property", "sov", "schedule", "values", "location", "premises", "data", "building", "asset", "locations", "properties", "statement"]
NEGATIVE_SHEET_KEYWORDS = ["instruction", "summary", "cover", "meta", "readme", "config", "notes", "index", "template", "guidance", "toc", "instructions", "help"]


def analyze_sheet_header(rows: List[List[Any]]) -> Tuple[int, float, List[str]]:
    """
    Analyzes top rows of a sheet to detect the header row index (1-based), header score, and matched SOV keywords.
    Scans up to top 20 rows and handles title blocks, metadata, and blank rows.
    """
    if not rows:
        return 1, 0.0, []

    best_row_idx = 1
    best_score = -1.0
    best_matches: List[str] = []

    max_check_rows = min(20, len(rows))

    for idx in range(max_check_rows):
        row = rows[idx]
        if not row:
            continue

        non_empty_cells = [c for c in row if c is not None and str(c).strip() != ""]
        if not non_empty_cells:
            continue

        string_cells = [str(c).strip() for c in non_empty_cells if not isinstance(c, (int, float))]
        numeric_cells = [c for c in non_empty_cells if isinstance(c, (int, float))]

        matched_keywords = []
        for cell_str in string_cells:
            cell_lower = cell_str.lower()
            for kw in SOV_HEADER_KEYWORDS:
                if len(kw) <= 3:
                    if re.search(r'\b' + re.escape(kw) + r'\b', cell_lower):
                        matched_keywords.append(cell_str)
                        break
                else:
                    if kw in cell_lower:
                        matched_keywords.append(cell_str)
                        break

        header_width = len(non_empty_cells)
        # Title block penalty: Single cell or tiny cell count rows with few matches
        if header_width <= 2 and len(matched_keywords) <= 1:
            score = -2.0 + (len(matched_keywords) * 1.0)
        else:
            score = (len(matched_keywords) * 4.0) + (len(string_cells) * 1.0) - (len(numeric_cells) * 2.5)

        # Look ahead for data row indicators below
        if idx + 1 < len(rows):
            next_row = rows[idx + 1]
            next_non_empty = [c for c in next_row if c is not None and str(c).strip() != ""]
            if len(next_non_empty) >= max(2, len(non_empty_cells) * 0.4):
                score += 3.0

        if score > best_score:
            best_score = score
            best_row_idx = idx + 1
            best_matches = matched_keywords

    return best_row_idx, max(0.0, best_score), best_matches


def evaluate_sheets_data(sheets_data: Dict[str, List[List[Any]]]) -> SheetIntelligenceResult:
    """
    Core evaluation engine that scores one or more sheets/tables, detects the primary SOV table and header row,
    and returns SheetIntelligenceResult.
    """
    if not sheets_data:
        raise ValueError("Workbook contains no sheets.")

    sheet_summaries: List[SheetSummary] = []
    sheet_scores: Dict[str, float] = {}
    sheet_header_info: Dict[str, Tuple[int, List[str]]] = {}

    for name, rows in sheets_data.items():
        max_row = len(rows)
        max_col = max(len(r) for r in rows) if rows else 0
        sample_rows = rows[:5]

        sheet_summaries.append(
            SheetSummary(
                sheet_name=name,
                row_count=max_row,
                column_count=max_col,
                sample_rows=sample_rows
            )
        )

        name_lower = name.lower()
        title_bonus = 0.0
        if any(kw in name_lower for kw in POSITIVE_SHEET_KEYWORDS):
            title_bonus += 5.0
        if any(kw in name_lower for kw in NEGATIVE_SHEET_KEYWORDS):
            title_bonus -= 10.0

        header_row, h_score, matched_kws = analyze_sheet_header(rows)

        if matched_kws or title_bonus > 0:
            data_rows_count = max(0, max_row - header_row)
            size_bonus = min(5.0, data_rows_count * 0.5) if max_row > 1 else 0.0
        else:
            size_bonus = 0.0

        total_sheet_score = title_bonus + h_score + size_bonus
        if not matched_kws and any(kw in name_lower for kw in NEGATIVE_SHEET_KEYWORDS):
            total_sheet_score -= 10.0

        if not matched_kws and title_bonus <= 0:
            total_sheet_score = 0.0

        sheet_scores[name] = total_sheet_score
        sheet_header_info[name] = (header_row, matched_kws)

    selected_sheet = max(sheet_scores, key=lambda s: sheet_scores[s])
    selected_header_row, matched_kws = sheet_header_info[selected_sheet]
    selected_score = sheet_scores[selected_sheet]

    if selected_score <= 0.0:
        raise ValueError("No valid Statement of Values (SOV) sheet detected in workbook.")

    confidence = min(0.98, max(0.50, round(0.50 + (selected_score / 25.0), 2)))

    kw_list_str = ", ".join([f"'{k}'" for k in matched_kws[:5]]) if matched_kws else "property records"
    reasoning = (
        f"The sheet '{selected_sheet}' was selected because it contains property-level records and "
        f"SOV-related column headers (e.g. {kw_list_str}) with a header detected at row {selected_header_row}."
    )

    return SheetIntelligenceResult(
        selected_sheet=selected_sheet,
        header_row=selected_header_row,
        confidence=confidence,
        reasoning=reasoning,
        sheets=sheet_summaries,
        all_sheets=sheet_summaries
    )


def run_sheet_intelligence(wb: openpyxl.Workbook) -> SheetIntelligenceResult:
    """
    Evaluates all sheets in an openpyxl workbook. Guarantees original workbook immutability.
    """
    if wb is None:
        raise ValueError("Workbook input cannot be None.")
    if not wb.sheetnames:
        raise ValueError("Workbook contains no sheets.")
    sheets_data = {name: extract_sheet_rows(wb[name], max_rows=50) for name in wb.sheetnames}
    return evaluate_sheets_data(sheets_data)


def run_csv_intelligence(
    csv_input: Union[bytes, str],
    sheet_name: str = "CSV Data",
    max_rows: int = 1000,
    max_cols: int = 100
) -> SheetIntelligenceResult:
    """
    Evaluates CSV tabular data as a single logical sheet.
    """
    if csv_input is None:
        raise ValueError("CSV input cannot be None.")
    if isinstance(csv_input, bytes):
        rows = load_csv_rows_from_bytes(csv_input, max_rows=max_rows, max_cols=max_cols)
    elif isinstance(csv_input, str):
        rows = load_csv_rows_from_path(csv_input, max_rows=max_rows, max_cols=max_cols)
    else:
        raise ValueError(f"Unsupported CSV input type: {type(csv_input)}")
    return evaluate_sheets_data({sheet_name: rows})


def analyze_workbook(
    file_input: Union[openpyxl.Workbook, bytes, str],
    filename: Optional[str] = None
) -> SheetIntelligenceResult:
    """
    Main entry point for Agent 1. Accepts openpyxl Workbook, raw bytes, or file path string
    supporting .xlsx, .xls, .xlsm, .ods, .csv, .tsv, and .pdf files.
    """
    if file_input is None:
        raise ValueError("File input cannot be None.")

    if isinstance(file_input, openpyxl.Workbook):
        return run_sheet_intelligence(file_input)
    elif isinstance(file_input, str):
        fname = filename or os.path.basename(file_input)
        from utils.excel_utils import load_all_sheets_from_bytes
        with open(file_input, "rb") as f:
            file_bytes = f.read()
        sheets_data = load_all_sheets_from_bytes(file_bytes, filename=fname)
        return evaluate_sheets_data(sheets_data)
    elif isinstance(file_input, bytes):
        fname = filename or "uploaded_sov.xlsx"
        from utils.excel_utils import load_all_sheets_from_bytes
        sheets_data = load_all_sheets_from_bytes(file_input, filename=fname)
        return evaluate_sheets_data(sheets_data)
    else:
        raise ValueError(f"Unsupported file_input type: {type(file_input)}")


