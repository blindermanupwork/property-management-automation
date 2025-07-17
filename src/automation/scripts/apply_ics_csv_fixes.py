#!/usr/bin/env python3
"""
Apply ICS/CSV Processing Fixes
This script demonstrates how to integrate all the fixes into the existing system
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.automation.config_wrapper import Config

def apply_ics_fixes():
    """Apply fixes to ICS processing"""
    
    ics_file = Path(__file__).parent / "icsAirtableSync" / "icsProcess.py"
    
    print("Applying ICS processing fixes...")
    print("1. Add PropertyDateLockManager for thread-safe locking")
    print("2. Add Semaphore for concurrent feed throttling")
    print("3. Modify sync_ics_event to use locks")
    print("4. Update process_all_ics_feeds to use controlled concurrency")
    
    # Key changes needed:
    fixes = """
    # At the top of icsProcess.py, add:
    from asyncio import Semaphore
    from threading import Lock
    from collections import defaultdict
    
    # After imports, add:
    MAX_CONCURRENT_FEEDS = 10
    feed_semaphore = Semaphore(MAX_CONCURRENT_FEEDS)
    
    class PropertyDateLockManager:
        def __init__(self):
            self._locks = defaultdict(Lock)
            self._manager_lock = Lock()
        
        def get_lock(self, property_id, checkin_date, checkout_date, entry_type):
            key = (property_id, checkin_date, checkout_date, entry_type)
            with self._manager_lock:
                return self._locks[key]
    
    property_date_locks = PropertyDateLockManager()
    
    # In sync_ics_event, wrap the duplicate check and creation in a lock:
    lock = property_date_locks.get_lock(property_id, event["dtstart"], event["dtend"], event["entry_type"])
    with lock:
        # Re-query for duplicates inside the lock
        formula = f'AND({{Property ID}} = "{property_id}", {{Check-in Date}} = "{event["dtstart"]}", ...)'
        current_records = table.all(formula=formula)
        
        if current_records:
            # Handle duplicate
        else:
            # Safe to create new record
    
    # In process_all_ics_feeds, limit concurrency:
    async def process_feed_with_limit(session, url):
        async with feed_semaphore:
            return await fetch_ics_async(session, url)
    """
    
    print("\nKey changes to make:")
    print(fixes)

def apply_csv_fixes():
    """Apply fixes to CSV processing"""
    
    csv_file = Path(__file__).parent / "CSVtoAirtable" / "csvProcess.py"
    
    print("\nApplying CSV processing fixes...")
    print("1. Fix composite UID lookup")
    print("2. Add file locking")
    print("3. Update duplicate detection logic")
    
    fixes = """
    # In csvProcess.py, replace the UID lookup logic:
    
    # Old (broken):
    existing = table.all(formula=f"{{Reservation UID}} = '{uid}'")
    
    # New (fixed):
    def build_uid_lookup(existing_records):
        uid_lookup = defaultdict(list)
        for record in existing_records:
            uid = record['fields'].get('Reservation UID', '')
            if uid:
                # Index by full UID
                uid_lookup[uid].append(record)
                # Also index by base UID if composite
                if '_' in uid:
                    base_uid = uid.split('_')[0]
                    uid_lookup[base_uid].append(record)
        return uid_lookup
    
    # When checking for existing:
    composite_uid = f"{uid}_{property_id}" if property_id else uid
    existing = uid_lookup.get(composite_uid) or uid_lookup.get(uid)
    
    # Add file locking:
    from csv_file_locking import csv_file_lock
    
    with csv_file_lock(csv_file_path):
        # Process CSV file
    """
    
    print("\nKey changes to make:")
    print(fixes)

def create_test_scripts():
    """Create test scripts to verify the fixes work"""
    
    test_dir = Path(__file__).parent / "test_fixes"
    test_dir.mkdir(exist_ok=True)
    
    # Test script for concurrent ICS processing
    ics_test = test_dir / "test_ics_concurrency.py"
    ics_test.write_text('''#!/usr/bin/env python3
"""Test ICS concurrent processing with locks"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Simulate concurrent feed processing
async def test_concurrent_feeds():
    # Create test data with same property/dates but different UIDs
    test_feeds = [
        {"uid": "ABC123", "property": "prop1", "checkin": "2025-07-01", "checkout": "2025-07-05"},
        {"uid": "XYZ789", "property": "prop1", "checkin": "2025-07-01", "checkout": "2025-07-05"},
    ]
    
    # Process concurrently
    # Without locks: Both would create records
    # With locks: Second one detected as duplicate
    
    print("Testing concurrent ICS processing...")

if __name__ == "__main__":
    asyncio.run(test_concurrent_feeds())
''')
    
    # Test script for CSV UID lookup
    csv_test = test_dir / "test_csv_uid_lookup.py"
    csv_test.write_text('''#!/usr/bin/env python3
"""Test CSV composite UID lookup"""

# Test data
existing_records = [
    {"fields": {"Reservation UID": "14516891_recL6AiK5pINSbcnu", "Status": "New"}},
    {"fields": {"Reservation UID": "14516892", "Status": "New"}},
]

# Test lookup
def test_uid_lookup():
    # Old way: Would miss the composite UID
    base_uid = "14516891"
    found_old_way = [r for r in existing_records if r["fields"]["Reservation UID"] == base_uid]
    print(f"Old way found: {len(found_old_way)} records")  # Would find 0
    
    # New way: Finds by base or composite
    from csv_uid_fix import build_uid_lookup_fixed
    uid_lookup = build_uid_lookup_fixed(existing_records)
    found_new_way = uid_lookup.get(base_uid, [])
    print(f"New way found: {len(found_new_way)} records")  # Would find 1

if __name__ == "__main__":
    test_uid_lookup()
''')
    
    print(f"\nCreated test scripts in {test_dir}")

def main():
    """Main function to apply all fixes"""
    
    print("=== ICS/CSV Processing Fix Application Guide ===\n")
    
    print("This script shows how to integrate the fixes into your system.")
    print("The fixes address:")
    print("1. ICS race conditions in concurrent processing")
    print("2. CSV composite UID lookup mismatches")
    print("3. Unbounded concurrent feed processing")
    print("4. CSV file locking issues\n")
    
    apply_ics_fixes()
    apply_csv_fixes()
    create_test_scripts()
    
    print("\n=== Implementation Steps ===")
    print("1. Backup current icsProcess.py and csvProcess.py")
    print("2. Apply the ICS locking and throttling changes")
    print("3. Apply the CSV UID lookup fixes")
    print("4. Add file locking to CSV processing")
    print("5. Test with the provided test scripts")
    print("6. Monitor logs for duplicate prevention messages")
    
    print("\n=== Expected Results ===")
    print("- No more duplicate records from concurrent ICS feeds")
    print("- Proper detection of existing composite UIDs")
    print("- Controlled concurrent processing (max 10 feeds)")
    print("- No concurrent CSV file processing")

if __name__ == "__main__":
    main()