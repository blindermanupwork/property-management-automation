# Clear Sync Messages Implementation (Dev Only)

## Overview
Implemented a clearer sync messaging system for the development environment that replaces vague messages with explicit "Source A says X, Source B says Y" format.

## What Changed

### Before (Vague Messages)
- ❌ "Matches service date & time" 
- ❌ "Final Service Time is 10:00 AM but service is 2:00 PM"
- ❌ "Updated schedule"
- ❌ "No HCP job"

### After (Clear Messages)
- ✅ "HCP schedule matches Airtable (Jun 12 at 10:00 AM)"
- ✅ "Airtable expects 10:00 AM, HCP scheduled for 2:00 PM (4 hours off)"
- ✅ "Updated HCP schedule from 2:00 PM to 10:00 AM"
- ✅ "Airtable expects cleaning job, HCP has no job created"

## Files Modified

### 1. **Sync Message Builder** (New)
- `src/automation/scripts/shared/syncMessageBuilder.js`
- Centralized message generation with severity icons
- Shows time differences (15 min off, 4 hours off, 1 day off)
- Only loads in development environment

### 2. **Webhook Handler** 
- `src/automation/scripts/webhook/webhook.py`
- Updated 8 message types for clearer webhook notifications
- Examples:
  - "✅ Updated HCP job status to 'completed'"
  - "⚠️ HCP appointment 12345 discarded, job unscheduled"

### 3. **Schedule Handler**
- `src/automation/scripts/airscripts-api/handlers/schedules.js`
- Updated 12 message types for schedule comparisons
- Examples:
  - "🚨 Airtable expects Jun 12, HCP scheduled for Jun 13 (1 day off)"
  - "✅ Updated HCP schedule from Jun 12 at 2:00 PM to Jun 12 at 10:00 AM"

### 4. **Job Creation Handler**
- `src/automation/scripts/airscripts-api/handlers/createJob.js`
- Updated 4 message types for job creation sync
- Examples:
  - "⚠️ Airtable expects 10:00 AM, HCP scheduled for 10:15 AM (15 min off)"

### 5. **HCP Sync Script**
- `src/automation/scripts/hcp/hcp_sync.js`
- Updated 6 message types for main sync operations
- Examples:
  - "❌ Cannot create HCP job - no template found for 'Turnover' service"

## Key Features

### Severity Indicators
- 🚨 **Critical**: Date mismatches (days off)
- ⚠️ **Warning**: Time mismatches (hours/minutes off)
- ✅ **Success**: Everything working correctly
- ❌ **Error**: Missing jobs, templates, etc.

### Time Difference Detection
- Automatically calculates and shows:
  - "15 min off" for minor issues
  - "4 hours off" for major issues
  - "1 day off" for critical issues

### Environment Separation
- **Development**: Uses new clear messages
- **Production**: Keeps original messages (no disruption)
- Graceful fallback if message builder fails to load

## Testing

Run the test script to see all message examples:
```bash
cd /home/opc/automation
node test_sync_messages.js
```

## Benefits for Operations

1. **Immediately Clear**: No more guessing what "matches service date & time" means
2. **Actionable**: Shows exactly what needs to be fixed
3. **Prioritized**: Icons indicate severity (🚨 = urgent, ⚠️ = needs attention)
4. **Specific**: Shows actual times/dates from both systems
5. **Safe**: Only affects dev environment for testing

## Example Scenarios

### Perfect Sync
```
Old: "Matches service date & time"
New: "✅ HCP schedule matches Airtable (Jun 12 at 10:00 AM)"
```

### Time Problem
```
Old: "Final Service Time is 10:00 AM but service is 2:00 PM"
New: "⚠️ Airtable expects 10:00 AM, HCP scheduled for 2:00 PM (4 hours off)"
```

### Date Problem
```
Old: "Final Service Time is June 12 but service is June 13"  
New: "🚨 Airtable expects Jun 12, HCP scheduled for Jun 13 (1 day off)"
```

### Missing Job
```
Old: "No HCP job"
New: "❌ Airtable expects cleaning job, HCP has no job created"
```

### Successful Update
```
Old: "Updated schedule"
New: "✅ Updated HCP schedule from Jun 12 at 2:00 PM to Jun 12 at 10:00 AM"
```

## Next Steps

1. **Test in Dev**: Use development environment to see new messages
2. **Gather Feedback**: See if operations team finds them clearer
3. **Refine**: Adjust message format based on feedback
4. **Production**: If successful, enable for production environment

## Rollback Plan

To revert to original messages:
1. Set `ENVIRONMENT=production` in dev environment
2. Or remove the sync message builder import from files
3. Original messages will be used automatically