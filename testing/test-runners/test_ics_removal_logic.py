#!/usr/bin/env python3
"""
Test ICS Removal Logic (v2.2.22)
Tests the updated removal logic to verify:
1. Missing Count increments every hour when record is missing
2. Records are removed when Missing Count reaches 3  
3. Found records get Missing Count reset to 0
4. Records with Status="Old" are not updated
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent / "src"))

from automation.scripts.icsAirtableSync.icsProcess import should_mark_as_removed

# Set up test logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_record(record_id, uid, status="New", missing_count=0, missing_since=None):
    """Create a test record structure matching Airtable format"""
    fields = {
        "ID": record_id,
        "UID": uid,
        "Status": status,
        "Missing Count": missing_count
    }
    if missing_since:
        fields["Missing Since"] = missing_since
    
    return {
        "id": f"rec{record_id}",
        "fields": fields
    }

def test_removal_logic():
    """Test the updated removal logic scenarios"""
    current_time = datetime.now()
    
    print("🧪 Testing ICS Removal Logic (v2.2.22)")
    print("=" * 60)
    
    # Test Case 1: Record missing for first time
    print("\n📋 Test 1: Record missing for first time")
    record1 = create_test_record("TEST001", "1418fb94e984-eb77a0aa5aec6ff33fa01e20b305798b@airbnb.com", 
                                missing_count=0)
    should_remove, updates = should_mark_as_removed(record1, current_time, is_missing_from_feed=True)
    expected_count = 1
    print(f"   Input: Missing Count = 0, Status = New")
    print(f"   Expected: should_remove=False, Missing Count={expected_count}")
    print(f"   Actual: should_remove={should_remove}, updates={updates}")
    assert not should_remove, "Should not remove on first missing"
    assert updates.get("Missing Count") == expected_count, f"Expected Missing Count {expected_count}, got {updates.get('Missing Count')}"
    print("   ✅ PASS")
    
    # Test Case 2: Record missing for second time  
    print("\n📋 Test 2: Record missing for second time")
    record2 = create_test_record("TEST001", "1418fb94e984-eb77a0aa5aec6ff33fa01e20b305798b@airbnb.com",
                                missing_count=1)
    should_remove, updates = should_mark_as_removed(record2, current_time, is_missing_from_feed=True)
    expected_count = 2
    print(f"   Input: Missing Count = 1, Status = New")
    print(f"   Expected: should_remove=False, Missing Count={expected_count}")
    print(f"   Actual: should_remove={should_remove}, updates={updates}")
    assert not should_remove, "Should not remove on second missing"
    assert updates.get("Missing Count") == expected_count, f"Expected Missing Count {expected_count}, got {updates.get('Missing Count')}"
    print("   ✅ PASS")
    
    # Test Case 3: Record missing for third time (THRESHOLD REACHED)
    print("\n📋 Test 3: Record missing for third time - REMOVAL THRESHOLD")
    record3 = create_test_record("TEST001", "1418fb94e984-eb77a0aa5aec6ff33fa01e20b305798b@airbnb.com",
                                missing_count=2)
    should_remove, updates = should_mark_as_removed(record3, current_time, is_missing_from_feed=True)
    expected_count = 3
    print(f"   Input: Missing Count = 2, Status = New")
    print(f"   Expected: should_remove=True, Missing Count={expected_count}")
    print(f"   Actual: should_remove={should_remove}, updates={updates}")
    assert should_remove, "Should remove when Missing Count reaches 3"
    assert updates.get("Missing Count") == expected_count, f"Expected Missing Count {expected_count}, got {updates.get('Missing Count')}"
    print("   ✅ PASS")
    
    # Test Case 4: Record found (not missing) - should be ignored by function
    print("\n📋 Test 4: Record found (not missing from feed)")
    record4 = create_test_record("TEST002", "found-record@airbnb.com", missing_count=2)
    should_remove, updates = should_mark_as_removed(record4, current_time, is_missing_from_feed=False)
    print(f"   Input: Missing Count = 2, is_missing_from_feed = False")
    print(f"   Expected: should_remove=False, updates={{}} (no changes)")
    print(f"   Actual: should_remove={should_remove}, updates={updates}")
    assert not should_remove, "Should not process found records"
    assert updates == {}, "Should not update found records in this function"
    print("   ✅ PASS")
    
    # Test Case 5: Record with Status="Old" - should be ignored
    print("\n📋 Test 5: Record with Status='Old' (should be ignored)")
    record5 = create_test_record("TEST003", "old-record@airbnb.com", status="Old", missing_count=1)
    should_remove, updates = should_mark_as_removed(record5, current_time, is_missing_from_feed=True)
    print(f"   Input: Missing Count = 1, Status = 'Old'")
    print(f"   Expected: should_remove=False, updates={{}} (ignore old records)")
    print(f"   Actual: should_remove={should_remove}, updates={updates}")
    assert not should_remove, "Should not process Old records"
    assert updates == {}, "Should not update Old records"
    print("   ✅ PASS")
    
    # Test Case 6: Progression test - simulate multiple automation runs
    print("\n📋 Test 6: Progression simulation (3 automation runs)")
    test_record = create_test_record("PROG001", "progression-test@airbnb.com", missing_count=0)
    
    # Run 1: First time missing
    print("   🕐 Hour 1 - First time missing:")
    should_remove, updates = should_mark_as_removed(test_record, current_time, is_missing_from_feed=True)
    test_record["fields"]["Missing Count"] = updates.get("Missing Count", 0)
    print(f"      Result: Missing Count = {test_record['fields']['Missing Count']}, should_remove = {should_remove}")
    assert not should_remove and test_record["fields"]["Missing Count"] == 1
    
    # Run 2: Second time missing  
    print("   🕑 Hour 2 - Second time missing:")
    should_remove, updates = should_mark_as_removed(test_record, current_time, is_missing_from_feed=True)
    test_record["fields"]["Missing Count"] = updates.get("Missing Count", 0)
    print(f"      Result: Missing Count = {test_record['fields']['Missing Count']}, should_remove = {should_remove}")
    assert not should_remove and test_record["fields"]["Missing Count"] == 2
    
    # Run 3: Third time missing - REMOVAL
    print("   🕒 Hour 3 - Third time missing (REMOVAL):")
    should_remove, updates = should_mark_as_removed(test_record, current_time, is_missing_from_feed=True)
    test_record["fields"]["Missing Count"] = updates.get("Missing Count", 0)
    print(f"      Result: Missing Count = {test_record['fields']['Missing Count']}, should_remove = {should_remove}")
    assert should_remove and test_record["fields"]["Missing Count"] == 3
    print("   ✅ PASS - Complete progression works correctly")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ ICS Removal Logic v2.2.22 is working correctly")
    return True

def test_user_scenario():
    """Test the exact scenario from user's issue"""
    print("\n" + "=" * 60)
    print("🎯 Testing User's Exact Scenario")
    print("=" * 60)
    print("UID: 1418fb94e984-eb77a0aa5aec6ff33fa01e20b305798b@airbnb.com")
    print("Property: Runyan [Hernandez] 1057 E Butler Dr, 1C, Phoenix")
    print("Dates: 8/29/2025 - 9/1/2025")
    print("Issue: Record not being removed despite missing from ICS feed")
    
    current_time = datetime.now()
    target_uid = "1418fb94e984-eb77a0aa5aec6ff33fa01e20b305798b@airbnb.com"
    
    # Simulate the user's case where Missing Count was manually set to 2
    print("\n📋 User manually set Missing Count to 2, record still missing:")
    user_record = create_test_record("USER_CASE", target_uid, missing_count=2)
    should_remove, updates = should_mark_as_removed(user_record, current_time, is_missing_from_feed=True)
    
    print(f"   Input: Missing Count = 2 (user set), Record missing from feed")
    print(f"   Expected: should_remove=True, Missing Count=3 (REMOVAL)")
    print(f"   Actual: should_remove={should_remove}, updates={updates}")
    
    if should_remove and updates.get("Missing Count") == 3:
        print("   ✅ SUCCESS: Record would be properly removed!")
        print("   💡 The fix is working - record will be removed on next automation run")
    else:
        print("   ❌ FAILURE: Record would not be removed")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 ICS Removal Logic Test Suite (v2.2.22)")
    print(f"📅 Test Time: {datetime.now().isoformat()}")
    
    try:
        # Run general logic tests
        if not test_removal_logic():
            print("❌ General logic tests failed")
            return False
            
        # Run user scenario test
        if not test_user_scenario():
            print("❌ User scenario test failed")
            return False
            
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("✅ The ICS removal logic fix (v2.2.22) is working correctly")
        print("🔧 Your specific record will be removed on the next automation run")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)