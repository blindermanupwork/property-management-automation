#!/usr/bin/env python3
"""Test the fix for Same-day Turnover None values"""

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Simulate the fixed cloning logic
WRITE_BLACKLIST = {
    "Final Service Time",
    "Sync Date and Time", 
    "Service Sync Details"
}

def mark_all_as_old_and_clone_fixed(old_f, field_to_change, status="Modified"):
    """Simulated fixed version of the clone function"""
    # Build clone (copy everything except blacklist)
    clone = {k: v for k, v in old_f.items() if k not in WRITE_BLACKLIST}
    
    # Apply the changes and status
    clone.update(Status=status, **field_to_change, **{"Last Updated": "2025-07-11T16:00:00Z"})
    
    # CRITICAL FIX: Ensure boolean fields are never None in cloned records
    boolean_fields = ["Same-day Turnover", "Overlapping Dates"]
    for field in boolean_fields:
        if field not in field_to_change and field in clone and clone[field] is None:
            clone[field] = False
            logging.info(f"🔧 FIX: Converted {field} from None to False in cloned record")
    
    # DEBUG: Log exactly what we're creating
    if "Same-day Turnover" in clone:
        logging.info(f"🔍 DEBUG: Creating clone with Same-day Turnover = {clone['Same-day Turnover']} (type: {type(clone['Same-day Turnover'])})")
    
    return clone

# Test Case 1: Old record has None, field_to_change doesn't include Same-day
print("=== Test Case 1: Old record with None, no Same-day in changes ===")
old_record1 = {
    "ID": 37190,
    "Status": "Old",
    "Same-day Turnover": None,
    "Overlapping Dates": None,
    "Service Line Description": "Turnover STR Next Guest Unknown",
    "Check-in Date": "2025-07-11",
    "Check-out Date": "2025-07-16",
}

field_to_change1 = {
    "Check-in Date": "2025-07-11",
    "Check-out Date": "2025-07-16",
}

result1 = mark_all_as_old_and_clone_fixed(old_record1, field_to_change1)
print(f"Result: Same-day = {result1.get('Same-day Turnover')} (should be False)")
print(f"        Overlapping = {result1.get('Overlapping Dates')} (should be False)")

# Test Case 2: Old record has None, field_to_change includes Same-day = True
print("\n=== Test Case 2: Old record with None, Same-day = True in changes ===")
field_to_change2 = {
    "Check-in Date": "2025-07-11",
    "Check-out Date": "2025-07-16",
    "Same-day Turnover": True,
    "Overlapping Dates": False,
}

result2 = mark_all_as_old_and_clone_fixed(old_record1, field_to_change2)
print(f"Result: Same-day = {result2.get('Same-day Turnover')} (should be True)")
print(f"        Overlapping = {result2.get('Overlapping Dates')} (should be False)")

# Test Case 3: Old record already has boolean values
print("\n=== Test Case 3: Old record with existing boolean values ===")
old_record3 = {
    "ID": 37926,
    "Status": "Old",
    "Same-day Turnover": True,
    "Overlapping Dates": False,
    "Service Line Description": "SAME DAY Turnover STR",
}

field_to_change3 = {
    "Service Line Description": "SAME DAY Turnover STR - Updated",
}

result3 = mark_all_as_old_and_clone_fixed(old_record3, field_to_change3)
print(f"Result: Same-day = {result3.get('Same-day Turnover')} (should be True)")
print(f"        Overlapping = {result3.get('Overlapping Dates')} (should be False)")