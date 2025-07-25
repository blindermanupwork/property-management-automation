# BusinessLogicAtoZ.md - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of every UI field, button action, and automation trigger in the property management system, using exact Airtable and HousecallPro field names and capturing all MCP logic.

## Core Business Entities

### Airtable Tables and Fields

#### **Main Table: "Reservations" (Primary Data Store)**
- **Reservation UID**: Unique identifier for each reservation
- **Guest Name**: Customer name for the reservation
- **Property Name**: Property where service is needed
- **Check-in Date**: Guest arrival date
- **Check-out Date**: Guest departure date  
- **Service Date**: Date when cleaning/service is scheduled
- **Service Time**: Specific time for service (format: HH:MM AM/PM)
- **Custom Service Time**: User-defined service time override
- **Same Day**: Boolean field indicating same-day turnover
- **Source**: Data source (iTrip, Evolve, ICS Feed, Manual)
- **Status**: Processing status (New, Processing, Job Created, Scheduled, Completed)
- **HCP Job ID**: HousecallPro job identifier when created
- **HCP Customer ID**: HousecallPro customer identifier
- **Address Line 1**: Street address
- **Address Line 2**: Apartment/unit number
- **City**: City name
- **State**: State/province
- **Zip**: Postal code
- **Phone**: Guest contact number
- **Email**: Guest email address
- **Notes**: Additional service instructions
- **Service Line Custom Instructions**: Custom instructions for HCP service line item (200-char limit, Unicode support)
- **Created Date**: Record creation timestamp
- **Modified Date**: Last modification timestamp
- **Scheduled Start**: HCP job scheduled start time
- **Scheduled End**: HCP job scheduled end time
- **Assigned Employee**: HCP employee assigned to job
- **Job Status**: HCP job status (mirrors HCP work_status)

#### **Configuration Table: "Automation Settings"**
- **Setting Name**: Configuration parameter name
- **Setting Value**: Configuration parameter value
- **Environment**: dev/prod environment specification
- **Active**: Boolean indicating if setting is active
- **Description**: Human-readable setting description

#### **Properties Table: "Property Directory"**
- **Property Name**: Official property name
- **Property Address**: Full property address
- **Property Type**: Type of property (Airbnb, VRBO, etc.)
- **Management Company**: Property management company
- **Special Instructions**: Property-specific service notes
- **Active**: Boolean indicating if property is active

### HousecallPro Entities and Fields

#### **Customer Object**
- **id**: Unique customer identifier (format: cus_xxxxxxxxx)
- **first_name**: Customer first name
- **last_name**: Customer last name  
- **email**: Customer email address
- **mobile_number**: Primary phone number
- **addresses**: Array of customer addresses

#### **Address Object (within Customer)**
- **id**: Unique address identifier (format: adr_xxxxxxxxx)
- **street**: Street address
- **street_line_2**: Apartment/unit number
- **city**: City name
- **state**: State abbreviation
- **zip**: ZIP code
- **type**: Address type (service, billing, etc.)

#### **Job Object**
- **id**: Unique job identifier (format: job_xxxxxxxxx)
- **customer_id**: Associated customer ID
- **address_id**: Service address ID
- **work_status**: Job status (unscheduled, scheduled, in_progress, completed, canceled)
- **scheduled_start**: Job start date/time (ISO 8601)
- **scheduled_end**: Job end date/time (ISO 8601)
- **assigned_employee_ids**: Array of assigned employee IDs
- **description**: Job description
- **notes**: Job notes
- **line_items**: Array of service line items

#### **Line Item Object (within Job)**
- **id**: Unique line item identifier
- **name**: Service name/description
- **unit_price**: Price per unit
- **quantity**: Number of units
- **kind**: Type (service, product, discount, fee)
- **taxable**: Boolean indicating if taxable
- **total**: Calculated total (unit_price × quantity)

## Business Workflows

### 1. Data Ingestion Workflows

#### **iTrip Email Processing (Gmail OAuth)**
**Trigger**: Automated every 4 hours via cron
**Business Logic**:
1. System connects to Gmail using OAuth credentials
2. Searches for emails with iTrip CSV attachments
3. Downloads CSV files to `CSV_process_[environment]/`
4. Parses CSV for reservation data including:
   - Guest names and contact information
   - Property addresses and details
   - Check-in/check-out dates
   - Service requirements
5. Creates/updates Airtable "Reservations" records
6. Moves processed files to `CSV_done_[environment]/`
7. Updates "Status" field to "New"

#### **Evolve Portal Scraping**
**Trigger**: Automated every 4 hours via cron
**Business Logic**:
1. Selenium browser automation logs into Evolve portal
2. Scrapes property data for active reservations
3. Extracts reservation details including dates and guest info
4. Creates Airtable records with "Source" = "Evolve"
5. Handles dynamic content loading and anti-bot measures
6. Maintains session persistence for efficiency

#### **ICS Feed Processing**
**Trigger**: Automated every 4 hours via cron  
**Business Logic**:
1. System processes 246 ICS feeds (prod) / 255 feeds (dev)
2. Downloads calendar data from property management systems
3. Parses iCal format for reservation events
4. Extracts check-in/check-out dates and property information
5. Creates Airtable records with "Source" = "ICS Feed"
6. Handles timezone conversions (MST for business data)
7. Concurrent processing for performance optimization

### 2. Job Creation and Management

#### **"Create Job & Sync Status" Button Action**
**UI Location**: Airtable Reservations table
**Prerequisites**: Record must have complete address and guest information
**Business Logic**:
1. **Data Validation**:
   - Validates required fields: Guest Name, Property Name, Service Date
   - Verifies address completeness
   - Checks for existing HCP Job ID (prevents duplicates)

2. **HCP Customer Creation/Lookup**:
   - Searches HCP for existing customer by name and address
   - If not found, creates new HCP customer with:
     - first_name/last_name from "Guest Name"
     - mobile_number from "Phone"
     - email from "Email"
     - address from Airtable address fields

3. **HCP Job Creation**:
   - Creates HCP job with:
     - customer_id from step 2
     - address_id from customer's addresses
     - scheduled_start/scheduled_end from "Service Date" + "Service Time"
     - work_status = "scheduled"
     - description = "Property Management Cleaning Service"

4. **Service Line Item Creation**:
   - Creates HCP line item with:
     - name = "Cleaning Service" + "Service Line Custom Instructions" (if provided)
     - unit_price = configured cleaning rate
     - quantity = 1
     - kind = "service"
     - taxable = true (configurable)

5. **Airtable Sync**:
   - Updates "HCP Job ID" with created job ID
   - Updates "HCP Customer ID" with customer ID
   - Updates "Status" to "Job Created"
   - Updates "Scheduled Start"/"Scheduled End" with HCP times

#### **Same-Day Turnover Logic**
**Business Logic**:
1. **Detection**: System automatically sets "Same Day" = true when:
   - Check-out date equals Check-in date of another reservation
   - Same property address
   - Service dates within same calendar day

2. **Scheduling Impact**:
   - Same-day turnovers prioritized for earlier time slots
   - Default service time adjusted to allow adequate turnover time
   - Special instructions automatically added to service notes

3. **Automation Behavior**:
   - Jobs created with "Priority" flag in HCP
   - Additional time buffer added to service duration
   - Notification sent to management for awareness

### 3. Scheduling and Time Management

#### **"Add/Update Schedule" Button Action**
**UI Location**: Airtable Reservations table
**Prerequisites**: Valid HCP Job ID must exist
**Business Logic**:
1. **Time Processing**:
   - Reads "Custom Service Time" if provided, else uses "Service Time"
   - Converts time to MST (Mountain Standard Time)
   - Calculates service duration (default: 2 hours)

2. **HCP Schedule Update**:
   - Updates HCP job with:
     - scheduled_start = Service Date + Service Time
     - scheduled_end = scheduled_start + service duration
     - arrival_window = 30 minutes (configurable)

3. **Employee Assignment** (if specified):
   - Updates assigned_employee_ids in HCP
   - Syncs employee assignment back to Airtable "Assigned Employee"

4. **Airtable Sync**:
   - Updates "Scheduled Start"/"Scheduled End" with confirmed times
   - Updates "Status" to "Scheduled"

#### **Employee Assignment Workflow**
**Business Logic**:
1. **HCP Employee Management**:
   - System maintains sync between HCP employees and Airtable
   - Employee assignments made in HCP interface
   - Changes automatically sync back to Airtable

2. **Assignment Rules**:
   - Same-day turnovers assigned to experienced cleaners
   - Geographic proximity considered for efficiency
   - Employee availability checked against HCP schedules

### 4. Status Tracking and Updates

#### **Bidirectional Sync Logic**
**Trigger**: Real-time via webhooks + periodic sync every 4 hours
**Business Logic**:
1. **HCP → Airtable Sync**:
   - Webhook receives HCP job status changes
   - Updates Airtable "Job Status" field
   - Syncs employee assignments
   - Updates completion timestamps

2. **Status Progression**:
   - New → Processing → Job Created → Scheduled → In Progress → Completed
   - Each status change logged with timestamp
   - Automatic notifications sent to stakeholders

3. **Completion Workflow**:
   - When HCP job marked "completed":
     - Airtable "Status" updated to "Completed"
     - Service completion time recorded
     - Invoice data synced if applicable

### 5. Webhook Processing

#### **HCP Webhook Handler**
**Endpoint**: `https://servativ.themomentcatchers.com/webhooks/hcp`
**Authentication**: Dual authentication (HCP signature + forwarding secret)
**Business Logic**:
1. **Webhook Validation**:
   - Verifies HCP HMAC signature
   - Validates forwarding authentication header
   - Returns 200 status to prevent webhook disabling

2. **Event Processing**:
   - Job status changes: Updates Airtable status
   - Employee assignments: Syncs to Airtable
   - Schedule changes: Updates Airtable times
   - Completion events: Triggers completion workflow

3. **Error Handling**:
   - Failed webhooks logged for manual review
   - Retry logic for transient failures
   - Fallback to periodic sync if webhooks fail

### 6. Service Line Custom Instructions

#### **Custom Instructions Workflow**
**UI Field**: "Service Line Custom Instructions" (Airtable)
**Business Logic**:
1. **Input Processing**:
   - Accepts Unicode characters (accents, special characters, emojis)
   - Automatically truncates to 200 characters for HCP compatibility
   - Preserves full text in Airtable for reference

2. **HCP Integration**:
   - Instructions appended to first line item name in HCP job
   - Format: "Cleaning Service - [Custom Instructions]"
   - Cannot be updated after job creation (HCP limitation)

3. **Use Cases**:
   - Special cleaning requirements
   - Property-specific instructions
   - Guest-requested services
   - Maintenance notes

### 7. Address and Customer Management

#### **Address Search and Validation**
**MCP Tools**: `search_addresses`, `get_jobs_by_address`
**Business Logic**:
1. **Address Normalization**:
   - Standardizes address formats
   - Validates ZIP codes and state abbreviations
   - Geocodes addresses for accuracy

2. **Duplicate Prevention**:
   - Searches HCP for existing addresses before creating
   - Fuzzy matching for similar addresses
   - Manual review queue for uncertain matches

3. **Customer Consolidation**:
   - Links multiple properties to single customer when appropriate
   - Maintains separate customer records for different guests
   - Handles corporate vs. individual customers

### 8. Reporting and Analytics

#### **MCP Analysis Tools**
**Available Tools**:
- `analyze_laundry_jobs`: Laundry service analysis
- `analyze_service_items`: Service item tracking
- `analyze_customer_revenue`: Revenue analysis
- `analyze_towel_usage`: Supply usage tracking
- `analyze_job_statistics`: Performance metrics

**Business Logic**:
1. **Revenue Tracking**:
   - Tracks revenue by property, customer, service type
   - Calculates monthly/quarterly trends
   - Identifies high-value customers

2. **Operational Metrics**:
   - Service completion rates
   - Average service times
   - Employee performance metrics
   - Customer satisfaction tracking

3. **Supply Management**:
   - Tracks towel and linen usage
   - Calculates replacement costs
   - Monitors inventory levels

## Environment Separation Logic

### Development Environment
**Airtable Base**: `app67yWFv0hKdl6jM`
**HCP Environment**: Sandbox/Development
**CSV Directory**: `CSV_*_development/`
**Log Files**: `automation_dev*.log`
**Cron Schedule**: Every 4 hours at :10 minutes

### Production Environment  
**Airtable Base**: `appZzebEIqCU5R9ER`
**HCP Environment**: Production
**CSV Directory**: `CSV_*_production/`
**Log Files**: `automation_prod*.log`
**Cron Schedule**: Every 4 hours at :00 minutes

### Cross-Environment Safeguards
1. **Complete Data Isolation**: No data shared between environments
2. **Separate API Keys**: Different credentials for each environment
3. **Environment Detection**: Automatic environment detection prevents cross-contamination
4. **Configuration Validation**: Startup checks confirm correct environment settings

## Error Handling and Recovery

### Automated Recovery Logic
1. **API Failures**: Exponential backoff with retry logic
2. **Data Validation Errors**: Quarantine invalid records for manual review
3. **Network Issues**: Graceful degradation and offline queuing
4. **Authentication Failures**: Automatic token refresh where possible

### Manual Intervention Triggers
1. **Duplicate Customer Detection**: Manual review queue
2. **Address Validation Failures**: Geocoding review
3. **Service Time Conflicts**: Schedule conflict resolution
4. **Payment Processing Issues**: Financial review queue

Last Updated: 2025-06-07
Scope: Complete business logic documentation
Environments: Development and Production