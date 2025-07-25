# iTrip Next Guest Date Feature - Documentation Update

## Update for CSV_PROCESSING_COMPLETE_GUIDE.md

### In the "CSV Sources & Formats" section, update the iTrip Format as follows:

```markdown
### 1. iTrip Format
**File Pattern**: `*Checkouts-Report*.csv` or timestamped files
**Key Fields:**
- `Checkin` - Arrival date/time (YYYY-MM-DD HH:MM:SS format)
- `Checkout` - Departure date/time (YYYY-MM-DD HH:MM:SS format)
- `Tenant Name` - Guest full name
- `Tenant Phone` - Guest phone number
- `Property Name` - Property name/identifier
- `Property Address` - Full property address
- `Property Owner` - Property owner name
- `Reservation ID` - Booking reference/confirmation code
- `Next Booking` - Next guest arrival date/time (YYYY-MM-DD HH:MM:SS) **[v2.2.9]**
- `Next Tenant Name` - Next guest name **[v2.2.9]**
- `Next Tenant Phone` - Next guest phone **[v2.2.9]**
- `Same Day?` - Same-day turnover indicator
- `Contractor Info` - Special instructions/work orders

**UID Generation**: Based on Reservation ID

#### iTrip Next Guest Date Feature (v2.2.9)
The system now captures and utilizes the "Next Booking" field from iTrip CSV exports:

- **Field Capture**: Automatically extracts "Next Booking" column during CSV processing
- **Format Parsing**: Converts datetime format "YYYY-MM-DD HH:MM:SS" to ISO date "YYYY-MM-DD"
- **Storage**: Saved in Airtable "iTrip Next Guest Date" field for iTrip-sourced reservations
- **Automation Integration**: The `find-next-guest-date.js` automation prioritizes this data
- **Fallback Logic**: When not available, falls back to calculating from other reservations
- **Benefits**: 
  - Eliminates guesswork about next guest arrivals
  - Reduces complex date calculation logic
  - Provides authoritative data directly from iTrip
  - Improves service line description accuracy
```

### Add to the "Data Transformation" section:

```markdown
### iTrip Next Guest Date Processing

When processing iTrip CSV files, the system performs special handling for the Next Booking field:

```python
# Extract Next Booking date if available
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
                logging.info(f"📅 Parsed Next Booking: {itrip_next_booking}")
            except Exception as e:
                logging.warning(f"Failed to parse Next Booking date: {e}")
        break

# Store in Airtable for iTrip reservations
if entry_source == "iTrip" and itrip_next_booking:
    airtable_fields["iTrip Next Guest Date"] = itrip_next_booking
```
```

### Add to the "Airtable Field Mapping" section:

```markdown
### iTrip-Specific Fields

| CSV Field | Airtable Field | Type | Notes |
|-----------|----------------|------|-------|
| Next Booking | iTrip Next Guest Date | Date | v2.2.9 - Authoritative next guest arrival |
| Contractor Info | iTrip Report Info | Long Text | Work orders and special instructions |
| Same Day? | Same-day Turnover | Checkbox | Direct mapping from CSV |
```

### Add to the "Common Issues & Solutions" section:

```markdown
### iTrip Next Guest Date Issues

**Problem**: "Unknown field name: 'iTrip Next Guest Date'" error
**Solution**: The field must be added to Airtable first. Add a Date field named exactly "iTrip Next Guest Date" to the Reservations table.

**Problem**: Next Booking dates not being captured
**Solution**: Check that the CSV column is named exactly "Next Booking" (case-sensitive). The system supports variations but exact match is preferred.

**Problem**: Invalid date format in Next Booking field
**Solution**: The system expects "YYYY-MM-DD HH:MM:SS" format. Invalid dates are logged as warnings but don't stop processing.
```