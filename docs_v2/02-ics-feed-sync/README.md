# ICS Feed Sync

## Purpose
Synchronize calendar feeds from multiple property management platforms including Airbnb, VRBO, Booking.com, Hospitable, and other ICS-compatible sources. This feature processes calendar events to create and update reservation records in Airtable.

## Quick Start
1. ICS feeds configured in Airtable with URLs and status
2. Automation runs every 4 hours via cron
3. Concurrent processing of all active feeds
4. Events converted to reservations with UIDs
5. Duplicate detection and history preservation

## Key Components
- **Feed Management**: Active/Inactive/Remove status handling
- **Concurrent Processing**: Asyncio-based parallel fetching
- **Event Parsing**: icalendar library for ICS parsing
- **UID Generation**: Composite UIDs with property ID
- **Removal Detection**: Identifies deleted events
- **Status Tracking**: Feed health monitoring

## Directory Structure
```
02-ics-feed-sync/
├── README.md                    # This file
├── BusinessLogicAtoZ.md         # ICS sync rules
├── SYSTEM_LOGICAL_FLOW.md       # Processing flow diagrams
├── version-history.md           # Change tracking
├── flows/
│   ├── concurrent-flow.mmd     # Parallel processing
│   ├── event-parsing.mmd       # ICS event extraction
│   ├── uid-composite.mmd       # UID generation logic
│   └── removal-detection.mmd  # Orphan detection
└── examples/
    ├── sample-feed.ics         # Example ICS format
    ├── feed-config.json        # Feed configuration
    └── processing-log.txt      # Sample run output
```

## Processing Scripts
- **Main**: `/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py`
- **Legacy**: `/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess.py`
- **Logs**: `/home/opc/automation/src/automation/logs/ics_sync.log`

## Related Features
- [Duplicate Detection](../09-duplicate-detection/) - UID matching logic
- [Airtable Integration](../05-airtable-integration/) - Database operations
- [Automation Controller](../13-automation-controller/) - Scheduling
- [Environment Management](../14-environment-management/) - Feed separation

## Common Issues
1. **Feed Timeouts**: 30-second timeout per feed
2. **Invalid ICS**: Some providers have malformed feeds
3. **Orphaned Records**: Events removed from feed but active in Airtable
4. **Timezone Issues**: All dates converted to date-only format
5. **Rate Limiting**: Some providers limit request frequency

## Configuration
```python
# Key Settings
CONCURRENT_LIMIT = 10  # Max parallel feeds
FEED_TIMEOUT = 30      # Seconds per feed
DATE_RANGE_PAST = 6    # Months to look back
DATE_RANGE_FUTURE = 12 # Months to look ahead
```

## Feed Sources
- **Airbnb**: Individual listing calendars
- **VRBO**: Property calendar exports  
- **Booking.com**: iCal sync URLs
- **Hospitable**: Unified calendar feeds
- **Custom**: Any ICS-compliant source

## Maintenance Notes
- Monitor feed health weekly
- Clean orphaned records monthly
- Verify feed URLs quarterly
- Test removal detection regularly

## Version
Current: v1.0.0 (July 11, 2025)