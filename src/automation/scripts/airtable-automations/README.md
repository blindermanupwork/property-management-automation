# Airtable Automation Scripts

This directory contains Airtable automation scripts that run directly within Airtable's scripting environment.

## Scripts

### 1. find-next-guest-date.js
**Purpose**: Finds the next guest reservation for a property and determines if it's a same-day turnover.

**Updates**:
- `Next Guest Date` - The check-in date of the next reservation at the same property
- `Same-day Turnover` - Checkbox indicating if the next guest checks in on the same day as current guest checks out

**Key Logic**:
- Queries all reservations for the same property
- Filters for future reservations (check-in date >= checkout date)
- Uses >= comparison to properly detect same-day turnovers
- Sorts by check-in date to find the chronologically next guest

### 2. update-service-line-description.js
**Purpose**: Builds the complete service line description following the 3-step construction process.

**Updates**:
- `Service Line Description` - The complete service name including all modifiers

**Dependencies**: 
- Should run AFTER `find-next-guest-date.js` to use pre-calculated next guest date
- Falls back to finding next guest if needed

**Construction Logic (3-step process)**:
1. **Base Service Name**:
   - Same-day: `[Service Type] STR SAME DAY`
   - With next guest: `[Service Type] STR Next Guest [Month] [Day]`
   - No next guest: `[Service Type] STR Next Guest Unknown`

2. **Long-term Guest Detection**:
   - Checks if stay duration >= 14 days
   - Adds "LONG TERM GUEST DEPARTING" prefix when applicable

3. **Final Assembly with Custom Instructions**:
   - Custom + Long-term: `[Custom] - LONG TERM GUEST DEPARTING [Base Name]`
   - Custom only: `[Custom] - [Base Name]`
   - Long-term only: `LONG TERM GUEST DEPARTING [Base Name]`
   - Neither: `[Base Name]`

## Example Outputs

- `"POOL NEEDS CLEANING - LONG TERM GUEST DEPARTING Turnover STR SAME DAY"`
- `"LONG TERM GUEST DEPARTING Turnover STR SAME DAY"`
- `"CHECK GARAGE DOOR - Turnover STR Next Guest June 13"`
- `"Turnover STR Next Guest Unknown"`

## Implementation Notes

- Both scripts use the same long-term guest logic as the HCP sync scripts
- Custom instructions are limited to 200 characters (truncated with "..." if longer)
- Scripts handle all edge cases: missing dates, no next guest, etc.
- Same-day detection uses date comparison without time components

## Airtable Automation Setup

1. Create an automation triggered on record update
2. Add "Run script" action
3. Configure input variables:
   - `recordId` - Record ID from trigger
4. Copy the appropriate script content
5. Test with sample records before enabling