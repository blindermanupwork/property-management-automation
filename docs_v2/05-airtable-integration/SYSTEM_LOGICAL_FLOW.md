# Airtable Integration - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** Natural language flow for Airtable operations, data synchronization, and environment management

---

## 📊 **AIRTABLE INTEGRATION TRIGGERS**

**Automated**: All data ingestion processes (CSV, ICS, Evolve) write to Airtable
**Manual**: Button automations for job creation and schedule management
**Real-time**: Webhook updates from HousecallPro sync back to Airtable

---

## 📋 **PRIMARY LOGIC FLOW**

### **STEP 1**: Environment-Specific Base Selection
- **Development Operations**:
  - **THEN** use Airtable base ID: `app67yWFv0hKdl6jM`
  - **THEN** all dev automation processes write to this base
  - **THEN** API endpoints: `/api/dev/*` routes to dev base

- **Production Operations**:
  - **THEN** use Airtable base ID: `appZzebEIqCU5R9ER`
  - **THEN** all prod automation processes write to this base
  - **THEN** API endpoints: `/api/prod/*` routes to prod base

### **STEP 2**: Core Table Structure and Relationships
- **Reservations Table** (Primary data store):
  - **Purpose**: All reservation records from CSV, ICS, and manual entry
  - **Key Fields**: Reservation UID, Property ID (linked), dates, guest info, service fields
  - **Status Tracking**: "New", "Modified", "Removed", "Old"

- **Properties Table** (Master property data):
  - **Purpose**: Property definitions with HCP integration details
  - **Key Fields**: Property Name, HCP Customer ID, HCP Address ID, Service Templates
  - **Links**: Connected to Reservations via Property ID field

- **ICS Feeds Table** (Feed management):
  - **Purpose**: Calendar feed configuration and status
  - **Key Fields**: ICS URL, Property ID (linked), Feed Status, Last Run tracking

- **Automation Control Table** (System management):
  - **Purpose**: Enable/disable automations and track execution
  - **Key Fields**: Name, Active (boolean), Last Ran Time, Sync Details

### **STEP 3**: Data Ingestion and Record Management
- **New Record Creation**:
  - **FOR EACH** incoming data record (CSV, ICS, Evolve):
    - **THEN** generate unique UID based on source, property, dates, guest
    - **THEN** search for existing records with same UID + feed URL
    - **IF** no existing record: create new with **"Status"** = "New"

- **Change Detection and History Preservation**:
  - **IF** existing record found:
    - **THEN** compare critical fields: dates, property, guest, service type, flags
    - **IF** any critical field changed:
      - **THEN** mark ALL existing records for this UID as **"Status"** = "Old"
      - **THEN** create new record with **"Status"** = "Modified"
      - **THEN** preserve ALL HCP service fields from latest active record

  - **IF** no critical changes detected:
    - **THEN** leave existing records completely unchanged (no API writes)

- **Record Removal Handling**:
  - **FOR EACH** existing Airtable record not found in current data source:
    - **IF** record is active (Status = "New" or "Modified") AND has future dates:
      - **THEN** mark ALL records for this UID as **"Status"** = "Old"
      - **THEN** create new record with **"Status"** = "Removed"

### **STEP 4**: Property Linking and Validation
- **Property Matching Logic**:
  - **CSV iTrip**: Match **"Property Name"** column to Properties table **"Property Name"** field
  - **CSV Evolve**: Extract listing number, match to Properties table entry
  - **ICS Feeds**: Use feed URL → property mapping from ICS Feeds table

- **Missing Property Handling**:
  - **IF** property not found in Properties table:
    - **THEN** skip record creation, log error with suggested matches
    - **THEN** continue processing remaining records

- **Property Link Updates**:
  - **FOR EACH** reservation with missing **"Property ID"** link:
    - **IF** **"ICS URL"** has mapping in **"ICS Feeds"** table:
      - **THEN** update **"Property ID"** = linked property from feeds table

### **STEP 5**: Service Field Management and Button Automations
- **Service Job Creation** (Manual trigger):
  - **Trigger**: User clicks "Create Job & Sync Status" button
  - **Validation**: Check **"Property ID"** link and **"Final Service Time"** exist
  - **Property Configuration**: Extract **"HCP Customer ID"** and **"HCP Address ID"** from property
  - **Job Creation**: Call HCP API, update **"Service Job ID"** field
  - **Service Line Construction**: Build service name with custom instructions + flags

- **Schedule Management** (Manual trigger):
  - **Trigger**: User clicks "Add/Update Schedule" button
  - **Validation**: Check **"Service Job ID"** exists
  - **Time Priority**: Use **"Custom Service Time"** if set, else **"Final Service Time"**
  - **HCP Sync**: Create/update appointment, update sync status fields

### **STEP 6**: Real-Time Webhook Updates
- **Webhook Data Reception**:
  - **THEN** receive HCP webhook at environment-specific endpoint
  - **THEN** find Airtable record with matching **"Service Job ID"**
  - **THEN** validate record should be updated (has Service Job ID OR Entry Source = "HCP")

- **Field Updates from Webhooks**:
  - **Job Status**: Map HCP work_status to Airtable job status values
  - **Employee Assignment**: Format **"Assignee"** from dispatched_employees
  - **Timestamps**: Update **"On My Way Time"**, **"Job Started Time"**, **"Job Completed Time"**
  - **Sync Tracking**: Update **"Sync Date and Time"**, **"Sync Details"** with timestamp format

### **STEP 7**: Automation Control and Execution Tracking
- **Automation Status Management**:
  - **FOR EACH** automation in controller:
    - **THEN** query **"Automation Control"** table for matching **"Name"** field
    - **IF** **"Active"** field = true: execute automation
    - **IF** **"Active"** field = false: skip automation, log skip reason

- **Execution Metrics Tracking**:
  - **THEN** record start time for each automation (Arizona timezone)
  - **THEN** catch all exceptions and errors during execution
  - **THEN** calculate duration and success/failure status
  - **THEN** update **"Last Ran Time"** and **"Sync Details"** with results

### **STEP 8**: Data Quality and Validation
- **Field Validation Rules**:
  - **Dates**: Must be valid MM/DD/YYYY format, within configured date range
  - **UIDs**: Must be unique within same feed URL, follow naming convention
  - **Property Links**: Must reference valid Properties table record
  - **Service Times**: Must be valid time format, within business hours

- **Data Consistency Checks**:
  - **Same-Day Turnover**: Validate checkout date = check-in date at same property
  - **Overlapping Dates**: Check for date range conflicts at same property
  - **Service Types**: Validate against allowed values for property type

### **STEP 9**: API Rate Limiting and Error Handling
- **Rate Limit Management**:
  - **THEN** implement exponential backoff for API retries
  - **THEN** batch record operations where possible
  - **THEN** monitor API usage to stay within Airtable limits

- **Error Recovery Strategies**:
  - **Network timeouts**: Retry up to 3 times with increasing delays
  - **Invalid field values**: Log validation error, skip problematic field
  - **Authentication failures**: Refresh token, retry operation
  - **Record conflicts**: Use "upsert" operations where supported

---

## 🚨 **ERROR HANDLING**

### **Data Validation Errors**:
- **Invalid dates**: Skip record, log parsing error with suggested format
- **Missing required fields**: Skip record, log missing field details
- **Invalid property links**: Skip record, log property matching suggestions

### **API Communication Errors**:
- **Rate limit exceeded**: Implement exponential backoff, retry after delay
- **Network connectivity**: Retry with increasing timeouts
- **Authentication expired**: Refresh credentials, retry operation

### **Record Conflict Errors**:
- **Duplicate UIDs**: Log conflict details, use most recent data
- **Concurrent updates**: Retry with fresh record data
- **Field validation failures**: Log field-specific errors, continue with valid fields

---

## 🔧 **ENVIRONMENT-SPECIFIC CONFIGURATION**

### **Development Environment Features**:
- **Base ID**: `app67yWFv0hKdl6jM`
- **Testing Data**: Limited property set for safe testing
- **API Endpoints**: All `/api/dev/*` routes
- **Webhook Processing**: `/webhooks/hcp-dev` endpoint
- **Logging**: Environment-specific log files

### **Production Environment Features**:
- **Base ID**: `appZzebEIqCU5R9ER`
- **Live Data**: Full property portfolio with real reservations
- **API Endpoints**: All `/api/prod/*` routes
- **Webhook Processing**: `/webhooks/hcp` endpoint
- **Data Volume**: 246+ ICS feeds, hundreds of daily reservations

---

## 📊 **PERFORMANCE OPTIMIZATION**

### **Batch Operations**:
- **Record Creation**: Group new records into batches for efficient API usage
- **Field Updates**: Combine multiple field updates into single API calls
- **Property Linking**: Batch property lookups to reduce API overhead

### **Caching Strategies**:
- **Property Mappings**: Cache property lookups for duration of processing
- **Template Data**: Cache job templates to avoid repeated API calls
- **Employee Lists**: Cache employee data for webhook processing

### **Data Filtering**:
- **Date Range Filtering**: Apply date filters before API operations
- **Status Filtering**: Only process active records for updates
- **Change Detection**: Skip API writes when no changes detected

---

*This document captures the complete logical flow for Airtable integration, from environment selection through real-time updates, with emphasis on data quality and performance optimization.*