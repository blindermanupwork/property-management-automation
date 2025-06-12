# Timestamp Standardization Guide

## Overview
This document outlines the standardized approach to handling timestamps across the property management automation system. Previously, different components used inconsistent timestamp formats, leading to confusion and potential data inconsistencies.

## The Problem

### Current Inconsistencies (As of June 2025)
1. **Webhook (Python)**: `2025-06-11T23:42:05.280562-07:00` (microseconds included)
2. **CSV Processor (Python)**: `2025-06-11 23:42:05-07:00` (space separator, seconds only)
3. **HCP Sync (JavaScript)**: `2025-06-11T23:42:05.280Z` (incorrect - shows UTC but time is MST)

### Issues Identified
- Different precision levels (microseconds vs seconds)
- Different separators ('T' vs space)
- Incorrect timezone representation in JavaScript (shows 'Z' for UTC but time is actually MST)
- No single source of truth for timestamp generation

## The Solution

### Standard Format
**ISO 8601 with seconds precision and proper timezone offset**
```
2025-06-11T23:42:05-07:00
```

### Key Characteristics
- ISO 8601 compliant
- 'T' separator between date and time
- Seconds precision (no microseconds)
- Proper timezone offset (-07:00 for Arizona/MST)
- No daylight saving time complications (Arizona doesn't observe DST)

## Implementation

### Python Utility Module
Location: `/src/automation/scripts/shared/timestamp_utils.py`

```python
from timestamp_utils import get_arizona_timestamp

# Get current timestamp
timestamp = get_arizona_timestamp()
# Returns: "2025-06-11T23:42:05-07:00"
```

### JavaScript Utility Module
Location: `/src/automation/scripts/shared/timestampUtils.js`

```javascript
const { getArizonaTimestamp } = require('./shared/timestampUtils');

// Get current timestamp
const timestamp = getArizonaTimestamp();
// Returns: "2025-06-11T23:42:05-07:00"
```

## Migration Plan

### Phase 1: Update Critical Components
1. **Webhook Processing** (`webhook.py`)
   - Change: Use `get_arizona_timestamp()` instead of `get_arizona_time().isoformat()`
   - Impact: Removes microseconds from timestamps

2. **CSV Processing** (`csvProcess.py`)
   - Change: Use `get_arizona_timestamp()` instead of `datetime.now(arizona_tz).isoformat(sep=' ', timespec='seconds')`
   - Impact: Changes separator from space to 'T'

3. **HCP Sync** (`hcp_sync.js`)
   - Change: Use `getArizonaTimestamp()` instead of manual UTC adjustment
   - Impact: Fixes incorrect timezone representation

### Phase 2: Update Secondary Components
- ICS Processing (`icsProcess.py`)
- Evolve Scraping (`evolveScrape.py`)
- Any other scripts that generate timestamps

### Phase 3: Data Cleanup (Optional)
- Write a one-time script to standardize existing timestamps in Airtable
- This is optional as Airtable can parse various timestamp formats

## Backward Compatibility

### Space Separator Support
For systems that require space separator, use:
- Python: `get_arizona_timestamp_space()`
- JavaScript: `getArizonaTimestampSpace()`

### Parsing Various Formats
The utility modules include parsing functions that can handle:
- Standard format: `2025-06-11T23:42:05-07:00`
- Space format: `2025-06-11 23:42:05-07:00`
- With microseconds: `2025-06-11T23:42:05.123456-07:00`
- UTC format: `2025-06-11T23:42:05Z`

## Testing

### Python Test
```bash
python3 src/automation/scripts/shared/timestamp_utils.py
```

### JavaScript Test
```bash
node src/automation/scripts/shared/timestampUtils.js
```

### Integration Test
```bash
python3 test_timestamp_formats.py
```

## Benefits

1. **Consistency**: All components use the same format
2. **Accuracy**: Correct timezone representation
3. **Compatibility**: ISO 8601 standard works everywhere
4. **Maintainability**: Single source of truth for timestamp logic
5. **Debugging**: Easier to compare timestamps across logs

## Rollout Checklist

- [ ] Deploy utility modules (`timestamp_utils.py` and `timestampUtils.js`)
- [ ] Update webhook processing to use new format
- [ ] Update CSV processing to use new format
- [ ] Update HCP sync to use new format
- [ ] Update ICS processing to use new format
- [ ] Test each component after update
- [ ] Monitor logs for any timestamp-related errors
- [ ] Update any documentation referencing timestamp formats

## Notes for Developers

1. **Always use the utility functions** - Don't create timestamps manually
2. **Arizona timezone only** - All business data uses MST (no DST)
3. **Logs can use different formats** - PST for logs is fine, but Airtable data must use Arizona time
4. **Test timezone handling** - Especially important for JavaScript code
5. **Document any exceptions** - If you must use a different format, document why

## Common Pitfalls to Avoid

1. **Don't manually subtract hours from UTC** - Use proper timezone-aware functions
2. **Don't use 'Z' suffix for non-UTC times** - It's misleading
3. **Don't include microseconds** - Airtable doesn't need that precision
4. **Don't forget timezone info** - Always include the offset

## Questions?

If you have questions about timestamp handling:
1. Check the utility module documentation
2. Run the test scripts to see examples
3. Look at the migration examples in this document
4. Ask the team if still unclear