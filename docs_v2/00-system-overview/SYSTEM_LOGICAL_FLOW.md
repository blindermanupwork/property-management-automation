# System Overview - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** High-level system flow covering all major components

---

## 🔄 **AUTOMATED CRON CYCLES (Every 4 Hours)**

### **Development Environment**: Every 4 hours at :10 minutes (4:10 AM, 8:10 AM, 12:10 PM, 4:10 PM, 8:10 PM, 12:10 AM)
### **Production Environment**: Every 4 hours at :00 minutes (4:00 AM, 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM, 12:00 AM)

---

## 📋 **OVERALL SYSTEM FLOW**

### **STEP 1**: Data Ingestion (Automated)
- **Email Processing**: CloudMailin receives iTrip CSV emails → saves to environment-specific folders
- **Web Scraping**: Evolve portal scraped for property bookings and owner blocks
- **Calendar Sync**: 246+ ICS feeds processed for reservation updates
- **All sources** feed into Airtable Reservations table with environment separation

### **STEP 2**: Data Processing (Automated)
- **CSV Processing**: iTrip and Evolve CSV files parsed → UIDs generated → duplicates handled
- **ICS Processing**: Calendar events parsed → classified by keywords → synchronized
- **Property Matching**: All reservations linked to Properties table records
- **Flag Calculation**: Same-day turnover, overlapping dates, long-term guest detection

### **STEP 3**: Service Job Creation (Manual Trigger)
- **User Action**: Click "Create Job & Sync Status" button in Airtable
- **System Action**: Creates HousecallPro job using property's HCP Customer/Address IDs
- **Service Line Generation**: Combines custom instructions + special flags + base service name
- **Template Application**: Copies line items from job templates based on Service Type

### **STEP 4**: Schedule Management (Manual Trigger)
- **User Action**: Set Custom Service Time + click "Add/Update Schedule" button
- **System Action**: Creates/updates HCP appointment with specified date/time
- **Sync Status**: Real-time comparison between expected and actual schedule

### **STEP 5**: Real-Time Updates (Webhook)
- **HCP Webhooks**: Job status changes, appointments, employee assignments
- **Airtable Updates**: Job Status, Assignee, timestamps, Sync Details automatically updated
- **Bidirectional Sync**: Changes in HCP immediately reflected in Airtable

---

## 🌐 **COMPONENT INTEGRATION FLOW**

### **Data Sources** → **Processing** → **Storage** → **Job Management** → **Sync**

1. **CloudMailin + Evolve + ICS Feeds** 
   ↓
2. **CSV Processor + ICS Processor + Evolve Scraper**
   ↓  
3. **Airtable Reservations Table** (environment-specific)
   ↓
4. **Manual Job Creation** (via API Server)
   ↓
5. **HousecallPro Jobs + Appointments**
   ↓
6. **Webhook Updates** (bidirectional sync)

---

## 🔧 **ENVIRONMENT ARCHITECTURE**

### **Development Environment**:
- **Airtable Base**: `app67yWFv0hKdl6jM`
- **CSV Folders**: `CSV_process_development/`, `CSV_done_development/`
- **API Endpoints**: `/api/dev/*`
- **Webhook URL**: `/webhooks/hcp-dev`
- **HCP Account**: Boris's development account

### **Production Environment**:
- **Airtable Base**: `appZzebEIqCU5R9ER`  
- **CSV Folders**: `CSV_process_production/`, `CSV_done_production/`
- **API Endpoints**: `/api/prod/*`
- **Webhook URL**: `/webhooks/hcp`
- **HCP Account**: Production account (forwarded webhooks)

---

## 🎯 **KEY BUSINESS RULES**

### **Service Line Construction Order**:
1. **Custom Instructions** (if present, max 200 chars)
2. **Owner Arriving** (if owner block detected same/next day)
3. **Long Term Guest Departing** (if 14+ day stay)
4. **Base Service Name** (Turnover STR Next Guest [Date] or SAME DAY)

### **Same-Day Turnover Logic**:
- **IF** checkout date = check-in date at same property: flag both reservations
- **Service Times**: 8:00 AM (checkout service), 2:00 PM (check-in service)

### **Duplicate Handling**:
- **New Data**: Create with Status = "New"
- **Changed Data**: Mark old as "Old", create with Status = "Modified" 
- **Removed Data**: Mark as "Removed"
- **Unchanged Data**: No Airtable writes

---

## 📊 **AUTOMATION CONTROL**

### **Controller System**:
- **Airtable Table**: "Automation Control" with Active field toggles
- **Execution Order**: CSV → Evolve → ICS → HCP → Gmail OAuth
- **Tracking**: Last Run Time, Sync Details, Success/Error status
- **Environment Separation**: Separate runners for dev/prod

### **Error Handling**:
- **File Errors**: Skip and continue processing
- **API Errors**: Retry with exponential backoff
- **Property Missing**: Log suggestions, skip record
- **Authentication**: Auto-refresh OAuth tokens

---

*This document provides the high-level logical flow of the entire property management automation system, showing how all components work together across both environments.*