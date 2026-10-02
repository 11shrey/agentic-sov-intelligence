import re
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process

from models.schemas import SchemaMappingRecommendation, SchemaMappingResponse
from models.sov_schema import STANDARD_SOV_FIELDS, StandardSOVField

ALIAS_MAP: Dict[str, List[str]] = {
    "Reference": ["loc #", "loc", "location #", "location id", "loc id", "ref #", "reference #", "ref id", "building #", "bldg #", "asset #", "item #", "site #"],
    "Address": ["premises address", "property address", "street address", "location address", "address 1", "addr", "location"],
    "City": ["town", "city name", "municipality"],
    "State": ["st", "state code", "province"],
    "Zip": ["zip code", "zipcode", "postal code", "post code"],
    "County": ["parish", "district"],
    "Country": ["nation"],
    "Building Value": ["bldg repl cost", "building repl cost", "bldg replacement cost", "building replacement cost", "bldg value", "building value", "bldg val", "structure value", "building limit"],
    "Contents": ["contents val", "contents value", "personal property", "bpp", "equipment value", "contents limit"],
    "BI": ["business income", "bi value", "loss of income", "business interruption", "bi limit"],
    "Occupancy": ["use/occupancy", "occupancy", "use", "occupancy type", "property use", "occupancy description", "business description"],
    "Construction": ["const type", "construction type", "building construction", "construction class", "const class"],
    "Storeys": ["stories", "storeys", "num stories", "no of stories", "number of stories", "floors"],
    "Number of Buildings": ["no. of buildings", "number of buildings", "bldg count", "num buildings", "building count"],
    "Year Built": ["yr built", "year built", "year constructed", "built year", "year of construction"],
    "Fire Sprinklers (Y/N)": ["fire prot.", "fire protection", "sprinklers", "sprinklered", "fire sprinkler", "fire prot", "sprinkler (y/n)", "fire sprinklers"],
    "Other": []
}

def normalize_text(text: str) -> str:
    """Normalize string by lowercasing and removing non-alphanumeric chars."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(text)).lower()

def map_single_column(source_column: str) -> SchemaMappingRecommendation:
    """
    Map a single client column header to one of the 17 Standard SOV Fields.
    """
    col_raw = str(source_column).strip()
    col_clean = col_raw.lower()
    col_norm = normalize_text(col_raw)

    if not col_raw:
        return SchemaMappingRecommendation(
            source_column=source_column,
            target_field="Other",
            confidence=0.50,
            matching_method="default",
            reasoning="Empty column header mapped to 'Other'.",
            status="needs_review"
        )

    # 1. Exact Match
    for std_field in STANDARD_SOV_FIELDS:
        if col_clean == std_field.lower():
            return SchemaMappingRecommendation(
                source_column=col_raw,
                target_field=std_field,
                confidence=1.0,
                matching_method="exact",
                reasoning=f"Exact match found for standard field '{std_field}'.",
                status="approved"
            )

    # 2. Normalized Match
    for std_field in STANDARD_SOV_FIELDS:
        if col_norm == normalize_text(std_field):
            return SchemaMappingRecommendation(
                source_column=col_raw,
                target_field=std_field,
                confidence=0.95,
                matching_method="normalized",
                reasoning=f"Normalized match found for standard field '{std_field}'.",
                status="approved"
            )

    # 3. Alias Match
    for std_field, aliases in ALIAS_MAP.items():
        for alias in aliases:
            if col_clean == alias.lower() or col_norm == normalize_text(alias):
                return SchemaMappingRecommendation(
                    source_column=col_raw,
                    target_field=std_field,
                    confidence=0.92,
                    matching_method="alias",
                    reasoning=f"Matched known alias '{col_raw}' to standard field '{std_field}'.",
                    status="approved"
                )

    # 4. RapidFuzz Fuzzy Match
    best_target = "Other"
    best_score = 0.0
    best_method_detail = ""

    # Check fuzzy match against standard fields and aliases
    candidate_targets = []
    for std_field in STANDARD_SOV_FIELDS:
        candidate_targets.append((std_field, std_field))
        for alias in ALIAS_MAP.get(std_field, []):
            candidate_targets.append((alias, std_field))

    for candidate_str, target_field in candidate_targets:
        score = fuzz.token_sort_ratio(col_clean, candidate_str.lower())
        if score > best_score:
            best_score = score
            best_target = target_field
            best_method_detail = candidate_str

    if best_score >= 70.0:
        confidence = round(min(0.95, best_score / 100.0), 2)
        status = "approved" if confidence >= 0.85 else "needs_review"
        return SchemaMappingRecommendation(
            source_column=col_raw,
            target_field=best_target,
            confidence=confidence,
            matching_method="fuzzy",
            reasoning=f"Fuzzy matched '{col_raw}' to '{best_target}' (matched '{best_method_detail}' with score {int(best_score)}%).",
            status=status
        )

    # 5. Default Fallback
    return SchemaMappingRecommendation(
        source_column=col_raw,
        target_field="Other",
        confidence=0.50,
        matching_method="default",
        reasoning=f"Could not confidently map '{col_raw}'. Defaulted to 'Other'.",
        status="needs_review"
    )

def map_schema(
    sheet_data: List[List[Any]], 
    header_row: int, 
    target_fields: Optional[List[str]] = None
) -> SchemaMappingResponse:
    """
    Agent 2 Engine: Maps client columns from the header row to standardized 17 SOV fields.
    """
    if not sheet_data or len(sheet_data) < header_row:
        return SchemaMappingResponse(selected_sheet="", mappings=[])

    header_cells = sheet_data[header_row - 1]
    mappings: List[SchemaMappingRecommendation] = []

    for cell in header_cells:
        if cell is None or str(cell).strip() == "":
            continue
        mapping = map_single_column(str(cell))
        mappings.append(mapping)

    return SchemaMappingResponse(
        selected_sheet="",
        mappings=mappings
    )
