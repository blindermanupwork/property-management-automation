# CSV Processing Field Cloning Analysis

## Overview
When a modification occurs in the CSV processing system (csvProcess.py), the `mark_all_as_old_and_clone` function handles the cloning of records. This analysis documents exactly which fields are preserved and which are updated.

## Cloning Process

### 1. Base Cloning Logic
```python
# Build clone (copy everything except blacklist)
clone = {k: v for k, v in old_f.items() if k not in WRITE_BLACKLIST}
```

The system starts by copying ALL fields from the original record EXCEPT those in the WRITE_BLACKLIST.

### 2. WRITE_BLACKLIST Fields (Excluded from Clone)
```python
WRITE_BLACKLIST = {
    "Final Service Time",          # computed roll-ups
    "Sync Date and Time",
    "Service Sync Details"         # Environment-specific field name
}
```

These fields are NOT copied to the cloned record.

### 3. HCP Fields (Explicitly Preserved)
```python
HCP_FIELDS = [
    "Service Job ID", "Job Creation Time", "Sync Status",
    "Scheduled Service Time", "Sync Date and Time", "Service Sync Details",
    "Job Status", "Custom Service Time", "Entry Source",
    "Service Appointment ID", "Assignee", "On My Way Time",
    "Job Started Time", "Job Completed Time", "Next Entry Is Block",
    "Owner Arriving", "Custom Service Line Instructions",
    "Service Line Description", "HCP Service Line Description",
    "Schedule Sync Details"
]
```

ALL HCP fields are explicitly preserved from the latest record, with special handling:
- **Service Job ID**: For "Removed" status, this is set to None. For "Modified" status, the original value is preserved.
- All other HCP fields are copied as-is from the original record.

### 4. Fields Updated During Modification

When a CSV modification is detected, these fields are typically updated:

```python
new_fields = {
    "Check-in Date": res["dtstart"],
    "Check-out Date": res["dtend"],
    "Entry Type": res["entry_type"],
    "Service Type": res["service_type"],
    "Overlapping Dates": res["overlapping"],
    "Same-day Turnover": res["same_day_turnover"],
    "Property ID": [res["property_id"]]
}
```

Additional conditional fields:
- **iTrip Report Info**: Added if source is "iTrip" and contractor_info exists
- **Block Type**: Added if block_type exists in the reservation data

### 5. System Fields Always Updated
```python
clone.update(Status=status, **field_to_change, **{"Last Updated": now_iso})
```

- **Status**: Changed to the new status ("Modified", "Removed", etc.)
- **Last Updated**: Set to current timestamp

### 6. Boolean Field Handling
The system ensures boolean fields are never None:
```python
boolean_fields = ["Same-day Turnover", "Overlapping Dates"]
```
If these fields are None in the clone and not being explicitly updated, they are converted to False.

## Summary of Field Behavior

### Preserved Fields (Copied from Original)
- All HCP-related fields (Job IDs, sync status, times, etc.)
- Reservation UID
- ICS URL
- Entry Source
- Any custom fields not in WRITE_BLACKLIST
- Tenant information
- Any other fields from the original record

### Updated Fields (From New CSV Data)
- Check-in Date
- Check-out Date
- Entry Type
- Service Type
- Overlapping Dates
- Same-day Turnover
- Property ID
- iTrip Report Info (if applicable)
- Block Type (if applicable)
- Status
- Last Updated

### Excluded Fields (Not Copied)
- Final Service Time
- Sync Date and Time
- Service Sync Details

### Special Handling
- **Service Job ID**: Cleared for "Removed" status, preserved for "Modified"
- **Boolean fields**: Converted from None to False if not explicitly set
- **Old records**: Service Job ID is prefixed with "old_" to disconnect webhook updates

## Use Cases

1. **Date Changes**: When check-in/out dates change, a new record is created with updated dates but preserving all HCP job information.

2. **Property Changes**: When property assignment changes, HCP fields are preserved to maintain job continuity.

3. **Flag Changes**: When overlapping dates or same-day turnover flags change, the HCP integration remains intact.

4. **Removals**: When a reservation is removed, HCP fields are preserved but Service Job ID is cleared.

5. **Reactivations**: When a removed reservation is reactivated, it gets fresh data from CSV but preserves any existing HCP fields from the old record.

## Race Condition Prevention
Before creating a clone, the system:
1. Waits 0.1 seconds
2. Re-fetches records for the UID
3. Checks if any newer records were created
4. Skips cloning if a race condition is detected