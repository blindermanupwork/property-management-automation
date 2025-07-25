# Complete Root Cause Analysis: Record 37717 Not Being Marked as Removed

## Executive Summary
Record 37717 is being incorrectly marked as "Removed" instead of "Old" due to a bug in the duplicate detection logic. When Airbnb changes the UID for a reservation, the system correctly detects the duplicate but fails to track it properly, leading to the old record being marked as removed during the removal detection phase.

## The Complete Flow

### 1. Initial State
- **Old Record (37717)**: UID `1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com`, dates July 20-Aug 20
- **Feed Update**: Airbnb changes the reservation to July 20-Aug 18 with new UID `1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com`

### 2. Event Processing Phase
When the new UID is processed:
```python
# In process_single_event(), around line 1146-1160
if property_id and check_for_duplicate(...):
    # Duplicate found!
    if active_records:
        # Check if it's the same reservation (different code path)
        if (dates match):
            # Not this case
        else:
            # Line 1156: Different dates - true duplicate
            return "Duplicate_Ignored"
    else:
        # Line 1160: No records with this UID but duplicate exists
        return "Duplicate_Ignored"
```

### 3. The Critical Bug
After returning "Duplicate_Ignored", the code tracks this duplicate:
```python
# Line 1283-1285
if status == "Duplicate_Ignored" and property_id:
    duplicate_key = (property_id, event["dtstart"], event["dtend"], event["entry_type"])
    duplicate_detected_dates.add(duplicate_key)
```

**THE PROBLEM**: The code adds the NEW event's dates (July 20-Aug 18) to `duplicate_detected_dates`, but the OLD record has dates July 20-Aug 20. These don't match!

### 4. Removal Detection Phase
When checking if the old record should be removed:
```python
# Around line 1337-1340
duplicate_key = (record_property_id, record_checkin, record_checkout, record_entry_type)
if duplicate_key in duplicate_detected_dates:
    logging.info(f"Skipping removal of {uid} - same reservation detected with different UID")
    continue
```

**THE FAILURE**: 
- Looking for: `(property, "2025-07-20", "2025-08-20", "Reservation")` (old record's dates)
- Set contains: `(property, "2025-07-20", "2025-08-18", "Reservation")` (new record's dates)
- Result: No match found, removal proceeds!

### 5. Secondary Issue: Check-in Date Filter
The trace script revealed another issue:
```python
# Check-in date is July 20, today is July 11
# The removal logic skips records with future check-ins
if checkin >= today_iso:
    # Skip removal for future check-ins
    continue
```

This is preventing ANY removal from happening, which is why we see 0 removals in the logs.

## The Fix

### Primary Fix: Track All Duplicate Combinations
We need to track BOTH the old and new date combinations when a duplicate is detected:

```python
def check_for_duplicate_with_tracking(table, property_id, checkin_date, checkout_date, entry_type):
    """
    Enhanced duplicate check that returns both the duplicate status 
    and any existing records with same property but different dates.
    """
    if not property_id:
        return False, []
    
    try:
        # Get ALL records for this property regardless of dates
        property_formula = f"FIND('{property_id}', ARRAYJOIN({{Property ID}}, ','))"
        all_property_records = table.all(
            formula=property_formula, 
            fields=["Reservation UID", "Status", "Check-in Date", "Check-out Date", "Entry Type"]
        )
        
        # Find exact duplicates and related records
        exact_duplicates = []
        related_records = []
        
        for record in all_property_records:
            fields = record["fields"]
            if (fields.get("Check-in Date") == checkin_date and 
                fields.get("Check-out Date") == checkout_date and
                fields.get("Entry Type") == entry_type and
                fields.get("Status") in ("New", "Modified")):
                exact_duplicates.append(record)
            elif fields.get("Status") in ("New", "Modified"):
                # Different dates but same property - potential UID change
                related_records.append(record)
        
        return len(exact_duplicates) > 0, related_records
        
    except Exception as e:
        logging.error(f"Error checking for duplicates: {str(e)}")
        return False, []
```

Then in the main processing:
```python
# When processing events
is_duplicate, related_records = check_for_duplicate_with_tracking(...)

if is_duplicate:
    # Track the current event's dates
    duplicate_detected_dates.add((property_id, event["dtstart"], event["dtend"], event["entry_type"]))
    
    # ALSO track all related records' dates to prevent false removals
    for related in related_records:
        fields = related["fields"]
        related_key = (
            property_id,
            fields.get("Check-in Date"),
            fields.get("Check-out Date"),
            fields.get("Entry Type")
        )
        duplicate_detected_dates.add(related_key)
    
    return "Duplicate_Ignored"
```

### Secondary Fix: Remove Future Check-in Filter for Removals
The removal logic should not skip future check-ins if they're genuinely missing from the feed:

```python
# In removal detection, remove this condition:
# if checkin >= today_iso:
#     continue

# Or modify it to only skip far-future dates:
future_cutoff = (date.today() + relativedelta(months=6)).isoformat()
if checkin > future_cutoff:
    continue  # Only skip if more than 6 months out
```

## Impact Analysis

### Current Behavior
1. Legitimate reservations marked as "Removed" when UIDs change
2. Removal detection completely skipped for future check-ins
3. Data integrity issues when Airbnb modifies reservations

### After Fix
1. UID changes properly handled - old records marked as "Old"
2. Removal detection works for all missing reservations
3. Proper tracking prevents false removals

## Testing Recommendations

1. **Test Case 1**: Feed with changed UID for same property/dates
   - Verify old record marked as "Old", not "Removed"
   
2. **Test Case 2**: Feed with changed UID AND changed dates
   - Verify both old and new date combinations tracked
   - Verify old record marked as "Old", not "Removed"

3. **Test Case 3**: Genuine removal (event missing from feed)
   - Verify record properly marked as "Removed"

4. **Test Case 4**: Future check-in removal
   - Verify future reservations can be marked as removed if missing

## Other Potential Issues Found

1. **Race Conditions**: The session_tracker helps but may not catch all race conditions
2. **Composite UID Complexity**: The composite UID system adds complexity that may hide bugs
3. **Date Comparison Sensitivity**: String date comparisons assume consistent formatting
4. **Memory Usage**: duplicate_detected_dates grows unbounded during processing

## Recommended Implementation Priority

1. **Immediate**: Fix duplicate tracking to include all related records
2. **Soon**: Adjust or remove the future check-in filter  
3. **Later**: Add comprehensive logging for duplicate detection
4. **Future**: Refactor to use database transactions instead of in-memory tracking