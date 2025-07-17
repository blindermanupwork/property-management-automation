# API Server Documentation

## Overview

The API Server is a Node.js/Express application that serves as the bridge between Airtable and HousecallPro. It enables job creation, schedule management, and real-time synchronization through RESTful endpoints. The server handles environment-specific routing, webhook processing, and provides the core automation interface for the property management system.

## Quick Navigation

- **BusinessLogicAtoZ.md** - Complete business logic and API endpoints
- **SYSTEM_LOGICAL_FLOW.md** - Text-based operational flow descriptions
- **mermaid-flows.md** - Visual workflow diagrams
- **version-history.md** - Documentation change tracking

## Key Capabilities

### 1. Job Creation and Synchronization
- Create HCP jobs from Airtable reservations
- Apply job templates and line items
- Generate service line descriptions
- Update Airtable with job IDs

### 2. Schedule Management  
- Create/update HCP appointments
- Handle custom service times
- Sync schedule changes
- Manage employee assignments

### 3. Webhook Processing
- Receive HCP status updates
- Process job completion events
- Update Airtable in real-time
- Handle employee assignments

### 4. Environment Separation
- Separate dev/prod endpoints
- Environment-specific configurations
- Isolated data flows
- Different HCP accounts

## API Endpoints

### Development Environment
Base URL: `https://servativ.themomentcatchers.com/api/dev`

### Production Environment
Base URL: `https://servativ.themomentcatchers.com/api/prod`

### Key Endpoints

#### Job Management
- `POST /api/{env}/jobs/create` - Create HCP job from reservation
- `PUT /api/{env}/jobs/sync` - Sync job status
- `GET /api/{env}/jobs/{jobId}` - Get job details

#### Schedule Management
- `POST /api/{env}/schedules/add` - Create appointment
- `PUT /api/{env}/schedules/update` - Update appointment
- `DELETE /api/{env}/schedules/{appointmentId}` - Cancel appointment

#### Webhook Receipt
- `POST /api/{env}/webhooks/hcp` - Receive HCP updates

## Common Use Cases

### Property Management Context
1. **Daily Job Creation**: Create service jobs for upcoming checkouts
2. **Schedule Updates**: Adjust service times based on needs
3. **Status Tracking**: Monitor job progress in real-time
4. **Employee Assignment**: Track who's assigned to each job

### Button Actions in Airtable
1. **"Create Job & Sync Status"**: Calls job creation endpoint
2. **"Add/Update Schedule"**: Manages appointment times
3. **"Sync Job Status"**: Fetches latest from HCP
4. **"Cancel Job"**: Marks job as canceled

## Configuration

### Environment Variables
```bash
# Development
AIRTABLE_API_KEY_DEV=keyXXX
HCP_API_KEY_DEV=devKeyXXX
AIRTABLE_BASE_ID_DEV=app67yWFv0hKdl6jM

# Production  
AIRTABLE_API_KEY_PROD=keyYYY
HCP_API_KEY_PROD=prodKeyYYY
AIRTABLE_BASE_ID_PROD=appZzebEIqCU5R9ER

# Server Configuration
PORT=3000
NODE_ENV=production
```

### Job Type Configuration
```javascript
// Environment-specific job types
JOB_TYPE_STANDARD_CLEANING_DEV=jt_dev_123
JOB_TYPE_STANDARD_CLEANING_PROD=jt_prod_456
```

## Business Logic Highlights

### Service Line Generation
1. Start with custom instructions (if any)
2. Add "OWNER ARRIVING" (if applicable)
3. Add "LONG TERM GUEST DEPARTING" (if 14+ days)
4. Append base service name
5. Truncate to 200 characters for HCP

### Job Creation Flow
1. Validate reservation has required fields
2. Check property has HCP IDs
3. Generate service line description
4. Apply job template
5. Create job in HCP
6. Update Airtable with job ID

### Schedule Synchronization
1. Compare expected vs actual times
2. Update if mismatch detected
3. Log changes in sync fields
4. Alert on major discrepancies

## Error Handling

### Common Errors
1. **Missing HCP IDs**: Property not configured
2. **Invalid Service Time**: Format must be HH:MM AM/PM
3. **Job Already Exists**: Duplicate creation attempt
4. **Rate Limit**: Too many API calls

### Error Responses
```javascript
{
    error: "Property missing HCP Customer ID",
    details: "Property 'Beach House' needs HCP integration",
    suggestion: "Configure property in HCP first"
}
```

## Security

### Authentication
- API key validation for all endpoints
- Environment-specific keys
- CORS configuration for Airtable

### Data Protection
- No sensitive data in logs
- Sanitized error messages
- Request validation

## Performance

### Optimizations
- Connection pooling for APIs
- Response caching where appropriate
- Batch operations support
- Async processing

### Rate Limits
- HCP: 300 requests/minute
- Airtable: 5 requests/second
- Internal: No hard limits

## Deployment

### Server Management
```bash
# Start server
npm start

# Development mode
npm run dev

# View logs
pm2 logs airscripts-api

# Restart server
pm2 restart airscripts-api
```

### Health Checks
- `GET /health` - Server status
- `GET /api/{env}/status` - Environment status

## Related Documentation

- See **BusinessLogicAtoZ.md** for detailed endpoint documentation
- See **mermaid-flows.md** for visual workflows
- See **SYSTEM_LOGICAL_FLOW.md** for process descriptions

---

**Primary Code Location**: `/src/automation/scripts/airscripts-api/`  
**Main Files**: `server.js`, `handlers/jobs.js`, `handlers/schedules.js`  
**Port**: 3000 (HTTP), 3001 (HTTPS)  
**Last Updated**: July 12, 2025