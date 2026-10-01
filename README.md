# Agentic SOV Intelligence System for Insurance

> **Problem Statement: PS3**  
> **Core Principle:** *"AI recommends. Humans decide. Only approved changes are transformed."*

An enterprise AI Statement of Values (SOV) data intelligence, human review approval workflow, and controlled transformation pipeline for insurance underwriters and risk analysts.

---

## Architecture Overview

```
                        Excel SOV Upload (.xlsx)
                                   │
                                   ▼
                      Agent 1 — Sheet Intelligence
                        (Sheet & Header Detection)
                                   │
                                   ▼
                       Agent 2 — Schema Mapping
               (Exact, Alias, Normalized & RapidFuzz Match)
                                   │
                                   ▼
                   Agent 3 — Data Quality & Reasoning
             (Read-Only Anomaly & Quality Issue Detection)
                                   │
                                   ▼
                      Human Review Decision Center
                    [ ACCEPT ]  [ REJECT ]  [ EDIT ]
                                   │
                                   ▼
                   Agent 4 — Controlled Transformation
            (Applies Approved Decisions & Deterministic Rules)
                                   │
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
        Cleaned_SOV.xlsx                     Audit_Log.xlsx
   (Exactly 17 Standard Fields)        (Full Traceability Log)
                 │                                   │
                 └─────────────────┬─────────────────┘
                                   ▼
                     Executive Dashboard Analytics
```

---

## Centralized 17-Field Standard Schema

The output `Cleaned_SOV.xlsx` is guaranteed to contain **exactly** these 17 fields:

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

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup & Run

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run pytest test suite (16 tests)
python -m pytest tests -v

# Run backend API server
python main.py
```

Backend server runs at: `http://127.0.0.1:8000`  
Interactive API Docs (Swagger): `http://127.0.0.1:8000/docs`

### 3. Frontend Setup & Run

```bash
cd frontend

# Install packages
npm install

# Run Vite development server
npm run dev
```

Frontend UI runs at: `http://127.0.0.1:3000`

---

## Running the End-to-End Demo Script

To execute the automated demo using `backend/sample_data/messy_sov.xlsx`:

```bash
python backend/sample_data/run_demo.py
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/schema` | Returns central 17 Standard SOV Fields |
| `POST` | `/analyze` | Upload `.xlsx` and run Agents 1-3 pipeline |
| `POST` | `/map` | Run Agent 2 Schema Mapping |
| `POST` | `/quality` | Run Agent 3 Data Quality Analysis |
| `POST` | `/review` | Submit human review decisions (`accept`, `reject`, `edit`) |
| `POST` | `/transform` | Run Agent 4 Controlled Transformation & generate files |
| `GET` | `/download/{filename}` | Download `Cleaned_SOV.xlsx` or `Audit_Log.xlsx` |

---

## Testing

Run all automated pytest suites:

```bash
python -m pytest backend/tests -v
```

All 16 test cases pass 100%.
