#!/usr/bin/env python3
"""
Diagnose why record 37717 is not being marked as removed
"""

import os
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

# Simulate the data
record_37717 = {
    "uid": "1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com",
    "property_id": "recVu3YtfTaoK3siK",
    "checkin": "2025-07-20",
    "checkout": "2025-08-20",
    "status": "New",
    "composite_uid": "1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com_recVu3YtfTaoK3siK"
}

# New event in feed
new_event = {
    "uid": "1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com",
    "property_id": "recVu3YtfTaoK3siK",
    "checkin": "2025-07-20",
    "checkout": "2025-08-18",
    "composite_uid": "1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com_recVu3YtfTaoK3siK"
}

print("ANALYZING RECORD 37717 REMOVAL")
print("="*80)

# Step 1: Check if these are duplicates
print("\n1. Duplicate Check:")
print(f"   Old: {record_37717['checkin']} to {record_37717['checkout']}")
print(f"   New: {new_event['checkin']} to {new_event['checkout']}")
print(f"   Same dates? {record_37717['checkin'] == new_event['checkin'] and record_37717['checkout'] == new_event['checkout']}")
print(f"   Result: NOT duplicates (different checkout dates)")

# Step 2: Processing simulation
print("\n2. Processing new event:")
processed_uid_url_pairs = set()
url = "https://example.com/feed.ics"

# Add new event to processed
processed_uid_url_pairs.add((new_event['composite_uid'], url))
print(f"   Added to processed: ({new_event['composite_uid']}, {url})")

# Step 3: Removal detection
print("\n3. Removal Detection:")
existing_records = {
    (record_37717['composite_uid'], url): [{"fields": {
        "ID": "37717",
        "Status": "New",
        "Check-in Date": record_37717['checkin'],
        "Check-out Date": record_37717['checkout'],
        "Property ID": [record_37717['property_id']]
    }}]
}

# Get feed keys
feed_keys = [(uid, feed_url) for uid, feed_url in existing_records.keys() if feed_url == url]
print(f"   Feed keys: {len(feed_keys)} records exist for this feed")

# Find missing keys
missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
print(f"   Missing keys: {len(missing_keys)} records not in processed set")

if missing_keys:
    print(f"   Missing: {missing_keys[0]}")
    
# Step 4: Check removal conditions
print("\n4. Removal Conditions:")
today_iso = date.today().isoformat()
future_cutoff = (date.today() + relativedelta(months=6)).isoformat()

print(f"   Today: {today_iso}")
print(f"   Checkout date: {record_37717['checkout']}")
print(f"   Checkout < today? {record_37717['checkout'] < today_iso} (should skip if true)")

print(f"\n   Checkin date: {record_37717['checkin']}")
print(f"   Future cutoff (6mo): {future_cutoff}")
print(f"   Checkin > 6mo future? {record_37717['checkin'] > future_cutoff} (should skip if true)")

# Step 5: Check duplicate_detected_dates
print("\n5. Duplicate Prevention Check:")
duplicate_detected_dates = set()
# If new event was processed as new (not duplicate), this would be empty
# If it was a duplicate, it would contain the property/date combo

duplicate_key = (record_37717['property_id'], record_37717['checkin'], record_37717['checkout'], "Reservation")
print(f"   Looking for: {duplicate_key}")
print(f"   In duplicate set? {duplicate_key in duplicate_detected_dates}")

print("\n" + "="*80)
print("CONCLUSION:")
if record_37717['checkout'] < today_iso:
    print("❌ Record 37717 would NOT be marked as removed - checkout is in the past")
elif record_37717['checkin'] > future_cutoff:
    print("❌ Record 37717 would NOT be marked as removed - checkin is >6 months future")
elif duplicate_key in duplicate_detected_dates:
    print("❌ Record 37717 would NOT be marked as removed - detected as duplicate")
else:
    print("✅ Record 37717 SHOULD be marked as removed!")
    print("   - Different UID, not in feed")
    print("   - Not a duplicate (different dates)")
    print("   - Passes all removal filters")