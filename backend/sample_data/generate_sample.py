import os
import openpyxl

def create_messy_sov_file():
    target_dir = os.path.dirname(__file__)
    file_path = os.path.join(target_dir, "messy_sov.xlsx")

    wb = openpyxl.Workbook()
    
    # Sheet 1: Instructions (Irrelevant sheet)
    ws_inst = wb.active
    ws_inst.title = "Instructions"
    ws_inst.append(["INSTRUCTIONS FOR PROPERTY SCHEDULE SUBMISSION"])
    ws_inst.append([])
    ws_inst.append(["1. Please ensure all values are reported in USD."])
    ws_inst.append(["2. Complete all rows for primary location assets."])
    ws_inst.append(["3. Contact underwriting support for assistance."])

    # Sheet 2: Property Data (Actual SOV data sheet)
    ws_prop = wb.create_sheet(title="Property Data")
    
    # Title blocks on rows 1 and 2
    ws_prop.append(["CONFIDENTIAL STATEMENT OF VALUES (SOV) 2024", "", "", "", "", "", "", "", "", "", "", "", ""])
    ws_prop.append(["Client Name: Acme Global Commercial Portfolio", "", "", "", "", "", "", "", "", "", "", "", ""])
    
    # Row 3: Header Row with messy column names
    ws_prop.append([
        "Loc #",
        "Premises Address",
        "Town",
        "St",
        "ZIP Code",
        "Bldg Repl Cost",
        "Contents Val",
        "Business Income",
        "Use/Occupancy",
        "Const Type",
        "Yr Built",
        "Fire Prot.",
        "Stories"
    ])
    
    # Rows 4 to 15: 12 realistic records with various data quality issues
    records = [
        ["Loc 101", "100 Main St", "New York", "NY", "10001", "$1,500,000", "250000", "50000", "Commercial Office", "Frame", 1998, "YES", 3],
        ["Loc 102", "250 Industrial Pkwy", "Newark", "NJ", "07102", "3200000", "1000000", "150000", "Warehouse", "Joisted Masonry", 2005, "Y", 2],
        ["Loc 103", "500 Ocean Ave", "Miami", "FL", "33139", "4500000", "500000", "N/A", "Hotel", "Non-Combustible", "189", "Yes", 10],  # "189" invalid year
        ["Loc 104", "12 Epic Way", "Austin", "TX", "78701", "2100000", "300000", "75000", "Retail", "Frame", 2012, "NO", 1],
        ["Loc 105", "88 Pine Street", "Seattle", "WA", "98101", "5800000", "1200000", "300000", "Residential Apt", "Modified Fire Resistive", 1985, "N", 8],
        ["Loc 106", "404 Elm Drive", "Chicago", "IL", "60601", "1900000", "150000", "40000", "Office", "Masonry Non-Combustible", 2018, "YES", 4],
        ["Loc 107", "777 Sunset Blvd", "Los Angeles", "CA", "90028", "8500000", "2000000", "500000", "Restaurant", "Frame", 1974, "1", 2],
        ["Loc 108", "1200 Market St", "Philadelphia", "PA", "19107", "3100000", "450000", "90000", "Bank", "Fire Resistive", 2000, "Y", 5],
        ["Loc 109", "33 Peachtree St", "Atlanta", "GA", "30303", "6200000", "800000", "200000", "Healthcare", "Non-Combustible", 2015, "Yes", 6],
        ["Loc 110", "555 California St", "San Francisco", "CA", "94104", "12500000", "3500000", "1000000", "Commercial Office", "Fire Resistive", 1990, "YES", 25],
        ["Loc 111", "99 Broadway", "Denver", "CO", "80203", "2800000", "400000", "80000", "Light Mfg", "Joisted Masonry", 1965, "N", 2],
        ["Loc 112", "1010 Grand Ave", "Kansas City", "MO", "64106", "1750000", "220000", "35000", "Storage", "Frame", 2008, "0", 1]
    ]

    for rec in records:
        ws_prop.append(rec)

    wb.save(file_path)
    print(f"Sample messy SOV file created successfully at {file_path}")

if __name__ == "__main__":
    create_messy_sov_file()
