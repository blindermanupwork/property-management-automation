#!/usr/bin/env python3
"""
Trace exactly why removal isn't happening for record 37717
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from automation.config_wrapper import Config
from datetime import date
from airtable import Airtable

# Use production config
os.environ['ENVIRONMENT'] = 'production'
from automation.config_prod import ProdConfig
config = ProdConfig()

# Initialize Airtable
airtable_base_id = config.get_airtable_base_id()
airtable_api_key = config.get_airtable_api_key()
table = Airtable(airtable_base_id, "Reservations", airtable_api_key)

def main():
    print("="*80)
    print("TRACING REMOVAL EXECUTION FOR RECORD 37717")
    print("="*80)
    
    # The specific feed and UID we're tracking
    feed_url = "https://www.airbnb.com.au/calendar/ical/33374849.ics?s=5b15ff2b078140ad2cb1ea3ef5a261a6"
    target_uid = "1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com_recVu3YtfTaoK3siK"
    
    print(f"\n1. FETCHING ALL RECORDS FOR FEED:")
    print(f"   {feed_url}")
    
    # Get all records for this feed
    formula = f"{{ICS URL}} = '{feed_url}'"
    all_records = table.get_all(formula=formula, fields=["ID", "Status", "Reservation UID", "Check-in Date", "Check-out Date"])
    
    print(f"\n2. FOUND {len(all_records)} RECORDS:")
    for rec in all_records:
        fields = rec["fields"]
        print(f"\n   ID: {fields.get('ID')}")
        print(f"   Status: {fields.get('Status')}")
        print(f"   UID: {fields.get('Reservation UID')}")
        print(f"   Dates: {fields.get('Check-in Date')} to {fields.get('Check-out Date')}")
    
    # Simulate existing_records dictionary
    existing_records = {}
    for rec in all_records:
        uid = rec["fields"].get("Reservation UID", "")
        if uid:
            key = (uid, feed_url)
            if key not in existing_records:
                existing_records[key] = []
            existing_records[key].append(rec)
    
    print(f"\n3. EXISTING_RECORDS KEYS:")
    for key in existing_records.keys():
        uid, url = key
        print(f"   {uid}")
    
    # Current events in feed (from our earlier check)
    current_uids = [
        "1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com_recVu3YtfTaoK3siK",
        "1418fb94e984-6a56b0697624e6d31fc2b44f698ca1eb@airbnb.com_recVu3YtfTaoK3siK",
        "7f662ec65913-9508399195d9b79b7e89754aba7ddb24@airbnb.com_recVu3YtfTaoK3siK"
    ]
    
    processed_uid_url_pairs = set()
    for uid in current_uids:
        processed_uid_url_pairs.add((uid, feed_url))
    
    print(f"\n4. CURRENT FEED UIDS:")
    for uid in current_uids:
        print(f"   {uid}")
    
    # Find missing keys
    feed_keys = [(uid, url) for uid, url in existing_records.keys() if url == feed_url]
    missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
    
    print(f"\n5. MISSING KEYS (should be removed): {len(missing_keys)}")
    for key in missing_keys:
        print(f"   {key[0]}")
    
    # Check removal conditions
    today_iso = date.today().isoformat()
    print(f"\n6. CHECKING REMOVAL CONDITIONS (today={today_iso}):")
    
    for uid, feed_url in missing_keys:
        records = existing_records.get((uid, feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        print(f"\n   UID: {uid}")
        print(f"   Total records: {len(records)}")
        print(f"   Active records: {len(active_records)}")
        
        for rec in active_records:
            fields = rec["fields"]
            record_id = fields.get("ID")
            checkout = fields.get("Check-out Date", "")
            checkin = fields.get("Check-in Date", "")
            
            print(f"\n   Record {record_id}:")
            print(f"     Checkout: {checkout}")
            print(f"     Checkout < today? {checkout < today_iso}")
            print(f"     Checkin: {checkin}")
            print(f"     Checkin >= today? {checkin >= today_iso}")
            
            if checkout < today_iso:
                print(f"     ❌ SKIPPED - checkout in past")
            elif checkin >= today_iso:
                print(f"     ❌ SKIPPED - checkin today or future")
            else:
                print(f"     ✅ SHOULD BE REMOVED")

if __name__ == "__main__":
    main()