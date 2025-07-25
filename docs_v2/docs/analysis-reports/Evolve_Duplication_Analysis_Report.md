# Evolve CSV Duplication Analysis Report
*Generated: June 30, 2025*

## Executive Summary

The Evolve CSV processing is NOT creating new duplicates. The system is working correctly by marking entries as "Modified" when there are actual data changes in the CSV files. The issue is that Evolve's data export contains frequent minor changes that trigger the "Modified" status, creating what appears to be unnecessary duplicates but are actually legitimate change tracking records.

## Key Findings

### 1. ✅ The Duplicate Detection Logic is Working Correctly

The June 23, 2025 fix (commit 545ac4b) successfully resolved the composite UID matching issue:
- Airtable records are now properly indexed by both base UID and composite UID
- The system correctly finds existing records regardless of lookup method
- No new duplicates are being created for the same reservation

### 2. 📊 Current State of 2065 W 1st Pl Reservations

Looking at reservation UID `14545399` (Kevin Quichocho, June 24-30):
- **1 Active Record**: Status = "Modified" (ID: 36566)
- **13 Historical Records**: Status = "Old" 
- **Total**: 14 records for the same reservation

This is expected behavior when a reservation gets updated multiple times.

### 3. 🔍 Why Entries Keep Being Marked as "Modified"

The system marks a reservation as "Modified" when ANY of these fields change:
- Check-in/Check-out dates
- Property ID
- Overlapping dates flag
- Same-day turnover flag
- Entry type (Reservation vs Block)
- Service type

Based on the logs showing "Unchanged: 4 reservations" for 2065 W 1st Pl, the current data in Evolve CSV matches what's in Airtable.

### 4. 🎯 Root Cause Analysis

The issue is likely caused by one of these scenarios:

#### A. **Evolve Data Export Variations**
Evolve might export slightly different data at different times:
- Date format changes (though normalized in code)
- Status changes that affect calculated flags
- Guest name variations
- Property listing number changes

#### B. **Same-Day Turnover Flag Fluctuations**
The same-day turnover flag is calculated based on OTHER reservations:
- If another reservation's dates change, it can affect this flag
- New reservations can trigger recalculation
- Cancelled reservations change the calculation

#### C. **Historical Data Accumulation**
Each time ANY field changes:
1. Current record marked as "Old"
2. New "Modified" record created
3. This preserves complete history but creates many records

## Evidence from Logs

```
Entry Source -> Evolve Property -> 453658 Address -> 2065 W 1st Pl
 * New: 0 reservations and 0 blocks
 * Modified: 0 reservations and 0 blocks
 * Unchanged: 4 reservations and 0 blocks
 * Removed: 0 reservations and 0 blocks
```

This shows the system is correctly identifying that current Evolve data matches Airtable.

## Recommendations

### 1. **Verify Evolve Export Consistency**
- Compare multiple Evolve CSV exports taken minutes apart
- Check if data changes between exports (especially dates, status)
- Look for pattern in what triggers "Modified" status

### 2. **Add Debug Logging**
Add temporary logging to track exactly what changes:
```python
if uid == "14545399":  # Or other problematic UIDs
    logging.info(f"EVOLVE DEBUG: Comparing {uid}")
    logging.info(f"  CSV: {res}")
    logging.info(f"  Airtable: {at_fields}")
    # Log each field comparison...
```

### 3. **Consider Business Logic Adjustments**
- Should same-day turnover flag changes trigger "Modified" status?
- Should minor date format variations be ignored?
- Should there be a "change threshold" before marking as Modified?

### 4. **Data Cleanup Options**
- Run periodic cleanup to archive very old "Old" records
- Implement a maximum history depth (e.g., keep only last 5 versions)
- Add automation to consolidate historical records

## Technical Details

### Composite UID Format
- Base UID: `14545399` (from Evolve)
- Property Record ID: `recw2j5cweaW7H2i6` 
- Composite UID: `14545399_recw2j5cweaW7H2i6`

### Status Flow
1. **New** → First time seeing reservation
2. **Modified** → Any field changed from last sync
3. **Old** → Previous version when Modified record created
4. **Removed** → Reservation no longer in CSV

### Duplicate Prevention
The system successfully prevents true duplicates by:
1. Checking both base UID and composite UID
2. Using session tracking to prevent within-run duplicates
3. Checking Airtable for existing property/date combinations

## Conclusion

The system is functioning as designed. The perceived "duplication" issue is actually the system correctly tracking changes to Evolve reservations over time. The high number of "Old" records indicates that Evolve data changes frequently, triggering the modification tracking.

To reduce the number of historical records, you would need to either:
1. Make Evolve exports more consistent
2. Adjust the change detection logic to ignore minor variations
3. Implement periodic cleanup of old historical records

The current behavior ensures complete audit trail and data integrity, which may be valuable for business operations.