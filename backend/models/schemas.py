from typing import List, Any, Dict, Optional, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, model_validator

from models.sov_schema import STANDARD_SOV_FIELDS, is_valid_sov_field

class HealthResponse(BaseModel):
    status: str = "ok"

class NotImplementedResponse(BaseModel):
    status: str = "not_implemented"
    message: str

# --- A. Sheet Intelligence Result ---

class SheetSummary(BaseModel):
    sheet_name: str
    row_count: int
    column_count: int
    sample_rows: List[List[Any]] = Field(default_factory=list)

class SheetIntelligenceResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    selected_sheet: str
    header_row: int  # 1-indexed row number
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    sheets: List[SheetSummary] = Field(default_factory=list)
    all_sheets: List[SheetSummary] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_sheet_lists(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "all_sheets" in data and "sheets" not in data:
                data["sheets"] = data["all_sheets"]
            elif "sheets" in data and "all_sheets" not in data:
                data["all_sheets"] = data["sheets"]
        return data

# --- B. Schema Mapping Recommendation ---

class SchemaMappingRecommendation(BaseModel):
    source_column: str
    target_field: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    matching_method: str  # e.g., "exact", "alias", "normalized", "fuzzy", "default"
    reasoning: str
    status: Literal["approved", "rejected", "needs_review"] = "needs_review"

class SchemaMappingResponse(BaseModel):
    selected_sheet: str
    mappings: List[SchemaMappingRecommendation]

# --- C. Data Quality Issue ---

class DataQualityIssue(BaseModel):
    row: int
    field: str
    value: Optional[Any] = None
    issue_type: str
    severity: Literal["low", "medium", "high"]
    reasoning: str
    recommendation: str

class DataQualityResponse(BaseModel):
    total_issues: int
    issues: List[DataQualityIssue]

# --- D. Human Review Decision ---

class HumanReviewDecision(BaseModel):
    recommendation_id: str  # maps to source_column or field name
    decision: Literal["accept", "reject", "edit"]
    edited_value: Optional[Any] = None
    approver: Optional[str] = "human"

    @model_validator(mode="after")
    def check_edited_value_required_for_edit(self):
        if self.decision == "edit":
            if self.edited_value is None or (isinstance(self.edited_value, str) and self.edited_value.strip() == ""):
                raise ValueError("edited_value is required when decision is 'edit'.")
        return self

class HumanReviewRequest(BaseModel):
    session_id: str = "default"
    approver: Optional[str] = "Senior Underwriter"
    decisions: List[HumanReviewDecision]

class HumanReviewResponse(BaseModel):
    status: str = "success"
    processed_decisions: int
    accepted: int
    rejected: int
    edited: int
    approver: str

# --- E. Audit Record ---

class AuditRecord(BaseModel):
    source_field: str
    target_field: str
    before_value: Optional[Any] = None
    after_value: Optional[Any] = None
    transformation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    approval_status: str  # "approved", "rejected", "edited"
    approver: str = "human"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# --- F. Transformation & Dashboard Metrics ---

class DashboardMetrics(BaseModel):
    total_records: int
    total_source_columns: int
    mapped_columns: int
    unmapped_columns: int
    quality_issues: int
    high_severity_issues: int
    recommendations: int
    accepted: int
    rejected: int
    edited: int
    transformations_applied: int
    output_records: int

class TransformationResponse(BaseModel):
    status: str = "success"
    message: str = "Controlled transformation completed successfully."
    cleaned_sov_filename: str
    audit_log_filename: str
    cleaned_sov_download_url: str
    audit_log_download_url: str
    metrics: DashboardMetrics
    preview_rows: List[Dict[str, Any]] = Field(default_factory=list)
