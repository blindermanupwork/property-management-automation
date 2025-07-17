# CSV Processing - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** Natural language flow for CSV email processing and data ingestion

---

## 📧 **CSV PROCESSING TRIGGER**

**Automated**: Every 4 hours via cron + Real-time via CloudMailin webhook
**Manual**: Files placed in `CSV_process_[environment]/` folder

---

## 📋 **PRIMARY LOGIC FLOW**

### **STEP 1**: Email Reception and File Extraction
- **CloudMailin Integration**: Receives forwarded emails from property management companies
- **Email Validation**: 
  - **IF** sender contains "itrip" AND subject contains "checkouts report" 
  - **THEN** process as iTrip reservation data
- **Attachment Processing**:
  - **THEN** extract CSV attachments from email (base64 decoded)
  - **THEN** save CSV files to BOTH `CSV_process_development/` AND `CSV_process_production/`
  - **THEN** each environment processes only its own directory during automation runs

### **STEP 2**: Supplier Detection and Format Identification
- **iTrip Detection**:
  - **IF** CSV header contains "Property Name" column
  - **THEN** supplier = "iTrip", format = regular reservations
- **Evolve Detection**:
  - **IF** CSV filename contains "_tab2.csv"
  - **THEN** supplier = "Evolve", format = owner blocks (Tab2)
  - **IF** CSV header does NOT contain "Property Name" AND no "_tab2" pattern
  - **THEN** supplier = "Evolve", format = regular reservations

### **STEP 3**: Regular Reservation Processing (iTrip & Evolve Main)
- **FOR EACH** CSV row with valid data:

  **Property Mapping**:
  - **IF** iTrip: match **"Property Name"** to Properties table **"Property Name"** field (case-insensitive)
  - **IF** Evolve: match **"Listing#"** to Properties table listing number (extracted after "#" in property names)
  - **IF** no property match found: skip row and log error

  **UID Generation**:
  - **THEN** create unique identifier: `[source]_[property]_[checkin]_[checkout]_[guest_lastname]`
  - **THEN** normalize all components (lowercase, remove spaces/special chars)

  **Entry Type & Service Type Detection**:
  - **Default**: **"Entry Type"** = "Reservation", **"Service Type"** = "Turnover"
  - **IF** tenant name OR contractor info contains "maintenance":
    - **THEN** **"Entry Type"** = "Block", **"Service Type"** = "Needs Review"

  **Data Field Mapping**:
  - Reservation ID → **"Reservation UID"** field
  - Guest/Tenant name → **"Guest Name"** field
  - Check-in date → **"Check-in Date"** field (MM/DD/YYYY format)
  - Check-out date → **"Check-out Date"** field (MM/DD/YYYY format)
  - Property mapping → **"Property ID"** field (linked record)
  - Source → **"Entry Source"** field ("iTrip" or "Evolve")
  - Feed URL → **"ICS URL"** field ("csv_itrip" or "csv_evolve")

  **iTrip-Specific Processing**:
  - **IF** "Same Day?" column = "Yes": set **"Same-day Turnover"** = true
  - **IF** "Contractor Info" exists: set **"iTrip Report Info"** = contractor info
  - **THEN** check for property owner overrides (guest name patterns can override property assignments)

### **STEP 4**: Evolve Tab2 Owner Block Processing
- **Build Owner Mapping**: Query Properties table → map "Full Name (from HCP Customer ID)" to property records
- **FOR EACH** Tab2 CSV row:

  **Owner Block Detection**:
  - **IF** Guest Name matches mapped property owner name (case-insensitive)
    - **AND IF** reservation status = "booked"
    - **THEN** create/update owner block record
  - **IF** Guest Name does NOT match any property owner
    - **THEN** skip row (not an owner block)
  - **IF** reservation status = "cancelled" AND existing block found
    - **THEN** mark existing block as "Removed"

  **Block Record Configuration**:
  - Always **"Entry Type"** = "Block"
  - Always **"Service Type"** = "Needs Review"
  - Always **"Entry Source"** = "Evolve"
  - Always **"ICS URL"** = "csv_evolve_blocks"

### **STEP 5**: Date Filtering and Validation
- **FOR EACH** processed record:
  - **IF** check-in date < (today - FETCH_RESERVATIONS_MONTHS_BEFORE)
    - **THEN** skip record (too old)
  - **IF** check-in date > (today + 3 months)
    - **THEN** skip record (too far ahead)
  - **IF** date format invalid or unparseable
    - **THEN** skip record and log parsing error

### **STEP 6**: Flag Calculation (Property-Level Processing)
- **FOR EACH** property in CSV, group all reservations
- **Reset All Flags**: Set overlapping = false, same_day_turnover = false

  **Overlap Detection**:
  - **IF** two reservations have overlapping date ranges at same property
  - **THEN** set **"Overlapping Dates"** = true for both reservations

  **Same-Day Turnover Detection**:
  - **IF** iTrip CSV has "Same Day?" = "Yes": use that value (takes precedence)
  - **ELSE IF** one reservation's checkout date = another's check-in date at same property
    - **THEN** set **"Same-day Turnover"** = true for checkout reservation

### **STEP 7**: Airtable Synchronization with History Preservation
- **FOR EACH** processed reservation:

  **Duplicate Detection**:
  - **THEN** search Airtable for existing records with same UID + feed URL combination

  **Change Comparison**:
  - **THEN** compare dates (normalized to MM/DD/YYYY), property ID, flags, entry type, service type
  - **IF** iTrip: also compare iTrip Report Info field

  **Update Logic**:
  - **IF** UID + feed URL exists AND changes detected:
    - **THEN** mark ALL existing records (any status) as **"Status"** = "Old"
    - **THEN** create new record with **"Status"** = "Modified"
    - **THEN** preserve ALL HCP service fields from latest active record

  - **IF** UID + feed URL exists AND no changes detected:
    - **THEN** leave existing records completely unchanged (no Airtable writes)

  - **IF** UID + feed URL does not exist:
    - **THEN** mark any existing non-active records as "Old"
    - **THEN** create new record with **"Status"** = "New"

  **Removal Detection**:
  - **FOR EACH** existing Airtable record not found in current CSV:
    - **IF** record has active status AND check-in date >= today
      - **THEN** mark ALL records for this UID as **"Status"** = "Old"
      - **THEN** create new record with **"Status"** = "Removed"

### **STEP 8**: File Cleanup and Reporting
- **IF** file processed successfully:
  - **THEN** move to `CSV_done_[environment]/` with timestamp
- **IF** file had processing errors:
  - **THEN** leave in `CSV_process_[environment]/` for manual review
- **THEN** log detailed statistics: new/modified/unchanged/removed counts by supplier and entry type
- **THEN** log property-level summary with addresses for verification

---

## 🚨 **ERROR HANDLING**

### **File-Level Errors**:
- **Missing required columns**: Skip entire file, log error
- **Invalid CSV format**: Skip file, notify admin
- **Empty file**: Skip file, log warning

### **Record-Level Errors**:
- **Property not found**: Skip record, log suggested matches
- **Invalid dates**: Skip record, log parsing error
- **Missing required fields**: Skip record, continue processing

### **API Errors**:
- **Airtable rate limits**: Retry with exponential backoff
- **Authentication failures**: Log error, continue with next file
- **Network timeouts**: Retry up to 3 times

---

*This document captures the complete logical flow for CSV processing, from email receipt through Airtable synchronization, with exact field names and decision logic.*