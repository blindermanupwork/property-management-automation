#!/usr/bin/env python3
"""
Test script to verify Service Type preservation logic
"""

# Test data
test_cases = [
    {
        "name": "Preserve Initial Service",
        "existing": "Initial Service",
        "new": "Turnover",
        "expected": "Initial Service",
        "should_preserve": True
    },
    {
        "name": "Preserve Deep Clean",
        "existing": "Deep Clean",
        "new": "Turnover",
        "expected": "Deep Clean",
        "should_preserve": True
    },
    {
        "name": "Allow change from default to custom",
        "existing": "Turnover",
        "new": "Initial Service",
        "expected": "Initial Service",
        "should_preserve": False
    },
    {
        "name": "Allow change between defaults",
        "existing": "Turnover",
        "new": "Needs Review",
        "expected": "Needs Review",
        "should_preserve": False
    },
    {
        "name": "Allow change from custom to another custom",
        "existing": "Initial Service",
        "new": "Deep Clean",
        "expected": "Deep Clean",
        "should_preserve": False
    },
    {
        "name": "Empty existing allows any change",
        "existing": "",
        "new": "Turnover",
        "expected": "Turnover",
        "should_preserve": False
    }
]

# Default service types
default_service_types = ["Turnover", "Needs Review", "Owner Arrival"]

print("Testing Service Type Preservation Logic\n")
print("=" * 60)

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"  Existing: '{test['existing']}'")
    print(f"  New:      '{test['new']}'")
    
    # Apply preservation logic
    preserve_service_type = (
        test['existing'] not in default_service_types and 
        test['new'] in default_service_types and
        test['existing'] != ""
    )
    
    if preserve_service_type:
        result = test['existing']  # Preserve existing
        print(f"  🛡️  PRESERVED")
    else:
        result = test['new']  # Use new value
        print(f"  ✏️  CHANGED")
    
    print(f"  Result:   '{result}'")
    print(f"  Expected: '{test['expected']}'")
    
    if result == test['expected']:
        print(f"  ✅ PASS")
    else:
        print(f"  ❌ FAIL")
    
    if preserve_service_type != test['should_preserve']:
        print(f"  ⚠️  Preservation logic mismatch!")

print("\n" + "=" * 60)
print("\nDefault Service Types:", default_service_types)
print("\nPreservation Rule:")
print("  - If existing is NOT a default value")
print("  - AND new value IS a default value")
print("  - AND existing is not empty")
print("  - THEN preserve the existing value")
print("\nThis prevents automated syncs from overwriting manual Service Type entries.")