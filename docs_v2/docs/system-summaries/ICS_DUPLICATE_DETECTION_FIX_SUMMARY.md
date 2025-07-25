# ICS Duplicate Detection Fix Summary

## Problem Statement
Record 37717 was being incorrectly marked as "Removed" instead of "Old" when Airbnb changed the UID for the same reservation. This was causing legitimate reservations to appear as removed in the system.

## Root Causes Identified

### 1. **Incomplete Duplicate Tracking**
When a duplicate was detected (same property/dates but different UID), the system only tracked the NEW event's dates in `duplicate_detected_dates`. When the OLD record was checked for removal, its dates didn't match what was tracked, causing it to be marked as removed.

**Example:**
- Old record (37717): July 20 to Aug 20
- New record (37941): July 20 to Aug 18 (modified dates)
- Only tracked: (property, "2025-07-20", "2025-08-18", "Reservation")
- Checking for: (property, "2025-07-20", "2025-08-20", "Reservation") - NOT FOUND!

### 2. **Overly Restrictive Future Check-in Filter**
The removal logic was skipping ALL reservations with future check-ins, preventing legitimate removals of near-future reservations that disappear from feeds.

## Fixes Applied

### 1. **Enhanced Duplicate Detection Function**
Added `check_for_duplicate_with_tracking()` that:
- Detects exact duplicates (same property/dates/type)
- Also returns related records (same property, different dates)
- Helps identify UID changes for the same reservation

### 2. **Comprehensive Duplicate Tracking**
Modified the duplicate tracking to include:
- The current event's dates (as before)
- ALL related records' dates for the same property
- This ensures old records with changed UIDs aren't marked as removed

### 3. **Relaxed Future Check-in Filter**
Changed from:
- Skip if check-in >= today (too restrictive)

To:
- Skip only if check-in > 6 months in future
- Allows removal of near-future reservations that legitimately disappear

## Code Changes

### New Function Added:
```python
def check_for_duplicate_with_tracking(table, property_id, checkin_date, checkout_date, entry_type):
    """
    Enhanced duplicate check that returns both the duplicate status 
    and any existing records with same property but different dates.
    This helps track UID changes for the same reservation.
    """
    # ... implementation ...
    return is_duplicate, related_records
```

### Modified Duplicate Tracking:
```python
# If this was a duplicate, track the property/date combination
if status == "Duplicate_Ignored" and property_id:
    # Track the current event's dates
    duplicate_key = (property_id, event["dtstart"], event["dtend"], event["entry_type"])
    duplicate_detected_dates.add(duplicate_key)
    
    # ALSO get and track all related records to prevent false removals
    _, related_records = check_for_duplicate_with_tracking(
        table, property_id, event["dtstart"], event["dtend"], event["entry_type"]
    )
    for related in related_records:
        fields = related["fields"]
        related_key = (
            property_id,
            fields.get("Check-in Date", ""),
            fields.get("Check-out Date", ""),
            fields.get("Entry Type", "")
        )
        if related_key[1] and related_key[2]:  # Only add if dates are present
            duplicate_detected_dates.add(related_key)
            logging.info(f"Also tracking related record dates: {related_key[1]} to {related_key[2]}")
```

### Updated Removal Filter:
```python
# Skip only if check-in is far in the future (>6 months)
# This allows removal of near-future reservations that disappear from feeds
future_cutoff = (date.today() + relativedelta(months=6)).isoformat()
if fields.get("Check-in Date", "") > future_cutoff:
    logging.info(f"Skipping removal check for far-future reservation (check-in: {fields.get('Check-in Date', '')})")
    continue
```

## Expected Behavior After Fix

1. **UID Changes**: When Airbnb changes a reservation's UID:
   - Old record marked as "Old" (not "Removed")
   - New record created with "New" or "Modified" status
   - No false removals

2. **Genuine Removals**: When a reservation truly disappears:
   - Record marked as "Removed" if within 6 months
   - Far-future reservations (>6 months) not checked for removal

3. **Modified Reservations**: When dates change with UID change:
   - Both old and new date combinations tracked
   - Old record marked as "Old"
   - New record reflects updated dates

## Testing Recommendations

1. **Test Case 1: UID Change, Same Dates**
   - Feed contains new UID for same property/dates
   - Verify old record → "Old" status

2. **Test Case 2: UID Change, Different Dates**
   - Feed contains new UID with modified dates
   - Verify old record → "Old" status
   - Verify new record created with new dates

3. **Test Case 3: Genuine Removal**
   - Event missing from feed entirely
   - No other events for same property/dates
   - Verify record → "Removed" status

4. **Test Case 4: Future Removals**
   - Test with various future check-in dates
   - Verify <6 months → can be removed
   - Verify >6 months → skipped

## Other Issues Found

1. **Debug Logging**: Added comprehensive debug logging for troubleshooting
2. **Race Conditions**: Session tracker helps but may not catch all cases
3. **Composite UID Complexity**: The UID_propertyID system adds complexity
4. **Memory Usage**: `duplicate_detected_dates` grows during processing

## Files Modified

- `/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py`

## Verification

Run the ICS sync and check:
1. Record 37717 should NOT be marked as "Removed"
2. Related record 37941 should exist with updated dates
3. No false removals for UID changes
4. Genuine removals still work correctly

## Long-term Recommendations

1. Consider storing UID history in Airtable to track changes
2. Add unit tests for duplicate detection logic
3. Monitor memory usage with large numbers of feeds
4. Consider database transactions instead of in-memory tracking