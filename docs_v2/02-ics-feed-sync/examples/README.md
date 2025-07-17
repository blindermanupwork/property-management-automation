# ICS Feed Sync - Examples

**Feature:** 02-ics-feed-sync  
**Purpose:** Real-world examples of calendar feed synchronization from multiple property management systems  
**Last Updated:** July 14, 2025

---

## 📋 Table of Contents

1. [Sample ICS Feed Files](#sample-ics-feed-files)
2. [Feed Processing Examples](#feed-processing-examples)
3. [Airtable Sync Operations](#airtable-sync-operations)
4. [Multi-Source Integration](#multi-source-integration)
5. [Error Scenarios](#error-scenarios)
6. [Performance Metrics](#performance-metrics)

---

## 📅 Sample ICS Feed Files

### Example 1: Airbnb Calendar Feed
```icalendar
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Airbnb Inc//Hosting Calendar 0.8.8//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Airbnb calendar for Sunset Villa (12345678)
X-WR-CALDESC:Airbnb calendar for Sunset Villa (12345678)
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250615
DTEND;VALUE=DATE:20250620
UID:abc123-airbnb-reservation@airbnb.com
SUMMARY:Reserved - John Smith
DESCRIPTION:PHONE: +1 555-123-4567\nEMAIL: john.smith@email.com\nPROPERTY: Sunset Villa\nCONFIRMATION: ABC123456
LOCATION:Sunset Villa
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250625
DTEND;VALUE=DATE:20250630
UID:def456-airbnb-reservation@airbnb.com
SUMMARY:Blocked by owner
DESCRIPTION:Owner maintenance period
LOCATION:Sunset Villa
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
```

### Example 2: VRBO/Hospitable Feed
```icalendar
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//VRBO//Calendar//EN
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250710
DTEND;VALUE=DATE:20250717
UID:vrbo-booking-789012
SUMMARY:Sarah Johnson (VRBO)
DESCRIPTION:Check-in: 07/10/2025\nCheck-out: 07/17/2025\nGuests: 4\nProperty: Mountain Retreat\nConfirmation: VRB789012
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR
```

### Example 3: Booking.com Feed with Special Characters
```icalendar
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Booking.com//Calendar//EN
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250801
DTEND;VALUE=DATE:20250808
UID:booking.com-456789
SUMMARY:José García - €1,200
DESCRIPTION:Teléfono: +34 555 987 654\nHuéspedes: 3 adultos\nPROPIEDAD: L'Étoile Café & Suites
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
```

---

## 🔄 Feed Processing Examples

### Feed Configuration in Airtable
```javascript
// ICS Links Table Record
{
  "fields": {
    "Property Name": "Sunset Villa",
    "Property ID": "PROP_001",
    "Property Link Record": ["rec123ABC"],  // Link to Properties table
    "Link": "https://www.airbnb.com/calendar/ical/12345678.ics?s=secret123",
    "Active": true,
    "Last Sync": "2025-07-14T10:30:00.000Z",
    "Sync Status": "✅ Success - 15 events processed"
  }
}
```

### Processing Logic
```python
# ICS Processing for single feed
feed_url = "https://www.airbnb.com/calendar/ical/12345678.ics?s=secret123"
property_id = "PROP_001"
property_name = "Sunset Villa"

# Download and parse
response = requests.get(feed_url, timeout=30)
calendar = Calendar.from_ical(response.content)

# Process events
events_processed = 0
for component in calendar.walk():
    if component.name == "VEVENT":
        # Extract event data
        start_date = component.get('DTSTART').dt
        end_date = component.get('DTEND').dt
        summary = str(component.get('SUMMARY', ''))
        description = str(component.get('DESCRIPTION', ''))
        uid = str(component.get('UID', ''))
        
        # Generate composite UID
        composite_uid = f"{uid}|{property_id}|{start_date.strftime('%m/%d/%Y')}"
        
        # Determine reservation type
        if 'blocked' in summary.lower() or 'owner' in summary.lower():
            entry_source = "Block"
        else:
            entry_source = extract_source_from_description(description)
```

### Composite UID Generation
```python
def generate_composite_uid(ical_uid, property_id, start_date):
    """
    Generate composite UID for ICS events
    Format: {ical_uid}|{property_id}|{checkin_date}
    """
    # Sanitize ICS UID (remove @ symbols and clean)
    clean_uid = ical_uid.replace('@', '_').replace('.ics', '')
    
    # Format date consistently
    date_str = start_date.strftime('%m/%d/%Y')
    
    # Create composite
    composite = f"{clean_uid}|{property_id}|{date_str}"
    
    return composite

# Examples:
# "abc123-airbnb-reservation_airbnb.com|PROP_001|06/15/2025"
# "vrbo-booking-789012|PROP_002|07/10/2025"
# "booking.com-456789|PROP_003|08/01/2025"
```

---

## 🗄️ Airtable Sync Operations

### New ICS Event → Airtable Record
```javascript
// Parsing guest information from ICS
const guestInfo = parseICSDescription(description);
/*
Example parsed data:
{
  name: "John Smith",
  phone: "+1 555-123-4567",
  email: "john.smith@email.com",
  confirmation: "ABC123456",
  guests: 4
}
*/

// Create Airtable record
{
  "fields": {
    "UID": "abc123-airbnb-reservation_airbnb.com|PROP_001|06/15/2025",
    "Property ID": "PROP_001",
    "Property Name": "Sunset Villa",
    "Check In Date": "2025-06-15",
    "Check Out Date": "2025-06-20",
    "Guest First Name": "John",
    "Guest Last Name": "Smith",
    "Guest Email": "john.smith@email.com",
    "Guest Phone": "+1 555-123-4567",
    "Entry Source": "Airbnb",
    "Confirmation Code": "ABC123456",
    "Adults": 4,
    "Status": "Active",
    "Service Type": "Turnover",
    "Date Imported": "2025-07-14T10:30:00.000Z",
    "Outcome": "New",
    "ICS UID": "abc123-airbnb-reservation@airbnb.com"
  }
}
```

### Block Event Processing
```javascript
// Owner block detected
{
  "fields": {
    "UID": "def456-airbnb-reservation_airbnb.com|PROP_001|06/25/2025",
    "Property ID": "PROP_001",
    "Property Name": "Sunset Villa",
    "Check In Date": "2025-06-25",
    "Check Out Date": "2025-06-30",
    "Guest First Name": "BLOCK",
    "Guest Last Name": "BLOCK",
    "Entry Source": "Block",
    "Status": "Active",
    "Service Type": "Block",
    "Notes": "Owner maintenance period",
    "Date Imported": "2025-07-14T10:30:00.000Z",
    "Outcome": "New"
  }
}
```

### Event Removal Detection
```python
# Previous sync had these UIDs
previous_uids = {
    "abc123-airbnb-reservation_airbnb.com|PROP_001|06/15/2025",
    "def456-airbnb-reservation_airbnb.com|PROP_001|06/25/2025",
    "ghi789-airbnb-reservation_airbnb.com|PROP_001|07/01/2025"  # This one removed
}

# Current sync found these UIDs
current_uids = {
    "abc123-airbnb-reservation_airbnb.com|PROP_001|06/15/2025",
    "def456-airbnb-reservation_airbnb.com|PROP_001|06/25/2025"
}

# Detect removal
removed_uids = previous_uids - current_uids
# Result: {"ghi789-airbnb-reservation_airbnb.com|PROP_001|07/01/2025"}

# Update removed record
for uid in removed_uids:
    record = find_record_by_uid(uid)
    if record and record['fields']['Status'] == 'Active':
        update_fields = {
            'Status': 'Removed',
            'History': f"{datetime.now()}: Removed from ICS feed\n{existing_history}"
        }
        table.update(record['id'], update_fields)
```

---

## 🔄 Multi-Source Integration

### Handling Multiple Feeds for Same Property
```python
# Property PROP_001 has feeds from Airbnb, VRBO, and direct booking
feeds = [
    {
        "url": "https://airbnb.com/calendar/ical/12345.ics",
        "source": "Airbnb",
        "property_id": "PROP_001"
    },
    {
        "url": "https://vrbo.com/calendar/98765.ics", 
        "source": "VRBO",
        "property_id": "PROP_001"
    },
    {
        "url": "https://direct-booking.com/prop1.ics",
        "source": "Direct",
        "property_id": "PROP_001"
    }
]

# Conflict detection
all_events = []
for feed in feeds:
    events = process_feed(feed)
    all_events.extend(events)

# Check for overlapping dates
def detect_conflicts(events):
    conflicts = []
    for i, event1 in enumerate(events):
        for event2 in events[i+1:]:
            if event1['property_id'] == event2['property_id']:
                if dates_overlap(event1, event2):
                    conflicts.append({
                        'property': event1['property_id'],
                        'event1': event1['uid'],
                        'event2': event2['uid'],
                        'overlap': calculate_overlap(event1, event2)
                    })
    return conflicts
```

### Source Priority Resolution
```python
# Priority order when conflicts detected
SOURCE_PRIORITY = {
    'Airbnb': 1,
    'VRBO': 2,
    'Booking.com': 3,
    'Direct': 4,
    'Block': 0  # Blocks always take priority
}

def resolve_conflict(event1, event2):
    priority1 = SOURCE_PRIORITY.get(event1['source'], 99)
    priority2 = SOURCE_PRIORITY.get(event2['source'], 99)
    
    if priority1 < priority2:
        # event1 wins, mark event2 as duplicate
        return event1, event2
    else:
        # event2 wins, mark event1 as duplicate
        return event2, event1
```

---

## ❌ Error Scenarios

### Scenario 1: Feed Timeout
```python
try:
    response = requests.get(feed_url, timeout=30)
except requests.Timeout:
    logging.error(f"Timeout fetching feed: {feed_url}")
    # Update ICS Links table
    update_feed_status(feed_id, "❌ Timeout - Failed to fetch")
    # Continue with next feed
```

### Scenario 2: Invalid ICS Format
```python
try:
    calendar = Calendar.from_ical(response.content)
except ValueError as e:
    logging.error(f"Invalid ICS format from {feed_url}: {e}")
    # Try to salvage what we can
    events = parse_raw_ics(response.text)
    if events:
        logging.warning(f"Recovered {len(events)} events using fallback parser")
```

### Scenario 3: Missing Required Data
```icalendar
BEGIN:VEVENT
DTSTART;VALUE=DATE:20250815
DTEND;VALUE=DATE:20250820
UID:incomplete-event
SUMMARY:Missing guest info
END:VEVENT
```

**Handling:**
```python
# Extract what we can, use defaults for missing
guest_name = extract_guest_name(summary) or "ICS Guest"
guest_first = guest_name.split()[0] if ' ' in guest_name else guest_name
guest_last = guest_name.split()[-1] if ' ' in guest_name else "Guest"
```

### Scenario 4: Encoding Issues
```python
# Handle various encodings
def safe_decode(text):
    if isinstance(text, bytes):
        # Try encodings in order
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                return text.decode(encoding)
            except UnicodeDecodeError:
                continue
        # Last resort - ignore errors
        return text.decode('utf-8', errors='ignore')
    return str(text)
```

---

## 📊 Performance Metrics

### Feed Processing Statistics (Production - 246 feeds)
```python
# Real production metrics from July 2025
PROCESSING_STATS = {
    "total_feeds": 246,
    "successful": 241,
    "failed": 5,
    "total_events": 3847,
    "new_reservations": 287,
    "modified_reservations": 156,
    "removed_reservations": 42,
    "blocks_processed": 523,
    "processing_time": "4m 32s",
    "average_per_feed": "1.1s"
}

# Feed source breakdown
SOURCE_BREAKDOWN = {
    "Airbnb": 98,
    "VRBO": 67,
    "Booking.com": 45,
    "Hospitable": 23,
    "Direct": 13
}

# Error breakdown
ERROR_TYPES = {
    "Timeout": 2,
    "Invalid ICS": 1,
    "404 Not Found": 1,
    "SSL Error": 1
}
```

### Optimization Techniques
```python
# Parallel processing with thread pool
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_feeds_parallel(feed_list, max_workers=10):
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all feeds
        future_to_feed = {
            executor.submit(process_single_feed, feed): feed 
            for feed in feed_list
        }
        
        # Process results as they complete
        for future in as_completed(future_to_feed):
            feed = future_to_feed[future]
            try:
                result = future.result(timeout=60)
                results.append(result)
            except Exception as e:
                logging.error(f"Feed {feed['url']} failed: {e}")
                results.append({
                    'feed': feed,
                    'status': 'failed',
                    'error': str(e)
                })
    
    return results
```

---

## 🔗 Related Documentation
- [ICS Feed Sync Business Logic](../BusinessLogicAtoZ.md)
- [ICS Processing Flows](../flows/)
- [CSV Processing Examples](../../01-csv-processing/examples/)