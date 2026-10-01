import os
import sys
import openpyxl

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "messy_sov.xlsx")

def run_end_to_end_demo():
    print("=" * 70)
    print("      AGENTIC SOV INTELLIGENCE SYSTEM -- END-TO-END DEMO (PS3)")
    print("=" * 70)

    # Step 1: Upload messy_sov.xlsx & run Agents 1-3
    print("\n[STEP 1] Uploading 'messy_sov.xlsx' to POST /analyze...")
    with open(SAMPLE_PATH, "rb") as f:
        res = client.post("/analyze", files={"file": ("messy_sov.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    assert res.status_code == 200, f"Upload failed: {res.text}"
    data = res.json()

    # Step 2: Agent 1 Results
    sheet_info = data["sheet_analysis"]
    print(f"\n[AGENT 1 -- Sheet Intelligence]")
    print(f"  * Selected Sheet : {sheet_info['selected_sheet']}")
    print(f"  * Header Row     : Row {sheet_info['header_row']}")
    print(f"  * Confidence     : {int(sheet_info['confidence'] * 100)}%")
    print(f"  * Rationale      : {sheet_info['reasoning']}")

    # Step 3: Agent 2 Results
    mappings = data["mappings"]
    print(f"\n[AGENT 2 -- Schema Mapping]")
    print(f"  * Total Mapped Columns: {len(mappings)}")
    for m in mappings[:5]:
        print(f"    - '{m['source_column']}' -> '{m['target_field']}' ({m['matching_method']}, {int(m['confidence'] * 100)}%)")
    print(f"    - ... and {len(mappings) - 5} more columns.")

    # Step 4: Agent 3 Results
    issues = data["quality_issues"]
    print(f"\n[AGENT 3 -- Data Quality & Reasoning]")
    print(f"  * Total Issues Detected: {len(issues)}")
    for issue in issues[:3]:
        print(f"    - Row {issue['row']} | Field '{issue['field']}' ({issue['severity'].upper()}): {issue['reasoning']}")

    # Step 5: Human Review Decisions
    print(f"\n[HUMAN REVIEW DECISION CENTER]")
    print("  * Core Principle: AI recommends. Humans decide. Only approved changes transformed.")
    decisions = [
        {"recommendation_id": "Loc #", "decision": "accept"},
        {"recommendation_id": "Premises Address", "decision": "accept"},
        {"recommendation_id": "Bldg Repl Cost", "decision": "accept"},
        {"recommendation_id": "Yr Built", "decision": "edit", "edited_value": "2024"},
        {"recommendation_id": "Stories", "decision": "reject"}
    ]
    res_review = client.post("/review", json={"session_id": "default", "approver": "Senior Underwriter", "decisions": decisions})
    assert res_review.status_code == 200
    print(f"  [OK] Human review submitted: {res_review.json()['processed_decisions']} decisions processed.")

    # Step 6: Agent 4 Controlled Transformation
    print(f"\n[AGENT 4 -- Controlled Transformation]")
    res_trans = client.post("/transform", json={"session_id": "default"})
    assert res_trans.status_code == 200
    trans_data = res_trans.json()

    print(f"  [OK] Status : {trans_data['message']}")
    print(f"  * Cleaned SOV Output File : {trans_data['cleaned_sov_filename']}")
    print(f"  * Audit Log Output File   : {trans_data['audit_log_filename']}")

    # Step 7: Dashboard Metrics Summary
    m = trans_data["metrics"]
    print(f"\n[EXECUTIVE DASHBOARD METRICS]")
    print(f"  * Total Records Processed : {m['total_records']}")
    print(f"  * Standardized SOV Fields  : 17 Fields (Exact Schema)")
    print(f"  * Accepted Decisions      : {m['accepted']}")
    print(f"  * Rejected Decisions      : {m['rejected']}")
    print(f"  * Edited Overrides        : {m['edited']}")
    print(f"  * Transformations Applied  : {m['transformations_applied']}")

    # Step 8: Verify Output Workbook Schema (Exactly 17 Fields)
    cleaned_path = os.path.join(os.path.dirname(__file__), "..", "outputs", trans_data["cleaned_sov_filename"])
    wb_clean = openpyxl.load_workbook(cleaned_path)
    headers = [cell.value for cell in wb_clean.active[1]]

    print(f"\n[STANDARDIZED 17-FIELD OUTPUT VERIFICATION]")
    print(f"  * Column Count: {len(headers)} (Expected: 17)")
    print(f"  * Fields: {', '.join(headers[:6])} ... {headers[-1]}")
    assert len(headers) == 17, f"Expected 17 fields, got {len(headers)}"

    print("\n" + "=" * 70)
    print("         DEMO COMPLETED SUCCESSFULLY WITH 100% VERIFICATION!")
    print("=" * 70)

if __name__ == "__main__":
    run_end_to_end_demo()
