import os
import io
import uuid
from typing import Dict, List, Any, Tuple
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

def validate_excel_filename(filename: str) -> None:
    """Validate that the file has a valid Excel extension."""
    if not filename:
        raise ValueError("Filename cannot be empty.")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Invalid file extension '{ext}'. Only .xlsx files are supported.")

def save_uploaded_file(file_bytes: bytes, original_filename: str, target_dir: str) -> Tuple[str, str]:
    """
    Safely saves raw uploaded file bytes to target_dir with a unique non-colliding filename.
    Returns: (unique_saved_filename, full_saved_file_path)
    """
    validate_excel_filename(original_filename)
    os.makedirs(target_dir, exist_ok=True)

    file_ext = os.path.splitext(original_filename)[1].lower()
    base_name = os.path.splitext(os.path.basename(original_filename))[0]
    # Remove non-alphanumeric chars from filename for safety
    safe_base = "".join(c for c in base_name if c.isalnum() or c in ("_", "-")).strip() or "uploaded_sov"
    
    unique_id = uuid.uuid4().hex[:8]
    unique_filename = f"{safe_base}_{unique_id}{file_ext}"
    full_path = os.path.join(target_dir, unique_filename)

    # Ensure no collision
    while os.path.exists(full_path):
        unique_id = uuid.uuid4().hex[:8]
        unique_filename = f"{safe_base}_{unique_id}{file_ext}"
        full_path = os.path.join(target_dir, unique_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return unique_filename, full_path

def load_workbook_from_bytes(file_bytes: bytes) -> openpyxl.Workbook:
    """Load an openpyxl workbook safely from bytes."""
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    try:
        return openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as e:
        raise ValueError(f"Corrupted or invalid Excel file format: {str(e)}")

def load_workbook_from_path(file_path: str) -> openpyxl.Workbook:
    """Load an openpyxl workbook safely from a file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found at path: {file_path}")
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"Excel file at '{file_path}' is empty (0 bytes).")
    try:
        return openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        raise ValueError(f"Corrupted or invalid Excel file format at '{file_path}': {str(e)}")

def get_sheet_dimensions(sheet: Worksheet) -> Tuple[int, int]:
    """Return max_row and max_column for a worksheet."""
    if sheet is None:
        return 0, 0
    return sheet.max_row or 0, sheet.max_column or 0

def extract_sheet_rows(sheet: Worksheet, max_rows: int = 50, max_cols: int = 100) -> List[List[Any]]:
    """Extract top N rows and M columns from a sheet as raw python lists of values."""
    if sheet is None:
        return []
    rows = []
    effective_max_row = min(sheet.max_row or 1, max_rows) if sheet.max_row else max_rows
    effective_max_col = min(sheet.max_column or 1, max_cols) if sheet.max_column else max_cols
    for row in sheet.iter_rows(max_row=effective_max_row, max_col=effective_max_col, values_only=True):
        row_values = []
        for val in row:
            if val is None:
                row_values.append(None)
            elif isinstance(val, (int, float, str, bool)):
                row_values.append(val)
            else:
                row_values.append(str(val))
        rows.append(row_values)
    return rows
