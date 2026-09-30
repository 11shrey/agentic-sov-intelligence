from typing import List, Optional
from enum import Enum

class StandardSOVField(str, Enum):
    REFERENCE = "Reference"
    ADDRESS = "Address"
    CITY = "City"
    STATE = "State"
    ZIP = "Zip"
    COUNTY = "County"
    COUNTRY = "Country"
    BUILDING_VALUE = "Building Value"
    CONTENTS = "Contents"
    BI = "BI"
    OCCUPANCY = "Occupancy"
    CONSTRUCTION = "Construction"
    STOREYS = "Storeys"
    NUMBER_OF_BUILDINGS = "Number of Buildings"
    YEAR_BUILT = "Year Built"
    FIRE_SPRINKLERS = "Fire Sprinklers (Y/N)"
    OTHER = "Other"

STANDARD_SOV_FIELDS: List[str] = [field.value for field in StandardSOVField]

def is_valid_sov_field(field_name: str) -> bool:
    """Check if a given field name is one of the 17 standard SOV fields."""
    return field_name in STANDARD_SOV_FIELDS

def validate_sov_field(field_name: str) -> str:
    """Validate and return canonical standard field name, raising ValueError if invalid."""
    if not is_valid_sov_field(field_name):
        raise ValueError(f"'{field_name}' is not a valid 17-field standard SOV field.")
    return field_name
