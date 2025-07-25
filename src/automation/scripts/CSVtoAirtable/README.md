# CSV to Airtable Processors

## ACTIVE FILES (DO NOT DELETE)

### Primary Processor:
- **csvProcess_enhanced.py** - The main processor being used in production
  - Implements property-based grouping to prevent race conditions
  - Imports and extends csvProcess_best.py

### Core Implementation:
- **csvProcess_best.py** - Core CSV processing logic
  - Used by csvProcess_enhanced.py as base implementation
  - Contains all the business logic for CSV to Airtable sync
  - Fixed July 18: Misleading log messages about removals

### Configuration:
- **config.py** - Shared configuration for CSV processing
- **CLAUDE.md** - Detailed documentation for AI assistance

### Utilities:
- **csv_file_locking.py** - File locking utilities (if used)

## ARCHIVED FILES

The following files have been moved to `/home/opc/automation/archive/CSVtoAirtable/`:
- csvProcess.py - Original implementation (deprecated)
- csv_uid_fix.py - One-time fix script (no longer needed)
- csvProcess_memory.py - Experimental version (not used)
- csvProcess_memory_v2.py - Experimental version (not used)

## Processing Order

The automation runner (`run_automation.py`) tries processors in this order:
1. csvProcess_enhanced.py ✅ (USED)
2. csvProcess_memory.py (archived)
3. csvProcess_best.py (fallback if enhanced missing)
4. csvProcess.py (archived)

## Key Features

### Date Protection (Fixed July 18)
- Only removes reservations with checkout dates in the future
- Preserves all historical data (past checkouts)
- Log messages now correctly show when removals are skipped

### Property-Based Grouping
- Processes all CSV entries for a property together
- Prevents race conditions between parallel processors
- Maintains data consistency