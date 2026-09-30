# Agentic SOV Intelligence System - Backend

Backend pipeline and agentic contracts for the Agentic Statement of Values (SOV) Data Intelligence & Transformation System.

## Project Purpose
Automate the ingestion, sheet detection, column schema mapping, data quality analysis, human approval workflow, and controlled transformation of insurance Statement of Values (SOV) Excel files into a standardized 17-field format with audit logging.

## Core Principle
> **"AI recommends. Humans decide. Only approved changes are transformed."**

---

## Central 17-Field Standard Schema

The single source of truth for standard SOV fields (`backend/models/sov_schema.py`):

1. **Reference**
2. **Address**
3. **City**
4. **State**
5. **Zip**
6. **County**
7. **Country**
8. **Building Value**
9. **Contents**
10. **BI** (Business Income)
11. **Occupancy**
12. **Construction**
13. **Storeys**
14. **Number of Buildings**
15. **Year Built**
16. **Fire Sprinklers (Y/N)**
17. **Other**

---

## Current Implementation Status

### Implemented:
- [x] **GET /health** — Health check
- [x] **POST /analyze** — Agent 1: Sheet Intelligence (Detects SOV sheet & header row with confidence & reasoning)
- [x] **Central SOV Schema** (`backend/models/sov_schema.py`)
- [x] **Pydantic Data Models** (`backend/models/schemas.py`) — SheetIntelligenceResult, SchemaMappingRecommendation, DataQualityIssue, HumanReviewDecision, AuditRecord
- [x] **In-Memory Pipeline State** (`backend/models/state.py`)
- [x] **API Route Stubs** (`/map`, `/quality`, `/review`, `/transform`, `/download/{filename}`)
- [x] **Sample Dataset** (`backend/sample_data/messy_sov.xlsx`)
- [x] **Comprehensive Test Suite** (`backend/tests/`) — 12 passing tests

### Not Yet Implemented (Ready for Agent Developers):
- [ ] **Agent 2 — Schema Mapping** (`POST /map`)
- [ ] **Agent 3 — Data Quality & Reasoning** (`POST /quality`)
- [ ] **Human Approval State Processing** (`POST /review`)
- [ ] **Agent 4 — Controlled Transformation & Audit Log** (`POST /transform`)

---

## Installation & Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run FastAPI Application
```bash
uvicorn main:app --reload --port 8000
```
Interactive API docs available at: `http://127.0.0.1:8000/docs`

### 3. Run Test Suite
```bash
python -m pytest tests -v
```

---

## API Endpoints Overview

| Method | Endpoint | Description | Status |
|---|---|---|---|
| `GET` | `/health` | Backend status check | Implemented |
| `POST` | `/analyze` | Upload Excel workbook and run Agent 1 | Implemented |
| `POST` | `/map` | Run Agent 2 Schema Mapping | Stub (501 Not Implemented) |
| `POST` | `/quality` | Run Agent 3 Data Quality Analysis | Stub (501 Not Implemented) |
| `POST` | `/review` | Submit human review decisions (accept/reject/edit) | Stub (501 Not Implemented) |
| `POST` | `/transform` | Run Agent 4 Controlled Transformation | Stub (501 Not Implemented) |
| `GET` | `/download/{filename}` | Download output Excel files | Implemented |

---

## Folder Structure

```
backend/
├── main.py                         # FastAPI app & endpoint route contracts
├── agents/                         # Agent modules
│   ├── __init__.py
│   ├── sheet_intelligence.py       # Agent 1 (Implemented)
│   ├── schema_mapping.py           # Agent 2 (Interface signature ready)
│   ├── data_quality.py             # Agent 3 (Interface signature ready)
│   └── controlled_transformation.py# Agent 4 (Interface signature ready)
├── models/
│   ├── __init__.py
│   ├── sov_schema.py               # Central 17 Standard SOV Fields schema
│   ├── schemas.py                  # Pydantic contract models for all agents
│   └── state.py                    # PipelineState & in-memory PipelineStore
├── utils/
│   ├── __init__.py
│   ├── excel_utils.py              # Safe openpyxl & upload utilities
│   └── audit.py                    # Audit log record generator helper
├── sample_data/
│   ├── generate_sample.py          # Script to generate sample workbook
│   └── messy_sov.xlsx              # Sample input file
├── outputs/                        # Storage for generated Cleaned_SOV & Audit files
├── uploads/                        # Temporary uploaded files directory
├── tests/                          # Automated pytest suite
│   ├── test_agent1.py
│   └── test_contracts.py
├── requirements.txt
└── README.md
```
