# Duplicate Cleanup Script Guide

This script finds and removes duplicate reservations in Airtable by keeping the most recent record for each property/date combination.

## Environment Selection

**CRITICAL**: This script uses the default Config which runs in DEVELOPMENT mode. To run in production, you must use the environment-specific runners:

```bash
# For PRODUCTION data:
cd /home/opc/automation
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py

# For DEVELOPMENT data:
cd /home/opc/automation
ENVIRONMENT=development python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py
```

## Basic Usage

### 1. Analyze Mode (Dry Run - Default)
Shows what would be removed without making changes:
```bash
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py
```

### 2. Execute Mode
Actually marks duplicates as "Old" status:
```bash
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --execute
```

## Options

### Filter by Property
Target a specific property by name or Airtable ID:
```bash
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --property "1812 E Belmont"
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --property recXXXXXXXXXXXXXX
```

### Filter by Entry Type
Process only specific entry types:
```bash
# Only reservations
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --entry-type reservation

# Only blocks
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --entry-type block

# Both (default)
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --entry-type both
```

## How It Works

1. **Groups records** by Property ID, Check-in Date, Check-out Date, and Entry Type
2. **Sorts duplicates** by Last Updated timestamp (newest first), then by ID
3. **Keeps the newest** record from each group
4. **Marks others** as "Old" status (they remain in Airtable but are excluded from active operations)

## Export Files

CSV files are exported to: `src/automation/scripts/duplicate-cleanup/exports/`

Filename format: `{Env} {Action} {Date} {Property/ALL}.csv`
- Examples: 
  - `Prod Analyze 7-18-25 141pm ALL.csv`
  - `Dev Executed 7-18-25 141pm 1812 E Belmont Ave.csv`

## CSV Columns

1. **Action**: KEEP or DROP (both 4 characters for alignment)
2. **Property Name**: Human-readable property name
3. **Airtable ID**: The record's ID field value
4. **Check-in**: Check-in date
5. **Check-out**: Check-out date
6. **Entry Type**: Reservation or Block
7. **UID**: Reservation UID (shows "NO_UID" if field is missing)
8. **Source**: Entry source (e.g., Airbnb, VRBO)
9. **Status**: Current status (New, Modified, etc.)
10. **Last Updated**: Timestamp used for sorting
11. **Has HCP Job**: Yes/No if linked to HousecallPro

## Important Notes

- Records with HCP jobs are prioritized when possible
- The script will prompt for confirmation before executing changes
- All removed records are marked as "Old" (not deleted)
- Logs are saved in `logs/` directory

## Common Use Cases

### Daily Cleanup (All Properties)
```bash
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py
# Review the CSV, then if satisfied:
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --execute
```

### Fix Specific Property Issues
```bash
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --property "2065 W 1st Pl" 
# Review, then execute if needed
```

### Clean Only Reservation Duplicates
```bash
ENVIRONMENT=production python3 src/automation/scripts/duplicate-cleanup/cleanup-duplicates.py --entry-type reservation --execute
```