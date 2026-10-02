import io
import re
from typing import Dict, List, Any, Optional

def extract_tables_from_pdf(
    pdf_bytes: bytes,
    filename: str = "document.pdf",
    max_rows: int = 1000,
    max_cols: int = 100
) -> Dict[str, List[List[Any]]]:
    """
    Extracts text and table rows from a text-based PDF file.
    If the PDF is scanned or image-only (no extractable text), raises a clear ValueError.
    """
    if not pdf_bytes or len(pdf_bytes.strip()) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    try:
        import pypdf
    except ImportError:
        raise ValueError("PDF parsing dependency 'pypdf' is not installed.")

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Corrupted or invalid PDF file format: {str(e)}")

    if not reader.pages or len(reader.pages) == 0:
        raise ValueError("PDF file contains no pages.")

    sheets_data: Dict[str, List[List[Any]]] = {}
    total_extracted_chars = 0

    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_name = f"Page {page_num}"

        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        total_extracted_chars += len(page_text.strip())
        if not page_text.strip():
            continue

        raw_lines = page_text.splitlines()
        page_rows: List[List[Any]] = []

        for line in raw_lines:
            if len(page_rows) >= max_rows:
                break
            line_str = line.strip()
            if not line_str:
                continue

            # Split line into columns using 2+ spaces, tabs, or pipe/comma delimiters
            if "\t" in line_str:
                cells = [c.strip() for c in line_str.split("\t")]
            elif "  " in line_str:
                cells = [c.strip() for c in re.split(r"\s{2,}", line_str)]
            elif "|" in line_str:
                cells = [c.strip() for c in line_str.split("|")]
            elif "," in line_str:
                cells = [c.strip() for c in line_str.split(",")]
            else:
                cells = [line_str]

            # Filter or pad cells
            cleaned_cells = [c if c != "" else None for c in cells[:max_cols]]
            if any(c is not None for c in cleaned_cells):
                page_rows.append(cleaned_cells)

        if page_rows:
            sheets_data[page_name] = page_rows

    if total_extracted_chars == 0 or not sheets_data:
        raise ValueError(
            "Scanned or image-only PDF detected: no extractable text or tables found. "
            "OCR is required to process scanned PDFs."
        )

    return sheets_data
