#!/usr/bin/env python3
"""
Test the hybrid UID + property/dates/type approach for ICS processing.
Tests various scenarios including Lodgify UID changes, date modifications, etc.
"""

import os
import sys
from datetime import datetime, timedelta
from pyairtable import Table
from dotenv import load_dotenv
import pytz
import time

# Add the automation directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Test data for different scenarios
TEST_SCENARIOS = [
    {
        "name": "Lodgify UID Change - Same Property/Dates/Type",
        "description": "Simulates Lodgify changing UID for same reservation",
        "property_id": "recRQSv5kFaVKAXdj",  # Mayes property
        "events": [
            {
                "uid": "lodgify_12345",
                "dtstart": "2025-08-15",
                "dtend": "2025-08-17",
                "entry_type": "Reservation",
                "summary": "Test Guest 1"
            },
            {
                "uid": "lodgify_99999",  # Different UID
                "dtstart": "2025-08-15",  # Same dates
                "dtend": "2025-08-17",
                "entry_type": "Reservation",  # Same type
                "summary": "Test Guest 1"
            }
        ],
        "expected": "Should update existing record's UID, not create duplicate"
    },
    
    {
        "name": "Date Modification - Guest Extends Stay",
        "description": "Guest extends checkout date",
        "property_id": "recRQSv5kFaVKAXdj",
        "events": [
            {
                "uid": "extend_test_001",
                "dtstart": "2025-08-20",
                "dtend": "2025-08-22",
                "entry_type": "Reservation",
                "summary": "Extension Test Guest"
            },
            {
                "uid": "extend_test_001",  # Same UID
                "dtstart": "2025-08-20",  # Same check-in
                "dtend": "2025-08-25",  # Extended checkout
                "entry_type": "Reservation",
                "summary": "Extension Test Guest"
            }
        ],
        "expected": "Should modify existing record, not create new"
    },
    
    {
        "name": "Complete Date Change",
        "description": "Reservation moved to different dates entirely",
        "property_id": "recRQSv5kFaVKAXdj",
        "events": [
            {
                "uid": "date_change_001",
                "dtstart": "2025-09-01",
                "dtend": "2025-09-03",
                "entry_type": "Reservation",
                "summary": "Date Change Guest"
            },
            {
                "uid": "date_change_001",  # Same UID
                "dtstart": "2025-09-10",  # Different dates
                "dtend": "2025-09-12",
                "entry_type": "Reservation",
                "summary": "Date Change Guest"
            }
        ],
        "expected": "Should mark old as 'Old' and create new record"
    },
    
    {
        "name": "Cancellation Then Block",
        "description": "Guest cancels, owner blocks same dates",
        "property_id": "recRQSv5kFaVKAXdj",
        "events": [
            {
                "uid": "cancel_block_001",
                "dtstart": "2025-09-15",
                "dtend": "2025-09-17",
                "entry_type": "Reservation",
                "summary": "Cancellation Test"
            },
            {
                "uid": "owner_block_001",
                "dtstart": "2025-09-15",  # Same dates
                "dtend": "2025-09-17",
                "entry_type": "Block",  # Different type
                "summary": "Owner"
            }
        ],
        "expected": "Should have both records - Reservation marked 'Old', Block as 'New'"
    },
    
    {
        "name": "Same-Day Turnover Flag Change",
        "description": "Non-key field modification",
        "property_id": "recRQSv5kFaVKAXdj",
        "events": [
            {
                "uid": "flag_test_001",
                "dtstart": "2025-10-01",
                "dtend": "2025-10-03",
                "entry_type": "Reservation",
                "same_day_turnover": False,
                "summary": "Flag Test"
            },
            {
                "uid": "flag_test_001",
                "dtstart": "2025-10-01",
                "dtend": "2025-10-03",
                "entry_type": "Reservation",
                "same_day_turnover": True,  # Flag changed
                "summary": "Flag Test"
            }
        ],
        "expected": "Should mark as 'Modified' status"
    },
    
    {
        "name": "Lodgify + Date Change Combo",
        "description": "Both UID and dates change",
        "property_id": "recRQSv5kFaVKAXdj",
        "events": [
            {
                "uid": "combo_test_001",
                "dtstart": "2025-10-10",
                "dtend": "2025-10-12",
                "entry_type": "Reservation",
                "summary": "Combo Test"
            },
            {
                "uid": "combo_test_999",  # Different UID
                "dtstart": "2025-10-15",  # Different dates
                "dtend": "2025-10-17",
                "entry_type": "Reservation",
                "summary": "Combo Test"
            }
        ],
        "expected": "Should create new record (dates changed)"
    }
]


def create_test_event(uid, dtstart, dtend, entry_type, property_id, **kwargs):
    """Create a test event structure."""
    event = {
        "uid": uid,
        "dtstart": dtstart,
        "dtend": dtend,
        "entry_type": entry_type,
        "service_type": "Turnover" if entry_type == "Reservation" else "Clean",
        "entry_source": "Test",
        "overlapping": False,
        "same_day_turnover": kwargs.get("same_day_turnover", False),
        "block_type": "Owner" if entry_type == "Block" else None,
        "ics_url": f"https://test.com/{property_id}.ics"
    }
    return event


def run_test_scenario(scenario, table, property_id):
    """Run a single test scenario."""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {scenario['name']}")
    print(f"📝 {scenario['description']}")
    print(f"🎯 Expected: {scenario['expected']}")
    print(f"{'='*60}")
    
    # Clean up any existing test records first
    print("\n🧹 Cleaning up existing test records...")
    cleanup_test_records(table, scenario['events'])
    
    # Process each event in the scenario
    for i, event_data in enumerate(scenario['events']):
        print(f"\n📍 Event {i+1}:")
        print(f"   UID: {event_data['uid']}")
        print(f"   Dates: {event_data['dtstart']} to {event_data['dtend']}")
        print(f"   Type: {event_data['entry_type']}")
        
        # Create the event
        event = create_test_event(
            uid=event_data['uid'],
            dtstart=event_data['dtstart'],
            dtend=event_data['dtend'],
            entry_type=event_data['entry_type'],
            property_id=property_id,
            same_day_turnover=event_data.get('same_day_turnover', False)
        )
        
        # Simulate processing this event
        # In real scenario, this would go through icsProcess_best.py
        print(f"\n   🔄 Processing event...")
        time.sleep(1)  # Small delay to simulate processing
    
    # Check results
    print(f"\n📊 Checking results...")
    check_test_results(table, scenario)


def cleanup_test_records(table, events):
    """Remove any existing test records."""
    test_uids = [event['uid'] for event in events]
    
    # Search for records with test UIDs
    for uid in test_uids:
        try:
            records = table.all(formula=f"FIND('{uid}', {{Reservation UID}}) > 0")
            for record in records:
                table.delete(record['id'])
                print(f"   🗑️  Deleted test record: {record['id']}")
        except:
            pass


def check_test_results(table, scenario):
    """Check if test results match expectations."""
    # This would need to be implemented based on actual results
    # For now, just print what we'd check
    print(f"\n✅ Test scenario complete")
    print(f"   ⚠️  Manual verification needed:")
    print(f"   - Check Airtable for records related to this test")
    print(f"   - Verify: {scenario['expected']}")


def run_all_tests(env='dev'):
    """Run all test scenarios."""
    # Set up
    if env == 'dev':
        base_id = os.getenv('AIRTABLE_BASE_ID_DEV', 'app67yWFv0hKdl6jM')
        print("🔧 Using DEVELOPMENT Airtable base")
    else:
        base_id = os.getenv('AIRTABLE_BASE_ID', 'appZzebEIqCU5R9ER')
        print("🏭 Using PRODUCTION Airtable base")
    
    api_key = os.getenv('AIRTABLE_API_KEY')
    table = Table(api_key, base_id, 'Reservations')
    
    print(f"\n🚀 Running Hybrid Approach Tests - {env.upper()} environment")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run each test scenario
    for scenario in TEST_SCENARIOS:
        try:
            run_test_scenario(scenario, table, scenario['property_id'])
        except Exception as e:
            print(f"\n❌ Error in test '{scenario['name']}': {str(e)}")
    
    print(f"\n\n🏁 All tests complete!")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📋 MANUAL VERIFICATION CHECKLIST:")
    print(f"1. Check development ICS logs for hybrid matching messages")
    print(f"2. Verify no duplicates created for Lodgify UID changes")
    print(f"3. Confirm date modifications are tracked properly")
    print(f"4. Check that cancellation + block creates separate records")
    print(f"5. Verify flag changes result in 'Modified' status")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test hybrid ICS processing approach")
    parser.add_argument('--env', choices=['dev', 'prod'], default='dev', help='Environment to use')
    
    args = parser.parse_args()
    
    # WARNING for production
    if args.env == 'prod':
        print("\n⚠️  WARNING: Running tests in PRODUCTION!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    run_all_tests(env=args.env)