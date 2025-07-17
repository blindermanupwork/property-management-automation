# Comprehensive Business Rules Guide for Property Management Automation System
**Version Date: July 11, 2025**

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Reservation Management Rules](#reservation-management-rules)
3. [Property Management Rules](#property-management-rules)
4. [Service Type Determination](#service-type-determination)
5. [Scheduling Rules](#scheduling-rules)
6. [HousecallPro Integration Rules](#housecallpro-integration-rules)
7. [Data Synchronization Rules](#data-synchronization-rules)
8. [Customer and Owner Management](#customer-and-owner-management)
9. [Financial and Billing Rules](#financial-and-billing-rules)
10. [Notification and Communication Rules](#notification-and-communication-rules)
11. [Error Handling and Recovery Rules](#error-handling-and-recovery-rules)

---

## Executive Summary

This document consolidates all business rules implemented in the property management automation system. These rules govern how the system processes reservations, creates service jobs, manages schedules, and maintains data consistency across multiple platforms.

---

## Reservation Management Rules

### 1. Reservation Identification and UID Generation

#### **Unique Identifier (UID) Creation**
- **Format**: `{source}_{property_id}_{checkin}_{checkout}_{lastname}`
- **Components**:
  - `source`: iTrip, Evolve, ICS feed identifier
  - `property_id`: Normalized property identifier
  - `checkin/checkout`: YYYY-MM-DD format
  - `lastname`: Lowercase, spaces replaced with underscores
- **Example**: `itrip_12345_2025-07-15_2025-07-20_smith`

#### **Duplicate Prevention**
- Only ONE active record per UID allowed at any time
- When updating existing reservation:
  1. Clone existing record to preserve history
  2. Mark ALL older versions as "Old" status
  3. Create new record with "Modified" status
- Complete audit trail maintained for all changes

### 2. Reservation Status Lifecycle

#### **Status Values and Transitions**
- **New**: First appearance of reservation
- **Modified**: Any change to dates, guest info, or property
- **Old**: Historical version (multiple allowed per UID)
- **Removed**: Reservation canceled or deleted at source

#### **Active vs Inactive**
- **Active**: Status = "New" OR "Modified"
- **Inactive**: Status = "Old" OR "Removed"
- Only active records are considered for service creation

### 3. Entry Type Classification

#### **Reservation vs Block**
- **Reservation**: Has guest name AND not a known block pattern
- **Block**: No guest name OR matches block keywords:
  - Keywords: 'block', 'owner', 'maintenance', 'unavailable', 'blocked'
  - Owner name matches property owner name
  - Special handling for Evolve owner blocks

#### **Block Type Categories**
- **Owner Stay**: Property owner using the property
- **Maintenance**: Scheduled maintenance or repairs
- **Unavailable**: Generic blocking period
- **Other**: Unspecified blocking reason

### 4. Data Source Processing

#### **iTrip CSV Processing**
- **File Format**: Daily CSV reports via email
- **Property Matching**: Exact name match required
- **Owner Override**: Special guest names redirect to different properties
- **Processing Window**: 6 months past, 12 months future

#### **Evolve Portal Scraping**
- **Tab 1**: Next 60 days with Check-Out filter
- **Tab 2**: Configurable range for owner blocks
- **Owner Detection**: Guest name matches property owner
- **File Cleanup**: Remove old Evolve CSVs before export

#### **ICS Feed Processing**
- **Supported Sources**: Airbnb, VRBO, Booking.com, Hospitable, etc.
- **Feed Status**:
  - Active: Process every 4 hours
  - Inactive: Skip processing
  - Remove: Mark all records as "Removed"
- **Date Range**: Same as CSV (6/12 months)

---

## Property Management Rules

### 1. Property Identification

#### **Property Name Requirements**
- Must be unique within environment
- iTrip: Must match CSV exactly
- Evolve: Include listing number (e.g., "Beautiful Home #12345")
- Used as primary matching key across all sources

#### **Property Configuration**
- **Required for Job Creation**:
  - HCP Customer ID (links to customer)
  - HCP Address ID (service location)
  - Turnover Job Template ID
- **Optional Templates**:
  - Inspection Job Template ID
  - Return Laundry Job Template ID

### 2. Property Owner Overrides

#### **Override Rules**
- Map specific guest names to different properties
- Applied during CSV processing only
- Active flag controls application
- Use case: Same physical address, different billing entities

#### **Override Process**
1. Check if guest name matches override pattern
2. If match AND override active:
   - Use override property instead of original
   - Apply all rules to override property
3. Log override application for audit

---

## Service Type Determination

### 1. Automatic Service Type Assignment

#### **Turnover Service** (Default)
- Standard cleaning between guests
- Applied when:
  - Entry type = "Reservation"
  - No special conditions apply
  - Most common service type (~90%)

#### **Same-Day Turnover**
- Expedited service when checkout = next checkin
- Automatic detection based on dates
- Changes default service time (10:00 AM vs 10:15 AM)
- Priority scheduling for cleaning teams

#### **Owner Stay Services**
- Applied when Entry Type = "Block" AND Block Type = "Owner Stay"
- May require different service levels
- Special instructions often included

#### **Special Service Types**
- **Inspection**: Quality check without full cleaning
- **Return Laundry**: Linen delivery service
- **Touchup**: Light cleaning between stays
- **Deep Clean**: Intensive periodic cleaning
- **Move-out Clean**: End of lease cleaning

### 2. Service Flags and Modifiers

#### **Long-Term Guest Detection**
- **Rule**: Stay duration >= 14 days
- **Action**: Add "LONG TERM GUEST DEPARTING" to service description
- **Purpose**: Alert cleaners to expect more intensive cleaning

#### **Owner Arrival Detection**
- **Rule**: Block entry checks in 0-1 days after reservation checkout
- **Action**: Add "OWNER ARRIVING" to service description
- **Purpose**: Ensure property is in perfect condition for owner

#### **Needs Review Flag**
- Applied when automatic classification uncertain
- Requires manual review before job creation
- Common for ambiguous block entries

---

## Scheduling Rules

### 1. Service Time Calculation

#### **Default Service Times** (Arizona Timezone)
- **Regular Turnover**: Check-out date at 10:15 AM
- **Same-Day Turnover**: Check-out date at 10:00 AM
- **Custom Override**: User-specified time takes precedence

#### **Final Service Time Hierarchy**
1. Custom Service Time (if set by user)
2. Same-day rule (10:00 AM if same-day)
3. Default time (10:15 AM)

### 2. Schedule Synchronization

#### **Sync Status Values**
- **Synced**: Airtable and HCP times match exactly
- **Wrong Date**: Different calendar dates
- **Wrong Time**: Same date, different times
- **Not Created**: Job exists but no schedule

#### **Automatic Schedule Creation**
- Creates 1-hour appointment window
- 60-minute arrival window for flexibility
- Default employee assignment if configured
- Sends notifications to assigned staff

### 3. Schedule Modification Rules

#### **User-Initiated Changes**
- "Add/Update Schedule" button updates HCP
- Always updates Service Sync Details
- Only updates Schedule Sync Details if mismatch remains

#### **System-Initiated Changes**
- Webhook updates from HCP
- Only significant changes trigger updates
- Preserve user modifications within 2-minute window

---

## HousecallPro Integration Rules

### 1. Job Creation Requirements

#### **Prerequisites**
- Valid Property ID with HCP configuration
- Service Start Time (Final or Custom)
- No existing Service Job ID
- Active reservation status

#### **Job Creation Process**
1. Validate all required fields
2. Create/retrieve HCP customer
3. Create job with appropriate template
4. Copy template line items
5. Update service description
6. Create initial schedule
7. Capture appointment ID

### 2. Service Line Description Building

#### **Description Hierarchy** (max 255 characters)
1. **Custom Instructions** (max 200 chars)
   - Set in "Custom Service Line Instructions" field
   - Supports Unicode (accents, emojis)
   - Truncated with "..." if too long

2. **Status Flags**
   - "OWNER ARRIVING" (if owner arriving detected)
   - "LONG TERM GUEST DEPARTING" (if stay >= 14 days)

3. **Base Service Name**
   - Service type + context
   - Examples:
     - "Turnover STR Next Guest July 15"
     - "Turnover STR SAME DAY"
     - "Turnover STR Next Guest Unknown"

#### **Final Format Examples**
- "Special instructions - OWNER ARRIVING - Turnover STR Next Guest July 20"
- "LONG TERM GUEST DEPARTING - Turnover STR Next Guest Aug 1"
- "Clean master bedroom thoroughly - Turnover STR SAME DAY"

### 3. Job Status Management

#### **Status Values**
- **Unscheduled**: Job created but no appointment
- **Scheduled**: Has appointment time
- **In Progress**: Cleaner started work
- **Completed**: Job finished successfully
- **Canceled**: Job was canceled

#### **Status Transition Rules**
- Unscheduled → Scheduled (when appointment created)
- Scheduled → In Progress (when cleaner marks "On My Way" or starts)
- In Progress → Completed (when cleaner finishes)
- Any status → Canceled (manual cancellation)

### 4. Employee Assignment

#### **Assignment Rules**
- Read-only in Airtable (display only)
- Must be assigned in HousecallPro
- Updates via webhooks automatically
- Shows as comma-separated names

#### **Assignment Tracking**
- "On My Way Time": When cleaner departs
- "Job Started Time": Actual work start
- "Job Completed Time": Work finished

---

## Data Synchronization Rules

### 1. Sync Field Separation

#### **Schedule Sync Details** (Alert Field)
- **Purpose**: Flag schedule mismatches requiring attention
- **Updates When**:
  - Schedule times don't match
  - HCP reschedules appointment
  - Sync check finds discrepancy
- **Empty When**: Everything in sync

#### **Service Sync Details** (Activity Log)
- **Purpose**: Track all service operations
- **Updates For**:
  - Job creation results
  - Status changes (significant only)
  - Error messages
  - Manual operations
- **Never Empty**: Always shows latest activity

### 2. Webhook Processing Rules

#### **Event Filtering**
- Only process significant status changes:
  - In Progress, Completed, Canceled
- Ignore minor updates to reduce noise
- Employee assignment changes always processed

#### **Update Timing**
- Process within 30 seconds of HCP event
- Queue-based to prevent timeouts
- Rate limited to 5 requests/second to Airtable

#### **Conflict Resolution**
- User actions override webhooks within 2 minutes
- Last update wins for simultaneous changes
- Webhook always returns HTTP 200 to prevent disabling

### 3. Batch Synchronization

#### **ICS Feed Sync** (Every 4 hours)
- Process all active feeds concurrently
- Maintain complete history
- Handle feed removal gracefully
- Continue on individual feed failures

#### **CSV Processing** (On email receipt)
- Immediate processing via CloudMailin
- Environment-specific directory routing
- Move to "done" folder after processing
- Preserve files for audit trail

---

## Customer and Owner Management

### 1. Customer Records

#### **HCP Customer Requirements**
- First Name, Last Name (for display)
- Email (for communications)
- Mobile Number (primary contact)
- One customer can own multiple properties

#### **Customer ID Format**
- HCP: `cus_xxxxx` format
- Must exist in HCP before job creation
- Links properties to billing entity

### 2. Owner Detection Rules

#### **Evolve Owner Blocks**
- Compare guest name to property owner name
- Case-insensitive matching
- Creates Block instead of Reservation
- Special handling in Tab 2 processing

#### **Owner Arrival Tracking**
- Detect Block within 1 day of checkout
- Set "Owner Arriving" flag
- Include in service description
- May trigger premium service level

---

## Financial and Billing Rules

### 1. Line Item Management

#### **Template-Based Pricing**
- Job templates define standard line items
- Copied to each job on creation
- Can be modified per job if needed

#### **Line Item Types** (HCP API values)
- `labor`: Service work
- `materials`: Supplies, linens
- `discount`: Price reductions
- `fee`: Additional charges

### 2. Revenue Tracking

#### **Job Value Calculation**
- Sum of all line items
- Tracked in HCP for reporting
- Available via MCP analysis tools

---

## Notification and Communication Rules

### 1. System Notifications

#### **Job Creation**
- Confirmation in Service Sync Details
- Email to assigned employees (if configured)
- Update to reservation record

#### **Schedule Changes**
- Alert in Schedule Sync Details
- Notification to affected staff
- Webhook updates to Airtable

### 2. Message Formatting

#### **Timestamp Format**
- All messages include Arizona timezone
- Format: "Jul 10, 3:45 PM"
- Right-side positioning: "[message] - Jul 10, 3:45 PM"

#### **Status Indicators**
- ✅ Success operations
- ❌ Failed operations
- ⚠️ Warnings or mismatches
- 🔄 In-progress operations

---

## Error Handling and Recovery Rules

### 1. Retry Logic

#### **API Failures**
- 3 retry attempts
- Exponential backoff (2s, 4s, 8s)
- Log all attempts
- Graceful degradation

#### **Rate Limiting**
- Airtable: 5 requests/second
- HCP: 1000 requests/hour
- Automatic throttling
- Queue overflow handling

### 2. Data Integrity

#### **Transaction Consistency**
- Clone before update
- Rollback on critical errors
- Preserve historical data
- Audit trail for all changes

#### **Recovery Procedures**
- Automatic recovery for transient failures
- Manual intervention for data conflicts
- Daily backups for disaster recovery
- Version control for configuration

### 3. Monitoring and Alerts

#### **Health Checks**
- API connectivity every 5 minutes
- Disk space monitoring
- Memory usage tracking
- Process status verification

#### **Alert Conditions**
- Failed automation cycles
- High error rates (>5%)
- Sync discrepancies >10%
- Resource exhaustion warnings

---

## Environment-Specific Rules

### Development vs Production

#### **Complete Separation**
- No shared data
- No shared credentials
- No shared file systems
- Independent processing schedules

#### **Schedule Staggering**
- Production: On the hour (0, 4, 8, 12, 16, 20)
- Development: 10 past hour (10, 4:10, 8:10, etc.)
- Prevents resource contention
- Allows testing without interference

---

## Business Rule Validation

### Data Quality Rules

#### **Required Fields**
- Property must have valid name
- Dates must be in valid format
- Guest names cleaned and normalized
- Service times within business hours

#### **Business Constraints**
- No overlapping reservations at same property
- Service must be after checkout time
- Employees assigned must be active
- Templates must exist before use

---

This comprehensive guide documents all business rules implemented in the property management automation system. These rules ensure consistent, reliable operation while maintaining data integrity and providing excellent service delivery.