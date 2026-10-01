import os
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from models.schemas import AuditRecord

def generate_audit_excel(audit_records: List[AuditRecord], output_path: str) -> str:
    """
    Generates a cleanly formatted Excel workbook for the Audit Log.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Audit Log"

    # Header styling
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid") # Dark slate fill
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    headers = [
        "Source Field",
        "Target Field",
        "Before Value",
        "After Value",
        "Transformation",
        "Confidence",
        "Approval Status",
        "Approver",
        "Timestamp"
    ]

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align

    # Status Fills
    approved_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Soft green
    rejected_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # Soft red
    edited_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")   # Soft yellow

    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    for record in audit_records:
        row_values = [
            record.source_field,
            record.target_field,
            str(record.before_value) if record.before_value is not None else "",
            str(record.after_value) if record.after_value is not None else "",
            record.transformation,
            f"{int(record.confidence * 100)}%",
            record.approval_status.upper(),
            record.approver,
            record.timestamp
        ]
        ws.append(row_values)
        current_row = ws.max_row

        # Apply row borders and status fill
        for col_idx in range(1, len(row_values) + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.border = thin_border
            if col_idx == 7: # Status column
                cell.font = Font(bold=True)
                if record.approval_status.lower() in ("approved", "accept", "accepted"):
                    cell.fill = approved_fill
                elif record.approval_status.lower() in ("rejected", "reject"):
                    cell.fill = rejected_fill
                elif record.approval_status.lower() in ("edited", "edit"):
                    cell.fill = edited_fill

    # Auto-fit column widths
    for col in ws.columns:
        max_len = 0
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    return output_path
