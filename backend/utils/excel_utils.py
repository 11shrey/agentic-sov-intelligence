import io
from typing import Dict, List, Any, Union, Tuple
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

def load_workbook_from_bytes(file_bytes: bytes) -> openpyxl.Workbook:
    """Load an openpyxl workbook safely from bytes."""
    return openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)

def load_workbook_from_path(file_path: str) -> openpyxl.Workbook:
    """Load an openpyxl workbook safely from a file path."""
    return openpyxl.load_workbook(file_path, data_only=True)

def get_sheet_dimensions(sheet: Worksheet) -> Tuple[int, int]:
    """Return max_row and max_column for a worksheet."""
    return sheet.max_row or 0, sheet.max_column or 0

def extract_sheet_rows(sheet: Worksheet, max_rows: int = 50) -> List[List[Any]]:
    """Extract top N rows from a sheet as raw python lists of values."""
    rows = []
    for row in sheet.iter_rows(max_row=max_rows, values_only=True):
        # Convert non-serializable objects (like datetime) to str
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
