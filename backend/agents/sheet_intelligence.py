from typing import Dict, List, Any, Tuple
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
from models.schemas import SheetIntelligenceResult, SheetSummary
from utils.excel_utils import extract_sheet_rows, get_sheet_dimensions

# Keywords commonly present in SOV headers
SOV_HEADER_KEYWORDS = [
    "loc", "location", "ref", "reference", "address", "premises", "street", 
    "city", "town", "state", "st", "zip", "zip code", "postal", "county", 
    "country", "bldg", "building", "value", "repl cost", "replacement cost", 
    "contents", "bi", "business income", "occupancy", "use", "construction", 
    "const", "stories", "storeys", "year built", "yr built", "fire", 
    "sprinkler", "fire prot", "protection"
]

POSITIVE_SHEET_KEYWORDS = ["property", "sov", "schedule", "values", "location", "premises", "data", "building", "asset"]
NEGATIVE_SHEET_KEYWORDS = ["instruction", "summary", "cover", "meta", "readme", "config", "notes", "index", "template", "guidance"]

def analyze_sheet_header(rows: List[List[Any]]) -> Tuple[int, float, List[str]]:
    """
    Inspects top rows of a sheet to detect the header row index (1-indexed) and header score.
    Returns: (best_header_row_1indexed, header_score, list_of_matched_keywords)
    """
    if not rows:
        return 1, 0.0, []

    best_row_idx = 1
    best_score = -1.0
    best_matches: List[str] = []

    # Check top 15 rows for potential header row
    max_check_rows = min(15, len(rows))

    for idx in range(max_check_rows):
        row = rows[idx]
        if not row:
            continue

        non_empty_cells = [c for c in row if c is not None and str(c).strip() != ""]
        if not non_empty_cells:
            continue

        # Count text string cells vs numeric cells
        string_cells = [str(c).strip() for c in non_empty_cells if not isinstance(c, (int, float))]
        numeric_cells = [c for c in non_empty_cells if isinstance(c, (int, float))]

        matched_keywords = []
        for cell_str in string_cells:
            cell_lower = cell_str.lower()
            for kw in SOV_HEADER_KEYWORDS:
                if kw in cell_lower:
                    matched_keywords.append(cell_str)
                    break

        # Header scoring heuristic:
        # Heavily reward SOV keyword matches and distinct non-empty string column headers
        score = (len(matched_keywords) * 3.0) + (len(string_cells) * 0.5) - (len(numeric_cells) * 2.0)

        # Bonus if subsequent row (idx + 1) has numeric or structured data
        if idx + 1 < len(rows):
            next_row = rows[idx + 1]
            next_non_empty = [c for c in next_row if c is not None and str(c).strip() != ""]
            if len(next_non_empty) >= len(non_empty_cells) * 0.5:
                score += 2.0

        if score > best_score:
            best_score = score
            best_row_idx = idx + 1  # 1-indexed
            best_matches = matched_keywords

    return best_row_idx, max(0.0, best_score), best_matches


def run_sheet_intelligence(wb: openpyxl.Workbook) -> SheetIntelligenceResult:
    """
    Agent 1: Inspects workbook sheets, detects the most likely SOV sheet and header row,
    calculates confidence, and explains the reasoning.
    """
    sheet_names = wb.sheetnames
    if not sheet_names:
        raise ValueError("Workbook contains no sheets.")

    sheet_summaries: List[SheetSummary] = []
    sheet_scores: Dict[str, float] = {}
    sheet_header_info: Dict[str, Tuple[int, List[str]]] = {}

    for name in sheet_names:
        sheet: Worksheet = wb[name]
        max_row, max_col = get_sheet_dimensions(sheet)
        rows = extract_sheet_rows(sheet, max_rows=50)

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

        # Require a reasonable row count for an SOV sheet
        data_rows_count = max(0, max_row - header_row)
        size_bonus = min(5.0, data_rows_count * 0.5)

        total_sheet_score = title_bonus + h_score + size_bonus
        sheet_scores[name] = total_sheet_score
        sheet_header_info[name] = (header_row, matched_kws)

    # Select the sheet with highest total score
    selected_sheet = max(sheet_scores, key=lambda s: sheet_scores[s])
    selected_header_row, matched_kws = sheet_header_info[selected_sheet]

    selected_score = sheet_scores[selected_sheet]
    
    # Calculate confidence score between 0.0 and 1.0
    if selected_score <= 0:
        confidence = 0.30
    else:
        # Normalized confidence calculation
        confidence = min(0.98, max(0.50, round(0.50 + (selected_score / 25.0), 2)))

    # Construct reasoning text
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
        all_sheets=sheet_summaries
    )
