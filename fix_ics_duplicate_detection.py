#!/usr/bin/env python3
"""
Fix for ICS duplicate detection bug.

The issue: duplicate detection compares raw ICS dates (with time) 
against stored dates (date-only), causing mismatches and duplicates.

The fix: normalize dates before comparison using extract_date_only().
"""

import sys
import shutil
from datetime import datetime

# Backup and fix the ICS processor
source_file = '/home/opc/automation/src/automation/scripts/icsAirtableSync/icsProcess_optimized.py'
backup_file = f'{source_file}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

print(f"🔧 Fixing ICS duplicate detection bug...")
print(f"📄 Creating backup: {backup_file}")

# Create backup
shutil.copy2(source_file, backup_file)

# Read the current file
with open(source_file, 'r') as f:
    content = f.read()

# Find and fix the bug
old_code = """    # ALWAYS check for duplicates first, regardless of whether we have records with this UID
    # This prevents creating duplicates when the ICS feed provides different UIDs for the same reservation
    is_duplicate, related_records = check_for_duplicate_with_tracking(
        table, 
        property_id, 
        event["dtstart"], 
        event["dtend"], 
        event["entry_type"]
    )"""

new_code = """    # ALWAYS check for duplicates first, regardless of whether we have records with this UID
    # This prevents creating duplicates when the ICS feed provides different UIDs for the same reservation
    # FIX: Normalize dates before comparison to match stored format
    is_duplicate, related_records = check_for_duplicate_with_tracking(
        table, 
        property_id, 
        extract_date_only(event["dtstart"]), 
        extract_date_only(event["dtend"]), 
        event["entry_type"]
    )"""

if old_code in content:
    print("✅ Found the bug in sync_ics_event function")
    content = content.replace(old_code, new_code)
    
    # Write the fixed file
    with open(source_file, 'w') as f:
        f.write(content)
    
    print("✅ Applied fix - dates are now normalized before duplicate detection")
    print("🔍 The fix:")
    print("   - OLD: compare raw ICS dates (with time) vs stored dates (date-only)")
    print("   - NEW: normalize both sides using extract_date_only() before comparison")
    print("\n📋 Next steps:")
    print("   1. Test the fix with a small ICS feed")
    print("   2. Run system-wide duplicate cleanup")
    print("   3. Monitor for new duplicates")
    
else:
    print("❌ Could not find the expected code pattern to fix")
    print("   The file may have been modified or the bug may be elsewhere")
    print(f"   Backup created at: {backup_file}")

print(f"\n💾 Backup saved at: {backup_file}")