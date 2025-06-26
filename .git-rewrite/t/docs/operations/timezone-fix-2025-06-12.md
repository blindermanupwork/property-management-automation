# Timezone Fix for "Sync Date and Time" Field
**Date**: June 12, 2025  
**Issue**: Airtable rejecting timezone-aware timestamps in "Sync Date and Time" field

## Problem Description
The webhook script was setting "Sync Date and Time" with timezone-aware timestamps like `2025-06-11T18:13:31-07:00`, which Airtable was rejecting. Airtable expects UTC timestamps in ISO format ending with 'Z'.

## Root Cause
1. **webhook.py**: The `update_sync_info()` function was using `get_arizona_time().isoformat(timespec='seconds')` which included the timezone offset (`-07:00`)
2. **airscripts-api/utils/datetime.js**: The `getArizonaTime()` function was incorrectly manipulating UTC time by subtracting 7 hours, creating invalid timestamps

## Files Fixed

### 1. `/home/opc/automation/src/automation/scripts/webhook/webhook.py`
**Line 384**: Changed from:
```python
now = get_arizona_time().isoformat(timespec='seconds')
```
To:
```python
# Get current UTC time for Airtable (it expects UTC)
now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
```

### 2. `/home/opc/automation/src/automation/scripts/airscripts-api/utils/datetime.js`
**Lines 7-11**: Changed from:
```javascript
function getArizonaTime() {
  const now = new Date();
  // Arizona is UTC-7 (MST, no daylight saving)
  const arizonaTime = new Date(now.getTime() - (7 * 60 * 60 * 1000));
  return arizonaTime.toISOString();
}
```
To:
```javascript
function getArizonaTime() {
  // Return UTC time as Airtable expects UTC timestamps
  return new Date().toISOString();
}
```

## Why These Scripts Were Correct
The HCP sync scripts (dev-hcp-sync.cjs and prod-hcp-sync.cjs) were already using `new Date().toISOString()` which correctly returns UTC timestamps ending with 'Z'.

## Impact
- All timestamps stored in Airtable's "Sync Date and Time" field will now be in proper UTC format
- No more webhook processing errors due to invalid timestamp format
- Consistent timestamp handling across all automation scripts

## Testing Required
1. Trigger a webhook update and verify "Sync Date and Time" is set correctly
2. Run the airscripts-api schedule update and verify timestamps are correct
3. Confirm HCP sync scripts continue to work properly (they should be unaffected)

## Note on Display
While timestamps are stored in UTC, Airtable will display them in the viewer's local timezone automatically. This is the expected behavior.