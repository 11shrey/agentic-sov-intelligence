from typing import Dict, List, Any, Union, Tuple
import os
from pydantic import BaseModel, Field

from models.schemas import (
    SheetIntelligenceResult,
    SchemaMappingRecommendation,
    DataQualityIssue,
    DataQualityResponse,
    SchemaMappingResponse,
)
from models.state import pipeline_store, PipelineState
from agents.sheet_intelligence import analyze_workbook
from agents.schema_mapping import map_schema
from agents.data_quality import analyze_quality
from utils.excel_utils import (
    load_workbook_from_bytes,
    load_workbook_from_path,
    extract_sheet_rows,
    load_csv_rows_from_bytes,
    load_csv_rows_from_path,
    load_all_sheets_from_bytes
)

class SOVPipelineResult(BaseModel):
    sheet_analysis: SheetIntelligenceResult
    mappings: List[SchemaMappingRecommendation]
    quality_issues: List[DataQualityIssue]


def run_agent1_agent2(
    file_input: Union[bytes, str],
    filename: str = "uploaded_sov.xlsx",
    max_rows: int = 1000
) -> Tuple[SheetIntelligenceResult, SchemaMappingResponse]:
    """
    Adapter orchestrating Agent 1 (Sheet Intelligence) -> Agent 2 (Schema Mapping).
    
    1. Runs Agent 1 on input file bytes/path to produce a JSON-compatible SheetIntelligenceResult.
    2. Extracts selected_sheet and header_row from Agent 1's structured contract.
    3. Retrieves complete parsed tabular rows for the selected sheet (ensuring rows beyond row 5 are loaded).
    4. Passes complete sheet rows and 1-indexed header_row to Agent 2 (map_schema).
    5. Returns both (SheetIntelligenceResult, SchemaMappingResponse).
    """
    if isinstance(file_input, str):
        if not os.path.exists(file_input):
            raise FileNotFoundError(f"File not found at path: {file_input}")
        with open(file_input, "rb") as f:
            file_bytes = f.read()
        fname = filename or os.path.basename(file_input)
    elif isinstance(file_input, bytes):
        file_bytes = file_input
        fname = filename or "uploaded_sov.xlsx"
    else:
        raise ValueError(f"Unsupported file_input type: {type(file_input)}")

    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    # 1. Run Agent 1: Sheet Intelligence
    sheet_analysis: SheetIntelligenceResult = analyze_workbook(file_bytes, filename=fname)

    # 2. JSON-compatible structured contract
    agent1_contract = sheet_analysis.model_dump()
    selected_sheet_name = agent1_contract["selected_sheet"]
    header_row = agent1_contract["header_row"]

    # 3. Retrieve complete parsed rows for the selected sheet (ensures header rows > 5 receive full data)
    sheets_data = load_all_sheets_from_bytes(file_bytes, filename=fname, max_rows=max_rows)
    if selected_sheet_name in sheets_data:
        raw_sheet_rows = sheets_data[selected_sheet_name]
    elif sheets_data:
        raw_sheet_rows = list(sheets_data.values())[0]
    else:
        raw_sheet_rows = []

    # 4. Run Agent 2: Schema Mapping
    schema_mapping_res = map_schema(raw_sheet_rows, header_row=header_row)
    schema_mapping_res.selected_sheet = selected_sheet_name

    return sheet_analysis, schema_mapping_res


def run_sov_pipeline(
    file_input: Union[bytes, str], 
    filename: str = "uploaded_sov.xlsx",
    session_id: str = "default"
) -> SOVPipelineResult:
    """
    Integrates Agent 1 -> Agent 2 -> Agent 3 into an automated SOV analysis pipeline.
    Supports Excel (.xlsx, .xls, .xlsm), OpenDocument (.ods), Delimited (.csv, .tsv), and PDF (.pdf) files.
    
    Step 1: Agent 1 - Sheet Intelligence (Detect sheet & header row)
    Step 2: Agent 2 - Schema Mapping (Map column headers to standard 17 fields)
    Step 3: Agent 3 - Data Quality (Detect anomalies & quality issues without altering data)
    """
    if isinstance(file_input, str):
        if not os.path.exists(file_input):
            raise FileNotFoundError(f"File not found at path: {file_input}")
        with open(file_input, "rb") as f:
            file_bytes = f.read()
        fname = filename or os.path.basename(file_input)
    elif isinstance(file_input, bytes):
        file_bytes = file_input
        fname = filename or "uploaded_sov.xlsx"
    else:
        raise ValueError(f"Unsupported file_input type: {type(file_input)}")

    # 1 & 2. Run Integrated Agent 1 -> Agent 2 orchestration
    sheet_analysis, schema_mapping_res = run_agent1_agent2(file_bytes, filename=fname, max_rows=1000)
    selected_sheet_name = sheet_analysis.selected_sheet
    header_row = sheet_analysis.header_row
    mappings = schema_mapping_res.mappings

    # Retrieve full raw sheet rows for downstream Agent 3 analysis
    sheets_data = load_all_sheets_from_bytes(file_bytes, filename=fname, max_rows=1000)
    raw_sheet_rows = sheets_data.get(selected_sheet_name, list(sheets_data.values())[0] if sheets_data else [])

    # 3. Run Agent 3: Data Quality Analysis
    quality_res = analyze_quality(raw_sheet_rows, header_row=header_row, approved_mappings=mappings)
    quality_issues = quality_res.issues

    # 4. Store pipeline state in memory store
    state = pipeline_store.get_state(session_id)
    state.uploaded_filename = fname
    state.selected_sheet = selected_sheet_name
    state.header_row = header_row
    state.sheet_analysis = sheet_analysis
    state.schema_mappings = mappings
    state.quality_issues = quality_issues
    pipeline_store.set_state(state)

    # 5. Return combined pipeline result
    return SOVPipelineResult(
        sheet_analysis=sheet_analysis,
        mappings=mappings,
        quality_issues=quality_issues
    )
