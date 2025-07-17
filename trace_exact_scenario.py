#!/usr/bin/env python3
"""Trace the exact scenario that causes the issue"""

# Scenario: Record has None for Same-day, CSV says True, but only dates changed

# Airtable record
at_sameday_raw = None  # From Airtable
at_overlap_raw = None

# Convert using the same logic as the code
def convert_flag_value(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "checked", "t", "y", "1")
    return bool(value)

at_sameday = convert_flag_value(at_sameday_raw)
at_overlap = convert_flag_value(at_overlap_raw)

print(f"Airtable record:")
print(f"  Same-day raw: {at_sameday_raw} → converted: {at_sameday}")
print(f"  Overlap raw: {at_overlap_raw} → converted: {at_overlap}")

# CSV data
csv_sameday = True
csv_overlap = False

print(f"\nCSV data:")
print(f"  Same-day: {csv_sameday}")
print(f"  Overlap: {csv_overlap}")

# Check if flags changed
flags_changed = (at_overlap != csv_overlap or at_sameday != csv_sameday)

print(f"\nComparison:")
print(f"  Overlap: {at_overlap} != {csv_overlap} → {at_overlap != csv_overlap}")
print(f"  Same-day: {at_sameday} != {csv_sameday} → {at_sameday != csv_sameday}")
print(f"  flags_changed: {flags_changed}")

# If flags changed, Same-day WILL be in new_fields
if flags_changed:
    print("\n✅ Same-day Turnover WILL be included in new_fields because flags_changed = True")
else:
    print("\n❌ Same-day Turnover will NOT be included in new_fields")