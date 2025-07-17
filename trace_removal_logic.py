#!/usr/bin/env python3
"""
Trace the removal logic to find why 0 removals are happening
"""

import os
import sys
from datetime import date
from dateutil.relativedelta import relativedelta

# Simulate the removal detection section
print("TRACING REMOVAL DETECTION LOGIC")
print("="*80)

# Test data
url = "https://example.com/feed.ics"
uid = "1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com"
property_id = "recVu3YtfTaoK3siK"
composite_uid = f"{uid}_{property_id}"

# Simulate existing records
existing_records = {
    (composite_uid, url): [{
        "id": "rec37717",
        "fields": {
            "ID": "37717",
            "Status": "New",
            "Check-in Date": "2025-07-20",
            "Check-out Date": "2025-08-20",
            "Property ID": [property_id],
            "Entry Type": "Reservation",
            "Reservation UID": uid
        }
    }]
}

# Simulate processed UIDs (without the old UID)
processed_uid_url_pairs = set()
# New UID would be added during processing
new_uid = "1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com"
new_composite_uid = f"{new_uid}_{property_id}"
processed_uid_url_pairs.add((new_composite_uid, url))

print("1. Initial State:")
print(f"   Existing records: {len(existing_records)} keys")
print(f"   - Key: ({composite_uid}, {url})")
print(f"   Processed pairs: {len(processed_uid_url_pairs)} pairs")
print(f"   - Pair: ({new_composite_uid}, {url})")

# Get all UIDs for this feed URL
feed_keys = [(uid, feed_url) for uid, feed_url in existing_records.keys() if feed_url == url]
print(f"\n2. Feed Keys:")
print(f"   Found {len(feed_keys)} existing record keys for feed {url}")
for key in feed_keys:
    print(f"   - {key}")

# Find pairs that exist in Airtable but weren't in this feed
missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
print(f"\n3. Missing Keys:")
print(f"   Found {len(missing_keys)} missing keys that should be removed")
for key in missing_keys:
    print(f"   - {key}")

# Process missing keys
today_iso = date.today().isoformat()
future_cutoff = (date.today() + relativedelta(months=6)).isoformat()
removed_count = 0

print(f"\n4. Processing Missing Keys:")
print(f"   Today: {today_iso}")
print(f"   Future cutoff: {future_cutoff}")

for i, (uid, feed_url) in enumerate(missing_keys):
    print(f"\n   Processing key {i+1}: ({uid}, {feed_url})")
    records = existing_records.get((uid, feed_url), [])
    print(f"   - Found {len(records)} records")
    
    active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
    print(f"   - Active records: {len(active_records)}")
    
    for rec in active_records:
        fields = rec["fields"]
        record_id = fields.get("ID")
        checkin = fields.get("Check-in Date", "")
        checkout = fields.get("Check-out Date", "")
        
        print(f"\n   Checking record {record_id}:")
        print(f"   - Check-in: {checkin}")
        print(f"   - Check-out: {checkout}")
        
        # Check filters
        if checkout < today_iso:
            print(f"   ❌ SKIPPED - checkout date is in past")
            continue
            
        if checkin > future_cutoff:
            print(f"   ❌ SKIPPED - checkin >6 months future")
            continue
        
        # Check duplicate prevention
        duplicate_detected_dates = set()  # Would be populated during processing
        property_ids = fields.get("Property ID", [])
        if property_ids:
            record_property_id = property_ids[0]
            duplicate_key = (record_property_id, checkin, checkout, fields.get("Entry Type", ""))
            
            print(f"   - Checking duplicate key: {duplicate_key}")
            if duplicate_key in duplicate_detected_dates:
                print(f"   ❌ SKIPPED - detected as duplicate")
                continue
        
        print(f"   ✅ SHOULD BE REMOVED!")
        removed_count += 1

print(f"\n" + "="*80)
print(f"RESULT: {removed_count} records should be removed")