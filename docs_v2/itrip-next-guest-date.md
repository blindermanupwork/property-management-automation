# iTrip Next Guest Date Feature

## Overview

The iTrip Next Guest Date feature captures and utilizes the "Next Booking" field provided in iTrip CSV exports. This authoritative data from iTrip eliminates the need to calculate next guest arrival dates from other reservations in Airtable, improving accuracy and reliability of service line descriptions.

## Implementation Details

### CSV Processing Enhancement

The CSV processor (`src/automation/scripts/CSVtoAirtable/csvProcess.py`) now captures the "Next Booking" column from iTrip CSV files:

```python
# Get iTrip Next Booking date if available
itrip_next_booking = None
next_booking_keys = ["Next Booking", "next booking", "Next booking"]
for key in next_booking_keys:
    if key in row:
        next_booking_str = row[key].strip()
        if next_booking_str:
            try:
                # Parse the date (format: "2025-07-16 16:00:00")
                next_booking_date = parse(next_booking_str).date()
                itrip_next_booking = next_booking_date.isoformat()
            except Exception as e:
                logging.warning(f"Failed to parse Next Booking date '{next_booking_str}': {e}")
        break
```

The captured date is stored in the Airtable "iTrip Next Guest Date" field for iTrip-sourced reservations:

```python
# Add iTrip Next Guest Date if from iTrip and has next booking
if res["entry_source"] == "iTrip" and res.get("itrip_next_booking"):
    new_fields["iTrip Next Guest Date"] = res["itrip_next_booking"]
    logging.info(f"📅 iTrip Next Guest Date set to: {res['itrip_next_booking']} for {uid}")
```

### Airtable Automation Update

The `find-next-guest-date.js` automation script prioritizes iTrip's provided data when available:

```javascript
// Check if this is an iTrip reservation with next guest date
let iTripNextGuestDate = triggerRecord.getCellValue("iTrip Next Guest Date");
let entrySource = triggerRecord.getCellValue("Entry Source");

// If this is an iTrip reservation with next guest date, use it directly
if (entrySource && entrySource.name === "iTrip" && iTripNextGuestDate) {
    // Use iTrip's provided date
    let nextGuestDate = iTripNextGuestDate;
    
    // Still calculate same-day turnover
    const checkOutDateObj = new Date(checkOutDate);
    const nextCheckInDateObj = new Date(iTripNextGuestDate);
    
    checkOutDateObj.setHours(0, 0, 0, 0);
    nextCheckInDateObj.setHours(0, 0, 0, 0);
    
    let isSameDayTurnover = checkOutDateObj.getTime() === nextCheckInDateObj.getTime();
    
    console.log("Using iTrip provided next guest date:", iTripNextGuestDate);
    console.log("Same-day turnover:", isSameDayTurnover);
    
    // Update the record with iTrip data
    await table.updateRecordAsync(recordId, {
        "Next Guest Date": nextGuestDate,
        "Same-day Turnover": isSameDayTurnover,
        "Next Entry Is Block": false,  // iTrip next booking is always a guest
        "Owner Arriving": false
    });
    
    return;  // Exit early since we used iTrip data
}
```

## Data Flow

1. **CSV Import**: iTrip CSV files contain a "Next Booking" column with datetime values (e.g., "2025-07-16 16:00:00")
2. **Processing**: The CSV processor extracts and parses this date, converting it to ISO format (e.g., "2025-07-16")
3. **Storage**: The date is stored in the "iTrip Next Guest Date" field in Airtable
4. **Automation**: The find-next-guest-date.js script checks for this field and uses it when available
5. **Service Lines**: HousecallPro job service lines reflect the accurate next guest arrival date

## Benefits

- **Accuracy**: Uses iTrip's authoritative data instead of calculated guesses
- **Reliability**: Eliminates errors from missing or incorrect reservation data
- **Simplicity**: Reduces complex date calculation logic
- **Performance**: Faster execution by avoiding multiple record lookups

## Field Configuration

### Airtable Field
- **Field Name**: `iTrip Next Guest Date`
- **Field Type**: Date
- **Scope**: Only populated for iTrip-sourced reservations
- **Format**: ISO date format (YYYY-MM-DD)

### CSV Column
- **Column Names**: "Next Booking", "next booking", or "Next booking" (case variations supported)
- **Format**: DateTime string "YYYY-MM-DD HH:MM:SS"
- **Timezone**: Assumed to be in property's local timezone

## Error Handling

The implementation includes robust error handling:

1. **Missing Column**: If the "Next Booking" column is absent, the field remains empty
2. **Invalid Dates**: Parsing failures are logged as warnings but don't stop processing
3. **Empty Values**: Blank next booking values are skipped gracefully
4. **Field Errors**: If the Airtable field doesn't exist, a clear error message is provided

## Testing

Test the feature by creating a CSV with Next Booking data:

```csv
Checkin,Checkout,"Date Booked","Tenant Name","Property Name","Next Booking","Reservation ID"
"2025-07-23 16:00:00","2025-07-28 10:00:00","2025-07-01 10:00:00","Test Guest","321632","2025-07-28 16:00:00","TEST001"
```

After processing, verify:
1. The reservation record has "iTrip Next Guest Date" populated
2. The find-next-guest-date automation uses this date
3. Service line descriptions show the correct next guest arrival

## Fallback Behavior

When iTrip Next Guest Date is not available, the system falls back to the original calculation logic:
- Searches for the next reservation at the same property
- Considers both regular reservations and owner blocks
- Calculates same-day turnover status
- Updates owner arrival flags as needed

## Version History

- **v2.2.9** (July 2025): Initial implementation of iTrip Next Guest Date feature