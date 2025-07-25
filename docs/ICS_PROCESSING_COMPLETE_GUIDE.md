# ICS Processing System - Complete Technical Guide

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Key Components](#key-components)
4. [Data Flow](#data-flow)
5. [Duplicate Detection Strategy](#duplicate-detection-strategy)
6. [Configuration](#configuration)
7. [Execution Flow](#execution-flow)
8. [Error Handling](#error-handling)
9. [Monitoring & Logging](#monitoring--logging)
10. [Common Issues & Solutions](#common-issues--solutions)
11. [Testing](#testing)
12. [Maintenance](#maintenance)

## Overview

The ICS Processing System is a critical component of the property management automation suite that synchronizes calendar data from various property management systems (Airbnb, VRBO, Booking.com, Hospitable, Lodgify, etc.) with Airtable. It processes approximately 336 ICS feeds in production, handling thousands of reservations and blocks daily.

### Key Features
- **Multi-source Support**: Processes ICS feeds from 20+ different property management platforms
- **Hybrid Duplicate Detection**: Sophisticated system handling both static and dynamic UID systems
- **Batch Processing**: Optimized for performance with in-memory collection and batch updates
- **Environment Isolation**: Complete separation between development and production
- **Automated Scheduling**: Runs hourly in production via cron
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ICS Processing Pipeline                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Controller (controller.py)                              │
│     └─> Checks "ICS Calendar" automation status            │
│                                                             │
│  2. ICS Processor Selection                                 │
│     └─> icsProcess_enhanced.py (wrapper)                   │
│         └─> icsProcess_best.py (core processor)            │
│                                                             │
│  3. Feed Processing Loop                                    │
│     ├─> Download ICS feed                                   │
│     ├─> Parse VCALENDAR events                              │
│     ├─> Apply timezone conversions                          │
│     ├─> Hybrid duplicate detection                          │
│     └─> Batch operations (create/update/remove)            │
│                                                             │
│  4. Airtable Synchronization                                │
│     ├─> Batch creates (100 records)                         │
│     ├─> Batch updates (100 records)                         │
│     └─> Status management (New/Modified/Old/Removed)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Main Processor (`icsProcess_best.py`)
Location: `/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_best.py`

**Core Responsibilities:**
- Feed download and parsing
- Event transformation
- Duplicate detection
- Batch operations
- Status management

**Key Classes:**
```python
class InMemoryCollector:
    """Collects operations in memory for batch processing"""
    def __init__(self):
        self.to_create = []
        self.to_update = []
        self.to_remove = []
        self.existing_records = {}
        self.processed_uids = set()
        self.property_mapping = {}
        self.processed_property_dates = set()  # LODGIFY FIX
```

### 2. Enhanced Wrapper (`icsProcess_enhanced.py`)
Location: `/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_enhanced.py`

**Purpose:** Provides additional logging and wraps the core processor for the controller.

### 3. Configuration Module (`airtable_config.py`)
Handles environment-specific configuration:
- API keys
- Base IDs
- Table names
- Environment detection

### 4. Utility Modules
- `ultra_logger.py`: Enhanced logging with emoji support
- `airtable_utils.py`: Airtable API interactions
- `date_utils.py`: Timezone and date handling

## Data Flow

### 1. Feed Discovery
```python
# Fetch all ICS feeds from Properties table
properties = fetch_all_properties(airtable, properties_table)
feeds = [(prop['id'], url) for prop in properties 
         for url in get_ics_urls(prop.get('fields', {}))]
```

### 2. Event Processing
```python
# For each feed:
1. Download ICS content
2. Parse VCALENDAR
3. Extract events (VEVENT)
4. Transform to Airtable format:
   - UID + Property ID → Composite UID
   - Convert dates to ISO format
   - Map summary → Event Name
   - Determine Entry Type (Reservation/Block)
```

### 3. Hybrid Duplicate Detection
```python
# HYBRID APPROACH (v2.2.9):
1. Try UID matching first
2. If no match, try property+dates+type matching
3. Handle dynamic UID systems (Lodgify, Evolve)
```

## Duplicate Detection Strategy

### The Problem
Different property management systems handle UIDs differently:
- **Static UID Systems** (Airbnb, VRBO): Consistent UIDs across fetches
- **Dynamic UID Systems** (Lodgify, Evolve): New UIDs on every fetch

### The Solution: Hybrid Detection

```python
# Step 1: Try UID matching
all_records = existing_records.get((composite_uid, url), [])

# Step 2: If no UID match, try property+dates+type
if not all_records and property_id:
    # Find records with same property, check-in, check-out, and entry type
    for key, records in existing_records.items():
        for record in records:
            if (record['fields'].get('Property ID') == [property_id] and
                record['fields'].get('Check-in Date') == checkin_date and
                record['fields'].get('Check-out Date') == checkout_date and
                record['fields'].get('Entry Type') == entry_type):
                all_records.extend(records)
                break
```

### LODGIFY Protection
Prevents false removals when UIDs change:

```python
# Track all processed property+dates+type combinations
collector.processed_property_dates.add((property_id, checkin, checkout, entry_type))

# Before removal, check if combination was processed
if (property_id, checkin, checkout, entry_type) in collector.processed_property_dates:
    logging.info(f"🛡️ LODGIFY PROTECTION: Skipping removal")
    continue
```

## Configuration

### Environment Variables
```bash
# Required
ENVIRONMENT=production|development
AIRTABLE_API_KEY_PROD=your_prod_key
AIRTABLE_API_KEY_DEV=your_dev_key

# Base IDs
AIRTABLE_BASE_ID_PROD=appZzebEIqCU5R9ER
AIRTABLE_BASE_ID_DEV=app67yWFv0hKdl6jM
```

### ICS URL Configuration
Properties can have multiple ICS URLs:
- `ICS URL` - Primary calendar feed
- `ICS URL 2` through `ICS URL 10` - Additional feeds
- `Owner Calendar Link` - Owner availability

### Feed Metadata
Each feed URL can include metadata:
```
https://example.com/calendar.ics?source=airbnb&type=listing
```

## Execution Flow

### 1. Automation Controller
```python
# controller.py checks automation status
automation = get_automation_record("ICS Calendar")
if automation['Active']:
    run_ics_processor()
```

### 2. Main Processing Loop
```python
def main():
    # 1. Load configuration
    config = load_config()
    
    # 2. Fetch all properties
    properties = fetch_all_properties()
    
    # 3. Get existing reservations
    existing_records = get_all_reservation_records()
    
    # 4. Process each feed
    for property_id, feed_url in feeds:
        events = download_and_parse_feed(feed_url)
        process_events(events, property_id, collector)
    
    # 5. Detect removals
    detect_removed_records(collector, existing_records)
    
    # 6. Execute batch operations
    collector.execute_batch_operations()
```

### 3. Batch Operations
```python
# Creates - 100 records per batch
for batch in chunk(collector.to_create, 100):
    airtable.batch_create(batch)

# Updates - 100 records per batch  
for batch in chunk(collector.to_update, 100):
    airtable.batch_update(batch)
```

## Error Handling

### Feed-Level Error Handling
```python
try:
    content = download_feed(url)
except requests.exceptions.RequestException as e:
    logger.error(f"Failed to download {url}: {e}")
    stats[url] = {"error": str(e)}
    continue
```

### Parsing Error Handling
```python
try:
    cal = Calendar.from_ical(content)
except ValueError as e:
    logger.error(f"Failed to parse calendar: {e}")
    continue
```

### Batch Operation Error Handling
```python
def safe_batch_create(records):
    try:
        return airtable.batch_create(records)
    except Exception as e:
        logger.error(f"Batch create failed: {e}")
        # Fallback to individual creates
        for record in records:
            try:
                airtable.create(record)
            except Exception as e2:
                logger.error(f"Individual create failed: {e2}")
```

## Monitoring & Logging

### Log Files
- **Production**: `/home/opc/automation/src/automation/logs/ics_sync_prod.log`
- **Development**: `/home/opc/automation/src/automation/logs/ics_sync_dev.log`

### Log Format
```
2025-07-23 09:16:01 INFO: 🚀 Starting ICS sync process...
2025-07-23 09:16:02 INFO: 📊 Found 336 ICS feeds across 191 properties
2025-07-23 09:16:15 INFO: ✅ Feed 1/336: https://example.com/cal.ics - 5 events
2025-07-23 09:17:23 INFO: 📈 Summary: 336 feeds — new 4 — modified 1 — removed 0
```

### Key Metrics
- Total feeds processed
- Events per feed
- New/Modified/Removed counts
- Processing time per feed
- Error counts and types

## Common Issues & Solutions

### 1. Lodgify Add/Remove Cycle
**Problem**: Records repeatedly added and removed due to changing UIDs

**Solution**: Implemented LODGIFY PROTECTION checking property+dates+type

### 2. Timezone Issues
**Problem**: Events showing wrong times

**Solution**: 
```python
# Convert to property timezone
local_dt = utc_dt.astimezone(property_timezone)
# Store as date only for check-in/out
date_only = local_dt.date().isoformat()
```

### 3. Memory Issues with Large Feeds
**Problem**: Out of memory with huge calendars

**Solution**: Process in chunks, limit events to 6 months future

### 4. Duplicate Events in Feed
**Problem**: Some systems send duplicate events

**Solution**: Track processed UIDs within session

## Testing

### Test Framework
Location: `/home/opc/automation/src/automation/scripts/test_duplicate_detection_framework.py`

**Test Scenarios:**
1. New reservation creation
2. Same UID modifications
3. UID removed (future checkout)
4. Different UID same dates (Lodgify case)
5. Same UID different dates
6. Block vs Reservation separation

### Manual Testing
```bash
# Test single feed
python3 test_single_ics_feed.py

# Test with specific property
ENVIRONMENT=development python3 icsProcess_best.py --property "Property Name"

# Dry run mode
ENVIRONMENT=production python3 icsProcess_best.py --dry-run
```

## Maintenance

### Regular Tasks

#### 1. Monitor Log Files
```bash
# Check for errors
grep ERROR /home/opc/automation/src/automation/logs/ics_sync_prod.log

# Check processing stats
grep "Summary:" /home/opc/automation/src/automation/logs/ics_sync_prod.log
```

#### 2. Clean Old Logs
```bash
# Archive logs older than 30 days
find /home/opc/automation/src/automation/logs -name "ics_sync_*.log" -mtime +30 -exec gzip {} \;
```

#### 3. Verify Cron Schedule
```bash
# Production runs hourly
crontab -l | grep ics
# Should show: 0 * * * * /path/to/run_automation_prod.py
```

### Performance Optimization

#### 1. Feed Caching
Consider implementing feed caching for frequently unchanged feeds:
```python
# Cache feeds that rarely change
if feed_last_modified == cached_last_modified:
    return cached_events
```

#### 2. Parallel Processing
For future optimization:
```python
# Process feeds in parallel
with ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(process_feed, feeds)
```

### Troubleshooting Guide

#### Issue: "No events found in feed"
1. Check if feed URL is accessible
2. Verify feed contains VEVENT entries
3. Check date range filters

#### Issue: "Duplicate key error"
1. Check for race conditions
2. Verify composite UID generation
3. Check batch operation conflicts

#### Issue: "Memory usage high"
1. Check feed sizes
2. Verify batch sizes
3. Monitor collector object growth

## Code Structure

```
icsAirtableSync/
├── icsProcess_best.py          # Core processor (v2.2.9)
├── icsProcess_enhanced.py      # Wrapper for controller
├── icsProcess_original.py      # Legacy version (reference)
├── airtable_config.py          # Configuration management
├── airtable_utils.py           # Airtable API utilities
├── date_utils.py               # Date/timezone handling
├── ultra_logger.py             # Enhanced logging
└── test_single_ics_feed.py    # Testing utility
```

## Version History

- **v2.2.9** (July 2025): Hybrid duplicate detection with LODGIFY PROTECTION
- **v2.2.8** (July 2025): Enhanced logging and environment separation
- **v2.2.0** (June 2025): Batch processing optimization
- **v2.1.0** (June 2025): Multi-feed support
- **v2.0.0** (May 2025): Complete rewrite with InMemoryCollector

## Best Practices

1. **Always specify environment**: `ENVIRONMENT=production python3 script.py`
2. **Monitor logs regularly**: Set up alerts for ERROR level messages
3. **Test in development first**: Use dev environment for testing changes
4. **Backup before bulk operations**: Export Airtable data before major changes
5. **Document feed sources**: Keep Properties table metadata up to date

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **Feed URLs**: Validate and sanitize before processing
3. **Rate Limiting**: Respect source system limits
4. **Access Control**: Limit who can modify automation settings

## Future Enhancements

1. **Feed Validation**: Pre-validate feeds before processing
2. **Incremental Updates**: Only process changed events
3. **Multi-threading**: Parallel feed processing
4. **Smart Caching**: Cache unchanged feeds
5. **Real-time Processing**: Webhook-based updates

---

This documentation represents the complete ICS processing system as of v2.2.9. For questions or issues, refer to the troubleshooting guide or check the logs for detailed error messages.