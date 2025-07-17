# Webhook Processing - System Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Text-based operational flow descriptions for webhook processing system

---

## 🚀 **WEBHOOK PROCESSING OPERATIONAL FLOW**

### **1. WEBHOOK RECEPTION FLOW**

**Incoming Request Processing:**
- System receives HTTPS webhook request on port 443 (nginx)
- Nginx evaluates URL path to determine target environment
- Environment-specific routing based on webhook endpoint:
  - `/webhooks/hcp-dev` → development service (port 5001)
  - `/webhooks/hcp` → production service (port 5000)

**Rate Limiting Application:**
- Nginx applies rate limiting (30 requests per minute per IP)
- Burst capacity of 10 requests with no delay
- Rate exceeded requests return 429 status immediately

**Request Forwarding:**
- Valid requests forwarded to appropriate Python Flask service
- Headers preserved including authentication and client IP
- Request body passed unchanged for processing

### **2. AUTHENTICATION VALIDATION FLOW**

**Primary Authentication (HCP Signature):**
- Extract X-HousecallPro-Signature and X-HousecallPro-Timestamp headers
- Reconstruct signed content using timestamp and raw payload
- Calculate HMAC-SHA256 using webhook secret
- Compare calculated signature with provided signature
- Accept request if signatures match within 5-minute tolerance

**Secondary Authentication (Servativ Forwarding):**
- Extract X-Internal-Auth header from request
- Compare against SERVATIV_WEBHOOK_SECRET environment variable
- Accept request if header matches secret exactly
- Log authentication method used for audit trail

**Authentication Failure Handling:**
- Log security warning with request details and IP address
- Always return 200 OK status to prevent webhook disabling
- Skip processing but maintain webhook endpoint availability

### **3. PAYLOAD PROCESSING FLOW**

**JSON Parsing and Validation:**
- Parse webhook payload as JSON with error handling
- Validate required fields based on event type
- Extract event_type, job data, and metadata
- Log malformed payloads for debugging

**Event Type Classification:**
- Job-related events: job.*, job.work_status.*, job.scheduled.*
- Appointment events: job.appointment.*, appointment.*
- Schedule events: job.appointment.scheduled, job.appointment.rescheduled
- Status events: job.work_status.changed, job.completed

**Event Filtering Logic:**
- Process only events that affect job status or scheduling
- Ignore events for jobs without Airtable links
- Skip duplicate events within 30-second window
- Log all events for audit regardless of processing

### **4. AIRTABLE RECORD MATCHING FLOW**

**Job ID Lookup Process:**
- Search Airtable "Service Job ID" field for exact match
- Use environment-specific Airtable base for searches
- Return first matching record with full field data
- Cache lookup results for 5 minutes to improve performance

**Record Eligibility Validation:**
- Verify record has "Service Job ID" populated OR "Entry Source" = "HCP"
- Check record is not marked as "Old" status
- Ensure record type is "Reservation" not "Block"
- Skip updates for ineligible records with explanatory log

**Orphaned Job Handling:**
- Log warning for jobs without matching Airtable records
- Attempt automatic reconciliation based on timing and property
- Return success status to maintain webhook reliability
- Queue manual review for persistent orphaned jobs

### **5. APPOINTMENT EVENT PROCESSING FLOW**

**Scheduled Appointment Processing:**
- Extract appointment.id, start_time, and dispatched_employees
- Format employee names as "FirstName LastName" with comma separation
- Update Airtable fields: Service Appointment ID, Assignee, Scheduled Service Time
- Set Job Status to "Scheduled" and update sync timestamp

**Rescheduled Appointment Processing:**
- Update existing appointment with new timing and assignments
- Preserve appointment ID if unchanged, update if new appointment created
- Update Scheduled Service Time with new start_time
- Log rescheduling reason if provided in webhook

**Discarded Appointment Processing:**
- Clear all scheduling-related fields: appointment ID, assignee, scheduled time
- Reset Job Status to "Unscheduled"
- Clear work progress fields: on my way, started, completed times
- Log appointment cancellation with original appointment details

### **6. EMPLOYEE ASSIGNMENT PROCESSING FLOW**

**Assignment Updates:**
- Process dispatched_employees array from webhook
- Format multiple employees with proper comma separation
- Handle partial assignments (some employees removed)
- Update Assignee field with current assignment list

**Unassignment Processing:**
- Determine which employees were removed from assignment
- Update Assignee field with remaining employees
- Clear Assignee field entirely if no employees remain
- Log assignment changes for workforce tracking

**Employee Name Formatting:**
- Combine first_name and last_name with single space
- Handle missing names gracefully with fallbacks
- Format multiple employees as comma-separated list
- Limit total length to prevent field overflow

### **7. JOB STATUS SYNCHRONIZATION FLOW**

**Status Mapping Process:**
- Map HCP work statuses to Airtable job statuses
- Handle status variations and partial matches
- Apply business logic for status transitions
- Update Job Status field with mapped value

**Work Timestamp Processing:**
- Extract work_timestamps object from job data
- Update On My Way Time, Job Started Time, Job Completed Time
- Convert timestamps to ISO format for Airtable
- Handle timezone conversion to Arizona time

**Status Change Validation:**
- Verify status transitions are logical (scheduled → in progress → completed)
- Log unusual status changes for review
- Allow manual overrides for special circumstances
- Track status change frequency for performance analysis

### **8. SYNC MESSAGE FORMATTING FLOW**

**Message Construction Standards:**
- Use right-side timestamp format: "[content] - Jul 10, 3:45 PM"
- Avoid bold markdown that displays as literal asterisks
- Include relevant IDs for troubleshooting reference
- Limit message length to prevent field truncation

**Field-Specific Message Strategy:**
- Schedule Sync Details: Only populate when mismatched (alert field)
- Service Sync Details: Always update with activity (log field)
- Minimize noise by filtering significant changes
- Archive old messages to prevent field overflow

**Timestamp Formatting:**
- Use Arizona timezone for all displayed times
- Format as "MMM d, h:mm a" for readability
- Include full context for status changes
- Maintain consistency across all sync messages

### **9. ERROR HANDLING AND RECOVERY FLOW**

**Authentication Error Recovery:**
- Log detailed authentication failure information
- Continue processing with bypass for development environments
- Alert administrators for repeated authentication failures
- Maintain webhook availability despite authentication issues

**Airtable Update Error Recovery:**
- Retry failed updates with exponential backoff
- Maximum 3 retry attempts before marking as failed
- Log field-specific validation errors for troubleshooting
- Continue processing other webhooks despite individual failures

**System Error Recovery:**
- Catch and log unexpected exceptions with full stack traces
- Return success status to prevent webhook provider issues
- Queue failed webhooks for manual review
- Monitor error rates for system health indicators

### **10. PERFORMANCE MONITORING FLOW**

**Processing Time Tracking:**
- Measure webhook processing time from receipt to completion
- Track Airtable API response times separately
- Monitor queue depth and processing delays
- Alert on performance degradation

**Success Rate Monitoring:**
- Track percentage of successfully processed webhooks
- Categorize failures by type (auth, validation, system)
- Monitor trends in error rates over time
- Generate alerts for abnormal failure patterns

**Resource Usage Monitoring:**
- Monitor memory usage of webhook processing workers
- Track CPU utilization during peak webhook traffic
- Monitor disk space for log file growth
- Scale processing capacity based on usage patterns

---

## 🔧 **ENVIRONMENT-SPECIFIC OPERATIONAL DIFFERENCES**

### **Development Environment Operations:**
- **Endpoint**: `/webhooks/hcp-dev` on port 5001
- **Source**: Boris's HCP development account
- **Logging**: Debug level with full webhook payloads
- **Validation**: Relaxed authentication for testing
- **Processing**: Additional logging for development analysis

### **Production Environment Operations:**
- **Endpoint**: `/webhooks/hcp` on port 5000
- **Source**: Production HCP account via Servativ forwarding
- **Logging**: Production level focusing on errors and warnings
- **Validation**: Strict authentication and validation
- **Processing**: Optimized for performance and reliability

---

## 📊 **MONITORING AND ALERTING OPERATIONS**

### **Real-time Monitoring:**
- **Webhook Health**: Monitor endpoint availability and response times
- **Processing Queue**: Track queue depth and processing lag
- **Error Rates**: Alert on elevated error rates or patterns
- **Authentication**: Monitor for suspicious authentication patterns

### **Business Intelligence Operations:**
- **Job Status Tracking**: Monitor frequency of status changes
- **Employee Workload**: Track assignment patterns and utilization
- **Schedule Modifications**: Analyze rescheduling trends and reasons
- **System Performance**: Benchmark processing efficiency over time

---

*This document provides the complete operational flow for webhook processing, emphasizing the step-by-step logical progression from webhook receipt through final Airtable updates, with comprehensive error handling and environment-specific considerations.*