# System Overview - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of the property management automation system, including all core business entities, workflows, UI fields, automation triggers, and integration logic.

## System Purpose and Scope

The property management automation system orchestrates cleaning services for vacation rental properties by:
- Ingesting reservation data from multiple sources (email CSVs, ICS calendar feeds, web scraping)
- Creating and managing service jobs in HousecallPro
- Tracking job status and employee assignments
- Managing property and customer information
- Providing real-time status updates via webhooks

## Core Business Entities

### Primary Data Flow
```
Email/ICS/Web → Airtable Reservations → HCP Jobs → Service Completion
```

### Key System Components

#### **Data Ingestion Layer**
- **CloudMailin Webhook**: Receives iTrip reservation emails
- **ICS Feed Processor**: Syncs calendar data from 246+ feeds
- **Evolve Scraper**: Selenium-based web scraping
- **Manual Entry**: Direct Airtable input

#### **Data Storage Layer**
- **Airtable (Primary Database)**:
  - Development Base: `app67yWFv0hKdl6jM`
  - Production Base: `appZzebEIqCU5R9ER`
  - Tables: Reservations, Properties, Customers, Settings, ICS Feeds
  
#### **Service Management Layer**
- **HousecallPro Integration**:
  - Job creation and scheduling
  - Employee assignment
  - Status tracking
  - Invoice management

#### **Automation Layer**
- **Python Controller**: Orchestrates all automated processes
- **Cron Jobs**: Every 4 hours (prod at :00, dev at :10)
- **Webhook Handlers**: Real-time updates
- **API Server**: REST endpoints for UI operations

## Business Workflows

### 1. Reservation Ingestion Workflow

#### **Email-based Reservations (iTrip)**
**Trigger**: Email arrives at CloudMailin
**Business Logic**:
1. **Email Processing**:
   - CloudMailin receives email at configured address
   - Extracts CSV attachment
   - Sends webhook to automation system

2. **CSV Parsing**:
   - System downloads CSV to `CSV_process_[environment]/`
   - Parses columns: Guest Name, Property, Check-in, Check-out, etc.
   - Validates required fields

3. **UID Generation**:
   ```
   UID = {source}_{property_slug}_{checkin}_{checkout}_{guest_lastname}
   Example: itrip_beach_house_2025-07-15_2025-07-20_smith
   ```

4. **Duplicate Detection**:
   - Searches Airtable for existing UID
   - If found: Updates existing record
   - If not found: Creates new record

5. **Record Creation/Update**:
   - Links to Property record
   - Sets Status = "New"
   - Populates all guest information
   - Moves CSV to `CSV_done_[environment]/`

#### **Calendar Feed Reservations (ICS)**
**Trigger**: Cron job every 4 hours
**Business Logic**:
1. **Feed Processing**:
   - Reads active ICS feed URLs from Airtable
   - Downloads .ics files concurrently
   - Parses VEVENT blocks

2. **Composite UID Generation**:
   ```
   UID = {source}_{property_slug}_{checkin}_{checkout}_{uid_hash}
   Example: airbnb_beach_house_2025-07-15_2025-07-20_abc123
   ```
   - Uses last 6 characters of original UID for uniqueness

3. **Synchronization Logic**:
   - Marks all existing records for property as candidates for removal
   - For each event in feed:
     - If exists: Update and unmark for removal
     - If new: Create record
   - Records still marked get Status = "Removed"

4. **Special Handling**:
   - Timezone conversion to MST
   - Entry Type detection (Reservation vs Block)
   - Guest name extraction from SUMMARY field

#### **Web Scraping (Evolve)**
**Trigger**: Cron job every 4 hours
**Business Logic**:
1. **Browser Automation**:
   - Selenium ChromeDriver in headless mode
   - Logs into Evolve portal
   - Navigates through reservation pages

2. **Data Extraction**:
   - Scrapes reservation table
   - Extracts: Guest name, property, dates, confirmation number
   - Handles pagination

3. **Record Management**:
   - Creates records with Source = "Evolve"
   - Uses similar UID pattern
   - Updates existing reservations

### 2. Job Creation Workflow

#### **"Create Job & Sync Status" Button**
**UI Location**: Airtable Reservations table
**Prerequisites**: 
- Complete address information
- Valid guest name
- Service date populated

**Business Logic**:
1. **Validation Phase**:
   ```javascript
   // Check required fields
   if (!reservation['Guest Name'] || !reservation['Property']) {
       throw new Error('Missing required fields');
   }
   
   // Check for existing job
   if (reservation['HCP Job ID']) {
       throw new Error('Job already exists');
   }
   ```

2. **Customer Creation/Lookup**:
   - Search HCP for existing customer by name
   - If not found:
     - Create customer with guest information
     - Add property address to customer
   - Store HCP Customer ID in Airtable

3. **Job Creation**:
   ```javascript
   const job = {
       customer_id: hcpCustomerId,
       address_id: addressId,
       scheduled_start: serviceDateTime,
       scheduled_end: addHours(serviceDateTime, 2),
       description: 'Property Turnover Service',
       work_status: 'scheduled'
   };
   ```

4. **Service Line Creation**:
   - Name includes any custom instructions (200 char limit)
   - Checks for special flags:
     - Long Term Guest (14+ days): Adds "LONG TERM GUEST DEPARTING"
     - Owner Arriving: Adds "OWNER ARRIVING"
   - Example: "Custom text - OWNER ARRIVING - Turnover STR Next Guest July 3"

5. **Airtable Updates**:
   - HCP Job ID = created job ID
   - Status = "Job Created"
   - Service Sync Details = success message with timestamp

### 3. Schedule Management Workflow

#### **"Add/Update Schedule" Button**
**UI Location**: Airtable Reservations table
**Prerequisites**: Valid HCP Job ID exists

**Business Logic**:
1. **Time Calculation**:
   - Reads "Custom Service Time" or defaults to "Service Time"
   - Converts to MST (Mountain Standard Time)
   - Calculates end time based on service duration

2. **HCP API Update**:
   ```javascript
   const update = {
       scheduled_start: new Date(serviceDate + ' ' + serviceTime),
       scheduled_end: new Date(serviceDate + ' ' + endTime),
       arrival_window: 30 // minutes
   };
   ```

3. **Employee Assignment** (if specified):
   - Updates assigned_employee_ids array
   - Validates employee exists and is active

4. **Sync Back to Airtable**:
   - Updates "Scheduled Start" and "Scheduled End"
   - Updates "Schedule Sync Details" with timestamp
   - If schedule changed significantly, adds alert

#### **Same-Day Turnover Logic**
**Detection**: Check-out date equals check-in date for same property
**Special Handling**:
1. Sets "Same Day" flag = true
2. Prioritizes earlier service time
3. Adds note to job description
4. May assign to specific experienced cleaners

### 4. Status Synchronization Workflow

#### **HCP Webhook Processing**
**Endpoint**: `https://servativ.themomentcatchers.com/webhooks/hcp`
**Authentication**: HMAC signature verification + internal auth header

**Business Logic**:
1. **Webhook Receipt**:
   - Validates signature
   - Always returns 200 OK (prevents HCP from disabling)
   - Logs raw payload

2. **Event Processing**:
   ```python
   if event_type == 'job:update':
       # Update job status
       if 'work_status' in data:
           update_airtable_status(job_id, data['work_status'])
       
       # Update employee assignment
       if 'assigned_employees' in data:
           update_airtable_employees(job_id, data['assigned_employees'])
   ```

3. **Status Mapping**:
   - HCP "in_progress" → Airtable "In Progress"
   - HCP "completed" → Airtable "Completed"
   - HCP "canceled" → Airtable "Canceled"

4. **Activity Logging**:
   - Updates "Service Sync Details" with each change
   - Format: "[Action] - Jul 10, 3:45 PM"

### 5. Long-Term Guest Detection

**Business Logic**:
1. **Detection**:
   ```python
   stay_duration = (checkout_date - checkin_date).days
   if stay_duration >= 14:
       record['Long Term Guest'] = True
   ```

2. **Service Line Impact**:
   - Adds "LONG TERM GUEST DEPARTING" to service name
   - May adjust service duration
   - Alerts cleaners to expect more intensive cleaning

### 6. Owner Arrival Detection

**Business Logic**:
1. **Detection Algorithm**:
   ```python
   # Check if owner block starts same/next day after checkout
   for block in upcoming_blocks:
       if block['Entry Type'] == 'Block' and block['property'] == reservation['property']:
           days_between = (block['checkin'] - reservation['checkout']).days
           if days_between <= 1:
               reservation['Owner Arriving'] = True
   ```

2. **Service Line Impact**:
   - Adds "OWNER ARRIVING" to service name
   - May trigger additional quality checks
   - Ensures property is in perfect condition

## Environment Management

### Development Environment
- **Purpose**: Testing and development
- **Airtable Base**: `app67yWFv0hKdl6jM`
- **HCP Account**: Boris's sandbox account
- **Webhook URL**: `https://servativ.themomentcatchers.com/webhooks/hcp-dev`
- **CSV Directory**: `CSV_*_development/`
- **Logs**: `automation_dev*.log`, `webhook_development.log`
- **Cron**: Runs at :10 past the hour

### Production Environment
- **Purpose**: Live operations
- **Airtable Base**: `appZzebEIqCU5R9ER`
- **HCP Account**: Production account (via 3rd party)
- **Webhook URL**: `https://servativ.themomentcatchers.com/webhooks/hcp`
- **CSV Directory**: `CSV_*_production/`
- **Logs**: `automation_prod*.log`, `webhook.log`
- **Cron**: Runs at :00 on the hour

### Environment Isolation Rules
1. **No Cross-Environment Data**: Each environment completely isolated
2. **Separate API Keys**: Different credentials per environment
3. **Separate Webhooks**: Different endpoints and logs
4. **Configuration Check**: System validates environment on startup

## Critical Business Rules

### Data Integrity Rules
1. **UID Uniqueness**: Every reservation must have a unique identifier
2. **Status Progression**: Must follow defined state machine
3. **Soft Deletes**: Never permanently delete data
4. **Audit Trail**: All changes logged with timestamp

### Service Management Rules
1. **One Job Per Reservation**: Prevents duplicate job creation
2. **Service Time Windows**: Default 2-hour service window
3. **Employee Assignment**: Done in HCP, syncs to Airtable
4. **Schedule Changes**: Limited after job in progress

### Integration Rules
1. **API Rate Limits**: Respect all third-party limits
2. **Webhook Reliability**: Always return 200 OK
3. **Retry Logic**: 3 attempts with exponential backoff
4. **Error Handling**: Graceful degradation

### Operational Rules
1. **Timezone**: All business logic uses MST/Arizona time
2. **Processing Schedule**: Major syncs every 4 hours
3. **Log Retention**: 30 days for all logs
4. **Manual Override**: Always available

## System Health Monitoring

### Key Metrics
- **CSV Processing Time**: < 2 minutes per file
- **ICS Sync Time**: < 10 minutes for all feeds
- **Job Creation Success**: > 99% success rate
- **Webhook Processing**: < 1 second response time

### Health Checks
- **Systemd Services**: webhook, webhook-dev, airscripts-api
- **Cron Jobs**: Verify running every 4 hours
- **Database Connectivity**: Airtable API availability
- **External Services**: HCP API, CloudMailin status

### Error Recovery
1. **Transient Failures**: Automatic retry with backoff
2. **Persistent Failures**: Alert sent, manual intervention
3. **Data Recovery**: All operations idempotent
4. **Rollback Capability**: Status changes reversible

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Scope**: Complete system business logic
**Next Review**: August 11, 2025