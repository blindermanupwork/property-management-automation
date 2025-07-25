# iTrip Next Guest Date Solution

## Current Situation
- iTrip provides "Next Booking" date directly in their CSV
- Our system calculates next guest date by searching Airtable records
- This can lead to discrepancies if iTrip knows about bookings we haven't imported yet

## Proposed Solution

### 1. Add "iTrip Next Guest Date" Field to Airtable
Add a new field to the Reservations table:
- Field Name: `iTrip Next Guest Date`
- Field Type: Date
- Purpose: Store the "Next Booking" date from iTrip CSV

### 2. Update CSV Processor
Modify `csvProcess.py` to capture and store the "Next Booking" field:

```python
# In parse_itrip_row function, add:
next_booking = None
next_booking_keys = ["Next Booking", "next booking", "Next booking"]
for key in next_booking_keys:
    if key in hdr_map and hdr_map[key] < len(row):
        next_booking_str = row[hdr_map[key]].strip()
        if next_booking_str:
            try:
                # Parse the date (format: "2025-07-16 16:00:00")
                next_booking = datetime.strptime(next_booking_str, "%Y-%m-%d %H:%M:%S")
                next_booking_iso = next_booking.strftime("%Y-%m-%d")
            except:
                pass
        break

# Add to reservation dict:
reservation = {
    # ... existing fields ...
    "itrip_next_guest_date": next_booking_iso if next_booking else None,
}

# In create/update sections, add:
if res.get("entry_source") == "itrip" and res.get("itrip_next_guest_date"):
    fields["iTrip Next Guest Date"] = res["itrip_next_guest_date"]
```

### 3. Update find-next-guest-date.js
Modify the Airtable automation to prefer iTrip's data when available:

```javascript
// After getting the trigger record
let iTripNextGuestDate = triggerRecord.getCellValue("iTrip Next Guest Date");
let entrySource = triggerRecord.getCellValue("Entry Source");

// If this is an iTrip reservation with next guest date, use it
if (entrySource && entrySource.name === "iTrip" && iTripNextGuestDate) {
    // Use iTrip's provided date
    nextGuestDate = iTripNextGuestDate;
    
    // Still calculate same-day turnover
    const checkOutDateObj = new Date(checkOutDate);
    const nextCheckInDateObj = new Date(iTripNextGuestDate);
    
    checkOutDateObj.setHours(0, 0, 0, 0);
    nextCheckInDateObj.setHours(0, 0, 0, 0);
    
    isSameDayTurnover = checkOutDateObj.getTime() === nextCheckInDateObj.getTime();
    
    console.log("Using iTrip provided next guest date:", iTripNextGuestDate);
} else {
    // Continue with existing logic to calculate from Airtable data
    // ... existing calculation code ...
}
```

### 4. Update Service Line Description Logic
No changes needed - the update-service-lines script will automatically use the improved "Next Guest Date" field.

## Benefits
1. **More Accurate**: Uses iTrip's authoritative data about upcoming bookings
2. **Handles Unknown Bookings**: iTrip may know about future bookings not yet in our system
3. **Backwards Compatible**: Falls back to calculation for non-iTrip sources
4. **Consistent**: Same-day turnover logic remains consistent

## Implementation Steps
1. Add "iTrip Next Guest Date" field to Airtable Reservations table
2. Update csvProcess.py to capture and store this field
3. Update find-next-guest-date.js automation script
4. Test with sample iTrip CSV data
5. Deploy to production

## Testing
1. Process an iTrip CSV with "Next Booking" data
2. Verify "iTrip Next Guest Date" field is populated
3. Run find-next-guest-date automation
4. Verify it uses iTrip date instead of calculating
5. Check service line descriptions are correct