# HousecallPro Integration - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** Natural language flow for HCP job creation, scheduling, and webhook synchronization

---

## 🛠️ **HCP INTEGRATION TRIGGERS**

**Manual Job Creation**: User clicks "Create Job & Sync Status" button in Airtable
**Manual Scheduling**: User clicks "Add/Update Schedule" button in Airtable  
**Real-time Updates**: HCP webhooks for status changes, appointments, assignments

---

## 📋 **PRIMARY LOGIC FLOW**

### **STEP 1**: Manual Job Creation Process
- **Trigger Validation**:
  - **IF** **"Service Job ID"** field is empty: proceed with job creation
  - **IF** **"Service Job ID"** field has value: return "Job already exists"

- **Prerequisites Check**:
  - **IF** **"Property ID"** link exists AND **"Final Service Time"** exists: proceed
  - **IF** either field missing: return validation error

- **Property Configuration Validation**:
  - **THEN** get property record from **"Property ID"** link
  - **THEN** extract **"HCP Customer ID"** and **"HCP Address ID"** from property record
  - **IF** property missing **"HCP Customer ID"** OR **"HCP Address ID"**:
    - **THEN** return error: "Property missing HCP Customer ID or Address ID"
    - **THEN** no job created (property must be pre-configured)

### **STEP 2**: HCP Job Creation with Template Application
- **Create HCP Job**:
  - **THEN** use existing customer/address from property configuration:
    - customer_id = HCP Customer ID from property
    - address_id = HCP Address ID from property
    - scheduled_start = **"Final Service Time"**
    - scheduled_end = scheduled_start + 1 hour (default duration)
    - work_status = "scheduled"
    - assigned_employee_ids = default employee from environment config

- **Job Template Processing**:
  - **THEN** get template ID from property record based on **"Service Type"**
  - **THEN** copy template line items to new job
  - **THEN** update first line item name with service details

### **STEP 3**: Service Line Name Construction (Enhanced v2.2.8)
- **Custom Instructions Processing**:
  - **IF** **"Service Line Custom Instructions"** field has value:
    - **IF** instructions length > 200 characters: truncate to 197 characters + "..."
    - **THEN** customInstructions = processed instructions
  - **ELSE** customInstructions = null

- **Owner Arrival Detection** (New in v2.2.8):
  - **THEN** check for Block entries at same property
  - **IF** Block with checkout date = (current reservation checkout date OR checkout date + 1 day):
    - **THEN** isOwnerArriving = true
    - **THEN** set **"Owner Arriving"** field = true in Airtable

- **Base Service Name Construction**:
  - **IF** **"Same-day Turnover"** = true:
    - **THEN** baseSvcName = **"Service Type"** + " STR SAME DAY"
  - **ELSE IF** **"Service Type"** = "Turnover" AND checkout date exists:
    - **THEN** find next reservation for same property
    - **IF** next reservation found: baseSvcName = **"Service Type"** + " STR Next Guest [Month Day]"
    - **ELSE** baseSvcName = **"Service Type"** + " STR Next Guest Unknown"
  - **ELSE** baseSvcName = **"Service Type"** + " STR Next Guest Unknown"

- **Long-Term Guest Detection**:
  - **IF** (Check-out Date - Check-in Date) >= 14 days: isLongTermGuest = true

- **Final Service Name Assembly** (Hierarchical Order):
  1. **Custom Instructions** (if present)
  2. **Owner Arriving** (if detected)
  3. **Long Term Guest Departing** (if 14+ day stay)
  4. **Base Service Name**

  **Construction Logic**:
  - **IF** customInstructions AND isOwnerArriving AND isLongTermGuest:
    - **THEN** svcName = "customInstructions - OWNER ARRIVING - LONG TERM GUEST DEPARTING - baseSvcName"
  - **IF** customInstructions AND isOwnerArriving AND NOT isLongTermGuest:
    - **THEN** svcName = "customInstructions - OWNER ARRIVING - baseSvcName"
  - **IF** customInstructions AND NOT isOwnerArriving AND isLongTermGuest:
    - **THEN** svcName = "customInstructions - LONG TERM GUEST DEPARTING - baseSvcName"
  - **IF** customInstructions AND NOT isOwnerArriving AND NOT isLongTermGuest:
    - **THEN** svcName = "customInstructions - baseSvcName"
  - **Continue pattern for all combinations...**

### **STEP 4**: Airtable Record Updates After Job Creation
- **Update Service Fields**:
  - **"Service Job ID"** = created job ID
  - **"Job Creation Time"** = current timestamp
  - **"Service Appointment ID"** = appointment ID (if created)
  - **"Owner Arriving"** = true (if owner arrival detected)

### **STEP 5**: Schedule Management Process
- **Trigger Validation**:
  - **IF** **"Service Job ID"** field has value: proceed with scheduling
  - **IF** **"Service Job ID"** field is empty: return "Must create job first"

- **Service Time Priority**:
  - **IF** **"Custom Service Time"** field has value: use Custom Service Time
  - **IF** **"Custom Service Time"** field is empty: use **"Final Service Time"**

- **HCP Schedule Status Check**:
  - **THEN** call AirScripts API `/api/[environment]/schedules/update-schedule` endpoint
  - **THEN** compare current HCP schedule with expected schedule

  **Schedule Update Logic**:
  - **IF** job has no schedule (schedule is null):
    - **THEN** create new schedule in HCP
    - **THEN** set **"Sync Status"** = "Creating Schedule"

  - **IF** job has existing schedule with wrong date or time:
    - **THEN** update existing schedule in HCP
    - **THEN** set **"Sync Status"** = "Updating Date" or "Updating Time"

### **STEP 6**: HCP Schedule API Processing
- **Create/Update Schedule**:
  - scheduled_start = **"Service Date"** + selected service time
  - scheduled_end = scheduled_start + 1 hour (default duration)
  - arrival_window = 60 minutes (default)
  - notify = true (notify customer)
  - notify_pro = true (notify employee)
  - dispatched_employees = [default employee ID]

- **Airtable Sync Updates**:
  - **"Scheduled Service Time"** = updated scheduled_start (ISO format)
  - **"Sync Status"** = "Synced", "Wrong Date", "Wrong Time", "Not Created", or "Creating Schedule"
  - **"Sync Details"** = comparison details between expected and actual
  - **"Sync Date and Time"** = current Arizona timestamp
  - **"Job Status"** = current HCP work_status (mapped to Airtable values)
  - **"Service Appointment ID"** = fetched from HCP if missing

### **STEP 7**: Real-Time Webhook Processing
- **Webhook Reception and Validation**:
  - **IF** webhook received with valid HCP signature OR forwarded from Servativ (X-Internal-Auth header):
    - **THEN** parse webhook event type and route to appropriate handler
  - **IF** webhook signature invalid AND not forwarded: log security warning, return 200

- **Environment-Specific Routing**:
  - **Development webhooks**: `/webhooks/hcp-dev` → updates dev Airtable base
  - **Production webhooks**: `/webhooks/hcp` → updates prod Airtable base

- **Appointment Event Processing**:
  - **IF** event starts with "job.appointment.":
    - **THEN** extract appointment data and job_id from webhook
    - **THEN** find Airtable record with matching **"Service Job ID"** field

  **Event-Specific Updates**:
  - **"job.appointment.scheduled"**:
    - **"Service Appointment ID"** = appointment.id
    - **"Assignee"** = formatted employee names
    - **"Job Status"** = "Scheduled"
    - **"Scheduled Service Time"** = appointment.start_time
    - **"Sync Details"** = "Appointment [ID] scheduled, assignee: [names] - [timestamp]"

  - **"job.appointment.rescheduled"**:
    - **"Scheduled Service Time"** = new appointment.start_time
    - **"Sync Details"** = "Appointment [ID] rescheduled, assignee: [names] - [timestamp]"

  - **"job.appointment.appointment_discarded"**:
    - **"Job Status"** = "Unscheduled"
    - Clear: **"Service Appointment ID"**, **"On My Way Time"**, **"Job Started Time"**, **"Job Completed Time"**, **"Scheduled Service Time"**, **"Assignee"**
    - **"Sync Details"** = "Appointment [ID] discarded, job unscheduled - [timestamp]"

### **STEP 8**: Job Status Synchronization
- **Regular Job Event Processing**:
  - **THEN** extract job data and job.id from webhook
  - **THEN** update job status using HCP → Airtable mapping:
    - HCP "completed" → **"Job Status"** = "Completed"
    - HCP "canceled" → **"Job Status"** = "Canceled"
    - HCP "unscheduled"/"needs scheduling" → **"Job Status"** = "Unscheduled"
    - HCP "scheduled" → **"Job Status"** = "Scheduled"
    - HCP "in progress" → **"Job Status"** = "In Progress"

- **Work Timestamp Updates**:
  - **"On My Way Time"** = job.work_timestamps.on_my_way_at
  - **"Job Started Time"** = job.work_timestamps.started_at
  - **"Job Completed Time"** = job.work_timestamps.completed_at

---

## 🚨 **ERROR HANDLING**

### **Job Creation Errors**:
- **Missing property configuration**: Return clear error message, no job created
- **HCP API failures**: Retry with exponential backoff, log detailed error
- **Template not found**: Log template error, create job without line items

### **Scheduling Errors**:
- **Invalid service time**: Return validation error, suggest valid format
- **HCP schedule conflicts**: Log conflict details, attempt resolution
- **API timeouts**: Retry up to 3 times, then mark as error

### **Webhook Processing Errors**:
- **No matching reservation**: Log warning, return 200 (successful receipt)
- **Invalid webhook data**: Log malformed data, continue processing
- **Airtable update failures**: Retry update, log if persistent failure

---

## 🔧 **ENVIRONMENT CONFIGURATION**

### **Development Environment**:
- **HCP Account**: Boris's development account
- **API Endpoints**: `/api/dev/*`
- **Webhook URL**: `/webhooks/hcp-dev` (port 5001)
- **Airtable Base**: `app67yWFv0hKdl6jM`

### **Production Environment**:
- **HCP Account**: Production account (forwarded webhooks)
- **API Endpoints**: `/api/prod/*`
- **Webhook URL**: `/webhooks/hcp` (port 5000)
- **Airtable Base**: `appZzebEIqCU5R9ER`

---

*This document captures the complete logical flow for HousecallPro integration, from manual job creation through real-time webhook synchronization, with enhanced owner detection capabilities.*