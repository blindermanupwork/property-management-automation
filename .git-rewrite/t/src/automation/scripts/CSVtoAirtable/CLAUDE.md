# CSV to Airtable Processing - Complete Context

This document provides comprehensive context for the CSV processing system that converts reservation data from multiple sources into Airtable records.

## Overview

The CSV processing system handles reservation data from multiple vacation rental platforms (iTrip, Evolve) and converts them into standardized Airtable records. It supports both regular guest reservations and property owner blocks through different processing pipelines.

## File Structure

```
CSVtoAirtable/
├── csvProcess.py          # Main CSV processing engine
├── config.py             # Configuration and environment setup
└── CLAUDE.md             # This documentation file
```

## Business Logic Overview

### **Two Processing Types:**

1. **Regular CSV Processing** - Guest reservations from iTrip and Evolve
2. **Tab2 Processing** - Property owner blocks from Evolve Tab 2 export

### **Data Flow:**
```
CSV Files → Processing Logic → Property Mapping → Airtable Records → Job Creation
```

## Technical Implementation

### **Main Processing Functions**

#### `process_csv_files()` - Regular CSV Processing
- **Purpose**: Processes guest reservations from iTrip and Evolve regular exports
- **Input**: CSV files in `CSV_process_development/` or `CSV_process_production/`
- **Output**: Creates "Reservation" entries in Airtable
- **Entry Type**: `"Reservation"`
- **Service Type**: `"Turnover"` (default)

#### `process_tab2_csv()` - Owner Block Processing  
- **Purpose**: Processes property owner blocks from Evolve Tab 2 export
- **Input**: CSV files with `*_tab2.csv` pattern
- **Output**: Creates "Block" entries in Airtable
- **Entry Type**: `"Block"`
- **Service Type**: `"Needs Review"`
- **Entry Source**: `"Evolve"`
- **ICS URL**: `"csv_evolve_blocks"`

### **Key Data Structures**

#### **Regular CSV Formats:**

**iTrip Format:**
```csv
Checkin,Checkout,"Date Booked","Tenant Name","Tenant Phone","Property Name","Property Address","Property Owner",BR/BA,Size,"Next Booking","Next Tenant Name","Next Tenant Phone","Same Day?","Contractor Info","Reservation ID"
```

**Evolve Regular Format:**
```csv
Reservation,Property Address,Property Owner,Status,Check-In,Check-Out,Guest Name
```

**Tab2 Format (Owner Blocks):**
```csv
Reservation,Property Address,Property Owner,Status,Check-In,Check-Out,Guest Name
```

### **Property Mapping Logic**

#### `build_guest_to_property_map()` - Tab2 Property Mapping
- **Purpose**: Maps guest names to properties for owner block identification
- **Source**: Airtable Properties table
- **Logic**: Creates mapping from "Full Name (from HCP Customer ID)" to Property record
- **Filter**: Only properties where `{Entry Source (from ICS Feeds)} = 'Evolve'`
- **Usage**: Determines if guest name matches property owner (creates block vs skips)

#### `find_property_by_name()` - Regular Property Mapping
- **Purpose**: Maps property names to Airtable property records
- **Strategies**:
  1. Direct name match with "Property Name" field
  2. Fuzzy matching for variations
  3. Address-based matching for complex names

### **Record Creation Logic**

#### **Reservation Records (Regular Processing)**
```python
# Required Airtable Fields:
{
    'Entry Type': 'Reservation',
    'Service Type': 'Turnover',  # Default, can be overridden
    'Guest Name': guest_name,
    'Check-in Date': checkin_date,
    'Check-out Date': checkout_date,
    'Property ID': [property_record_id],
    'Entry Source': entry_source,  # 'iTrip', 'Evolve', etc.
    'Reservation UID': reservation_uid,
    'Status': 'New',  # New/Modified/Removed based on changes
    'Same-day Turnover': same_day_flag,
    'ICS URL': ics_url,  # Maps to feed source
}
```

#### **Block Records (Tab2 Processing)**
```python
# Required Airtable Fields:
{
    'Entry Type': 'Block',
    'Service Type': 'Needs Review',
    'Guest Name': owner_name,  # Same as property owner
    'Check-in Date': checkin_date,
    'Check-out Date': checkout_date,
    'Property ID': [property_record_id],
    'Entry Source': 'Evolve',
    'Reservation UID': reservation_uid,
    'Status': 'New',
    'ICS URL': 'csv_evolve_blocks',
}
```

### **Status Management**

#### **Record Status Logic:**
- **New**: First time seeing this reservation UID
- **Modified**: Reservation UID exists but dates/details changed
- **Removed**: Reservation UID missing from new data (marked as cancelled)
- **Unchanged**: Reservation UID exists with identical data

#### **Historical Preservation:**
- **All changes create new records** - original records are preserved
- **Old records marked as "Old"** when new version created
- **Only ONE active record per reservation UID** at any time

### **Date Filtering**

#### **Global Date Configuration:**
```python
# Date filtering variables (from icsProcess.py pattern)
TAB2_FILTER_MONTHS_PAST = 2      # Keep blocks from 2 months ago
TAB2_FILTER_MONTHS_FUTURE = 6    # Keep blocks up to 6 months ahead
```

#### **Processing Windows:**
- **Tab2**: Filters check-in dates between configured past/future months
- **Regular CSV**: Typically processes all dates in file

### **Entry Source Detection**

#### **Source Mapping:**
```python
# Entry sources based on file content/names:
'iTrip'     # From iTrip email CSV files
'Evolve'    # From Evolve portal exports (both regular and tab2)
```

#### **ICS URL Mapping:**
```python
# Maps to ICS Feeds table entries:
'csv_itrip'           # iTrip CSV processing
'csv_evolve'          # Evolve regular CSV processing  
'csv_evolve_blocks'   # Evolve tab2 owner blocks
```

### **Same-Day Turnover Logic**

#### **Detection Rules:**
1. **iTrip**: Uses "Same Day?" column from CSV
2. **Evolve**: Calculated based on checkout date matching next checkin date
3. **Tab2**: Not applicable (blocks don't have turnover logic)

#### **Service Type Override:**
- When same-day turnover detected, may override default "Turnover" service type
- Used for scheduling optimization and special handling

### **Error Handling**

#### **Tab2 Specific Errors:**
- **skipped_no_property**: Guest name doesn't match any property owner
- **date_parsing_error**: Invalid date formats in CSV
- **missing_required_fields**: CSV missing required columns

#### **Regular CSV Errors:**
- **property_not_found**: Cannot map property name to Airtable record
- **duplicate_reservation_uid**: Multiple records with same UID in same processing run
- **invalid_date_range**: Check-out before check-in dates

### **Statistics and Reporting**

#### **Global Counters:**
```python
# Tab2 processing statistics
tab2_global = {
    'processed': 0,
    'skipped_no_property': 0,
    'date_errors': 0,
    'created': 0,
    'updated': 0,
}

# Regular CSV statistics  
csv_global = {
    'total_processed': 0,
    'new_reservations': 0,
    'modified_reservations': 0,
    'removed_reservations': 0,
    'unchanged_reservations': 0,
}
```

#### **Report Generation:**
- **Per-file statistics**: Shows processing results for each CSV file
- **Overall summary**: Aggregates results across all files
- **Error reporting**: Details any processing failures or skipped records

### **Integration Points**

#### **Airtable Tables Used:**
1. **Reservations** (`tblaPnk0jxF47xWhL`) - Main data destination
2. **Properties** (`tblWbCY6Fi1YEcFcQ`) - Property mapping and validation
3. **ICS Feeds** (`tblpJuwYSWFW9Sy7c`) - Entry source and feed URL mapping

#### **Configuration Dependencies:**
- **Environment variables**: DEV vs PROD Airtable base selection
- **Date filtering**: Configurable time windows for data retention
- **Property matching**: Relies on accurate property name/address data

### **File Processing Workflow**

#### **Processing Sequence:**
1. **File Discovery**: Scan `CSV_process_{environment}/` directory
2. **Format Detection**: Identify iTrip vs Evolve vs Tab2 format
3. **Data Validation**: Check required columns and date formats
4. **Property Mapping**: Match reservations/blocks to properties
5. **Change Detection**: Compare with existing Airtable records
6. **Record Creation**: Create new/modified/removed records
7. **File Cleanup**: Move processed files to `CSV_done_{environment}/`
8. **Statistics**: Generate processing reports

#### **Tab2 Specific Logic:**
- **Owner Detection**: Guest name must match "Full Name (from HCP Customer ID)" 
- **Block Creation**: Creates calendar blocks instead of reservations
- **Service Type**: Always "Needs Review" for manual handling
- **Property Filtering**: Only processes Evolve properties

### **Environment Separation**

#### **Development vs Production:**
- **Separate processing directories**: `CSV_process_development/` vs `CSV_process_production/`
- **Separate Airtable bases**: DEV (`app67yWFv0hKdl6jM`) vs PROD (`appZzebEIqCU5R9ER`)
- **Separate completion directories**: `CSV_done_development/` vs `CSV_done_production/`
- **Environment detection**: Based on configuration and runtime parameters

### **Critical Business Rules**

#### **Tab2 Owner Block Rules:**
1. **Guest Name = Property Owner Name** → Creates Block
2. **Guest Name ≠ Property Owner Name** → Skipped (not an owner block)
3. **Blocks always need manual review** → Service Type = "Needs Review"
4. **Blocks are calendar blocks** → Entry Type = "Block"

#### **Regular Reservation Rules:**
1. **Property must exist in Airtable** → Mapped via name/address
2. **Duplicate UIDs within same file** → Error condition
3. **Missing reservations** → Marked as "Removed"
4. **Date changes** → Creates "Modified" record, marks original as "Old"

### **Testing Considerations**

#### **Test Data Requirements:**
- **Tab2 Testing**: Guest names must match existing property owners in Airtable
- **Regular Testing**: Property names must match Airtable Property records
- **Date Testing**: Use realistic future dates within filtering windows
- **UID Testing**: Use consistent UID patterns for change detection

#### **Validation Points:**
- **Property mapping accuracy**: Verify correct property association
- **Status transitions**: Test New → Modified → Removed flows
- **Tab2 block creation**: Verify blocks vs reservations created correctly
- **Historical preservation**: Confirm old records marked properly

### **Performance Considerations**

#### **Optimization Strategies:**
- **Batch processing**: Process multiple CSV files in single run
- **Property caching**: Cache property lookups to avoid repeated API calls
- **Date filtering**: Limit processing to relevant date ranges
- **Change detection**: Only update records when actual changes detected

#### **Scalability Limits:**
- **Airtable API limits**: 5 requests per second, 100,000 records per base
- **File size limits**: Large CSV files may require chunked processing
- **Memory usage**: Property mapping data loaded into memory

This documentation provides complete context for understanding, maintaining, and extending the CSV to Airtable processing system.