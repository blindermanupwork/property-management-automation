# Deletables.md - Files Safe to Delete/Archive

## Overview
This document lists files and directories that can be safely deleted or archived without affecting the system functionality. All items listed have been verified as unused, duplicated, or superseded by newer implementations.

## Safe to Delete - Archive Directory
- `/home/opc/automation/archive/` (entire directory)
  - Contains old airscripts implementation that has been replaced
  - Historical code no longer in use
  - Can be safely archived or removed

## Safe to Delete - Analysis Files
- `/home/opc/automation/analyze_duplicates.cjs`
  - One-time analysis script for duplicate detection
  - Analysis complete, no longer needed
- `/home/opc/automation/final_unique_uids.txt`
  - Output file from duplicate analysis
  - Analysis complete, can be removed
- `/home/opc/automation/unique_uids_list.txt`
  - Another output from duplicate analysis
  - No longer needed
- `/home/opc/automation/duplicate_records_list.csv`
  - Duplicate analysis output
  - Can be archived
- `/home/opc/automation/duplicate_reservation_uids.txt`
  - Duplicate analysis output
  - Can be archived

## Safe to Delete - Utility Scripts
- `/home/opc/automation/paste.js`
  - Appears to be a temporary utility script
  - No references found in main codebase
- `/home/opc/automation/find_duplicates.js`
  - One-time analysis script
  - Analysis complete, no longer needed
- `/home/opc/automation/find_latest_records.py`
  - One-time analysis script
  - Analysis complete, no longer needed
- `/home/opc/automation/process_duplicate_uids.py`
  - One-time analysis script
  - Analysis complete, no longer needed

## Safe to Archive - Old CSV Backups
- `/home/opc/automation/backups/` (if contains old CSV files)
  - Check for old CSV backups that are no longer needed
  - Keep recent backups, archive older ones

## Safe to Delete - Build Artifacts
- `/home/opc/automation/dist/` (if present and not in use)
  - Build output directory
  - Can be regenerated from source

## Safe to Delete - Test Files
- `/home/opc/automation/test_setup.py` (after verification it's not used in CI/CD)
  - Appears to be a one-time setup validation script

## Files to Keep (DO NOT DELETE)
- All files in `/home/opc/automation/src/`
- All files in `/home/opc/automation/tools/`
- All files in `/home/opc/automation/config/`
- All environment files (`.env`)
- All package files (`package.json`, `requirements.txt`, etc.)
- All documentation files
- All current CSV processing directories
- All log files

## Recommendations
1. Archive rather than delete for historical reference
2. Verify each file is not referenced in any configuration before removal
3. Create backup before any deletion
4. Remove files gradually and test system functionality after each removal

## Estimated Space Savings
- Archive directory: ~50MB
- Analysis files: ~10MB
- Utility scripts: ~5MB
- Total potential savings: ~65MB

Last Updated: 2025-06-07