import re
from typing import List, Dict, Any, Optional
from models.schemas import DataQualityIssue, DataQualityResponse, SchemaMappingRecommendation

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
}

def clean_currency_str(val_str: str) -> Optional[float]:
    """Parse numeric currency strings like '$1,500,000' or '250000'."""
    clean = re.sub(r'[^\d.-]', '', val_str)
    try:
        return float(clean)
    except ValueError:
        return None

def analyze_quality(
    raw_data: List[List[Any]], 
    header_row: int, 
    approved_mappings: List[SchemaMappingRecommendation]
) -> DataQualityResponse:
    """
    Agent 3 Engine: Analyzes mapped SOV data rows for data quality issues & anomalies.
    Does NOT modify raw data. Returns list of DataQualityIssue items.
    """
    if not raw_data or len(raw_data) <= header_row:
        return DataQualityResponse(total_issues=0, issues=[])

    # Map column index (0-indexed) to target standard SOV field
    col_to_target: Dict[int, str] = {}
    header_cells = raw_data[header_row - 1]

    # Create mapping lookup dictionary from source column name to target field
    mapping_dict = {m.source_column.strip().lower(): m.target_field for m in approved_mappings}

    for col_idx, cell in enumerate(header_cells):
        if cell is not None and str(cell).strip():
            cell_str = str(cell).strip().lower()
            if cell_str in mapping_dict:
                col_to_target[col_idx] = mapping_dict[cell_str]

    issues: List[DataQualityIssue] = []
    seen_addresses: Dict[str, int] = {}

    # Inspect data rows starting after header_row
    for row_offset, row in enumerate(raw_data[header_row:], start=header_row + 1):
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue  # Skip completely empty rows

        row_dict: Dict[str, Any] = {}
        for col_idx, target_field in col_to_target.items():
            if col_idx < len(row):
                row_dict[target_field] = row[col_idx]

        # 1. Check Missing Critical Fields
        critical_fields = ["Address", "Building Value"]
        for field in critical_fields:
            val = row_dict.get(field)
            if val is None or str(val).strip() == "" or str(val).strip().lower() in ("n/a", "null", "none"):
                issues.append(DataQualityIssue(
                    row=row_offset,
                    field=field,
                    value=str(val) if val is not None else None,
                    issue_type="missing_value",
                    severity="high",
                    reasoning=f"Critical field '{field}' is missing or empty.",
                    recommendation=f"Provide a valid {field} value for row {row_offset}."
                ))

        # 2. Check Year Built
        if "Year Built" in row_dict:
            yr_val = row_dict.get("Year Built")
            if yr_val is not None and str(yr_val).strip() != "":
                yr_str = str(yr_val).strip()
                # Check if it's numeric 4-digit
                if not yr_str.isdigit() or len(yr_str) != 4 or int(yr_str) < 1700 or int(yr_str) > 2030:
                    issues.append(DataQualityIssue(
                        row=row_offset,
                        field="Year Built",
                        value=yr_str,
                        issue_type="invalid_year",
                        severity="high",
                        reasoning=f"Year Built '{yr_str}' is not a valid 4-digit year (1700-2030).",
                        recommendation="Review and correct Year Built to a valid four-digit year."
                    ))

        # 3. Check State Values
        if "State" in row_dict:
            st_val = row_dict.get("State")
            if st_val is not None and str(st_val).strip() != "":
                st_str = str(st_val).strip().upper()
                if st_str not in US_STATES:
                    issues.append(DataQualityIssue(
                        row=row_offset,
                        field="State",
                        value=str(st_val),
                        issue_type="invalid_state",
                        severity="medium",
                        reasoning=f"State value '{st_val}' is not a recognized 2-letter US state code.",
                        recommendation="Verify and standardize state code (e.g. NY, CA, TX)."
                    ))

        # 4. Check Zip Code
        if "Zip" in row_dict:
            zip_val = row_dict.get("Zip")
            if zip_val is not None and str(zip_val).strip() != "":
                zip_str = str(zip_val).strip()
                # Basic zip format check
                clean_zip = re.sub(r'[^\d]', '', zip_str)
                if len(clean_zip) not in (5, 9):
                    issues.append(DataQualityIssue(
                        row=row_offset,
                        field="Zip",
                        value=zip_str,
                        issue_type="malformed_zip",
                        severity="medium",
                        reasoning=f"Zip code '{zip_str}' does not conform to standard 5-digit or 9-digit format.",
                        recommendation="Format Zip code to 5 digits (e.g. 10001)."
                    ))

        # 5. Check Inconsistent Fire Sprinklers (Y/N)
        if "Fire Sprinklers (Y/N)" in row_dict:
            sp_val = row_dict.get("Fire Sprinklers (Y/N)")
            if sp_val is not None and str(sp_val).strip() != "":
                sp_str = str(sp_val).strip()
                if sp_str.upper() not in ("Y", "N"):
                    issues.append(DataQualityIssue(
                        row=row_offset,
                        field="Fire Sprinklers (Y/N)",
                        value=sp_str,
                        issue_type="inconsistent_yes_no",
                        severity="medium",
                        reasoning=f"Fire Sprinklers value '{sp_str}' should be standardized to 'Y' or 'N'.",
                        recommendation="Standardize value to 'Y' or 'N'."
                    ))

        # 6. Check Formatted Currency Strings in Values
        numeric_fields = ["Building Value", "Contents", "BI"]
        for num_field in numeric_fields:
            if num_field in row_dict:
                n_val = row_dict.get(num_field)
                if n_val is not None and str(n_val).strip() != "":
                    n_str = str(n_val).strip()
                    if "$" in n_str or "," in n_str or n_str.lower() in ("n/a", "none"):
                        parsed_num = clean_currency_str(n_str)
                        if parsed_num is None:
                            issues.append(DataQualityIssue(
                                row=row_offset,
                                field=num_field,
                                value=n_str,
                                issue_type="invalid_numeric",
                                severity="high",
                                reasoning=f"Field '{num_field}' contains non-numeric string '{n_str}'.",
                                recommendation=f"Correct '{num_field}' to a clean numeric float/int."
                            ))
                        elif "$" in n_str or "," in n_str:
                            issues.append(DataQualityIssue(
                                row=row_offset,
                                field=num_field,
                                value=n_str,
                                issue_type="formatting_inconsistency",
                                severity="low",
                                reasoning=f"Field '{num_field}' contains formatted currency string '{n_str}'.",
                                recommendation="Strip currency formatting ('$', ',') into clean numeric format."
                            ))

        # 7. Check Duplicate Address Records
        if "Address" in row_dict:
            addr_val = row_dict.get("Address")
            if addr_val is not None and str(addr_val).strip() != "":
                norm_addr = str(addr_val).strip().lower()
                if norm_addr in seen_addresses:
                    prev_row = seen_addresses[norm_addr]
                    issues.append(DataQualityIssue(
                        row=row_offset,
                        field="Address",
                        value=str(addr_val),
                        issue_type="duplicate_record",
                        severity="medium",
                        reasoning=f"Duplicate address '{addr_val}' previously seen at row {prev_row}.",
                        recommendation="Check if this record is an accidental duplicate."
                    ))
                else:
                    seen_addresses[norm_addr] = row_offset

    return DataQualityResponse(
        total_issues=len(issues),
        issues=issues
    )
