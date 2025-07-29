# Owner Arrival Logic Documentation

## Overview
This document explains the owner arrival detection and handling logic implemented in v2.2.13. The system automatically detects when property owners are arriving and adjusts service scheduling accordingly.

## Key Changes in v2.2.13

### Problem Solved
Previously, when an owner (Block entry) was checking in the same day as a guest checkout, the system would:
1. Mark it as a "same-day turnover"
2. This would cause sync issues when ICS/CSV sources didn't have same-day marked
3. Result in "modified" records being created unnecessarily

### Solution Implemented
Owner arrivals are now handled specially:
- **NOT** marked as same-day turnovers (even when checking in same day)
- Still properly detected and labeled as "OWNER ARRIVING"
- Service time should be set to 10:00 AM (vs default 10:15 AM) via Airtable formula

## Technical Implementation

### 1. Owner Arrival Detection (`find-next-guest-date.js`)
```javascript
// Check if dates are the same
const datesAreSame = checkOutDateObj.getTime() === nextCheckInDateObj.getTime();

// Only mark as same-day turnover if it's NOT an owner arrival
// Owner arrivals should not be marked as same-day to avoid creating modified records
isSameDayTurnover = datesAreSame && !isBlock;

// Owner arriving = Block checking in within 1 day
if (isBlock && daysBetween <= 1) {
    isNextEntryBlock = true;
    // Sets "Owner Arriving" checkbox in Airtable
}
```

### 2. Service Line Description (`update-service-line-description.js`)
When owner is arriving, the service line includes "OWNER ARRIVING":
```javascript
if (isOwnerArriving) {
    baseSvcName = `OWNER ARRIVING ${serviceType} STR ${month} ${day}`;
}
```

Service line hierarchy:
1. Custom Instructions (if any)
2. OWNER ARRIVING (if applicable)
3. LONG TERM GUEST DEPARTING (if 14+ day stay)
4. Base service name

## Business Logic

### When is Owner Arriving Detected?
- Next entry after checkout is a **Block** (not Reservation)
- Block checks in within **0-1 days** of checkout
- Both same-day and next-day owner arrivals are detected

### What Changes for Owner Arrivals?
1. **Same-day Turnover**: Always FALSE (even if same day)
2. **Owner Arriving Checkbox**: Set to TRUE
3. **Service Line**: Includes "OWNER ARRIVING"
4. **Final Service Time**: Should be set to 10:00 AM (via Airtable formula)

### Examples

#### Example 1: Owner Same Day
- Guest checks out: July 29
- Owner (Block) checks in: July 29
- Result:
  - Same-day Turnover: FALSE
  - Owner Arriving: TRUE
  - Service Line: "OWNER ARRIVING Turnover STR July 29"

#### Example 2: Owner Next Day
- Guest checks out: July 29
- Owner (Block) checks in: July 30
- Result:
  - Same-day Turnover: FALSE
  - Owner Arriving: TRUE
  - Service Line: "OWNER ARRIVING Turnover STR July 30"

#### Example 3: Regular Guest Same Day
- Guest checks out: July 29
- Next guest checks in: July 29
- Result:
  - Same-day Turnover: TRUE
  - Owner Arriving: FALSE
  - Service Line: "SAME DAY Turnover STR"

## Airtable Configuration Required

### Final Service Time Formula
The "Final Service Time" field should be updated to check for owner arrivals separately from same-day turnovers. Here's the formula structure you'll need:

```
IF(
  {Custom Service Time},
  {Custom Service Time},
  IF(
    {Owner Arriving},
    DATETIME_PARSE(
      DATETIME_FORMAT({Check-out Date}, 'YYYY-MM-DD') & ' 10:00',
      'YYYY-MM-DD HH:mm'
    ),
    IF(
      {Same-day Turnover},
      DATETIME_PARSE(
        DATETIME_FORMAT({Check-out Date}, 'YYYY-MM-DD') & ' 10:15',
        'YYYY-MM-DD HH:mm'
      ),
      DATETIME_PARSE(
        DATETIME_FORMAT({Check-out Date}, 'YYYY-MM-DD') & ' 10:15',
        'YYYY-MM-DD HH:mm'
      )
    )
  )
)
```

This formula:
1. First checks for Custom Service Time (user override)
2. If owner arriving: sets 10:00 AM
3. Otherwise: sets 10:15 AM for all other turnovers (including same-day)

### Fields Used
- **Owner Arriving**: Checkbox - Set by automation
- **Next Entry Is Block**: Text field - Legacy field, still checked for compatibility
- **Same-day Turnover**: Checkbox - NOT set for owner arrivals
- **Final Service Time**: Formula field - Should check Owner Arriving

## Testing

A test script is available at:
```bash
node src/automation/scripts/test-owner-arrival-logic.js
```

This verifies:
- Owner arrivals are NOT marked as same-day
- Regular same-day turnovers still work
- Both same-day and next-day owner arrivals are detected

## Benefits
1. **Prevents Sync Issues**: No more false "modified" records due to same-day mismatch
2. **Accurate Scheduling**: Owners get 10:00 AM service time
3. **Clear Communication**: "OWNER ARRIVING" in service descriptions
4. **Backward Compatible**: Still checks legacy "Next Entry Is Block" field