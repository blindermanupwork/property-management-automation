# Duplicate Detection Bug Analysis

## Root Cause Identified

The ICS sync system has a critical bug in its duplicate detection logic that causes legitimate reservations to be incorrectly marked as "Removed" when Airbnb changes the UID for the same reservation.

## The Problem

### What's Happening:
1. Airbnb sometimes changes the UID for a reservation while keeping the same dates/property
2. When this happens:
   - Old UID: `1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com` (Record 37717)
   - New UID: `1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com` (Record 37941)
   - Same dates: 2025-07-20 to 2025-08-18
   - Same property: recVu3YtfTaoK3siK

### The Bug:
The duplicate detection logic has a flaw in how it tracks duplicates:

1. **During Event Processing**: 
   - When the new UID is processed, it calls `check_for_duplicate()`
   - This function finds the existing record (37717) and returns `True`
   - The event is marked as "Duplicate_Ignored" and skipped
   - **BUT**: The code only adds to `duplicate_detected_dates` if `status == "Duplicate_Ignored"`
   - Since the duplicate was ignored, no NEW record is created

2. **During Removal Detection**:
   - The old UID is missing from the feed (correctly detected)
   - The code checks if this record's dates are in `duplicate_detected_dates`
   - But `duplicate_detected_dates` is EMPTY because no new record was created
   - Therefore, the old record is marked for removal

## The Fix Needed

The duplicate detection needs to be fixed in one of two ways:

### Option 1: Track All Duplicates (Recommended)
Add duplicate dates to the tracking set whenever a duplicate is detected, regardless of whether a new record is created:

```python
# In process_ics_feed, after check_for_duplicate returns True:
if check_for_duplicate(...):
    status = "Duplicate_Ignored"
    # Add this line:
    duplicate_detected_dates.add((property_id, event["dtstart"], event["dtend"], event["entry_type"]))
```

### Option 2: Enhanced Removal Check
During removal detection, actively check if any current event in the feed has the same property/dates:

```python
# In removal detection, check current events for same property/dates
for current_event in events:
    if (current_event.get("property_id") == record_property_id and
        current_event.get("dtstart") == record_checkin and
        current_event.get("dtend") == record_checkout):
        logging.info(f"Skipping removal - found matching event with different UID")
        continue
```

## Impact

This bug causes:
1. Valid reservations to be marked as "Removed" incorrectly
2. Potential loss of HCP job links and sync status
3. Confusion when the "removed" reservation still appears in the property calendar

## Verification

The logs show:
- Record 37941 was created with the new UID
- Record 37717 should be marked as "Old" (duplicate), not "Removed"
- The removal count shows 0, indicating the removal logic isn't even running properly