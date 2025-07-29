# Safe Removal Testing Plan

## Current Status
- **Production**: Fields added (`Missing Count`, `Missing Since`, `Last Seen`) 
- **Development**: Fields added (same fields)
- **Code**: Modified `icsProcess.py` with embedded safety logic NOT ACTIVE yet
- **Test file**: `icsProcess_dev_test.py` created with embedded logic

## How to Activate & Test

### Option 1: Test in Dev Environment (RECOMMENDED)
```bash
# 1. Backup current processor
cd /home/opc/automation/src/automation/scripts/icsAirtableSync
cp icsProcess.py icsProcess_backup_$(date +%Y%m%d_%H%M%S).py

# 2. Activate the test version
cp icsProcess_dev_test.py icsProcess.py

# 3. Run dev automation with dry-run
cd /home/opc/automation
python3 src/run_automation_dev.py --dry-run

# 4. Check logs for safety messages
tail -f src/automation/logs/ics_sync_dev.log | grep -E "REMOVAL SAFETY|Missing Count|found again|exempted"

# 5. If satisfied, run without dry-run
python3 src/run_automation_dev.py

# 6. Restore original when done testing
cd src/automation/scripts/icsAirtableSync
cp icsProcess_backup_*.py icsProcess.py
```

### Option 2: Create Module Version (Cleaner)
```bash
# 1. Move removal_safety.py to proper location
cd /home/opc/automation
mv src/automation/scripts/icsAirtableSync/removal_safety.py src/automation/scripts/icsAirtableSync/

# 2. The current icsProcess.py will automatically use it
# (It already has the import logic)

# 3. Test in dev
python3 src/run_automation_dev.py --dry-run
```

### Option 3: Manual Testing Without Running Full Automation
```bash
# Test specific ICS feed
cd /home/opc/automation
python3 -c "
import sys
sys.path.append('.')
from src.automation.scripts.icsAirtableSync.icsProcess_dev_test import *
# Test removal logic on specific feed
"
```

## What Will Happen

### First Run
- Records missing from feeds will get `Missing Count = 1`
- Records found will get `Last Seen` updated
- NO removals will happen (need 3 consecutive missing)

### Second Run (if still missing)
- `Missing Count = 2`
- Still NO removals

### Third Run (if still missing)
- `Missing Count = 3`
- Records will be marked as "Removed"
- Unless they have:
  - Active HCP job (Scheduled/In Progress)
  - Recent check-in (within 7 days)
  - Imminent checkout (today/tomorrow)

### If Record Reappears
- `Missing Count` reset to 0
- `Last Seen` updated
- Status remains active

## Monitoring Commands
```bash
# Watch removal tracking in dev
watch -n 60 'psql -h localhost -U airtable -d airtable_dev -c "
SELECT id, reservation_uid, missing_count, missing_since::date, last_seen::date 
FROM reservations 
WHERE missing_count > 0 
ORDER BY missing_count DESC;"'

# Check logs
tail -f src/automation/logs/ics_sync_dev.log | grep -E "Missing Count|REMOVAL|exempted|found again"

# Check specific reservation
grep "45425\|1418fb94e984" src/automation/logs/ics_sync_dev.log
```

## Rollback Plan
If issues arise:
```bash
# 1. Restore original processor
cd /home/opc/automation/src/automation/scripts/icsAirtableSync
cp icsProcess_backup_*.py icsProcess.py

# 2. Clear tracking fields (optional)
# Use Airtable MCP to bulk update Missing Count = 0, Missing Since = null

# 3. The fields in Airtable are harmless if unused
```

## Key Safety Features
1. **3 sync threshold**: Prevents temporary glitches from removing records
2. **12-hour grace period**: Additional buffer time
3. **Active job protection**: Never removes records with HCP jobs
4. **Recent activity protection**: Protects recent/imminent reservations
5. **Reset on reappear**: Automatically recovers when record found again