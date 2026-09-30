from typing import List, Any, Dict, Optional
from pydantic import BaseModel, Field

# Standardized 17 SOV Fields as defined in specifications
STANDARD_SOV_FIELDS: List[str] = [
    "Reference",
    "Address",
    "City",
    "State",
    "Zip",
    "County",
    "Country",
    "Building Value",
    "Contents",
    "BI",
    "Occupancy",
    "Construction",
    "Storeys",
    "Number of Buildings",
    "Year Built",
    "Fire Sprinklers (Y/N)",
    "Other",
]

class HealthResponse(BaseModel):
    status: str = "ok"

class SheetSummary(BaseModel):
    sheet_name: str
    row_count: int
    column_count: int
    sample_rows: List[List[Any]] = Field(default_factory=list)

class SheetIntelligenceResult(BaseModel):
    selected_sheet: str
    header_row: int  # 1-indexed row number
    confidence: float
    reasoning: str
    all_sheets: List[SheetSummary] = Field(default_factory=list)
