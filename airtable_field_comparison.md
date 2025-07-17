# Airtable Reservations Field Comparison Analysis

## Overview
This document compares all fields in the Airtable Reservations table against what's being cloned in the CSV processing logic.

## Field Categories and Analysis

### 1. Auto-Generated/System Fields (Not Cloned - Correct)
- **ID** (autoNumber) - Auto-generated, cannot be edited
- **Final Service Time** (formula) - Computed field, in WRITE_BLACKLIST
- **Sync Date and Time** - In WRITE_BLACKLIST
- **Service Sync Details** - In WRITE_BLACKLIST (environment-specific)

### 2. Core Reservation Fields (Properly Handled)
- **Reservation UID** ✅ - Set from CSV data
- **Check-in Date** ✅ - Set from CSV data
- **Check-out Date** ✅ - Set from CSV data
- **Property ID** ✅ - Set from CSV data
- **ICS URL** ✅ - Set from CSV data (source identifier)
- **Status** ✅ - Set to New/Modified/Old/Removed
- **Entry Type** ✅ - Set to Reservation/Block
- **Service Type** ✅ - Set based on logic
- **Entry Source** ✅ - Set from CSV data
- **Same-day Turnover** ✅ - Calculated and set
- **Overlapping Dates** ✅ - Calculated and set
- **Last Updated** ✅ - Set to current time
- **iTrip Report Info** ✅ - Set from CSV data

### 3. HCP Integration Fields (Explicitly Preserved)
All these fields are in HCP_FIELDS list and are explicitly preserved during cloning:
- **Service Job ID** ✅
- **Job Creation Time** ✅
- **Job Status** ✅
- **Scheduled Service Time** ✅
- **Custom Service Time** ✅
- **Service Appointment ID** ✅
- **Assignee** ✅
- **On My Way Time** ✅
- **Job Started Time** ✅
- **Job Completed Time** ✅
- **Next Entry Is Block** ✅
- **Owner Arriving** ✅
- **Custom Service Line Instructions** ✅
- **Service Line Description** ✅
- **HCP Service Line Description** ✅
- **Schedule Sync Details** ✅

### 4. Lookup/Computed Fields (Not Set Directly - Correct)
- **HCP Address (from Property ID)** - Lookup field, auto-populated
- **Full Name (from HCP Customer ID) (from Property ID)** - Lookup field, auto-populated

### 5. Button Fields (Not Data - Correct)
- **Add/Update Schedule** - Button, not data
- **Create Job & Sync Status** - Button, not data
- **Service Job Link** - Button, not data
- **Delete Job Schedule** - Button, not data

### 6. Optional/Manual Fields (Potentially Missing)
These fields are NOT explicitly mentioned in the code and may not be preserved during cloning:
- **Block Type** ⚠️ - Only set for new blocks, but NOT preserved during cloning
- **Next Guest Date** ⚠️ - Not mentioned in HCP_FIELDS or cloning logic
- **Service Job Images** ⚠️ - Not mentioned in HCP_FIELDS or cloning logic

## Critical Findings

### 1. Block Type Field Issue
The `Block Type` field is set when creating new blocks from Evolve data:
```python
if res.get("block_type"):
    new_fields["Block Type"] = res["block_type"]
```
However, it's NOT in the HCP_FIELDS list, so it won't be preserved when cloning existing records.

### 2. Next Guest Date Field
This field is used in service line descriptions but is NOT in HCP_FIELDS, so it may be lost during cloning operations.

### 3. Service Job Images Field
This attachment field (for Supabase webhooks) is not preserved during cloning.

## Recommendations

1. **Add Missing Fields to HCP_FIELDS**:
   ```python
   HCP_FIELDS = [
       # ... existing fields ...
       "Block Type",           # Add this
       "Next Guest Date",      # Add this
       "Service Job Images",   # Add this
   ]
   ```

2. **Alternative: Generic Field Preservation**
   Instead of maintaining a specific list, consider preserving ALL fields except those in WRITE_BLACKLIST:
   ```python
   # Build clone (copy everything except blacklist)
   clone = {k: v for k, v in old_f.items() if k not in WRITE_BLACKLIST}
   ```
   This approach is already used but the explicit HCP_FIELDS copying might override some fields.

3. **Review Field Usage**
   - Verify if `Next Guest Date` is being calculated elsewhere or needs preservation
   - Check if `Service Job Images` needs to be preserved during cloning
   - Ensure `Block Type` is preserved for existing blocks when they're modified

## Summary
The CSV processing correctly handles most fields, but three fields may not be properly preserved during cloning operations:
- Block Type (important for blocks)
- Next Guest Date (used in service descriptions)
- Service Job Images (webhook attachments)

These should be added to the HCP_FIELDS list to ensure they're preserved when records are cloned.