# ICS Feed Sync Documentation

## Overview
The ICS (iCalendar) feed sync system processes calendar feeds from various property management platforms (Airbnb, VRBO, Booking.com, etc.) and synchronizes reservations and blocks with Airtable.

## Key Features

### 1. Multi-Source Support
- Processes feeds from: Airbnb, VRBO, Booking.com, Hospitable, HostTools, Lodgify, OwnerRez, YourPorter
- Automatic source detection from feed URL and content
- Handles both reservations and various block types

### 2. Intelligent Duplicate Detection
- Composite UID system: `{original_uid}_{property_id}`
- Prevents duplicates when platforms provide different UIDs for same reservation
- Cross-feed duplicate detection within same property

### 3. Historical Preservation
- Never deletes records - marks old versions with "Old" status
- Creates new "Modified" records when changes detected
- Complete audit trail of all changes

### 4. Safe Removal System (v2.2.12) 🆕

#### Problem Solved
Previously, if a reservation temporarily disappeared from an ICS feed (due to API issues, network problems, or timing), it would be immediately marked as "Removed" even if still active. This caused operational disruptions.

#### Solution: Multi-Sync Confirmation
The safe removal system requires reservations to be missing from **3 consecutive syncs** before marking as removed.

#### How It Works
1. **First miss**: Sets `Missing Count = 1`, records `Missing Since` timestamp
2. **Second miss**: Increments `Missing Count = 2` 
3. **Third miss**: Only now marks as "Removed" (after 12+ hour grace period)
4. **If found again**: Resets `Missing Count = 0`, updates `Last Seen`

#### Protection Rules
Records are NEVER removed if they have:
- **Active HCP job** (Status: Scheduled or In Progress)
- **Recent check-in** (within last 7 days)
- **Imminent checkout** (today or tomorrow)

#### Tracking Fields
- `Missing Count`: Number of consecutive syncs where missing (0-3)
- `Missing Since`: When first detected missing
- `Last Seen`: Last time found in ICS feed

#### Activation Status
- **Current**: Safe removal logic implemented but NOT ACTIVE
- **Fields**: Already added to both dev and prod Airtable bases
- **Activation**: Requires enabling `removal_safety.py` module or using test version

### 5. Date Filtering
Matches CSV processing logic:
- **Lookback**: Events from 2 months ago (configurable)
- **Future limit**: Events up to 3 months ahead
- **Focus**: Filters by check-in date only

### 6. Flag Calculation
- **Overlapping dates**: Detects reservation conflicts
- **Same-day turnover**: Identifies back-to-back reservations (checkout = next checkin)
- Flags apply to reservations only, not blocks

### 7. Service Type Preservation
- Preserves custom service types (e.g., "Deep Clean")
- Only overwrites with defaults ("Turnover", "Needs Review") if currently empty

## Processing Flow

1. **Feed Collection**
   - Fetches active feeds from "ICS Feeds" table
   - Concurrent HTTP requests with 15-second timeout
   - Handles failures gracefully

2. **Event Parsing**
   - Extracts: UID, dates, summary, description
   - Detects: entry type, service type, block type, source
   - Applies date filters

3. **Flag Calculation**
   - Groups by property
   - Calculates overlaps and same-day turnovers
   - Only between reservations (not blocks)

4. **Synchronization**
   - Checks for existing records by composite UID
   - Detects changes in dates, types, flags
   - Creates new or marks old as needed

5. **Removal Processing**
   - With safe removal: Tracks missing count, requires 3 syncs
   - Without safe removal: Immediate removal (current behavior)
   - Skips past checkouts and detected duplicates

6. **Post-Processing**
   - Links reservations to properties
   - Updates ICS Cron table with run stats
   - Generates detailed reports

## Configuration

### Environment Variables
```bash
# Date filtering
FETCH_RESERVATIONS_MONTHS_BEFORE=2  # Include events from 2 months ago
# Future limit: Hardcoded to 3 months (matches CSV)

# Removal safety (when activated)
MISSING_SYNC_THRESHOLD=3      # Syncs required before removal
GRACE_PERIOD_HOURS=12         # Additional safety buffer
```

### Required Airtable Structure

#### ICS Feeds Table
- `ICS URL`: Feed URL
- `Feed Status`: Active/Remove
- `Property Name`: Link to Properties table

#### Reservations Table  
- `Reservation UID`: Composite UID
- `ICS URL`: Source feed
- `Property ID`: Link to property
- `Status`: New/Modified/Old/Removed
- `Missing Count`: Removal tracking (0-3)
- `Missing Since`: First missing timestamp
- `Last Seen`: Last found timestamp

## Monitoring

### Log Locations
- Development: `logs/ics_sync_dev.log`
- Production: `logs/ics_sync_prod.log`

### Key Log Patterns
```bash
# Watch removal safety
tail -f logs/ics_sync_*.log | grep -E "REMOVAL SAFETY|Missing Count|found again"

# Track specific reservation
grep "UID_PATTERN" logs/ics_sync_*.log

# Monitor duplicates
grep "duplicate" logs/ics_sync_*.log -i
```

### Metrics
- Total events processed
- New/Modified/Unchanged/Removed counts
- Duplicate detections
- Feed success/failure rates

## Troubleshooting

### Common Issues

1. **Reservation marked as removed incorrectly**
   - Check if safe removal is active
   - Verify feed is returning reservation
   - Check `Missing Count` field

2. **Duplicates created**
   - Verify Property ID linkage
   - Check for UID changes
   - Review duplicate detection logs

3. **Missing property links**
   - Check ICS Feeds table mappings
   - Verify Property Name field
   - Run property ID update

### Manual Interventions

```python
# Reset removal tracking
record.update({
    "Missing Count": 0,
    "Missing Since": None,
    "Status": "Modified"
})

# Force property linking
update_property_id(reservations_table, ics_feeds_table)
```

## Best Practices

1. **Feed Management**
   - Keep ICS Feeds table updated
   - Remove inactive feeds promptly
   - Verify property mappings

2. **Monitoring**
   - Check removal counts regularly
   - Monitor for stuck "tracked" records
   - Review exception logs

3. **Testing**
   - Test in development first
   - Use dry-run mode
   - Verify with small feed subset

## Future Enhancements

1. **Configurable thresholds** per feed/property
2. **Webhook notifications** for removals
3. **Auto-recovery** for known feed issues
4. **Performance metrics** dashboard