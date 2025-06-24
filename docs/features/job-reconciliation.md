# HCP Job Reconciliation Feature

## Overview

The job reconciliation feature automatically matches existing HousecallPro (HCP) jobs with Airtable reservations when jobs are created outside the normal automation flow. This is particularly useful when properties are activated after jobs have already been created in HCP.

## Two Implementation Options

### 1. Standalone Script (Ready to Use)

**Location**: `/home/opc/automation/src/automation/scripts/hcp/reconcile-jobs-dev.py`

**Usage**:
```bash
# Dry run (default) - shows what would be matched without making changes
python3 /home/opc/automation/src/automation/scripts/hcp/reconcile-jobs-dev.py

# Execute reconciliation
python3 /home/opc/automation/src/automation/scripts/hcp/reconcile-jobs-dev.py --execute
```

**Features**:
- Fetches reservations without Service Job IDs
- Fetches HCP jobs within date range
- Matches based on:
  - HCP customer ID
  - HCP address ID  
  - Scheduled time (within 1 hour window)
- Updates Airtable with matched job IDs
- Detailed logging of matches and mismatches

### 2. Webhook Integration (Automatic)

**Location**: `/home/opc/automation/src/automation/scripts/webhook/webhook_reconciliation.py`

**Setup Instructions**: Run the integration helper:
```bash
python3 /home/opc/automation/src/automation/scripts/webhook/integrate_reconciliation.py
```

**Features**:
- Automatically triggered when webhooks arrive for unlinked jobs
- Same matching logic as standalone script
- Real-time reconciliation as jobs are updated
- Currently enabled only in dev environment for safety

## How Matching Works

The reconciliation process matches jobs based on three criteria:

1. **Property Match**: The HCP customer ID and address ID must match the property's linked customer and address
2. **Time Match**: The job's scheduled start time must be within 1 hour of the reservation's Final Service Time
3. **Availability**: The reservation must not already have a Service Job ID

When multiple matches are found, the closest time match is selected.

## Example Scenarios

### Scenario 1: Property Activated After Jobs Created
1. Client creates jobs in HCP before property is set up in our system
2. Property is activated and reservations are imported
3. Run reconciliation to link existing jobs to reservations

### Scenario 2: Manual Job Creation
1. User creates job directly in HCP (bypassing our automation)
2. Webhook arrives for the manually created job
3. Webhook integration automatically finds and links matching reservation

## Monitoring

### Logs to Watch

**Standalone Script**:
- Look for "Starting HCP job reconciliation" messages
- Check for "Found match" and "No matching job found" entries
- Review summary at end showing matched/unmatched counts

**Webhook Integration**:
- Watch for "🔍 No reservation linked to job" (triggers reconciliation)
- Look for "🔄 Attempting to reconcile job" (reconciliation in progress)
- Check for "✅ Successfully reconciled job" (successful match)

### Webhook Log Files:
- Development: `/home/opc/automation/src/automation/logs/webhook_development.log`
- Production: `/home/opc/automation/src/automation/logs/webhook.log`

## Safety Features

1. **Dry Run Mode**: Standalone script defaults to dry run
2. **Environment Restriction**: Webhook integration only runs in dev by default
3. **Time Window**: Only matches jobs within 1 hour of reservation time
4. **No Overwrites**: Only updates reservations without existing job IDs

## Troubleshooting

### No Matches Found
- Verify property has HCP Customer ID and HCP Address ID set
- Check that job times are within 1 hour of reservation times
- Ensure reservations don't already have Service Job IDs

### Webhook Not Reconciling
- Confirm webhook integration is enabled (check logs)
- Verify environment is set to 'development'
- Check that webhook events are being received

## Future Enhancements

1. **Production Enablement**: Remove dev-only restriction after testing
2. **Wider Time Windows**: Allow configuration of matching time window
3. **Partial Matches**: Handle cases where only customer OR address matches
4. **Bulk Operations**: Add ability to reconcile specific date ranges