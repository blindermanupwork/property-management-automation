#!/usr/bin/env python3
"""
Test the safe removal logic in DEVELOPMENT environment
This creates test records and simulates missing ICS entries
"""
import os
import sys
from datetime import datetime, timedelta
import pytz
from pyairtable import Api

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_test_environment():
    """Setup test records in dev Airtable"""
    
    # Development base
    base_id = 'app67yWFv0hKdl6jM'
    table_id = 'tblaPnk0jxF47xWhL'  # Assuming same table structure
    
    # Get API key from dev environment
    api_key = os.environ.get('AIRTABLE_API_KEY')
    if not api_key:
        # Try to load from dev config
        dev_env_path = 'config/environments/dev/.env'
        if os.path.exists(dev_env_path):
            with open(dev_env_path, 'r') as f:
                for line in f:
                    if line.startswith('AIRTABLE_API_KEY='):
                        api_key = line.split('=')[1].strip()
                        break
    
    if not api_key:
        print("ERROR: AIRTABLE_API_KEY not found")
        return None
        
    api = Api(api_key)
    base = api.base(base_id)
    table = base.table(table_id)
    
    return table

def add_tracking_fields_to_dev():
    """Add the same tracking fields to dev base"""
    print("Adding tracking fields to development base...")
    
    # We'll use the MCP server for this
    print("\nPlease run these commands to add fields to dev:")
    print("1. Missing Count (number, precision 0)")
    print("2. Missing Since (dateTime)")  
    print("3. Last Seen (dateTime)")
    
    return True

def create_test_scenarios(table):
    """Create test records for different removal scenarios"""
    
    arizona_tz = pytz.timezone('America/Phoenix')
    now = datetime.now(arizona_tz)
    
    test_records = [
        {
            "name": "Test 1: Active reservation - should track but not remove",
            "fields": {
                "Check-in Date": (now + timedelta(days=5)).strftime('%Y-%m-%d'),
                "Check-out Date": (now + timedelta(days=8)).strftime('%Y-%m-%d'),
                "Status": "New",
                "Entry Type": "Reservation",
                "Service Type": "Turnover",
                "Reservation UID": f"test_removal_1_{now.timestamp()}_recTEST1",
                "ICS URL": "test_feed_1",
                "Property ID": ["recWE5Fc8SGODAADs"],  # Use a real property ID from dev
                "Entry Source": "Test"
            }
        },
        {
            "name": "Test 2: Reservation with active HCP job - should never remove",
            "fields": {
                "Check-in Date": (now + timedelta(days=10)).strftime('%Y-%m-%d'),
                "Check-out Date": (now + timedelta(days=12)).strftime('%Y-%m-%d'),
                "Status": "New",
                "Entry Type": "Reservation",
                "Service Type": "Turnover",
                "Reservation UID": f"test_removal_2_{now.timestamp()}_recTEST2",
                "ICS URL": "test_feed_1",
                "Property ID": ["recWE5Fc8SGODAADs"],
                "Service Job ID": "job_test123",
                "Job Status": "Scheduled",
                "Entry Source": "Test"
            }
        },
        {
            "name": "Test 3: Past reservation - should not track",
            "fields": {
                "Check-in Date": (now - timedelta(days=10)).strftime('%Y-%m-%d'),
                "Check-out Date": (now - timedelta(days=7)).strftime('%Y-%m-%d'),
                "Status": "New",
                "Entry Type": "Reservation",
                "Service Type": "Turnover",
                "Reservation UID": f"test_removal_3_{now.timestamp()}_recTEST3",
                "ICS URL": "test_feed_1",
                "Property ID": ["recWE5Fc8SGODAADs"],
                "Entry Source": "Test"
            }
        },
        {
            "name": "Test 4: Reservation already being tracked",
            "fields": {
                "Check-in Date": (now + timedelta(days=15)).strftime('%Y-%m-%d'),
                "Check-out Date": (now + timedelta(days=18)).strftime('%Y-%m-%d'),
                "Status": "New",
                "Entry Type": "Reservation",
                "Service Type": "Turnover",
                "Reservation UID": f"test_removal_4_{now.timestamp()}_recTEST4",
                "ICS URL": "test_feed_1",
                "Property ID": ["recWE5Fc8SGODAADs"],
                "Missing Count": 2,
                "Missing Since": (now - timedelta(hours=36)).isoformat(),
                "Entry Source": "Test"
            }
        }
    ]
    
    created_records = []
    
    for test in test_records:
        print(f"\nCreating: {test['name']}")
        try:
            record = table.create(test['fields'])
            created_records.append({
                'id': record['id'],
                'name': test['name'],
                'uid': test['fields']['Reservation UID']
            })
            print(f"  ✅ Created with ID: {record['id']}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return created_records

def simulate_removal_logic(table, test_records):
    """Simulate what would happen with the safe removal logic"""
    
    print("\n" + "="*70)
    print("SIMULATING SAFE REMOVAL LOGIC")
    print("="*70)
    
    from icsAirtableSync.removal_safety import (
        should_mark_as_removed,
        check_removal_exceptions,
        MISSING_SYNC_THRESHOLD,
        GRACE_PERIOD_HOURS
    )
    
    arizona_tz = pytz.timezone('America/Phoenix')
    now = datetime.now(arizona_tz)
    
    for test_record in test_records:
        print(f"\n{test_record['name']}")
        
        # Get the actual record
        try:
            records = table.all(formula=f"{{Reservation UID}}='{test_record['uid']}'")
            if not records:
                print("  ⚠️  Record not found")
                continue
                
            record = records[0]
            fields = record['fields']
            
            # Check removal exceptions
            exception_reason = check_removal_exceptions(fields)
            if exception_reason:
                print(f"  🛡️  Protected from removal: {exception_reason}")
                continue
            
            # Check if should be removed
            should_remove, updates = should_mark_as_removed(record, now, is_missing_from_feed=True)
            
            if should_remove:
                print(f"  🚨 Would be REMOVED (missing count: {updates.get('Missing Count', 0)})")
            elif updates:
                print(f"  📊 Would update tracking:")
                for key, value in updates.items():
                    print(f"     - {key}: {value}")
            else:
                print(f"  ✅ No action needed")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def cleanup_test_records(table, test_records):
    """Remove test records after testing"""
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)
    
    for record in test_records:
        try:
            table.delete(record['id'])
            print(f"✅ Deleted test record: {record['id']}")
        except Exception as e:
            print(f"❌ Error deleting {record['id']}: {e}")


if __name__ == "__main__":
    print("SAFE REMOVAL TESTING IN DEVELOPMENT")
    print("="*70)
    
    # Setup
    table = setup_test_environment()
    if not table:
        sys.exit(1)
    
    # Check if we need to add fields first
    print("\nChecking for tracking fields in dev base...")
    try:
        # Try to fetch a record with the new fields
        records = table.all(fields=['Missing Count', 'Missing Since', 'Last Seen'], max_records=1)
        print("✅ Tracking fields already exist in dev")
    except:
        print("❌ Tracking fields missing - please add them using the Airtable MCP")
        add_tracking_fields_to_dev()
        print("\nAfter adding fields, run this script again.")
        sys.exit(0)
    
    # Create test scenarios
    print("\nCreating test scenarios...")
    test_records = create_test_scenarios(table)
    
    if test_records:
        # Wait for user confirmation
        input("\nPress Enter to simulate removal logic on test records...")
        
        # Run simulation
        try:
            simulate_removal_logic(table, test_records)
        except ImportError:
            print("\n⚠️  removal_safety module not found - this is expected")
            print("The actual logic would:")
            print("  1. Track missing reservations for 3 consecutive syncs")
            print("  2. Provide 12-hour grace period")
            print("  3. Protect active HCP jobs, recent check-ins, and imminent checkouts")
        
        # Cleanup
        input("\nPress Enter to clean up test records...")
        cleanup_test_records(table, test_records)
    
    print("\n✅ Test complete!")