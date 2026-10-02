from typing import Dict, List, Any, Union
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
from utils.excel_utils import load_workbook_from_bytes, load_workbook_from_path, extract_sheet_rows

class SOVPipelineResult(BaseModel):
    sheet_analysis: SheetIntelligenceResult
    mappings: List[SchemaMappingRecommendation]
    quality_issues: List[DataQualityIssue]

def run_sov_pipeline(
    file_input: Union[bytes, str], 
    filename: str = "uploaded_sov.xlsx",
    session_id: str = "default"
) -> SOVPipelineResult:
    """
    Integrates Agent 1 -> Agent 2 -> Agent 3 into an automated SOV analysis pipeline.
    
    Step 1: Agent 1 - Sheet Intelligence (Detect sheet & header row)
    Step 2: Agent 2 - Schema Mapping (Map column headers to standard 17 fields)
    Step 3: Agent 3 - Data Quality (Detect anomalies & quality issues without altering data)
    """
    # 1. Load Workbook safely
    if isinstance(file_input, bytes):
        wb = load_workbook_from_bytes(file_input)
    elif isinstance(file_input, str):
        wb = load_workbook_from_path(file_input)
    else:
        raise ValueError(f"Unsupported file_input type: {type(file_input)}")

    # 2. Run Agent 1: Sheet Intelligence
    sheet_analysis = analyze_workbook(wb)
    selected_sheet_name = sheet_analysis.selected_sheet
    header_row = sheet_analysis.header_row

    if selected_sheet_name not in wb.sheetnames:
        raise ValueError(f"Selected sheet '{selected_sheet_name}' not found in workbook.")

    # 3. Extract raw sheet data
    sheet = wb[selected_sheet_name]
    raw_sheet_rows = extract_sheet_rows(sheet, max_rows=1000)

    # 4. Run Agent 2: Schema Mapping
    schema_mapping_res = map_schema(raw_sheet_rows, header_row=header_row)
    mappings = schema_mapping_res.mappings

    # 5. Run Agent 3: Data Quality Analysis
    quality_res = analyze_quality(raw_sheet_rows, header_row=header_row, approved_mappings=mappings)
    quality_issues = quality_res.issues

    # 6. Store pipeline state in memory store
    state = pipeline_store.get_state(session_id)
    state.uploaded_filename = filename
    state.selected_sheet = selected_sheet_name
    state.header_row = header_row
    state.sheet_analysis = sheet_analysis
    state.schema_mappings = mappings
    state.quality_issues = quality_issues
    pipeline_store.set_state(state)

    # 7. Return combined pipeline result
    return SOVPipelineResult(
        sheet_analysis=sheet_analysis,
        mappings=mappings,
        quality_issues=quality_issues
    )
