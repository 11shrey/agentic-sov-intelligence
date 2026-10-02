import os
import io
import uuid
from typing import Dict, List, Any, Tuple
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".ods", ".csv", ".tsv", ".pdf"}

def validate_excel_filename(filename: str) -> None:
    """Validate that the file has a supported spreadsheet, delimited, or PDF extension."""
    if not filename:
        raise ValueError("Filename cannot be empty.")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file extension '{ext}'. Only .xlsx, .xls, .xlsm, .ods, .csv, .tsv, and .pdf files are supported."
        )

def save_uploaded_file(file_bytes: bytes, original_filename: str, target_dir: str) -> Tuple[str, str]:
    """
    Safely saves raw uploaded file bytes to target_dir with a unique non-colliding filename.
    Returns: (unique_saved_filename, full_saved_file_path)
    """
    validate_excel_filename(original_filename)
    os.makedirs(target_dir, exist_ok=True)

    file_ext = os.path.splitext(original_filename)[1].lower()
    base_name = os.path.splitext(os.path.basename(original_filename))[0]
    safe_base = "".join(c for c in base_name if c.isalnum() or c in ("_", "-")).strip() or "uploaded_sov"
    
    unique_id = uuid.uuid4().hex[:8]
    unique_filename = f"{safe_base}_{unique_id}{file_ext}"
    full_path = os.path.join(target_dir, unique_filename)

    while os.path.exists(full_path):
        unique_id = uuid.uuid4().hex[:8]
        unique_filename = f"{safe_base}_{unique_id}{file_ext}"
        full_path = os.path.join(target_dir, unique_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return unique_filename, full_path

def load_workbook_from_bytes(file_bytes: bytes) -> openpyxl.Workbook:
    """Load an openpyxl workbook safely from bytes without executing macros."""
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    try:
        return openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, keep_vba=False)
    except Exception as e:
        raise ValueError(f"Corrupted or invalid Excel file format: {str(e)}")

def load_workbook_from_path(file_path: str) -> openpyxl.Workbook:
    """Load an openpyxl workbook safely from a file path without executing macros."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found at path: {file_path}")
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"Excel file at '{file_path}' is empty (0 bytes).")
    try:
        return openpyxl.load_workbook(file_path, data_only=True, keep_vba=False)
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


def load_delimited_rows_from_bytes(
    file_bytes: bytes,
    delimiter: str = ",",
    max_rows: int = 1000,
    max_cols: int = 100
) -> List[List[Any]]:
    """
    Safely loads delimited text (CSV/TSV) rows using standard csv reader & pandas.
    """
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
        except Exception as e:
            raise ValueError(f"Corrupted or invalid file encoding: {str(e)}")

    try:
        import csv
        import pandas as pd

        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        raw_lines = []
        for i, line in enumerate(reader):
            if i >= max_rows:
                break
            raw_lines.append(line)

        if not raw_lines:
            raise ValueError("Uploaded delimited file is empty.")

        df = pd.DataFrame(raw_lines)
        if df.empty or len(df.columns) == 0:
            raise ValueError("Uploaded file contains no data.")

        if len(df.columns) > max_cols:
            df = df.iloc[:, :max_cols]

        rows: List[List[Any]] = []
        for _, row in df.iterrows():
            row_vals = []
            for val in row:
                if val is None or pd.isna(val):
                    row_vals.append(None)
                else:
                    s_val = str(val).strip()
                    row_vals.append(s_val if s_val != "" else None)
            rows.append(row_vals)

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Corrupted or invalid delimited file format: {str(e)}")

    has_content = any(any(c is not None for c in r) for r in rows)
    if not has_content:
        raise ValueError("Uploaded file contains only empty cells.")

    return rows


def load_csv_rows_from_bytes(file_bytes: bytes, max_rows: int = 1000, max_cols: int = 100) -> List[List[Any]]:
    return load_delimited_rows_from_bytes(file_bytes, delimiter=",", max_rows=max_rows, max_cols=max_cols)

def load_csv_rows_from_path(file_path: str, max_rows: int = 1000, max_cols: int = 100) -> List[List[Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found at path: {file_path}")
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"CSV file at '{file_path}' is empty (0 bytes).")
    with open(file_path, "rb") as f:
        return load_csv_rows_from_bytes(f.read(), max_rows=max_rows, max_cols=max_cols)


def load_xls_sheets_from_bytes(file_bytes: bytes, max_rows: int = 1000, max_cols: int = 100) -> Dict[str, List[List[Any]]]:
    """Load sheets from legacy Excel (.xls) bytes using xlrd."""
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    try:
        import xlrd
        wb = xlrd.open_workbook(file_contents=file_bytes)
    except Exception as e:
        raise ValueError(f"Corrupted or invalid Excel .xls file format: {str(e)}")

    if not wb.sheet_names():
        raise ValueError("Workbook contains no sheets.")

    sheets: Dict[str, List[List[Any]]] = {}
    for sname in wb.sheet_names():
        sh = wb.sheet_by_name(sname)
        num_rows = min(sh.nrows, max_rows)
        num_cols = min(sh.ncols, max_cols)
        sheet_rows = []
        for r_idx in range(num_rows):
            row_vals = []
            for c_idx in range(num_cols):
                val = sh.cell_value(r_idx, c_idx)
                row_vals.append(None if val == "" else val)
            sheet_rows.append(row_vals)
        sheets[sname] = sheet_rows
    return sheets


def load_ods_sheets_from_bytes(file_bytes: bytes, max_rows: int = 1000, max_cols: int = 100) -> Dict[str, List[List[Any]]]:
    """Load sheets from OpenDocument Spreadsheet (.ods) bytes using pandas/odfpy."""
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")
    try:
        import pandas as pd
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes), engine="odf")
    except Exception as e:
        raise ValueError(f"Corrupted or invalid ODS file format: {str(e)}")

    if not excel_file.sheet_names:
        raise ValueError("Workbook contains no sheets.")

    import pandas as pd
    sheets: Dict[str, List[List[Any]]] = {}
    for sname in excel_file.sheet_names:
        try:
            df = pd.read_excel(excel_file, sheet_name=sname, header=None, nrows=max_rows)
            if df.empty:
                sheets[sname] = []
                continue
            if len(df.columns) > max_cols:
                df = df.iloc[:, :max_cols]
            sheet_rows = []
            for _, row in df.iterrows():
                r_vals = [None if pd.isna(v) else v for v in row]
                sheet_rows.append(r_vals)
            sheets[sname] = sheet_rows
        except Exception:
            sheets[sname] = []
    return sheets


def load_all_sheets_from_bytes(
    file_bytes: bytes,
    filename: str = "uploaded_sov.xlsx",
    max_rows: int = 1000,
    max_cols: int = 100
) -> Dict[str, List[List[Any]]]:
    """
    Universal tabular extractor that maps any supported format (.xlsx, .xls, .xlsm, .ods, .csv, .tsv, .pdf)
    into a dictionary of sheet_name -> List[List[Any]].
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    ext = os.path.splitext(filename)[1].lower() if filename else ".xlsx"
    base_stem = os.path.splitext(os.path.basename(filename))[0] if filename else "Data"

    if ext in (".xlsx", ".xlsm"):
        wb = load_workbook_from_bytes(file_bytes)
        sheets: Dict[str, List[List[Any]]] = {}
        for sname in wb.sheetnames:
            sheets[sname] = extract_sheet_rows(wb[sname], max_rows=max_rows, max_cols=max_cols)
        return sheets

    elif ext == ".xls":
        return load_xls_sheets_from_bytes(file_bytes, max_rows=max_rows, max_cols=max_cols)

    elif ext == ".ods":
        return load_ods_sheets_from_bytes(file_bytes, max_rows=max_rows, max_cols=max_cols)

    elif ext == ".tsv":
        rows = load_delimited_rows_from_bytes(file_bytes, delimiter="\t", max_rows=max_rows, max_cols=max_cols)
        return {base_stem or "TSV Data": rows}

    elif ext == ".csv":
        rows = load_delimited_rows_from_bytes(file_bytes, delimiter=",", max_rows=max_rows, max_cols=max_cols)
        return {base_stem or "CSV Data": rows}

    elif ext == ".pdf":
        from utils.pdf_utils import extract_tables_from_pdf
        return extract_tables_from_pdf(file_bytes, filename=filename, max_rows=max_rows, max_cols=max_cols)

    else:
        # Fallback to standard openpyxl if unknown
        wb = load_workbook_from_bytes(file_bytes)
        sheets = {}
        for sname in wb.sheetnames:
            sheets[sname] = extract_sheet_rows(wb[sname], max_rows=max_rows, max_cols=max_cols)
        return sheets


