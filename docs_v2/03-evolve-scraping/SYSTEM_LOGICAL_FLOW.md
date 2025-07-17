# Evolve Scraping - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** Natural language flow for Evolve portal web scraping automation

---

## 🌐 **EVOLVE SCRAPING TRIGGER**

**Automated**: Every 4 hours via cron
**Manual**: `ENVIRONMENT=[environment] python3 src/automation/scripts/evolve/evolveScrape.py --headless --sequential`

---

## 📋 **PRIMARY LOGIC FLOW**

### **STEP 1**: Portal Authentication and Setup
- **Browser Initialization**:
  - **THEN** launch Chrome browser in headless mode (--headless flag)
  - **THEN** set user agent and viewport for consistent rendering
  - **THEN** enable sequential tab processing (--sequential flag) to avoid Chrome conflicts

- **Login Process**:
  - **THEN** navigate to Evolve partner portal login page
  - **THEN** retrieve credentials from environment-specific configuration
  - **THEN** enter username and password, submit login form
  - **IF** login fails: log error, retry once, then exit
  - **IF** login successful: proceed to data extraction

### **STEP 2**: Regular Bookings Data Extraction (Tab 1)
- **Navigate to Upcoming Bookings**:
  - **THEN** go to bookings section (60 days forward)
  - **THEN** load all booking entries on page

- **FOR EACH** booking entry found:
  
  **Data Validation**:
  - **IF** booking has guest name AND property information
  - **THEN** proceed with extraction
  - **IF** missing critical data: skip booking, log warning

  **Field Extraction**:
  - Guest details → **"Guest Name"**, **"Phone"**, **"Email"** fields
  - Property name → **"Property Name"** field  
  - Check-in date → **"Check-in Date"** field
  - Check-out date → **"Check-out Date"** field
  - Booking status → used for filtering and validation

  **Reservation Processing**:
  - **THEN** generate UID: `evolve_[property]_[checkin]_[checkout]_[guest_lastname]`
  - **IF** reservation not already in Airtable:
    - **THEN** create new record in **"Reservations"** table
    - **THEN** set **"Entry Source"** = "Evolve"
    - **THEN** set **"Status"** = "New"
    - **THEN** set **"Entry Type"** = "Reservation"
    - **THEN** set **"Service Type"** = "Turnover"

### **STEP 3**: Owner Blocks Data Extraction (Tab 2)
- **Navigate to All Bookings Tab**:
  - **THEN** switch to tab2 (all bookings view)
  - **THEN** apply date filtering for configured time range

- **Build Owner Mapping**:
  - **THEN** query Properties table for Evolve properties
  - **THEN** extract owner names from **"Full Name (from HCP Customer ID)"** field
  - **THEN** create mapping: owner name → property record

- **FOR EACH** booking in tab2:

  **Owner Block Detection**:
  - **IF** Guest Name matches mapped property owner name (case-insensitive):
    - **AND IF** property has **"Entry Source"** = "Evolve"
    - **AND IF** booking date is within configured months range
    - **AND IF** booking status = "booked"
    - **THEN** identify as owner block

  - **IF** Guest Name does NOT match any property owner:
    - **THEN** skip record (not an owner block)

  **Block Record Creation**:
  - **THEN** extract booking details:
    - Guest Name → **"Guest Name"** field (property owner name)
    - Property → **"Property ID"** field (linked to Properties table)
    - Check-in date → **"Check-in Date"** field
    - Check-out date → **"Check-out Date"** field

  - **THEN** set block-specific fields:
    - **"Entry Type"** = "Block"
    - **"Service Type"** = "Needs Review"  
    - **"Entry Source"** = "Evolve"
    - **"ICS URL"** = "csv_evolve_blocks"
    - **"Status"** = "New"

  **Cancellation Handling**:
  - **IF** booking status = "cancelled" AND existing block found in Airtable:
    - **THEN** mark existing block record as **"Status"** = "Removed"

### **STEP 4**: Data Export and CSV Generation
- **Sequential Tab Processing**:
  - **THEN** process Tab 1 export (regular reservations)
  - **THEN** wait for download completion
  - **THEN** process Tab 2 export (owner blocks)
  - **THEN** avoid concurrent downloads to prevent Chrome conflicts

- **CSV File Management**:
  - **THEN** save exported CSV files with timestamp
  - **THEN** move files to appropriate environment folder for processing
  - **THEN** trigger CSV processing workflow for new data

### **STEP 5**: Data Synchronization with Airtable
- **Property Matching**:
  - **FOR EACH** extracted record:
    - **IF** Evolve property: match **"Listing#"** to Properties table
    - **IF** property not found: skip record, log missing property warning

- **Duplicate Detection and History Preservation**:
  - **THEN** check for existing records with same UID
  - **IF** data changed: mark old as "Old", create "Modified" record
  - **IF** no changes: leave existing records unchanged
  - **IF** new record: create with "New" status

### **STEP 6**: Browser Cleanup and Error Handling
- **Session Management**:
  - **THEN** clear browser cache and cookies
  - **THEN** close all browser tabs and windows
  - **THEN** terminate Chrome processes cleanly

- **Error Recovery**:
  - **IF** any step fails: capture screenshot for debugging
  - **THEN** log detailed error information with timestamp
  - **THEN** attempt graceful browser shutdown
  - **THEN** exit with appropriate error code

---

## 🚨 **ERROR HANDLING**

### **Authentication Errors**:
- **Login failure**: Retry once, then abort with error
- **Session timeout**: Re-authenticate and continue
- **Credential issues**: Log security error, notify admin

### **Navigation Errors**:
- **Page load timeout**: Wait additional time, then retry
- **Element not found**: Log selector error, continue with next element
- **Tab switching failure**: Refresh page, retry tab switch

### **Data Extraction Errors**:
- **Missing guest information**: Skip booking, log incomplete data
- **Invalid date format**: Skip booking, log parsing error  
- **Property mapping failure**: Skip booking, log property mismatch

### **Browser/System Errors**:
- **Chrome crash**: Restart browser, continue from last successful point
- **Memory issues**: Reduce batch size, implement garbage collection
- **Network connectivity**: Retry with exponential backoff

### **File System Errors**:
- **Download failure**: Retry download up to 3 times
- **File permission issues**: Log filesystem error, notify admin
- **Disk space full**: Clean temporary files, alert monitoring

---

## 🔧 **ENVIRONMENT-SPECIFIC CONFIGURATION**

### **Development Environment**:
- **Credentials**: Development portal account
- **Data Volume**: Limited property set for testing
- **Export Destination**: `CSV_process_development/`
- **Error Logging**: `automation_dev_YYYY-MM-DD.log`

### **Production Environment**:
- **Credentials**: Production portal account
- **Data Volume**: Full property portfolio
- **Export Destination**: `CSV_process_production/`  
- **Error Logging**: `automation_prod_YYYY-MM-DD.log`

---

## 📊 **PERFORMANCE CONSIDERATIONS**

### **Resource Management**:
- **Memory Usage**: Monitor Chrome memory consumption
- **CPU Usage**: Use headless mode to reduce CPU load
- **Network Bandwidth**: Optimize page loading with selective element loading

### **Timing Optimization**:
- **Page Load Waits**: Dynamic waits based on content loading
- **Download Timing**: Sequential processing to avoid conflicts
- **Rate Limiting**: Respect portal rate limits to avoid blocking

---

*This document captures the complete logical flow for Evolve portal scraping, from authentication through data synchronization, with emphasis on error handling and browser management.*