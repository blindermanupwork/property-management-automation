# API Server - Complete System Logical Flow

## Overview
This document describes the complete operational flow of the API Server, which bridges Airtable and HousecallPro for job creation, schedule management, webhook processing, and status synchronization.

## Primary Data Flow

### 1. Request Entry Points
The API server receives requests through multiple pathways:
- Airtable button scripts call endpoints directly
- Webhook endpoints receive real-time updates from HCP
- Internal automation scripts make programmatic calls
- Test scripts validate functionality

### 2. Environment Routing
Every request is routed based on the URL path:
- Requests to `/api/dev/*` use development configuration
- Requests to `/api/prod/*` use production configuration
- Environment determines which Airtable base and HCP account
- Configuration is loaded dynamically per request

### 3. Authentication Flow
All API requests require authentication:
- X-API-Key header must be present
- Key is validated against environment variables
- Invalid or missing keys return 401 Unauthorized
- Successful authentication proceeds to business logic

### 4. Core Processing Flows

#### Job Creation Flow
1. **Reservation Validation**
   - Load reservation from Airtable by record ID
   - Validate required fields (Guest Name, Property ID, Service Type)
   - Check Final Service Time is populated
   - Verify reservation hasn't already created a job

2. **Property Verification**
   - Load linked property record
   - Verify HCP Customer ID exists
   - Verify HCP Address ID exists
   - Load job template based on service type

3. **Service Line Generation**
   - Start with custom instructions (if any)
   - Add "OWNER ARRIVING" if next entry is block
   - Add "LONG TERM GUEST DEPARTING" if stay >= 14 days
   - Append base service name with next guest date
   - Truncate complete line to 200 characters

4. **HCP Job Creation**
   - Create job with customer and address IDs
   - Set schedule based on Final Service Time
   - Assign default employee
   - Job creation returns job ID

5. **Line Item Application**
   - Fetch template line items from HCP
   - Replace first item name with generated service line
   - Bulk update all line items to new job
   - Handle truncation if name too long

6. **Airtable Update**
   - Store HCP Job ID in reservation
   - Update Job Creation Time
   - Capture appointment ID if available
   - Set initial sync status

#### Schedule Management Flow
1. **Time Parsing**
   - Parse custom service time (HH:MM AM/PM)
   - Convert to 24-hour format
   - Apply Mountain Standard Time zone
   - Calculate service window (default 4 hours)

2. **Schedule Creation**
   - Check if appointment already exists
   - Create new appointment with parsed time
   - Assign to default employee
   - Update Airtable with appointment ID

3. **Schedule Updates**
   - Compare new time with existing
   - Only update if different
   - Log changes in Schedule Sync Details
   - Maintain audit trail

#### Webhook Processing Flow
1. **Event Receipt**
   - Receive POST request from HCP
   - Validate webhook signature (if configured)
   - Parse event type and payload
   - Route to appropriate handler

2. **Job Update Processing**
   - Find reservation by HCP Job ID
   - Map HCP status to Airtable status
   - Update assignee if changed
   - Log update in Service Sync Details

3. **Appointment Processing**
   - Find reservation by job ID
   - Update scheduled times
   - Flag schedule mismatches
   - Alert on major changes

#### Status Synchronization Flow
1. **Fetch Current State**
   - Get latest job details from HCP
   - Compare with Airtable values
   - Identify differences

2. **Status Mapping**
   - Convert HCP work_status to Airtable format
   - Handle special statuses (canceled, completed)
   - Preserve status history

3. **Schedule Comparison**
   - Compare dates and times
   - Flag "Wrong Date" or "Wrong Time"
   - Mark "Synced" if matching
   - Use timezone-aware comparisons

4. **Update Recording**
   - Write changes to appropriate sync fields
   - Schedule issues → Schedule Sync Details
   - Status changes → Service Sync Details
   - Timestamp all updates

### 5. Error Handling Flows

#### Validation Errors
- Missing required fields return 400 Bad Request
- Clear error messages indicate missing data
- Suggestions provided for resolution
- No partial updates on validation failure

#### API Errors
- HCP errors wrapped with context
- Rate limit errors trigger retry logic
- Network errors return 502 Bad Gateway
- Timeout errors after configured duration

#### Data Integrity
- Duplicate job creation prevented
- Canceled jobs can be rescheduled
- Missing records return 404 Not Found
- Orphaned data logged for review

### 6. Response Formatting

#### Success Responses
```
{
  success: true,
  jobId: "job_xxx",
  appointmentId: "apt_xxx",
  environment: "development",
  syncStatus: "Synced"
}
```

#### Error Responses
```
{
  error: "Validation failed",
  details: "Missing Guest Name",
  suggestion: "Ensure reservation has guest information",
  timestamp: "2025-07-12T10:30:00Z"
}
```

## Integration Points

### 1. Airtable Integration
- Uses official Airtable.js SDK
- Maintains connection pool per environment
- Handles linked record lookups
- Preserves field relationships

### 2. HousecallPro Integration
- Direct REST API calls
- Automatic retry on rate limits
- Token-based authentication
- Supports all CRUD operations

### 3. Webhook Integration
- Receives real-time updates
- Processes asynchronously
- Updates multiple records
- Maintains event history

## State Management

### 1. Job States
- **Unscheduled**: Created but no appointment
- **Scheduled**: Has appointment time
- **In Progress**: Work started
- **Completed**: Work finished
- **Canceled**: Job canceled

### 2. Sync States
- **Synced**: All fields match
- **Wrong Time**: Time mismatch
- **Wrong Date**: Date mismatch
- **Needs Update**: Pending sync

### 3. Environment States
- **Development**: Test data and systems
- **Production**: Live customer data
- **Maintenance**: Temporary hold
- **Error**: System issues

## Performance Optimization

### 1. Request Processing
- Async/await for all I/O operations
- Parallel fetches where possible
- Early validation exits
- Minimal database round trips

### 2. Caching Strategy
- Environment configs cached
- Connection pools maintained
- Template data cached
- Frequent lookups optimized

### 3. Rate Limit Management
- Automatic retry with backoff
- Request queuing
- Burst handling
- Per-endpoint limits

## Security Measures

### 1. Authentication Layers
- API key validation
- Environment isolation
- CORS restrictions
- Request sanitization

### 2. Data Protection
- No credentials in logs
- Sanitized error messages
- Encrypted connections
- Audit trail maintenance

### 3. Access Control
- Endpoint-level permissions
- Environment-based access
- Read/write separation
- Admin-only operations

## Monitoring and Logging

### 1. Request Logging
- All requests logged with timestamp
- Environment clearly indicated
- Errors include full context
- Success metrics tracked

### 2. Performance Monitoring
- Response time tracking
- Error rate monitoring
- API usage statistics
- Resource utilization

### 3. Alert Conditions
- High error rates
- Slow response times
- Authentication failures
- System resource limits

## Failure Recovery

### 1. Retry Logic
- Automatic retry on transient failures
- Exponential backoff
- Maximum retry limits
- Dead letter queue for failures

### 2. Data Recovery
- Failed webhooks logged
- Manual retry capability
- Sync status tracking
- Orphan detection

### 3. System Recovery
- Automatic reconnection
- Graceful degradation
- Circuit breaker pattern
- Health check endpoints

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Primary Code**: `/src/automation/scripts/airscripts-api/`
**Related**: BusinessLogicAtoZ.md, mermaid-flows.md