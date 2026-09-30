# Agentic SOV Intelligence System - Backend

Backend API for the Agentic Statement of Values (SOV) Data Intelligence & Transformation System.

## Architecture

```
backend/
├── main.py                         # FastAPI application & API endpoints
├── agents/                         # Agentic modules
│   ├── __init__.py
│   ├── sheet_intelligence.py       # Agent 1: Sheet & Header Intelligence
│   ├── schema_mapping.py           # Agent 2: Schema Mapping (Placeholder)
│   ├── data_quality.py             # Agent 3: Quality & Reasoning (Placeholder)
│   └── controlled_transformation.py# Agent 4: Controlled Transformation (Placeholder)
├── models/
│   ├── __init__.py
│   └── schemas.py                  # Pydantic schemas & 17 Standard SOV Fields
├── utils/
│   ├── __init__.py
│   ├── excel_utils.py              # Excel reading/inspection utilities
│   └── audit.py                    # Audit log generator (Placeholder)
├── sample_data/
│   └── messy_sov.xlsx              # Realistic sample messy SOV Excel file
├── outputs/                        # Storage for generated Cleaned_SOV & Audit files
├── requirements.txt
└── README.md
```

## Standard 17-Field Schema

1. Reference
2. Address
3. City
4. State
5. Zip
6. County
7. Country
8. Building Value
9. Contents
10. BI
11. Occupancy
12. Construction
13. Storeys
14. Number of Buildings
15. Year Built
16. Fire Sprinklers (Y/N)
17. Other

## Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

### 3. API Endpoints

- `GET /health` - Health check status
- `POST /analyze` - Upload Excel file to run Agent 1 Sheet Intelligence
