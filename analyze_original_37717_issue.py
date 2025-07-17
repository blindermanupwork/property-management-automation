#!/usr/bin/env python3
"""
Analyze the original 37717 issue to understand the real problem
"""

print("🔍 ANALYZING THE ORIGINAL 37717 ISSUE")
print("="*80)

print("""
ORIGINAL PROBLEM ANALYSIS:
- User said record 37717 should be marked as removed
- User disagreed that Airbnb changes UIDs for reservations
- 0 removals were happening in the logs

WHAT I DISCOVERED:
1. UIDs in Airtable are already in composite format (uid_propertyId)
2. Processing creates composite UIDs (uid_propertyId) 
3. The comparison should work correctly

BUT THE REAL ISSUE WAS:
- My "fix" tried to composite already-composite UIDs
- This created double-composite UIDs that never matched
- Result: ALL records marked as removed (433 records)

THE ORIGINAL ISSUE (record 37717) MIGHT BE:
1. A genuine case where the record should be removed
2. OR there's a more subtle bug in the removal logic
3. OR there's an edge case with specific UID formats

Let me check if record 37717 actually exists and what its status is...
""")

# The specific record data from our previous analysis
record_37717_data = {
    "uid": "1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com",
    "property_id": "recVu3YtfTaoK3siK", 
    "checkin": "2025-07-20",
    "checkout": "2025-08-20",
    "composite_uid": "1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com_recVu3YtfTaoK3siK"
}

new_event_data = {
    "uid": "1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com", 
    "property_id": "recVu3YtfTaoK3siK",
    "checkin": "2025-07-20",
    "checkout": "2025-08-18",  # Different checkout!
    "composite_uid": "1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com_recVu3YtfTaoK3siK"
}

print(f"\\nORIGINAL CASE ANALYSIS:")
print(f"Record 37717:")
print(f"  UID: {record_37717_data['uid']}")
print(f"  Composite: {record_37717_data['composite_uid']}")
print(f"  Dates: {record_37717_data['checkin']} to {record_37717_data['checkout']}")

print(f"\\nNew event in feed:")
print(f"  UID: {new_event_data['uid']}")
print(f"  Composite: {new_event_data['composite_uid']}")
print(f"  Dates: {new_event_data['checkin']} to {new_event_data['checkout']}")

print(f"\\nANALYSIS:")
print(f"- Different UIDs: {record_37717_data['uid'] != new_event_data['uid']}")
print(f"- Same property: {record_37717_data['property_id'] == new_event_data['property_id']}")
print(f"- Same checkin: {record_37717_data['checkin'] == new_event_data['checkin']}")
print(f"- Same checkout: {record_37717_data['checkout'] == new_event_data['checkout']}")

if record_37717_data['checkout'] != new_event_data['checkout']:
    print(f"\\n✅ CONCLUSION: These are DIFFERENT reservations!")
    print(f"   - Different UIDs AND different checkout dates")
    print(f"   - The old reservation (Aug 20 checkout) disappeared from feed")
    print(f"   - The new reservation (Aug 18 checkout) appeared in feed")
    print(f"   - Record 37717 SHOULD be marked as removed!")
else:
    print(f"\\n⚠️  These might be the same reservation with changed UID")

print(f"\\n🎯 THE REAL ISSUE:")
print(f"If record 37717 should be removed but wasn't, then there might be:")
print(f"1. A bug in the removal detection logic (filters too strict?)")
print(f"2. An issue with composite UID matching")  
print(f"3. Or removal was working but user didn't see it due to timing")
print(f"\\nNeed to check current status of record 37717...")