#!/usr/bin/env python3
"""Debug the cloning behavior with None values"""

# Simulate the cloning logic
WRITE_BLACKLIST = {
    "Final Service Time",
    "Sync Date and Time",
    "Service Sync Details"
}

# Simulate an old record with None value
old_record = {
    "ID": 37190,
    "Status": "Old",
    "Same-day Turnover": None,
    "Service Line Description": "Turnover STR Next Guest Unknown",
    "Check-in Date": "2025-07-11",
    "Check-out Date": "2025-07-16",
    "Entry Type": "Reservation",
    "Service Type": "Turnover",
}

# Build clone (copy everything except blacklist)
clone = {k: v for k, v in old_record.items() if k not in WRITE_BLACKLIST}

print("Original record:")
print(f"  Same-day Turnover: {old_record.get('Same-day Turnover')} (type: {type(old_record.get('Same-day Turnover'))})")

print("\nClone after copying:")
print(f"  Same-day Turnover: {clone.get('Same-day Turnover')} (type: {type(clone.get('Same-day Turnover'))})")

# Simulate field_to_change when flags haven't changed
field_to_change = {
    "Check-in Date": "2025-07-11",
    "Check-out Date": "2025-07-16",
    # Note: Same-day Turnover is NOT in field_to_change if it didn't change
}

# Apply changes
clone.update(Status="Modified", **field_to_change)

print("\nClone after update (without Same-day in field_to_change):")
print(f"  Same-day Turnover: {clone.get('Same-day Turnover')} (type: {type(clone.get('Same-day Turnover'))})")

# Now simulate when Same-day IS in field_to_change
field_to_change_with_sameday = {
    "Check-in Date": "2025-07-11",
    "Check-out Date": "2025-07-16",
    "Same-day Turnover": True,
}

clone2 = {k: v for k, v in old_record.items() if k not in WRITE_BLACKLIST}
clone2.update(Status="Modified", **field_to_change_with_sameday)

print("\nClone after update (WITH Same-day in field_to_change):")
print(f"  Same-day Turnover: {clone2.get('Same-day Turnover')} (type: {type(clone2.get('Same-day Turnover'))})")