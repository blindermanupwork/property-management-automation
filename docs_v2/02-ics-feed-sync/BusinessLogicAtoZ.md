# ICS Feed Sync - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of ICS (iCalendar) feed synchronization for property management systems, including webhook processing, calendar parsing, Airtable synchronization, and removal detection logic.

## Core Business Purpose

The ICS feed sync system automatically imports and maintains property availability calendars from various booking platforms (Airbnb, VRBO, Booking.com, Hospitable) to ensure accurate reservation tracking and prevent double-bookings.

## Business Workflows

### 1. Feed Configuration Management

#### **ICS Feeds Table in Airtable**
**Table**: ICS Feeds
**Key Fields**:
- **Feed URL**: The .ics calendar URL from booking platform
- **Property**: Linked record to Properties table
- **Status**: Active/Inactive (only Active feeds processed)
- **Source Platform**: Airbnb, VRBO, Booking.com, Hospitable
- **Last Sync**: Timestamp of last successful sync
- **Error Count**: Track consecutive failures

**Business Logic**:
1. **Feed Addition**:
   - User adds ICS feed URL from booking platform
   - Links to specific property record
   - Sets Status = "Active"
   - Source detected from URL patterns

2. **Feed Health Monitoring**:
   ```python
   def check_feed_health(feed):
       if feed['error_count'] >= 5:
           feed['status'] = 'Inactive'
           send_alert(f"Feed disabled: {feed['url']}")
   ```

### 2. Automated Synchronization Process

#### **Cron Job Execution**
**Trigger**: Every 4 hours (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
**Environment Stagger**: Production at :00, Development at :10

**Business Logic**:
1. **Feed Collection**:
   ```python
   def get_feeds_to_process():
       # Query Airtable for active feeds
       formula = "{Status} = 'Active'"
       feeds = airtable.get_all('ICS Feeds', formula=formula)
       return feeds
   ```

2. **Concurrent Processing**:
   - Process up to 10 feeds simultaneously
   - 30-second timeout per feed
   - Continue on individual failures

3. **Feed Download**:
   ```python
   async def download_feed(feed_url):
       async with aiohttp.ClientSession() as session:
           async with session.get(feed_url, timeout=30) as response:
               return await response.text()
   ```

### 3. Calendar Event Processing

#### **Event Parsing Logic**
**Business Rules**:
1. **Valid Event Requirements**:
   - Must have DTSTART (check-in date)
   - Must have DTEND (check-out date)  
   - Must have UID (unique identifier)
   - SUMMARY field determines reservation vs block

2. **Entry Type Determination**:
   ```python
   def determine_entry_type(event):
       if 'SUMMARY' not in event or event['SUMMARY'] == '':
           return 'Block'  # Owner/maintenance block
       else:
           return 'Reservation'  # Guest booking
   ```

3. **Date Range Filtering**:
   - Process events from 6 months past to 12 months future
   - Skip events outside this window
   - Convert all dates to YYYY-MM-DD format

### 4. Composite UID Generation

#### **UID Algorithm**
**Format**: `UID_{PropertyID}_{icsUID}`

**Implementation**:
```python
def generate_composite_uid(property_id, ics_uid):
    # Normalize property ID
    prop_id = str(property_id).lower()
    
    # Take last 6 chars of ICS UID for uniqueness
    uid_suffix = ics_uid[-6:].lower()
    
    # Build composite UID
    composite_uid = f"UID_{prop_id}_{uid_suffix}"
    return composite_uid
```

**Purpose**: Prevents UID collisions when same booking appears in multiple property feeds

### 5. Synchronization Logic

#### **Three-Phase Sync Process**

**Phase 1: Mark Candidates for Removal**
```python
def mark_removal_candidates(property_id, source):
    # Find all active records for this property/source
    formula = f"AND({{Property ID}}='{property_id}', {{Source}}='{source}', {{Status}}='Active')"
    records = airtable.get_all('Reservations', formula=formula)
    
    # Mark all as potential removals
    for record in records:
        record['_removal_candidate'] = True
```

**Phase 2: Process Current Feed Events**
```python
def process_feed_events(events, property_id):
    for event in events:
        composite_uid = generate_composite_uid(property_id, event['UID'])
        
        # Search for existing record
        existing = find_by_composite_uid(composite_uid)
        
        if existing:
            # Update and unmark for removal
            update_reservation(existing, event)
            existing['_removal_candidate'] = False
        else:
            # Create new reservation
            create_reservation(event, property_id)
```

**Phase 3: Remove Orphaned Records**
```python
def remove_orphaned_records(property_id):
    # Find records still marked for removal
    removal_candidates = [r for r in records if r.get('_removal_candidate')]
    
    for record in removal_candidates:
        # Soft delete - set status to "Removed"
        airtable.update(record['id'], {'Status': 'Removed'})
        log.info(f"Removed orphaned record: {record['UID']}")
```

### 6. Guest Information Extraction

#### **Platform-Specific Parsing**

**Airbnb ICS**:
```python
def parse_airbnb_summary(summary):
    # Format: "Guest Name (HMXXXXXXX)"
    match = re.match(r'^(.+?)\s*\(HM\w+\)$', summary)
    if match:
        return match.group(1).strip()
    return "ICS Guest"
```

**VRBO ICS**:
```python
def parse_vrbo_summary(summary):
    # Format varies: "Reservation - Guest Name" or just "Guest Name"
    if ' - ' in summary:
        return summary.split(' - ', 1)[1].strip()
    return summary.strip() or "ICS Guest"
```

**Booking.com ICS**:
```python
def parse_booking_summary(summary):
    # Often includes booking reference
    # Format: "Guest Name - Booking #12345678"
    if ' - Booking' in summary:
        return summary.split(' - Booking')[0].strip()
    return summary.strip() or "ICS Guest"
```

### 7. Airtable Record Management

#### **Record Creation Process**
**Field Mapping**:
```python
airtable_fields = {
    'UID': composite_uid,
    'Property': [property_record_id],  # Linked record
    'Guest Name': extracted_guest_name,
    'Check-in Date': checkin_date,
    'Check-out Date': checkout_date,
    'Entry Type': entry_type,  # "Reservation" or "Block"
    'Status': 'New',
    'Source': source_platform,  # "Airbnb ICS", "VRBO ICS", etc.
    'ICS UID': original_ics_uid,
    'Feed URL': feed_url,
    'Created Date': datetime.now().isoformat(),
    'Last Updated': datetime.now().isoformat()
}
```

#### **Update Logic**
**Business Rules**:
1. **Significant Changes**:
   - Date changes
   - Guest name changes
   - Entry type changes

2. **Update Process**:
   ```python
   def update_reservation(existing, new_data):
       changes = {}
       
       # Check for date changes
       if existing['Check-in Date'] != new_data['checkin']:
           changes['Check-in Date'] = new_data['checkin']
           
       if existing['Check-out Date'] != new_data['checkout']:
           changes['Check-out Date'] = new_data['checkout']
           
       # Check for guest changes
       new_guest = extract_guest_name(new_data['summary'])
       if existing['Guest Name'] != new_guest:
           changes['Guest Name'] = new_guest
           
       if changes:
           changes['Last Updated'] = datetime.now().isoformat()
           airtable.update(existing['id'], changes)
   ```

### 8. Error Handling and Recovery

#### **Feed-Level Error Handling**
**Business Logic**:
1. **Network Errors**:
   ```python
   try:
       content = await download_feed(feed_url)
   except (TimeoutError, NetworkError) as e:
       log.error(f"Feed download failed: {feed_url} - {e}")
       increment_error_count(feed)
       continue  # Skip to next feed
   ```

2. **Parse Errors**:
   ```python
   try:
       calendar = icalendar.Calendar.from_ical(content)
   except ValueError as e:
       log.error(f"Invalid ICS format: {feed_url} - {e}")
       increment_error_count(feed)
       continue
   ```

3. **Event-Level Errors**:
   - Skip individual malformed events
   - Log warnings but continue processing
   - Report summary statistics

### 9. Platform-Specific Handling

#### **Airbnb ICS**
- **Blocks**: No SUMMARY field
- **Reservations**: "Guest Name (HMXXXXXXX)" format
- **UIDs**: Stable across updates
- **Timezone**: UTC dates

#### **VRBO ICS**
- **Blocks**: SUMMARY = "Blocked" or empty
- **Reservations**: Variable formats
- **UIDs**: May change on updates
- **Special**: May include owner blocks

#### **Booking.com ICS**
- **Blocks**: Rare, usually maintenance
- **Reservations**: Include booking reference
- **UIDs**: Stable booking IDs
- **Language**: Multi-language support needed

#### **Hospitable ICS**
- **Blocks**: Clearly marked
- **Reservations**: Consistent format
- **UIDs**: Property management system IDs
- **Source**: Aggregates multiple platforms

### 10. Performance Optimization

#### **Concurrent Processing**
```python
async def process_all_feeds(feeds):
    # Create semaphore to limit concurrent feeds
    sem = asyncio.Semaphore(10)
    
    async def process_with_limit(feed):
        async with sem:
            await process_single_feed(feed)
    
    # Process all feeds concurrently
    tasks = [process_with_limit(feed) for feed in feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

#### **Memory Management**
- Stream processing for large calendars
- Release parsed events after processing
- Batch Airtable operations

## Environment Configuration

### Development Environment
- **Processing Directory**: `/src/automation/scripts/icsAirtableSync/`
- **Log File**: `ics_sync_development.log`
- **Airtable Base**: `app67yWFv0hKdl6jM`
- **Test Feeds**: Limited set for testing

### Production Environment
- **Processing Directory**: `/src/automation/scripts/icsAirtableSync/`
- **Log File**: `ics_sync_production.log`
- **Airtable Base**: `appZzebEIqCU5R9ER`
- **Live Feeds**: 246+ active feeds

## Critical Business Rules

### Data Integrity Rules
1. **Never Delete Source Data**: Only mark as "Removed"
2. **Preserve UIDs**: Maintain composite UID consistency
3. **Handle Duplicates**: Property ID prevents cross-property issues
4. **Audit Trail**: Log all operations with timestamps

### Processing Rules
1. **Active Feeds Only**: Skip inactive/error feeds
2. **Date Range Limits**: 6 months past, 12 months future
3. **Timeout Enforcement**: 30 seconds per feed
4. **Error Isolation**: One feed failure doesn't affect others

### Synchronization Rules
1. **Full Sync**: Process entire feed each time
2. **Soft Deletes**: Mark removed events, don't delete
3. **Update Detection**: Only update on actual changes
4. **Platform Agnostic**: Handle format variations

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Scope**: Complete ICS feed sync business logic
**Primary Code**: `/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py`