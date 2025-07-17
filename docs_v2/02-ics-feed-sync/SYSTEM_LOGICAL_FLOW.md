# ICS Feed Sync - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** Natural language flow for calendar feed processing and synchronization

---

## 📅 **ICS SYNC TRIGGER**

**Automated**: Every 4 hours via cron
**Volume**: 246 feeds (production), 255 feeds (development)

---

## 📋 **PRIMARY LOGIC FLOW**

### **STEP 1**: Feed Status Management
- **Mark Removed Feeds**:
  - **IF** feed in **"ICS Feeds"** table has **"Feed Status"** = "Remove"
  - **THEN** find all active reservations (Status = "New" or "Modified") for that feed URL
  - **THEN** mark all matching reservations as **"Status"** = "Old"
  - **THEN** log removal count for each affected feed

### **STEP 2**: Active Feed Discovery
- **Get Feed List**:
  - **IF** **"Feed Status"** = "Active" (or process all feeds if field missing)
  - **THEN** extract **"ICS URL"** and linked **"Property Name"** (Property ID)
  - **THEN** skip non-HTTP URLs (CSV feed identifiers like "csv_itrip", "csv_evolve")
  - **THEN** build mapping: ICS URL → Property Record ID

### **STEP 3**: Concurrent Feed Processing
- **FOR EACH** active ICS feed URL:
  - **Download Calendar Data**:
    - **THEN** fetch iCalendar data with 15-second timeout
    - **IF** download fails: log error, update tracking table, continue with next feed
    - **IF** successful: parse VEVENT components

  **Date Filtering** (matches CSV processing logic):
  - **IF** event start date < (today - FETCH_RESERVATIONS_MONTHS_BEFORE)
    - **THEN** skip event (too old)
  - **IF** event start date > (today + 3 months)
    - **THEN** skip event (too far ahead)
  - **IF** event end date > (today + IGNORE_EVENTS_ENDING_MONTHS_AWAY)
    - **THEN** skip event (ends too far in future)

### **STEP 4**: Event Data Extraction
- **FOR EACH** calendar event within date range:

  **Basic Field Mapping**:
  - Event UID → **"Reservation UID"** field
  - Event SUMMARY → used for Guest Name extraction and classification
  - Event DTSTART → **"Check-in Date"** field (converted to MM/DD/YYYY)
  - Event DTEND → **"Check-out Date"** field (converted to MM/DD/YYYY)
  - Feed URL → **"ICS URL"** field
  - Property ID from feed mapping → **"Property ID"** field

  **Content Classification** (keyword-based analysis):
  - **Event Summary Analysis**:
    - **IF** summary contains guest name patterns: extract to **"Guest Name"** field
    - **IF** summary contains "block", "maintenance", "owner": classify as Block
    - **IF** summary contains reservation patterns: classify as Reservation

  **Entry Type Detection**:
  - **"Entry Type"**: "Reservation", "Block", "Owner Stay" (based on summary keywords)
  - **"Service Type"**: "Turnover", "Maintenance", "Inspection" (based on summary content)
  - **"Block Type"**: "Owner Block", "Maintenance Block", etc. (if Entry Type = "Block")

  **Source Detection** (from URL patterns and content):
  - **"Entry Source"**: "Airbnb", "VRBO", "Booking.com", "Hospitable", etc.
  - **THEN** analyze feed URL and event content for platform indicators

### **STEP 5**: Property-Level Flag Calculation
- **FOR EACH** property, group all reservation events:

  **Overlapping Dates Detection**:
  - **IF** two reservation events have overlapping date ranges at same property
  - **THEN** set **"Overlapping Dates"** = true for both events

  **Same-Day Turnover Detection**:
  - **IF** one reservation's check-out date = another reservation's check-in date at same property
  - **THEN** set **"Same-day Turnover"** = true for checkout reservation
  - **THEN** priority scheduling required

### **STEP 6**: Airtable Synchronization with History Preservation
- **FOR EACH** processed event:

  **Duplicate Detection**:
  - **THEN** search for existing records with same UID + feed URL combination

  **Change Detection**:
  - **THEN** compare important fields: dates, entry type, service type, property, flags
  - **IF** any important field changed: trigger update process

  **Update Logic**:
  - **IF** event UID + feed URL exists AND changes detected:
    - **THEN** mark ALL existing records for this UID as **"Status"** = "Old"
    - **THEN** create new record with **"Status"** = "Modified"
    - **THEN** preserve all HCP service fields from latest active record

  - **IF** event UID + feed URL exists AND no changes detected:
    - **THEN** leave existing records completely unchanged (no Airtable writes)

  - **IF** event UID + feed URL does not exist:
    - **THEN** create new record with **"Status"** = "New"

  **Removal Detection**:
  - **FOR EACH** existing Airtable record not found in current feed:
    - **IF** record is active (Status = "New" or "Modified") AND checkout date is future
      - **THEN** mark ALL records for this UID as **"Status"** = "Old"
      - **THEN** create new record with **"Status"** = "Removed"

### **STEP 7**: Property Link Updates
- **Fix Missing Property Links**:
  - **FOR EACH** reservation record with missing **"Property ID"** link
  - **IF** **"ICS URL"** has mapping in **"ICS Feeds"** table
    - **THEN** update **"Property ID"** = linked property from feeds table

### **STEP 8**: Feed Tracking and Reporting
- **Update ICS Cron Table**:
  - **FOR EACH** processed feed:
    - **THEN** update or create tracking record with:
      - **"ICS URL VEVENTS #"** = total events found in calendar
      - **"ICS URL VEVENTS Reservations"** = events actually processed (after filtering)
      - **"Last Run"** = current timestamp
      - **"ICS URL Response"** = "Success" or detailed error message

  **Error Logging**:
  - **IF** feed inaccessible or malformed:
    - **THEN** log error to `automation_[environment]*.log`
    - **THEN** update tracking table with error details
    - **THEN** continue processing remaining feeds

### **STEP 9**: Performance Optimization
- **Async Processing**: All feeds processed concurrently for speed
- **Memory Management**: Process feeds in batches to prevent memory overload
- **Rate Limiting**: Respect feed provider rate limits
- **Caching**: Cache property mappings to reduce Airtable API calls

---

## 🚨 **ERROR HANDLING**

### **Feed-Level Errors**:
- **Timeout (15 seconds)**: Log timeout, mark feed as inaccessible, continue
- **Invalid calendar format**: Log parsing error, skip feed
- **HTTP errors (404, 500, etc.)**: Log status code, update tracking table
- **Authentication failures**: Log auth error, try next feed

### **Event-Level Errors**:
- **Invalid date format**: Skip event, log parsing error
- **Missing required fields**: Skip event, continue processing
- **Malformed UID**: Generate fallback UID from event data

### **Property Mapping Errors**:
- **Property not found**: Create record without property link, log warning
- **Multiple property matches**: Use first match, log ambiguity warning
- **Feed not in mapping table**: Skip property assignment, log missing mapping

### **Airtable API Errors**:
- **Rate limits**: Implement exponential backoff retry
- **Network timeouts**: Retry up to 3 times
- **Invalid field values**: Log validation error, skip problematic field

---

## 📊 **PROCESSING STATISTICS**

### **Logged Metrics**:
- Total feeds processed vs skipped
- Events found vs events processed (after filtering)
- New/Modified/Removed reservation counts
- Property mapping success rate
- Feed accessibility statistics
- Processing duration per feed and total

### **Quality Indicators**:
- Feeds with consistent data vs frequent changes
- Events successfully classified vs unclassified
- Property links resolved vs missing
- Error rates by feed source

---

*This document captures the complete logical flow for ICS feed processing, from feed discovery through Airtable synchronization, with emphasis on error handling and data quality.*