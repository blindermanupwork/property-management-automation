# Service Line Auto-Update Webhook Setup Guide

## Overview
This webhook automatically updates HCP service line descriptions when they change in Airtable, while preserving any manual notes added by staff.

## Current Limitations (Test Phase)
- **ONLY ENABLED FOR**: "Boris Blinderman Test Property"
- All other properties will be skipped to protect critical data

## Format
```
"Manual notes | Auto-generated service line"
Example: "BRING EXTRA TOWELS | Turnover STR Next Guest July 5"
```

## Behavior
1. **If pipe (|) exists**: Updates only the part after the pipe
2. **If no pipe exists**: Adds " | " then appends the service line
3. **If empty**: Uses just the service line without pipe

## Setup Instructions

### Step 1: Add Airtable Field
Add a new field to the Reservations table:
- **Field Name**: `Last Synced Service Line`
- **Field Type**: Single line text
- **Purpose**: Tracks what's currently in HCP to avoid redundant API calls

### Step 2: Create Airtable Automation (UI Method)

1. **Go to Automations tab** in your Airtable base
2. **Click "Create automation"**
3. **Name it**: "Update HCP Service Line - Test Property Only"

#### Configure Trigger:
1. **Choose trigger**: "When record is updated"
2. **Table**: Reservations
3. **Fields that trigger**: Service Line Description
4. **Test the trigger** with a sample record

#### Add Conditions:
1. **Click "Add advanced logic"** → "Add condition"
2. **Set conditions** (ALL must be true):
   - Property Name = "Boris Blinderman Test Property"
   - Service Job ID is not empty
   - Service Line Description is not empty

#### Configure Action (Script Method):
1. **Add action**: "Run a script"
2. **Add Input Variable**:
   - Name: `recordId`
   - Value: Click blue + and select "Airtable record ID" from the trigger record

3. **Copy the script** from:
   `/home/opc/automation/src/automation/scripts/airtable-automations/webhook-service-line-updater.js`

4. **IMPORTANT: Update these values in the script**:
   ```javascript
   const API_KEY = 'YOUR_API_KEY_HERE'; // Get from .env file
   const ENVIRONMENT = 'development'; // or 'production'
   ```

5. **Test the action** with your test record
6. **Review the output** - it will show if the webhook succeeded
7. **Turn on the automation**

#### Alternative: Configure Action (Webhook Method):
If you prefer the direct webhook approach:
1. **Add action**: "Send webhook"
2. **Configure webhook** with URL, headers, and body as described above

### Step 3: Test Process

1. Find a reservation for "Boris Blinderman Test Property" with an HCP job
2. Note the current line item name in HCP
3. Change the "Service Line Description" in Airtable
4. Verify:
   - Webhook fires (check Airtable automation history)
   - HCP line item updates correctly
   - Manual notes (if any) are preserved
   - "Last Synced Service Line" updates in Airtable

## Examples

### Scenario 1: Empty Line Item
- **Current HCP**: (empty)
- **Service Line**: "Turnover STR Next Guest July 5"
- **Result**: "Turnover STR Next Guest July 5"

### Scenario 2: Manual Notes Only
- **Current HCP**: "BRING EXTRA TOWELS"
- **Service Line**: "Turnover STR Next Guest July 5"
- **Result**: "BRING EXTRA TOWELS | Turnover STR Next Guest July 5"

### Scenario 3: Already Has Pipe
- **Current HCP**: "BRING TOWELS | Turnover STR Next Guest July 3"
- **Service Line**: "Turnover STR Next Guest July 5"
- **Result**: "BRING TOWELS | Turnover STR Next Guest July 5"

## Monitoring

### Check Webhook Logs
```bash
# API server logs
tail -f /var/log/airscripts-api.log | grep "Service line"

# Or check systemd logs
sudo journalctl -u airscripts-api-https -f | grep "Service line"
```

### Success Log Format
```
Service line update webhook received - Record: recXXX, Env: development
Adding pipe separator to existing content: "BRING EXTRA TOWELS"
Service line update successful for job job_xxx in 245ms
```

### Airtable Sync Details
The webhook updates "Service Sync Details" field with:
- ✅ Success: Shows previous and new values with timestamp
- ❌ Failure: Shows error message with timestamp

## Rollout Plan

1. **Phase 1** (Current): Test with Boris Blinderman Test Property only
2. **Phase 2**: Expand to a few trusted properties after validation
3. **Phase 3**: Enable for all properties after confirming safety

## Safety Features

1. **Property Filter**: Hard-coded to only process test property
2. **Preserve Manual Notes**: Never overwrites content before pipe
3. **Character Limit**: Intelligently truncates to fit HCP's 200-char limit
4. **Skip Unchanged**: Only calls API when content actually changes
5. **Error Recovery**: Updates Airtable with failure status if issues occur

## Rollback Plan

If issues occur:
1. Disable the Airtable automation
2. Manual notes remain preserved in HCP (before the pipe)
3. Python script continues running every 4 hours as fallback