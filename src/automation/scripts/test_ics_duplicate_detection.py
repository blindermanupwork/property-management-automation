#!/usr/bin/env python3
"""
Comprehensive test cases for ICS duplicate detection.
Tests all scenarios including dynamic UID systems like Lodgify.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import tempfile
import shutil

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can import our modules
from src.automation.scripts.icsAirtableSync.icsProcess_best import (
    sync_ics_event, 
    BatchCollector,
    InMemoryCollector,
    process_ics_feed
)
import pytz

# Initialize timezone
arizona_tz = pytz.timezone('America/Phoenix')

class MockTable:
    """Mock Airtable table for testing."""
    def __init__(self):
        self.records = {}
        self.next_id = 1
        
    def all(self, formula=None, fields=None):
        """Mock all() method."""
        if formula:
            # For testing, return all records
            return list(self.records.values())
        return list(self.records.values())
    
    def create(self, fields):
        """Mock create method for single record."""
        rec_id = f"rec{self.next_id:06d}"
        self.next_id += 1
        new_record = {
            "id": rec_id,
            "fields": fields.copy(),
            "createdTime": datetime.now().isoformat()
        }
        self.records[rec_id] = new_record
        return new_record
    
    def batch_create(self, records):
        """Mock batch_create method."""
        created = []
        for rec in records:
            rec_id = f"rec{self.next_id:06d}"
            self.next_id += 1
            new_record = {
                "id": rec_id,
                "fields": rec.copy(),
                "createdTime": datetime.now().isoformat()
            }
            self.records[rec_id] = new_record
            created.append(new_record)
        return created
    
    def batch_update(self, records):
        """Mock batch_update method."""
        updated = []
        for rec in records:
            rec_id = rec["id"]
            if rec_id in self.records:
                self.records[rec_id]["fields"].update(rec["fields"])
                updated.append(self.records[rec_id])
        return updated

class TestIcsDuplicateDetection:
    """Test suite for ICS duplicate detection."""
    
    def __init__(self):
        self.table = MockTable()
        self.property_id = "recTestProperty123"
        self.feed_url = "https://example.com/test.ics"
        self.url_to_prop = {self.feed_url: self.property_id}
        
    def create_test_event(self, uid, checkin="2025-08-01", checkout="2025-08-03", 
                         entry_type="Reservation", service_type="Turnover"):
        """Create a test event."""
        return {
            "uid": uid,
            "ics_url": self.feed_url,
            "dtstart": checkin,
            "dtend": checkout,
            "entry_type": entry_type,
            "service_type": service_type,
            "entry_source": "Test",
            "overlapping": False,
            "same_day_turnover": False,
            "block_type": None
        }
    
    def get_existing_records(self):
        """Get existing records in the format expected by sync_ics_event."""
        existing = defaultdict(list)
        for record in self.table.records.values():
            fields = record["fields"]
            uid = fields.get("Reservation UID", "")
            url = fields.get("ICS URL", "")
            if uid and url:
                existing[(uid, url)].append(record)
        return existing
    
    def run_test(self, test_name, test_func):
        """Run a single test."""
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        # Reset table for each test
        self.table = MockTable()
        
        try:
            result = test_func()
            if result:
                print(f"✅ PASSED: {test_name}")
            else:
                print(f"❌ FAILED: {test_name}")
            return result
        except Exception as e:
            print(f"❌ FAILED: {test_name} - Exception: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_scenario_1_new_reservation(self):
        """Test Scenario 1: New reservation comes in."""
        print("\nScenario: Processing a brand new reservation")
        
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        session_tracker = set()
        
        event = self.create_test_event("uid-001")
        existing = self.get_existing_records()
        
        # Process the event
        status = sync_ics_event(
            event, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        
        # Flush batches
        create_batch.done()
        update_batch.done()
        
        # Verify
        print(f"Status returned: {status}")
        print(f"Records created: {len(self.table.records)}")
        print(f"Session tracker size: {len(session_tracker)}")
        
        # Check assertions
        assert status == "New", f"Expected 'New', got '{status}'"
        assert len(self.table.records) == 1, f"Expected 1 record, got {len(self.table.records)}"
        assert len(session_tracker) == 1, f"Expected 1 tracker entry, got {len(session_tracker)}"
        
        # Verify the tracker key
        expected_key = (self.property_id, "2025-08-01", "2025-08-03", "Reservation")
        assert expected_key in session_tracker, f"Expected tracker key {expected_key} not found"
        
        return True
    
    def test_scenario_2_same_uid_modification(self):
        """Test Scenario 2: Same UID with modifications comes in."""
        print("\nScenario: Same UID comes in with modified service type")
        
        # First, create initial reservation
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        session_tracker = set()
        
        event1 = self.create_test_event("uid-002", service_type="Turnover")
        existing = self.get_existing_records()
        
        status1 = sync_ics_event(
            event1, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Initial creation status: {status1}")
        
        # Now process the same UID with a different service type
        # IMPORTANT: Clear session tracker to simulate a new processing run
        session_tracker = set()
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        
        event2 = self.create_test_event("uid-002", service_type="Deep Clean")
        existing = self.get_existing_records()
        
        status2 = sync_ics_event(
            event2, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Modification status: {status2}")
        print(f"Total records: {len(self.table.records)}")
        
        # Count active vs old records
        active_count = sum(1 for r in self.table.records.values() 
                          if r["fields"].get("Status") in ("New", "Modified"))
        old_count = sum(1 for r in self.table.records.values() 
                       if r["fields"].get("Status") == "Old")
        
        print(f"Active records: {active_count}, Old records: {old_count}")
        
        # Verify
        assert status2 == "Modified", f"Expected 'Modified', got '{status2}'"
        assert len(self.table.records) == 2, f"Expected 2 records total, got {len(self.table.records)}"
        assert active_count == 1, f"Expected 1 active record, got {active_count}"
        assert old_count == 1, f"Expected 1 old record, got {old_count}"
        
        return True
    
    def test_scenario_3_uid_removed(self):
        """Test Scenario 3: Same UID is missing (removal)."""
        print("\nScenario: UID missing from feed, checkout is in the FUTURE")
        
        # Create initial reservation with FUTURE checkout
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        session_tracker = set()
        
        # Use dates in the FUTURE
        future_checkin = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        future_checkout = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        event = self.create_test_event("uid-003", checkin=future_checkin, checkout=future_checkout)
        existing = self.get_existing_records()
        
        status = sync_ics_event(
            event, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Initial creation status: {status}")
        
        # Now simulate processing the feed without this UID
        # This is typically done in process_ics_feed, but we'll simulate the removal logic
        existing = self.get_existing_records()
        composite_uid = f"uid-003_{self.property_id}"
        
        # Check if the record should be removed
        records = existing.get((composite_uid, self.feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        print(f"Found {len(active_records)} active records to check for removal")
        
        removed_count = 0
        today = datetime.now(arizona_tz).date().isoformat()
        
        for rec in active_records:
            checkout_date = rec["fields"].get("Check-out Date", "")
            print(f"Checking record with checkout {checkout_date} against today {today}")
            
            if checkout_date > today:
                print(f"Record should be removed (checkout in future)")
                # In real code, this would update the record status to "Removed"
                removed_count += 1
            else:
                print(f"Record should NOT be removed (checkout in past or today)")
        
        assert removed_count == 1, f"Expected 1 record to be removed, got {removed_count}"
        
        return True
    
    def test_scenario_4_different_uid_same_dates(self):
        """Test Scenario 4: Different UID but same property/dates/entry (Lodgify case)."""
        print("\nScenario: Different UID but same property/dates/entry type")
        
        # Create initial reservation
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        session_tracker = set()
        
        event1 = self.create_test_event("uid-004")
        existing = self.get_existing_records()
        
        status1 = sync_ics_event(
            event1, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Initial creation status: {status1}")
        print(f"Session tracker after first event: {session_tracker}")
        
        # Now try to create with a different UID but same dates
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        
        event2 = self.create_test_event("uid-005")  # Different UID, same dates
        existing = self.get_existing_records()
        
        status2 = sync_ics_event(
            event2, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker  # Using same session tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Duplicate attempt status: {status2}")
        print(f"Total records: {len(self.table.records)}")
        
        # Verify
        assert status2 == "Duplicate_Ignored", f"Expected 'Duplicate_Ignored', got '{status2}'"
        assert len(self.table.records) == 1, f"Expected only 1 record, got {len(self.table.records)}"
        
        return True
    
    
    def test_scenario_5_different_dates_same_uid(self):
        """Test Scenario 5: Same UID but different dates (legitimate new reservation)."""
        print("\nScenario: Same UID with different dates")
        
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        session_tracker = set()
        
        # First reservation
        event1 = self.create_test_event("uid-006", checkin="2025-08-01", checkout="2025-08-03")
        existing = self.get_existing_records()
        
        status1 = sync_ics_event(
            event1, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"First reservation status: {status1}")
        
        # Second reservation with same UID but different dates
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        
        event2 = self.create_test_event("uid-006", checkin="2025-08-10", checkout="2025-08-12")
        existing = self.get_existing_records()
        
        status2 = sync_ics_event(
            event2, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Second reservation status: {status2}")
        print(f"Total records: {len(self.table.records)}")
        print(f"Session tracker entries: {len(session_tracker)}")
        
        # When same UID has different dates, it's treated as a modification
        assert status2 == "Modified", f"Expected 'Modified', got '{status2}'"
        assert len(self.table.records) == 2, f"Expected 2 records, got {len(self.table.records)}"
        # Session tracker only has 1 entry because modifications don't add new tracker entries
        assert len(session_tracker) == 1, f"Expected 1 tracker entry, got {len(session_tracker)}"
        
        return True
    
    def test_scenario_6_block_vs_reservation(self):
        """Test Scenario 6: Different entry types for same dates."""
        print("\nScenario: Block and Reservation for same property/dates")
        
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        session_tracker = set()
        
        # Create a reservation
        event1 = self.create_test_event("uid-007", entry_type="Reservation")
        existing = self.get_existing_records()
        
        status1 = sync_ics_event(
            event1, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Reservation status: {status1}")
        
        # Create a block for same dates
        create_batch = BatchCollector(self.table, op="create")
        update_batch = BatchCollector(self.table, op="update")
        
        event2 = self.create_test_event("uid-008", entry_type="Block", service_type="Needs Review")
        existing = self.get_existing_records()
        
        status2 = sync_ics_event(
            event2, existing, self.url_to_prop, self.table,
            create_batch, update_batch, session_tracker
        )
        create_batch.done()
        update_batch.done()
        
        print(f"Block status: {status2}")
        print(f"Total records: {len(self.table.records)}")
        
        # Both should exist as they have different entry types
        assert status2 == "New", f"Expected 'New', got '{status2}'"
        assert len(self.table.records) == 2, f"Expected 2 records, got {len(self.table.records)}"
        
        return True

def main():
    """Run all test scenarios."""
    print("🧪 ICS Duplicate Detection Test Suite")
    print("="*70)
    
    tester = TestIcsDuplicateDetection()
    results = []
    
    # Run all test scenarios
    test_scenarios = [
        ("Scenario 1: New reservation", tester.test_scenario_1_new_reservation),
        ("Scenario 2: Same UID with modifications", tester.test_scenario_2_same_uid_modification),
        ("Scenario 3: UID removed (future checkout)", tester.test_scenario_3_uid_removed),
        ("Scenario 4: Different UID, same dates (Lodgify case)", tester.test_scenario_4_different_uid_same_dates),
        ("Scenario 5: Same UID, different dates", tester.test_scenario_5_different_dates_same_uid),
        ("Scenario 6: Different entry types", tester.test_scenario_6_block_vs_reservation),
    ]
    
    for test_name, test_func in test_scenarios:
        result = tester.run_test(test_name, test_func)
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())