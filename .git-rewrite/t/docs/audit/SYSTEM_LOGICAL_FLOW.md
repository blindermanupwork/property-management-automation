# System Logical Flow - Property Management Automation

**Version:** 2.2.2  
**Last Updated:** June 9, 2025  
**Purpose:** Natural language logical flow with exact field names and update operations

---

## 🔄 **AUTOMATED CRON CYCLES (Every 4 Hours)**

### **Development Environment**: Every 4 hours at :10 minutes (4:10 AM, 8:10 AM, 12:10 PM, 4:10 PM, 8:10 PM, 12:10 AM)
### **Production Environment**: Every 4 hours at :00 minutes (4:00 AM, 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM, 12:00 AM)

---

## 📧 **CSV Processing Flow (iTrip & Evolve)**

**Trigger**: Every 4 hours OR CloudMailin webhook
**System Action**: CloudMailin webhook receives email → Saves CSV to both environments → Processing

### **Primary Logic**:

#### **STEP 1**: Receive CSV files via CloudMailin webhook
- **CloudMailin Integration**: 
  - **THEN** CloudMailin receives iTrip emails and forwards to `/webhooks/csv-email` endpoint
  - **THEN** webhook validates sender contains "itrip" AND subject contains "checkouts report"
  - **THEN** extracts CSV attachments from email (base64 decoded)
  - **THEN** saves CSV files to BOTH `CSV_process_development/` AND `CSV_process_production/`
  - **THEN** each environment's automation processes only its own directory

#### **STEP 2**: Identify supplier and processing type
- **IF** CSV header contains "Property Name" column
  - **THEN** supplier = "iTrip", format = regular reservations
- **IF** CSV filename contains "_tab2.csv"
  - **THEN** supplier = "Evolve", format = owner blocks (Tab2)
- **IF** CSV header does NOT contain "Property Name" AND no "_tab2" pattern
  - **THEN** supplier = "Evolve", format = regular reservations

#### **STEP 3**: Regular Reservation Processing (iTrip & Evolve main)
- **FOR EACH** CSV row with valid UID, check-in, check-out dates:
  
  **Property Mapping**:
  - **IF** iTrip: match **"Property Name"** to Properties table **"Property Name"** field (case-insensitive)
  - **IF** Evolve: match **"Listing#"** to Properties table listing number extraction (after "#" in property names)
  - **IF** no property match found: skip row and log error (processing fails for entire file)
  
  **Entry Type & Service Type Detection** (based on text analysis):
  - Default: **"Entry Type"** = "Reservation", **"Service Type"** = "Turnover"
  - **IF** tenant name OR contractor info contains "maintenance": 
    - **THEN** **"Entry Type"** = "Block", **"Service Type"** = "Needs Review"
  
  **Data Extraction**:
  - Reservation ID → **"Reservation UID"** field
  - Guest/Tenant name → **"Guest Name"** field (if available)
  - Check-in date → **"Check-in Date"** field (MM/DD/YYYY format)
  - Check-out date → **"Check-out Date"** field (MM/DD/YYYY format)
  - Property mapping → **"Property ID"** field (linked record)
  - Source → **"Entry Source"** field ("iTrip" or "Evolve")
  - Feed URL → **"ICS URL"** field ("csv_itrip" or "csv_evolve")
  - Entry Type and Service Type from detection logic above
  
  **iTrip-Specific Fields**:
  - **IF** "Same Day?" column = "Yes": set **"Same-day Turnover"** = true
  - **IF** "Contractor Info" exists: set **"iTrip Report Info"** = contractor info
  - Check for property owner overrides (guest name patterns override property assignments)

#### **STEP 4**: Evolve Tab2 Owner Block Processing (Separate Function)
- **Build owner mapping**: Query Properties table for Evolve properties → map "Full Name (from HCP Customer ID)" to property records
- **FOR EACH** Tab2 CSV row:
  
  **Owner Block Detection Logic**:
  - **IF** Guest Name matches mapped property owner name (case-insensitive)
    - **AND IF** reservation status = "booked"
    - **THEN** create/update owner block
  - **IF** Guest Name does NOT match any mapped property owner
    - **THEN** skip row (not an owner block)
  - **IF** reservation status = "cancelled" AND existing block found
    - **THEN** mark existing block as "Removed"
  
  **Block Record Management**:
  - Always **"Entry Type"** = "Block"
  - Always **"Service Type"** = "Needs Review"
  - Always **"Entry Source"** = "Evolve"
  - Always **"ICS URL"** = "csv_evolve_blocks"
  - Compare with existing records → create "New", "Modified", or mark "Unchanged"
  - Use same history preservation logic (mark old records as "Old")

#### **STEP 5**: Date filtering (all processing types)
- **IF** check-in date < (today - FETCH_RESERVATIONS_MONTHS_BEFORE)
  - **THEN** skip record (too old)
- **IF** check-in date > (today + 3 months)
  - **THEN** skip record (too far ahead)

#### **STEP 6**: Calculate flags locally (property by property)
- **FOR EACH** property, group all reservations from CSV
- **Reset flags**: Set overlapping = false, same_day_turnover = false for all
- **Calculate overlaps**: **IF** two reservations have date ranges that overlap
  - **THEN** set **"Overlapping Dates"** = true for both
- **Calculate same-day turnovers**: 
  - **IF** iTrip CSV has "Same Day?" = "Yes": use that value (takes precedence)
  - **ELSE IF** checkout date equals another reservation's check-in date at same property
    - **THEN** set **"Same-day Turnover"** = true for checkout reservation

#### **STEP 7**: Synchronize with Airtable (complete history preservation)
- **FOR EACH** processed reservation:
  
  **Change Detection** (compare with existing active records):
  - Check dates (normalized to MM/DD/YYYY), property ID, flags, entry type, service type
  - **IF** iTrip: also check iTrip Report Info field
  
  **IF** reservation UID + feed URL exists in Airtable AND changes detected:
    - **THEN** mark ALL existing records (any status) as **"Status"** = "Old"
    - **THEN** create new record with **"Status"** = "Modified"
    - **THEN** preserve ALL HCP service fields from latest active record (explicit field copying)
  
  **IF** reservation UID + feed URL exists AND no changes detected:
    - **THEN** leave existing records completely unchanged (no Airtable writes)
  
  **IF** reservation UID + feed URL does not exist:
    - **THEN** mark any existing non-active records as "Old"
    - **THEN** create new record with **"Status"** = "New"
  
  **FOR EACH** existing Airtable record not found in current CSV:
  - **IF** record has active status AND check-in date >= today
    - **THEN** mark ALL records for this UID as **"Status"** = "Old"
    - **THEN** create new record with **"Status"** = "Removed"

#### **STEP 8**: File cleanup and reporting
- **IF** file processed successfully: move to `CSV_done_[environment]/`
- **IF** file had errors: leave in `CSV_process_[environment]/`
- **THEN** log detailed statistics: new/modified/unchanged/removed counts by supplier and entry type
- **THEN** log property-level summary with addresses for verification

---

## 🏠 **Evolve Portal Scraping Flow**

**Trigger**: Every 4 hours
**System Action**: Selenium automation → Partner portal login → Data extraction

### **Primary Logic**:
- **IF** Evolve portal accessible
  - **THEN** log into partner portal using stored credentials
  - **THEN** navigate to upcoming bookings (60 days out)
  - **THEN** extract reservation data:
    
    **FOR EACH** upcoming booking:
    - **IF** booking has guest name
      - **THEN** extract:
        - Guest details → **"Guest Name"**, **"Phone"**, **"Email"** fields
        - Property name → **"Property Name"** field
        - Dates → **"Check-in Date"**, **"Check-out Date"** fields
      
      **IF** reservation not in Airtable
      - **THEN** create new record in **"Reservations"** table
      - **THEN** set **"Source"** = "Evolve"
      - **THEN** set **"Status"** = "New"
  
  - **THEN** navigate to all bookings tab (tab2)
  - **THEN** filter records:
    
    **FOR EACH** booking in tab2:
    - **IF** Guest Name matches property owner name from **"Properties"** table
      - **AND IF** property has **"Entry Source"** = "Evolve"
      - **AND IF** booking date is within configured months
      - **THEN** extract as owner block:
        - Guest Name → **"Guest Name"** field (property owner name)
        - Property → **"Property ID"** field (linked to Properties table)
        - Dates → **"Check-in Date"**, **"Check-out Date"** fields
        - Set **"Entry Type"** = "Block"
        - Set **"Service Type"** = "Needs Review"
        - Set **"Source"** = "Evolve"
        - Set **"ICS URL"** = "csv_evolve_blocks"
        - Set **"Status"** = "New"
    
    **IF** Guest Name does NOT match any property owner
    - **THEN** skip record (not an owner block)

---

## 📅 **ICS Feed Processing Flow**

**Trigger**: Every 4 hours
**System Action**: Process 246 feeds (prod) / 255 feeds (dev)

### **Primary Logic**:
- **STEP 1**: Mark feeds flagged as "Remove" status
  - **IF** feed in **"ICS Feeds"** table has **"Feed Status"** = "Remove"
  - **THEN** find all active reservations (Status = "New" or "Modified") for that feed URL
  - **THEN** mark all as **"Status"** = "Old"

- **STEP 2**: Get active ICS URLs from **"ICS Feeds"** table
  - **IF** **"Feed Status"** = "Active" (or all feeds if field missing)
  - **THEN** extract **"ICS URL"** and linked **"Property Name"** (Property ID)
  - **THEN** skip non-HTTP URLs (CSV feed identifiers)
  - **THEN** build mapping: ICS URL → Property Record ID

- **STEP 3**: Fetch all ICS feeds concurrently (async processing)
  - **FOR EACH** active ICS feed URL
    - **THEN** download iCalendar data with 15-second timeout
    - **THEN** parse calendar events with date filtering
    
    **Date Filtering Logic** (matches CSV processing):
    - **IF** check-in date < (today - FETCH_RESERVATIONS_MONTHS_BEFORE)
      - **THEN** skip event (too old)
    - **IF** check-in date > (today + 3 months)
      - **THEN** skip event (too far ahead)
    - **IF** check-out date > (today + IGNORE_EVENTS_ENDING_MONTHS_AWAY)
      - **THEN** skip event (ends too far in future)
    
    **FOR EACH** calendar event within date range:
    - **THEN** extract event details:
      - Event UID → **"Reservation UID"** field
      - Event summary → determines Guest Name
      - Event start → **"Check-in Date"** field
      - Event end → **"Check-out Date"** field
      - Feed URL → **"ICS URL"** field
      - Property ID from feed mapping → **"Property ID"** field
    
    - **THEN** apply keyword mapping for classification:
      - **"Entry Type"**: "Reservation", "Block", "Owner Stay" (based on summary keywords)
      - **"Service Type"**: "Turnover", "Maintenance", "Inspection" (based on summary keywords)
      - **"Block Type"**: "Owner Block", "Maintenance Block", etc. (if Entry Type = "Block")
      - **"Entry Source"**: "Airbnb", "VRBO", "Booking.com", etc. (from URL or content)

- **STEP 4**: Calculate overlapping dates and same-day turnover flags
  - **FOR EACH** property, group reservation events
  - **IF** two reservation events overlap dates at same property
    - **THEN** set **"Overlapping Dates"** = true for both
  - **IF** one reservation check-out date = another reservation check-in date at same property
    - **THEN** set **"Same-day Turnover"** = true for checkout reservation

- **STEP 5**: Synchronize events with Airtable (preserving history)
  - **FOR EACH** processed event
    - **IF** event UID + feed URL exists in Airtable
      - **IF** important fields changed (dates, type, property, flags)
        - **THEN** mark ALL existing records for this UID as **"Status"** = "Old"
        - **THEN** create new record with **"Status"** = "Modified"
        - **THEN** preserve all HCP service fields from latest active record
      - **IF** no important changes
        - **THEN** leave existing records unchanged
    - **IF** event UID + feed URL does not exist
      - **THEN** create new record with **"Status"** = "New"
  
  - **FOR EACH** existing Airtable record not found in current feed
    - **IF** record is active (Status = "New" or "Modified") and checkout date is future
      - **THEN** mark ALL records for this UID as **"Status"** = "Old"
      - **THEN** create new record with **"Status"** = "Removed"

- **STEP 6**: Update Property ID links
  - **FOR EACH** reservation record with missing **"Property ID"** link
  - **IF** **"ICS URL"** has mapping in **"ICS Feeds"** table
    - **THEN** update **"Property ID"** = linked property from feeds table

- **STEP 7**: Update **"ICS Cron"** table tracking
  - **FOR EACH** processed feed
    - **THEN** update or create tracking record with:
      - **"ICS URL VEVENTS #"** = total events found
      - **"ICS URL VEVENTS Reservations"** = events processed
      - **"Last Run"** = current timestamp
      - **"ICS URL Response"** = "Success" or error message

  - **IF** feed inaccessible
    - **THEN** log error to `automation_[environment]*.log`
    - **THEN** update tracking with error message
    - **THEN** continue with next feed

---

## 🛠️ **Manual Job Creation Flow**

**Trigger**: User clicks **"Create Job & Sync Status"** button in Airtable
**Prerequisites**: Record must have **"Property ID"** link and **"Final Service Time"**

### **Primary Logic**:
- **IF** **"Service Job ID"** field is empty
  - **THEN** validate required fields:
    
    **IF** **"Property ID"** link exists AND **"Final Service Time"** exists
    - **THEN** get property record from **"Property ID"** link
    - **THEN** get HCP Customer ID from property record's **"HCP Customer ID"** field (links to Customers table)
    - **THEN** get HCP Address ID from property record's **"HCP Address ID"** field
    
    **IF** property missing **"HCP Customer ID"** OR **"HCP Address ID"**
    - **THEN** return error: "Property missing HCP Customer ID or Address ID"
    - **THEN** no job created (property must be pre-configured)
    
    **IF** property has valid HCP IDs
    - **THEN** create HCP job using existing customer/address:
      - customer_id = HCP Customer ID from property
      - address_id = HCP Address ID from property  
      - scheduled_start = **"Final Service Time"**
      - scheduled_end = scheduled_start + 1 hour
      - work_status = "scheduled"
      - assigned_employee_ids = default employee
    
    - **THEN** copy line items from job template:
      - Get template ID from property record based on **"Service Type"**
      - Copy template line items to new job
      - Update first line item name with service details:
      
      **IF** **"Service Line Custom Instructions"** field has value
      - **AND IF** instructions length > 200 characters
        - **THEN** truncate to 197 characters + "..."
      - **THEN** set line item name = **"Service Line Custom Instructions"** + " - " + service name
      
      **Service Name Construction Order**:
      
      **STEP 1: Determine base service name**
      - **IF** **"Same-day Turnover"** = true
        - **THEN** baseSvcName = **"Service Type"** + " STR SAME DAY"
      - **ELSE IF** **"Service Type"** = "Turnover" AND checkout date exists
        - **THEN** find next reservation for same property
        - **IF** next reservation found: baseSvcName = **"Service Type"** + " STR Next Guest [Month Day]"
        - **ELSE**: baseSvcName = **"Service Type"** + " STR Next Guest Unknown"
      - **ELSE** baseSvcName = **"Service Type"** + " STR Next Guest Unknown"
      
      **STEP 2: Check for long-term guest**
      - **IF** (Check-out Date - Check-in Date) >= 14 days
        - **THEN** isLongTermGuest = true
      
      **STEP 3: Build final service name**
      - **IF** **"Service Line Custom Instructions"** has value AND isLongTermGuest = true
        - **THEN** svcName = **"Custom Instructions"** + " - LONG TERM GUEST DEPARTING " + baseSvcName
      - **ELSE IF** **"Service Line Custom Instructions"** has value AND isLongTermGuest = false
        - **THEN** svcName = **"Custom Instructions"** + " - " + baseSvcName
      - **ELSE IF** no custom instructions AND isLongTermGuest = true
        - **THEN** svcName = "LONG TERM GUEST DEPARTING " + baseSvcName
      - **ELSE** svcName = baseSvcName
      
      **Example Scenarios**:
      - Same-day + Long-term + Custom: "CUSTOM TEXT - LONG TERM GUEST DEPARTING Turnover STR SAME DAY"
      - Same-day + Long-term + No custom: "LONG TERM GUEST DEPARTING Turnover STR SAME DAY"
      - Same-day + Regular guest: "CUSTOM TEXT - Turnover STR SAME DAY"
      - Regular + Long-term: "CUSTOM TEXT - LONG TERM GUEST DEPARTING Turnover STR Next Guest July 15"
    
    - **THEN** update Airtable record:
      - **"Service Job ID"** = created job ID
      - **"Job Creation Time"** = current timestamp
      - **"Service Appointment ID"** = appointment ID (if available)

- **IF** **"Service Job ID"** field already has value
  - **THEN** return message: "Job already exists"
  - **THEN** no action taken

---

## ⏰ **Schedule Management Flow**

**Trigger**: User clicks **"Add/Update Schedule"** button in Airtable
**Prerequisites**: Valid **"Service Job ID"** must exist

### **Primary Logic**:
- **IF** **"Service Job ID"** field has value
  - **THEN** call AirScripts API `/api/[environment]/schedules/update-schedule` endpoint
  - **THEN** check current schedule status in HCP:
    
    **IF** job has no schedule (schedule is null)
    - **THEN** create new schedule in HCP
    - **THEN** set **"Sync Status"** = "Creating Schedule"
    
    **IF** job has existing schedule with wrong date or time
    - **THEN** update existing schedule in HCP
    - **THEN** set **"Sync Status"** = "Updating Date" or "Updating Time"
    
  - **THEN** determine service time priority:
    
    **IF** **"Custom Service Time"** field has value
    - **THEN** use **"Custom Service Time"** for scheduling
    
    **IF** **"Custom Service Time"** field is empty
    - **THEN** use **"Final Service Time"** field for scheduling
  
  - **THEN** create or update HCP job schedule via API:
    - scheduled_start = **"Service Date"** + selected service time
    - scheduled_end = scheduled_start + 1 hour (default duration)
    - arrival_window = 60 minutes (default)
    - notify = true (notify customer)
    - notify_pro = true (notify employee)
    - dispatched_employees = [default employee ID]
  
  - **THEN** API updates Airtable record:
    - **"Scheduled Service Time"** = updated scheduled_start (ISO format)
    - **"Sync Status"** = "Synced", "Wrong Date", "Wrong Time", "Not Created", or "Creating Schedule"
    - **"Sync Details"** = comparison details between expected and actual
    - **"Sync Date and Time"** = current Arizona timestamp
    - **"Job Status"** = current HCP work_status (mapped to Airtable values)
    - **"Service Appointment ID"** = fetched from HCP if missing

- **IF** **"Service Job ID"** field is empty
  - **THEN** display error message: "Must create job first"
  - **THEN** no action taken

- **IF** API call fails
  - **THEN** log error details
  - **THEN** update **"Sync Status"** = "Error"
  - **THEN** update **"Sync Details"** = error message

---

## 🔄 **Webhook Status Sync Flow**

**Trigger**: Real-time webhook from HousecallPro
**Endpoint**: `https://servativ.themomentcatchers.com/webhooks/hcp`

### **Primary Logic**:
- **IF** webhook received with valid HCP signature OR forwarded from Servativ (X-Internal-Auth header)
  - **THEN** parse webhook event type and route to appropriate handler:
    
    **IF** event starts with "job.appointment."
    - **THEN** extract appointment data and job_id from webhook
    - **THEN** find Airtable record with matching **"Service Job ID"** field
    - **THEN** check if record should be updated (has **"Service Job ID"** OR **"Entry Source"** = "HCP")
    
    **IF** event = "job.appointment.scheduled"
    - **THEN** update fields:
      - **"Service Appointment ID"** = appointment.id
      - **"Assignee"** = formatted employee names from dispatched_employees
      - **"Job Status"** = "Scheduled"
      - **"Scheduled Service Time"** = appointment.start_time
      - **"Sync Date and Time"** = current Arizona timestamp
      - **"Sync Details"** = "Appointment [ID] scheduled, assignee: [names]"
    
    **IF** event = "job.appointment.rescheduled"
    - **THEN** update fields:
      - **"Service Appointment ID"** = appointment.id
      - **"Assignee"** = formatted employee names from dispatched_employees
      - **"Scheduled Service Time"** = appointment.start_time
      - **"Sync Date and Time"** = current Arizona timestamp
      - **"Sync Details"** = "Appointment [ID] rescheduled, assignee: [names]"
    
    **IF** event = "job.appointment.appointment_discarded"
    - **THEN** update fields:
      - **"Job Status"** = "Unscheduled"
      - **"Service Appointment ID"** = null
      - **"On My Way Time"** = null
      - **"Job Started Time"** = null
      - **"Job Completed Time"** = null
      - **"Scheduled Service Time"** = null
      - **"Assignee"** = null
      - **"Sync Date and Time"** = current Arizona timestamp
      - **"Sync Details"** = "Appointment [ID] discarded, job unscheduled"
    
    **IF** event = "job.appointment.appointment_pros_assigned"
    - **THEN** update fields:
      - **"Service Appointment ID"** = appointment.id
      - **"Assignee"** = formatted employee names from dispatched_employees
      - **"Sync Date and Time"** = current Arizona timestamp
      - **"Sync Details"** = "Pros assigned to appointment [ID]: [names]"
    
    **IF** event = "job.appointment.appointment_pros_unassigned"
    - **THEN** update fields:
      - **"Service Appointment ID"** = appointment.id
      - **"Assignee"** = remaining employee names OR null if none
      - **"Sync Date and Time"** = current Arizona timestamp
      - **"Sync Details"** = "Pros unassigned from appointment [ID], remaining: [names]"
    
    **IF** event is regular job event (not appointment)
    - **THEN** extract job data and job.id from webhook
    - **THEN** find Airtable record with matching **"Service Job ID"** field
    - **THEN** update job status using status mapping:
      - HCP "completed" → **"Job Status"** = "Completed"
      - HCP "canceled" → **"Job Status"** = "Canceled"
      - HCP "unscheduled"/"needs scheduling" → **"Job Status"** = "Unscheduled"
      - HCP "scheduled" → **"Job Status"** = "Scheduled"
      - HCP "in progress" → **"Job Status"** = "In Progress"
    - **THEN** update work timestamps:
      - **"On My Way Time"** = job.work_timestamps.on_my_way_at
      - **"Job Started Time"** = job.work_timestamps.started_at
      - **"Job Completed Time"** = job.work_timestamps.completed_at
    - **THEN** update employee assignment and scheduling from job data

- **IF** webhook signature invalid AND not forwarded from Servativ
  - **THEN** log security warning
  - **THEN** return 200 status (to prevent webhook disabling)
  - **THEN** no data updates performed

- **IF** no matching reservation found for job ID
  - **THEN** log warning message
  - **THEN** return 200 status (successful receipt)

---

## 📧 **Gmail OAuth Token Management Flow**

**Trigger**: Every 6 hours at :30 minutes (12:30 AM, 6:30 AM, 12:30 PM, 6:30 PM)
**System Action**: Automated OAuth token health monitoring and refresh

### **Primary Logic**:
- **STEP 1**: Check Gmail OAuth token validity
  - **IF** token exists and valid: log success and exit
  - **IF** token missing or expired: proceed to refresh
  
- **STEP 2**: Attempt automatic token refresh
  - **IF** refresh token available: attempt refresh
  - **IF** refresh successful: save new token and log success
  - **IF** refresh fails: log error requiring manual intervention
  
- **STEP 3**: Validate refreshed token
  - **THEN** test Gmail API connection with new token
  - **THEN** log results to `automation_[environment]*.log`

**Purpose**: Prevents 99% of manual OAuth interventions, maintains continuous Gmail CSV download capability

---

## 🔄 **Service Field Update Automation**

**Trigger**: Manual execution or scheduled maintenance
**System Action**: Batch update service descriptions and next guest dates

### **Primary Logic** (update_service_fields.py):
- **STEP 1**: Query all reservations from Airtable
  - **IF** single record mode: process only specified record
  - **IF** batch mode: process all active reservations
  
- **STEP 2**: Calculate next guest information
  - **FOR EACH** reservation with checkout date:
    - **THEN** find next reservation at same property
    - **IF** next reservation found: format date as "Next Guest [Month Day]"
    - **IF** no next reservation: set as "Next Guest Unknown"
  
- **STEP 3**: Update service line descriptions
  - **THEN** combine service type with next guest information
  - **THEN** apply custom instructions if present
  - **THEN** update **"Service Line Description"** field
  
- **STEP 4**: Parallel processing
  - **THEN** use configurable worker threads for batch updates
  - **THEN** apply rate limiting to prevent API throttling

---

## 🎯 **Controller-Based Automation Orchestration** 

**Trigger**: Every 4 hours via cron
**System Action**: Environment-aware automation execution with Airtable tracking

### **Primary Logic** (controller.py):
- **STEP 1**: Check automation status in Airtable **"Automation Control"** table
  - **FOR EACH** automation: query **"Name"** field match
  - **IF** **"Active"** field = true: proceed with automation
  - **IF** **"Active"** field = false: skip automation and log
  
- **STEP 2**: Execute active automations in sequence:
  - **"iTrip CSV Gmail"** → run_gmail_automation()
  - **"Evolve"** → run_evolve_automation()
  - **"CSV Files"** → run_csv_automation()
  - **"ICS Calendar"** → run_ics_automation()
  - **"Add/Sync Service Jobs"** → run_hcp_automation()
  
- **STEP 3**: Track execution metrics for each automation
  - **THEN** record start time (Arizona timezone)
  - **THEN** catch all exceptions and errors
  - **THEN** calculate duration and success status
  
- **STEP 4**: Update automation tracking in Airtable
  - **THEN** update **"Last Ran Time"** = execution timestamp
  - **THEN** update **"Sync Details"** = success/error details with duration
  - **IF** success: prefix with "✅", **IF** error: prefix with "❌"

---

## 🌐 **AirScripts API Server Management**

**Trigger**: Persistent HTTP server for Airtable button automations
**System Action**: Environment-specific API endpoints with authentication

### **Primary Logic** (server.js):
- **STEP 1**: Environment separation enforcement
  - **"/api/dev/*"** endpoints → force development environment
  - **"/api/prod/*"** endpoints → force production environment
  - **Legacy "/api/*"** endpoints → return 410 error (removed)
  
- **STEP 2**: Security and rate limiting
  - **IF** **"X-API-Key"** header missing OR incorrect: return 401 Unauthorized
  - **THEN** apply rate limiting: 100 requests per minute per IP
  - **THEN** CORS policy: only allow Airtable domains
  
- **STEP 3**: Route processing
  - **"/api/[env]/jobs"** → job creation and management (createJob.js)
  - **"/api/[env]/schedules"** → schedule updates (schedules.js)
  - **"/health"** → health check (no authentication required)
  
- **STEP 4**: Request handling
  - **THEN** inject **"forceEnvironment"** into request based on URL path
  - **THEN** pass environment to handlers for config selection
  - **THEN** log all requests via morgan middleware

---

## 🔍 **Same-Day Turnover Detection Logic**

**Trigger**: During any data ingestion process
**System Action**: Automatic detection and flagging

### **Primary Logic**:
- **FOR EACH** newly processed reservation
  - **THEN** query existing reservations for same property:
    
    **IF** another reservation exists WHERE:
    - **"Property Name"** matches exactly
    - **AND** other reservation's **"Check-in Date"** = current reservation's **"Check-out Date"**
    - **AND** dates are same calendar day
    
    **THEN** mark both reservations:
    - Set **"Same Day"** = true for both records
    - Set **"Service Time"** = "8:00 AM" for checkout service
    - Set **"Service Time"** = "2:00 PM" for check-in prep service
    - Add to **"Notes"**: "SAME DAY TURNOVER - Priority scheduling required"

---

## 📊 **Field Update Tracking Matrix**

### **Automated Updates (System-Driven)**:
| Field Name | Updated By | Trigger | New Value Source |
|------------|------------|---------|------------------|
| **"Created Date"** | System | New record creation | Current timestamp |
| **"Modified Date"** | System | Any record change | Current timestamp |
| **"Source"** | System | Data ingestion | "iTrip", "Evolve", "ICS Feed", "Manual" |
| **"Same Day"** | System | Turnover detection | true/false |
| **"Service Date"** | System | Date calculation | Check-out date |
| **"Service Time"** | System | Same-day logic | "8:00 AM" or "11:00 AM" |
| **"HCP Job ID"** | System | Job creation | HCP job.id |
| **"HCP Customer ID"** | System | Customer creation/lookup | HCP customer.id |
| **"Scheduled Start"** | System | HCP sync/webhook | HCP job.scheduled_start |
| **"Scheduled End"** | System | HCP sync/webhook | HCP job.scheduled_end |
| **"Assigned Employee"** | System | Webhook sync | HCP employee name |
| **"Job Status"** | System | Webhook sync | HCP work_status |
| **"Status"** | System | Workflow progression | "New", "Processing", "Job Created", "Scheduled", "Completed" |

### **Manual Updates (User-Driven)**:
| Field Name | Updated By | Trigger | Purpose |
|------------|------------|---------|---------|
| **"Custom Service Time"** | User | Manual edit | Override default service time |
| **"Service Line Custom Instructions"** | User | Manual edit | Add special instructions (200 char limit) |
| **"Notes"** | User | Manual edit | Additional service notes |
| **"Phone"** | User | Manual edit | Correct contact information |
| **"Email"** | User | Manual edit | Correct contact information |

### **One-Time Updates (Creation Only)**:
| Field Name | Set Once By | When | Cannot Be Changed |
|------------|-------------|------|-------------------|
| **"Reservation UID"** | System | Record creation | System-generated unique ID |
| **"Guest Name"** | System | Data ingestion | From source data |
| **"Property Name"** | System | Data ingestion | From source data |
| **"Check-in Date"** | System | Data ingestion | From source data |
| **"Check-out Date"** | System | Data ingestion | From source data |
| **"Address Line 1"** | System | Data ingestion | From source data |
| **"City"** | System | Data ingestion | From source data |
| **"State"** | System | Data ingestion | From source data |
| **"Zip"** | System | Data ingestion | From source data |

---

## 🎛️ **Environment-Specific Configurations**

### **Development Environment**:
- **Airtable Base ID**: `app67yWFv0hKdl6jM`
- **CSV Directory**: `CSV_process_development/`, `CSV_done_development/`
- **Log Files**: `automation_dev_YYYY-MM-DD.log`
- **ICS Feeds**: 255 configured feeds
- **Cron Schedule**: `:10` minutes (4:10, 8:10, 12:10, etc.)

### **Production Environment**:
- **Airtable Base ID**: `appZzebEIqCU5R9ER`
- **CSV Directory**: `CSV_process_production/`, `CSV_done_production/`
- **Log Files**: `automation_prod_YYYY-MM-DD.log`
- **ICS Feeds**: 246 configured feeds
- **Cron Schedule**: `:00` minutes (4:00, 8:00, 12:00, etc.)

---

## 🚨 **Error Handling Logic**

### **Data Validation Failures**:
- **IF** required field missing during processing
  - **THEN** log error to `automation_[environment]*.log`
  - **THEN** skip record and continue processing
  - **THEN** send notification email to admin

### **API Communication Failures**:
- **IF** HousecallPro API returns error
  - **THEN** retry up to 3 times with exponential backoff
  - **THEN** log failure details
  - **THEN** continue with next operation

### **Authentication Failures**:
- **IF** Gmail OAuth token expired
  - **THEN** attempt automatic refresh
  - **THEN** IF refresh fails, log manual intervention required
- **IF** HCP API key invalid
  - **THEN** log authentication error
  - **THEN** skip HCP operations for current cycle

---

*This document captures the complete logical flow of the property management automation system, covering every automated trigger, manual action, field update, and decision point in natural language with exact field names and update operations.*