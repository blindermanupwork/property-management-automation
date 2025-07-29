# CSV Processing - Version History

## Version 1.2.0 (July 29, 2025)

### Hourly Duplicate Prevention Fix (v2.2.12)
- **Fixed by**: Claude AI Assistant
- **Requested by**: Boris
- **Issue**: Hourly duplicate record creation when same-day turnover flag changes
- **Root Cause**: System comparing against "Old" records with outdated same-day values
- **Solution**: Modified airtable_map to use active records for comparison

### Technical Details
- Problem: When same-day turnover changes on checkout day, system creates duplicates hourly
- Fix: Lines 969-980 in csvProcess.py now prioritize active records over "Old" ones
- Preserves: Self-healing, duplicate detection, and historical tracking still work
- Impact: Prevents unnecessary database growth and cleanup work

### Code Changes
```python
# Now uses active records for comparison when available
active_records = [r for r in records if r["fields"].get("Status") != "Old"]
if active_records:
    latest = max(active_records, key=sort_key)
else:
    latest = max(records, key=sort_key)
```

## Version 1.1.0 (July 29, 2025)

### iTrip Next Guest Date Integration
- **Created by**: Claude AI Assistant
- **Requested by**: Boris
- **Changes**:
  - Added documentation for iTrip Next Guest Date field processing
  - Documented same-day turnover detection from iTrip dates
  - Added integration with update-service-lines-enhanced.py
  - Updated business logic to show field precedence

### Key Features Added
- iTrip Next Guest Date field extraction from CSV
- Automatic same-day turnover detection when checkout equals iTrip next guest date
- Service line generation using iTrip-provided dates
- Automatic update of Same-day Turnover checkbox in Airtable

### Implementation Details
- CSV field "Next Guest Date" mapped to Airtable "iTrip Next Guest Date"
- Python script calculates same-day status by comparing dates
- Fixes issue where records weren't showing "SAME DAY Turnover STR"
- Verified with 17 production records successfully updated

## Version 1.0.0 (July 11, 2025)

### Initial Documentation Creation
- **Created by**: Claude AI Assistant
- **Reviewed by**: Pending
- **Changes**:
  - Documented all CSV processing business logic
  - Created comprehensive A-Z rules
  - Added 8 Mermaid flow diagrams
  - Documented iTrip and Evolve specific handling
  - Captured UID generation algorithm
  - Detailed duplicate detection logic

### Key Business Rules Documented
- UID format: `{source}_{property}_{checkin}_{checkout}_{lastname}`
- Date range: 6 months past, 12 months future
- Duplicate handling: Clone-mark-create pattern
- File movement: Only after successful processing
- Property matching: Exact name match required

### Integration Points Documented
- CloudMailin webhook integration
- Airtable synchronization
- File system management
- Error handling and recovery

---

## Migration Notes

### From Gmail OAuth to CloudMailin (Historical)
- Replaced Gmail OAuth with webhook approach
- More reliable email processing
- No authentication refresh needed
- Faster processing times

---

**Next Review Date**: August 11, 2025