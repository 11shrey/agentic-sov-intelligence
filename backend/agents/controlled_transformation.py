import os
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from models.schemas import (
    SchemaMappingRecommendation,
    DataQualityIssue,
    HumanReviewDecision,
    AuditRecord,
    TransformationResponse,
    DashboardMetrics,
)
from models.sov_schema import STANDARD_SOV_FIELDS
from utils.audit import generate_audit_excel
from utils.excel_utils import extract_sheet_rows, load_workbook_from_path, load_workbook_from_bytes

# Deterministic Standardization Rules
def standardize_sprinklers(val: Any) -> Tuple[Optional[str], str]:
    """Standardize Fire Sprinklers value to 'Y', 'N', or None."""
    if val is None:
        return None, "empty -> None"
    val_str = str(val).strip().upper()
    if val_str in ("YES", "Y", "1", "TRUE", "SPRINKLERED", "YES - FULL"):
        return "Y", f"'{val}' -> 'Y'"
    elif val_str in ("NO", "N", "0", "FALSE", "NONE", "UNSPRINKLERED"):
        return "N", f"'{val}' -> 'N'"
    return None, f"'{val}' -> None (invalid sprinkler value)"

def standardize_numeric(val: Any) -> Tuple[Optional[Union[int, float]], str]:
    """Standardize currency/number strings to clean numeric values."""
    if val is None:
        return None, "empty -> None"
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("n/a", "null", "none", "-"):
        return None, f"'{val}' -> None"
    
    clean_str = re.sub(r'[^\d.-]', '', val_str)
    try:
        num = float(clean_str)
        # Return integer if whole number
        final_num = int(num) if num.is_integer() else num
        return final_num, f"'{val}' -> {final_num}"
    except ValueError:
        return None, f"'{val}' -> None (invalid numeric)"

def standardize_year(val: Any) -> Tuple[Optional[int], str]:
    """Standardize Year Built to a valid 4-digit integer year."""
    if val is None:
        return None, "empty -> None"
    val_str = str(val).strip()
    if val_str.isdigit() and len(val_str) == 4 and 1700 <= int(val_str) <= 2030:
        yr = int(val_str)
        return yr, f"'{val}' -> {yr}"
    return None, f"'{val}' -> None (invalid 4-digit year)"

def standardize_int(val: Any) -> Tuple[Optional[int], str]:
    """Standardize storeys / number of buildings to clean integer."""
    if val is None:
        return None, "empty -> None"
    clean_str = re.sub(r'[^\d]', '', str(val))
    if clean_str:
        num = int(clean_str)
        return num, f"'{val}' -> {num}"
    return None, f"'{val}' -> None"

def standardize_state(val: Any) -> Tuple[Optional[str], str]:
    """Standardize state code to 2-letter uppercase string."""
    if val is None:
        return None, "empty -> None"
    val_str = str(val).strip().upper()
    if len(val_str) == 2 and val_str.isalpha():
        return val_str, f"'{val}' -> '{val_str}'"
    return val_str[:2] if len(val_str) >= 2 else val_str, f"'{val}' -> '{val_str}'"

def apply_field_standardization(field_name: str, raw_val: Any) -> Tuple[Any, str]:
    """Applies deterministic standardization rules based on the target 17 SOV field."""
    if raw_val is None or str(raw_val).strip() == "":
        return None, "empty -> None"

    raw_str = str(raw_val).strip()

    if field_name == "Fire Sprinklers (Y/N)":
        return standardize_sprinklers(raw_str)
    elif field_name in ("Building Value", "Contents", "BI"):
        return standardize_numeric(raw_str)
    elif field_name == "Year Built":
        return standardize_year(raw_str)
    elif field_name in ("Storeys", "Number of Buildings"):
        return standardize_int(raw_str)
    elif field_name == "State":
        return standardize_state(raw_str)
    else:
        # String field (Address, City, Zip, Reference, Occupancy, Construction, etc.)
        return raw_str, f"'{raw_str}' -> '{raw_str}'"


def transform_data(
    raw_sheet_rows: List[List[Any]],
    header_row: int,
    mappings: List[SchemaMappingRecommendation],
    quality_issues: List[DataQualityIssue],
    human_decisions: List[HumanReviewDecision],
    approver: str = "Senior Underwriter",
    output_dir: str = "backend/outputs"
) -> TransformationResponse:
    """
    Agent 4 Engine: Controlled Transformation.
    Applies ONLY approved human decisions and deterministic standardization rules.
    Produces Cleaned_SOV.xlsx (exactly 17 fields) and Audit_Log.xlsx.
    """
    os.makedirs(output_dir, exist_ok=True)
    session_id = uuid.uuid4().hex[:8]

    # Map decisions by recommendation_id / source_column header (lowercase)
    decision_map: Dict[str, HumanReviewDecision] = {}
    for d in human_decisions:
        decision_map[d.recommendation_id.strip().lower()] = d

    # Map column index (0-indexed) to mapping details
    col_mappings: Dict[int, SchemaMappingRecommendation] = {}
    if len(raw_sheet_rows) >= header_row:
        header_cells = raw_sheet_rows[header_row - 1]
        for col_idx, cell in enumerate(header_cells):
            if cell is not None and str(cell).strip():
                col_name = str(cell).strip().lower()
                for m in mappings:
                    if m.source_column.strip().lower() == col_name:
                        col_mappings[col_idx] = m
                        break

    # Build target field column mapping dictionary: target_field -> col_idx
    target_to_col_idx: Dict[str, int] = {}
    for col_idx, m in col_mappings.items():
        if m.target_field in STANDARD_SOV_FIELDS and m.target_field != "Other":
            target_to_col_idx[m.target_field] = col_idx

    # Data rows to process
    data_rows = raw_sheet_rows[header_row:] if len(raw_sheet_rows) >= header_row else []

    output_rows: List[Dict[str, Any]] = []
    audit_records: List[AuditRecord] = []

    accepted_cnt = 0
    rejected_cnt = 0
    edited_cnt = 0
    transformations_cnt = 0

    for row_idx, row in enumerate(data_rows, start=header_row + 1):
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue

        cleaned_row_dict: Dict[str, Any] = {field: None for field in STANDARD_SOV_FIELDS}

        for target_field in STANDARD_SOV_FIELDS:
            col_idx = target_to_col_idx.get(target_field)
            raw_val = row[col_idx] if (col_idx is not None and col_idx < len(row)) else None

            mapping_obj = col_mappings.get(col_idx) if col_idx is not None else None
            source_col_name = mapping_obj.source_column if mapping_obj else target_field
            confidence = mapping_obj.confidence if mapping_obj else 1.0

            # Check human decision for this column mapping or field
            decision_key = source_col_name.strip().lower()
            human_dec = decision_map.get(decision_key) or decision_map.get(target_field.lower())

            if human_dec:
                if human_dec.decision == "reject":
                    # REJECT: Set output value to None (blank) and record rejection
                    cleaned_val = None
                    trans_desc = f"REJECTED by human -> blanked out"
                    approval_status = "rejected"
                    rejected_cnt += 1

                elif human_dec.decision == "edit":
                    # EDIT: Set output value to edited_value
                    cleaned_val = human_dec.edited_value
                    trans_desc = f"EDITED by human -> {cleaned_val}"
                    approval_status = "edited"
                    edited_cnt += 1
                    transformations_cnt += 1

                else: # "accept"
                    cleaned_val, trans_desc = apply_field_standardization(target_field, raw_val)
                    approval_status = "approved"
                    accepted_cnt += 1
                    if trans_desc and "->" in trans_desc and not trans_desc.endswith("-> 'None'"):
                        transformations_cnt += 1

            else:
                # Default behavior: If mapped with confidence >= 0.85, approve & standardize
                if mapping_obj and mapping_obj.status == "approved":
                    cleaned_val, trans_desc = apply_field_standardization(target_field, raw_val)
                    approval_status = "approved"
                    accepted_cnt += 1
                    if trans_desc and "->" in trans_desc:
                        transformations_cnt += 1
                else:
                    cleaned_val, trans_desc = apply_field_standardization(target_field, raw_val)
                    approval_status = "approved"

            cleaned_row_dict[target_field] = cleaned_val

            # Record first row sample audit records (to avoid audit log overflow for huge sheets)
            if row_idx == header_row + 1 or human_dec or (raw_val != cleaned_val and raw_val is not None):
                audit_records.append(AuditRecord(
                    source_field=source_col_name,
                    target_field=target_field,
                    before_value=raw_val,
                    after_value=cleaned_val,
                    transformation=trans_desc,
                    confidence=confidence,
                    approval_status=approval_status,
                    approver=approver
                ))

        output_rows.append(cleaned_row_dict)

    # 1. Create Cleaned_SOV.xlsx
    cleaned_filename = f"Cleaned_SOV_{session_id}.xlsx"
    cleaned_filepath = os.path.join(output_dir, cleaned_filename)

    wb_cleaned = openpyxl.Workbook()
    ws_cleaned = wb_cleaned.active
    ws_cleaned.title = "Cleaned SOV"

    # Header styling for Cleaned SOV
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0D9488", end_color="0D9488", fill_type="solid") # Teal header
    header_align = Alignment(horizontal="center", vertical="center")

    ws_cleaned.append(STANDARD_SOV_FIELDS)
    for col_idx in range(1, len(STANDARD_SOV_FIELDS) + 1):
        cell = ws_cleaned.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    for row_dict in output_rows:
        row_vals = [row_dict.get(field) for field in STANDARD_SOV_FIELDS]
        ws_cleaned.append(row_vals)

    # Auto-fit columns
    for col in ws_cleaned.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws_cleaned.column_dimensions[col_letter].width = max(max_len + 4, 14)

    wb_cleaned.save(cleaned_filepath)

    # 2. Create Audit_Log.xlsx
    audit_filename = f"Audit_Log_{session_id}.xlsx"
    audit_filepath = os.path.join(output_dir, audit_filename)
    generate_audit_excel(audit_records, audit_filepath)

    # 3. Calculate Dashboard Metrics
    total_src_cols = len(col_mappings)
    mapped_cols = len([m for m in mappings if m.target_field != "Other"])
    unmapped_cols = total_src_cols - mapped_cols
    high_severity_cnt = len([q for q in quality_issues if q.severity == "high"])

    metrics = DashboardMetrics(
        total_records=len(output_rows),
        total_source_columns=total_src_cols,
        mapped_columns=mapped_cols,
        unmapped_columns=unmapped_cols,
        quality_issues=len(quality_issues),
        high_severity_issues=high_severity_cnt,
        recommendations=len(mappings),
        accepted=accepted_cnt,
        rejected=rejected_cnt,
        edited=edited_cnt,
        transformations_applied=transformations_cnt,
        output_records=len(output_rows)
    )

    # Limit preview rows to first 10 for dashboard preview
    preview_rows = output_rows[:10]

    return TransformationResponse(
        status="success",
        message="Controlled transformation completed successfully.",
        cleaned_sov_filename=cleaned_filename,
        audit_log_filename=audit_filename,
        cleaned_sov_download_url=f"/download/{cleaned_filename}",
        audit_log_download_url=f"/download/{audit_filename}",
        metrics=metrics,
        preview_rows=preview_rows
    )
