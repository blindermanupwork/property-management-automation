# HousecallPro Integration

## Purpose
Integrate Airtable reservations with HousecallPro (HCP) for service job management. This feature creates cleaning jobs, manages schedules, syncs job status, handles service line items, and processes webhooks for real-time updates between systems.

## Quick Start
1. Reservation marked "Ready for Job" in Airtable
2. User clicks "Create Job & Sync Status" button
3. Job created in HCP with schedule and line items
4. Webhook updates flow back to Airtable
5. Continuous two-way sync maintained

## Key Components
- **Job Creation**: REST API calls to HCP
- **Schedule Management**: Custom times and arrival windows
- **Service Lines**: Dynamic line items with custom instructions
- **Webhook Processing**: Real-time status updates
- **Status Sync**: Bidirectional synchronization
- **Long-term Guest Detection**: 14+ day stay flagging
- **Owner Arrival Detection**: Next-day owner check-in flagging

## Directory Structure
```
04-housecallpro-integration/
├── README.md                    # This file
├── BusinessLogicAtoZ.md         # HCP integration rules
├── SYSTEM_LOGICAL_FLOW.md       # Integration flow diagrams
├── version-history.md           # Change tracking
├── flows/
│   ├── job-creation.mmd        # Job creation process
│   ├── schedule-sync.mmd       # Schedule management
│   ├── webhook-flow.mmd        # Webhook processing
│   └── status-mapping.mmd      # Status synchronization
└── examples/
    ├── job-payload.json         # HCP job creation request
    ├── webhook-event.json       # Sample webhook payload
    └── service-lines.txt        # Line item examples
```

## Integration Scripts
- **Job Creation**: `/home/opc/automation/src/automation/scripts/hcp/dev-hcp-sync.cjs` (dev)
- **Job Creation**: `/home/opc/automation/src/automation/scripts/hcp/prod-hcp-sync.cjs` (prod)
- **Job Reconciliation (Optimized)**: `/home/opc/automation/src/automation/scripts/hcp/reconcile-jobs-optimized.py`
- **API Server**: `/home/opc/automation/src/automation/scripts/airscripts-api/handlers/jobs.js`
- **Webhook Handler**: `/home/opc/automation/src/automation/scripts/webhook/webhook.py`
- **Service Updates**: `/home/opc/automation/src/automation/scripts/hcp/update-service-lines-enhanced.py`

## API Endpoints
```
# Development
POST https://servativ.themomentcatchers.com/api/dev/create-job
POST https://servativ.themomentcatchers.com/api/dev/update-schedule
POST https://servativ.themomentcatchers.com/webhooks/hcp-dev

# Production  
POST https://servativ.themomentcatchers.com/api/prod/create-job
POST https://servativ.themomentcatchers.com/api/prod/update-schedule
POST https://servativ.themomentcatchers.com/webhooks/hcp
```

## Service Line Item Features
- **Custom Instructions**: 200-character limit, Unicode support
- **Long-term Guest Flag**: "LONG TERM GUEST DEPARTING" for 14+ days
- **Owner Arrival Flag**: "OWNER ARRIVING" when owner checks in next
- **Dynamic Naming**: Base service name + special flags
- **Template Support**: Configurable job templates

## Related Features
- [Airtable Integration](../05-airtable-integration/) - Database operations
- [Schedule Management](../08-schedule-management/) - Service timing logic
- [Webhook Processing](../12-webhook-processing/) - Real-time updates
- [API Server](../07-api-server/) - REST endpoints
- [MCP Servers](../06-mcp-servers/hcp-mcp/) - AI analysis tools

## Common Issues
1. **Job Creation Fails**: Check HCP customer exists
2. **Schedule Not Syncing**: Verify webhook URL configuration
3. **Wrong Status**: Check status mapping table
4. **Missing Line Items**: Ensure job type configured
5. **Webhook Errors**: Verify signature and environment
6. **Job Reconciliation Needed**: Use optimized script for existing unlinked jobs

## Configuration
```javascript
// Environment Variables
HCP_API_KEY_DEV=dev_key
HCP_API_KEY_PROD=prod_key
HCP_COMPANY_ID=company_id
SERVATIV_WEBHOOK_SECRET=webhook_secret

// Job Type IDs (per environment)
HCP_STR_NEXT_GUEST_JOB_TYPE_ID=jobtype_123
HCP_STR_OWNER_JOB_TYPE_ID=jobtype_456
```

## Maintenance Notes
- Test webhook connectivity monthly
- Verify job type IDs after HCP updates
- Monitor webhook logs for errors
- Update service line templates quarterly
- Check customer matching logic
- Run job reconciliation weekly for data quality

## Version
Current: v2.2.8 (July 11, 2025) - Enhanced Service Line Updates