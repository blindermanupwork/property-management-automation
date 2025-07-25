# Detailed Implementation Plan for UID Change Detection

**Created**: July 17, 2025  
**Purpose**: Step-by-step plan to safely implement UID change detection

---

## Current Situation

1. **Mayes duplicates cleaned**: 106 duplicate records removed
2. **icsProcess_best.py created**: Copy of optimized version with OperationCollector added
3. **Need to modify**: sync_ics_event, process_ics_feed, and related functions

---

## Implementation Strategy

### Option 1: Minimal Changes (Recommended)
Instead of rewriting the entire sync logic, we can:
1. Keep the existing sync_ics_event mostly intact
2. Add a collection phase that captures what WOULD be done
3. Add cross-reference logic BEFORE executing batch operations
4. Execute the filtered operations

### Option 2: Complete Rewrite (Risky)
1. Rewrite sync_ics_event to use OperationCollector
2. Change all function signatures
3. Update all calling code

**Decision**: Go with Option 1 for safety

---

## Revised Implementation Plan

### Step 1: Add Operation Tracking
Add a parameter to track operations without changing execution:

```python
def sync_ics_event(event, existing_records, url_to_prop, table, create_batch, update_batch, session_tracker=None, operation_tracker=None):
    # Existing logic stays the same
    # Just add tracking calls:
    if operation_tracker and creating_new:
        operation_tracker.track_addition(...)
    if operation_tracker and marking_removed:
        operation_tracker.track_removal(...)
```

### Step 2: Modify process_ics_feed
1. Create OperationCollector
2. Pass it as operation_tracker
3. After processing all events, cross-reference
4. Filter out UID changes from batch operations

### Step 3: Test Thoroughly
1. Run with dry-run mode
2. Compare outputs
3. Verify UID changes detected

---

## Simpler Alternative Approach

Since the existing code already handles most cases correctly, we could:

1. **Just fix the duplicate detection query** to include "Old" status
2. **Add UID change logging** without changing the core logic
3. **Monitor and iterate** based on results

This would be much safer and achieve the same goal.

---

## Recommendation

Let's go with the simpler approach first:
1. Fix the duplicate detection to include "Old" status records
2. Add comprehensive logging for UID changes
3. Test with Mayes property
4. If that doesn't work, then implement the full OperationCollector approach

This minimizes risk while still solving the problem.