# CSV Processing - Examples

**Feature:** 01-csv-processing  
**Purpose:** Real-world examples of CSV processing from CloudMailin emails to Airtable records  
**Last Updated:** July 14, 2025

---

## 📋 Table of Contents

1. [Sample CSV Files](#sample-csv-files)
2. [Email Processing Examples](#email-processing-examples)
3. [Airtable Record Creation](#airtable-record-creation)
4. [Error Scenarios](#error-scenarios)
5. [Test Data Sets](#test-data-sets)
6. [Edge Cases](#edge-cases)

---

## 🗂️ Sample CSV Files

### Example 1: Standard iTrip Reservation CSV
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email,Guest Phone,Adults,Children,Pets,Total Paid,Entry Source,Booking Date
"ABC123456","PROP_001","Sunset Villa - 3BR Ocean View","06/15/2025","06/20/2025","5","John","Smith","john.smith@email.com","555-123-4567","4","2","0","2500.00","Airbnb","06/01/2025"
"DEF789012","PROP_002","Mountain Retreat Studio","06/18/2025","06/22/2025","4","Sarah","Johnson","sarah.j@email.com","555-987-6543","2","0","1","800.00","Direct","06/05/2025"
```

### Example 2: CSV with Special Characters
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email,Guest Phone,Adults,Children,Pets,Total Paid,Entry Source,Booking Date
"GHI345678","PROP_003","L'Étoile Café & Suites","07/04/2025","07/10/2025","6","José","García","jose.garcia@email.com","555-456-7890","2","1","0","1800.00","VRBO","06/20/2025"
"JKL901234","PROP_004","The Smith's Haven","07/01/2025","07/15/2025","14","Marie-Claire","O'Brien","mc.obrien@email.com","555-234-5678","2","0","0","4200.00","Booking.com","06/15/2025"
```

### Example 3: Edge Case - Same Day Turnover
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email,Guest Phone,Adults,Children,Pets,Total Paid,Entry Source,Booking Date
"MNO567890","PROP_001","Sunset Villa - 3BR Ocean View","06/20/2025","06/25/2025","5","Alice","Williams","alice.w@email.com","555-345-6789","3","1","0","2750.00","Airbnb","06/08/2025"
```

---

## 📧 Email Processing Examples

### CloudMailin Webhook Payload
```json
{
  "headers": {
    "Received": "by mail.cloudmailin.net...",
    "From": "reservations@itrip.net",
    "To": "reservations@yourdomain.com",
    "Subject": "Daily Reservations Report - 06/10/2025",
    "Date": "Mon, 10 Jun 2025 02:15:00 -0700"
  },
  "envelope": {
    "to": "reservations@yourdomain.com",
    "from": "reservations@itrip.net"
  },
  "plain": "Please find attached the daily reservations report.",
  "attachments": [
    {
      "filename": "reservations_20250610.csv",
      "type": "text/csv",
      "disposition": "attachment",
      "content": "Q29uZmlybWF0aW9uIENvZGUsUHJvcGVydHkgSUQsUHJvcGVydHkgTmFtZSxDaGVjayBJbixDaGVjayBPdXQsTmlnaHRzLEd1ZXN0IEZpcnN0LEd1ZXN0IExhc3QsR3Vlc3QgRW1haWwsR3Vlc3QgUGhvbmUsQWR1bHRzLENoaWxkcmVuLFBldHMsVG90YWwgUGFpZCxFbnRyeSBTb3VyY2UsQm9va2luZyBEYXRlCiJBQkMxMjM0NTYiLCJQUk9QXzAwMSIsIlN1bnNldCBWaWxsYSAtIDNCUiBPY2VhbiBWaWV3IiwiMDYvMTUvMjAyNSIsIjA2LzIwLzIwMjUiLCI1IiwiSm9obiIsIlNtaXRoIiwiam9obi5zbWl0aEBlbWFpbC5jb20iLCI1NTUtMTIzLTQ1NjciLCI0IiwiMiIsIjAiLCIyNTAwLjAwIiwiQWlyYm5iIiwiMDYvMDEvMjAyNSI="
    }
  ]
}
```

### Processing Response
```python
# CSV saved to: /home/opc/automation/CSV_process_production/20250610_021500_reservations_20250610.csv
# Processing results:
{
    "status": "success",
    "file_saved": "/home/opc/automation/CSV_process_production/20250610_021500_reservations_20250610.csv",
    "records_found": 15,
    "processing_queued": true,
    "timestamp": "2025-06-10T02:15:00-07:00"
}
```

---

## 🗄️ Airtable Record Creation

### New Reservation Record
```javascript
// UID Generation Example
const uid = `ABC123456|PROP_001|06/15/2025`;  // Composite UID

// Airtable Record Created
{
  "fields": {
    "UID": "ABC123456|PROP_001|06/15/2025",
    "Confirmation Code": "ABC123456",
    "Property ID": "PROP_001",
    "Property Name": "Sunset Villa - 3BR Ocean View",
    "Check In Date": "2025-06-15",
    "Check Out Date": "2025-06-20",
    "Nights": 5,
    "Guest First Name": "John",
    "Guest Last Name": "Smith",
    "Guest Email": "john.smith@email.com",
    "Guest Phone": "555-123-4567",
    "Adults": 4,
    "Children": 2,
    "Pets": 0,
    "Total Paid": 2500.00,
    "Entry Source": "Airbnb",
    "Booking Date": "2025-06-01",
    "Status": "Active",
    "Service Type": "Turnover",
    "Date Imported": "2025-06-10T02:15:30.000Z",
    "Outcome": "New"
  }
}
```

### Modified Reservation Example
```javascript
// Existing record found with UID: "ABC123456|PROP_001|06/15/2025"
// Changes detected:
{
  "Total Paid": {
    "old": 2300.00,
    "new": 2500.00
  },
  "Adults": {
    "old": 3,
    "new": 4
  }
}

// Update applied with history preservation
{
  "fields": {
    "Total Paid": 2500.00,
    "Adults": 4,
    "History": "2025-06-10: Total Paid changed from 2300.00 to 2500.00\n2025-06-10: Adults changed from 3 to 4\n[Previous history...]",
    "Date Imported": "2025-06-10T02:15:30.000Z",
    "Outcome": "Modified"
  }
}
```

---

## ❌ Error Scenarios

### Scenario 1: Missing Required Fields
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email
"XYZ999999","","Beach House","06/25/2025","06/30/2025","5","Test","User","test@email.com"
```

**Error Handling:**
```python
logging.error("Row missing Property ID - skipping: {'Confirmation Code': 'XYZ999999', 'Property Name': 'Beach House'}")
# Record not created in Airtable
```

### Scenario 2: Invalid Date Format
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last
"BAD123456","PROP_005","Test Property","June 25, 2025","June 30, 2025","5","Bad","Date"
```

**Error Handling:**
```python
# Date parsing attempts multiple formats
parsed_date = try_parse_date("June 25, 2025")  # Converts to "06/25/2025"
```

### Scenario 3: Duplicate Active Reservations
```python
# Two active records found with overlapping dates for same property
# Resolution: Mark older record as "Duplicate" status
{
  "existing_uid": "OLD123456|PROP_001|06/15/2025",
  "new_uid": "NEW789012|PROP_001|06/15/2025",
  "action": "mark_old_as_duplicate",
  "reason": "Newer confirmation code for same property and dates"
}
```

---

## 🧪 Test Data Sets

### Long-Term Guest Test
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email,Guest Phone,Adults,Children,Pets,Total Paid,Entry Source,Booking Date
"LONG123456","PROP_006","Extended Stay Suite","07/01/2025","07/20/2025","19","Long","Term","longterm@email.com","555-111-2222","2","0","0","5700.00","Direct","06/01/2025"
```

**Expected Result:**
- Service Type: "Checkout Only"
- Special Flags: "LONG TERM GUEST DEPARTING"

### Same-Day Turnover Test
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email,Guest Phone,Adults,Children,Pets,Total Paid,Entry Source,Booking Date
"SAME123456","PROP_001","Sunset Villa - 3BR Ocean View","06/20/2025","06/25/2025","5","Same","Day","sameday@email.com","555-333-4444","2","0","0","2000.00","VRBO","06/10/2025"
```

**Expected Result:**
- Links to previous checkout on 06/20/2025
- Service Type: "Same Day Turnover"

---

## 🔧 Edge Cases

### Edge Case 1: UTF-8 Special Characters
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out,Nights,Guest First,Guest Last,Guest Email,Guest Phone,Adults,Children,Pets,Total Paid,Entry Source,Booking Date
"UTF123456","PROP_007","Château de la Côte d'Azur","07/14/2025","07/21/2025","7","François","Müller","francois@émâil.com","555-888-9999","2","0","0","3500.00","Airbnb","06/30/2025"
```

### Edge Case 2: Very Large CSV (1000+ rows)
- File size: 250KB+
- Processing time: ~45 seconds
- Memory usage peaks at 150MB
- Batch processing in chunks of 100

### Edge Case 3: Malformed CSV
```csv
Confirmation Code,Property ID,Property Name,Check In,Check Out
"BROKEN123","PROP_008","Missing quotes,06/25/2025,06/30/2025
"BROKEN456","PROP_009","Extra"Quote"Here","06/26/2025","06/28/2025"
```

**Recovery Strategy:**
- Secondary CSV parser with relaxed rules
- Manual quote escaping
- Row-by-row validation

---

## 📊 Performance Benchmarks

| Scenario | Rows | Processing Time | Memory Usage |
|----------|------|----------------|--------------|
| Small CSV | 10 | 2.3s | 25MB |
| Medium CSV | 100 | 8.5s | 45MB |
| Large CSV | 1000 | 45s | 150MB |
| Edge Cases | 50 | 12s | 35MB |

---

## 🔗 Related Documentation
- [CSV Processing Business Logic](../BusinessLogicAtoZ.md)
- [CSV Processing Flows](../flows/)
- [ICS Feed Sync Examples](../../02-ics-feed-sync/examples/)