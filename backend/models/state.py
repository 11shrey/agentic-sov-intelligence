from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from models.schemas import (
    SheetIntelligenceResult,
    SchemaMappingRecommendation,
    DataQualityIssue,
    HumanReviewDecision,
    AuditRecord,
)

class PipelineState(BaseModel):
    session_id: str = "default"
    uploaded_filename: Optional[str] = None
    saved_file_path: Optional[str] = None
    selected_sheet: Optional[str] = None
    header_row: Optional[int] = None
    sheet_analysis: Optional[SheetIntelligenceResult] = None
    schema_mappings: List[SchemaMappingRecommendation] = Field(default_factory=list)
    quality_issues: List[DataQualityIssue] = Field(default_factory=list)
    human_decisions: List[HumanReviewDecision] = Field(default_factory=list)
    audit_records: List[AuditRecord] = Field(default_factory=list)
    cleaned_sov_filename: Optional[str] = None
    audit_log_filename: Optional[str] = None

class PipelineStore:
    """In-memory state storage abstraction. Easily swappable with Redis/SQL later."""
    def __init__(self):
        self._store: Dict[str, PipelineState] = {}

    def get_state(self, session_id: str = "default") -> PipelineState:
        if session_id not in self._store:
            self._store[session_id] = PipelineState(session_id=session_id)
        return self._store[session_id]

    def set_state(self, state: PipelineState) -> None:
        self._store[state.session_id] = state

    def reset(self, session_id: str = "default") -> PipelineState:
        self._store[session_id] = PipelineState(session_id=session_id)
        return self._store[session_id]

# Central in-memory store singleton for MVP
pipeline_store = PipelineStore()
