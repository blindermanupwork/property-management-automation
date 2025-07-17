#!/usr/bin/env python3
"""
DETAILED debug script to understand exactly why record 37717 isn't being removed.
This will trace the exact removal logic execution.
"""

import os
from datetime import date
from pyairtable import Api
from dotenv import load_dotenv
from collections import defaultdict
import requests
from icalendar import Calendar

# Load production environment
load_dotenv('/home/opc/automation/config/environments/prod/.env')

def fetch_current_ics_uids(url):
    """Fetch current UIDs from the ICS feed"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        cal = Calendar.from_ical(response.content)
        uids = []
        
        for component in cal.walk():
            if component.name == "VEVENT":
                uid = component.get('UID')
                if uid:
                    uids.append(str(uid))
        
        return uids
    except Exception as e:
        print(f"Error fetching ICS: {e}")
        return []

def simulate_get_records_by_uid_feed(table, feed_url):
    """Simulate the exact logic of get_records_by_uid_feed for this specific feed"""
    by_feed = defaultdict(list)
    
    # Get all records for this feed
    all_records = table.all(
        formula=f"{{ICS URL}} = '{feed_url}'",
        fields=['ID', 'Reservation UID', 'ICS URL', 'Status', 'Check-in Date', 'Check-out Date', 'Entry Type', 'Property ID']
    )
    
    print(f"\n🔍 SIMULATING get_records_by_uid_feed():")
    print(f"   Found {len(all_records)} records for feed: {feed_url}")
    
    for record in all_records:
        fields = record.get("fields", {})
        res_uid = fields.get("Reservation UID")
        feed = fields.get("ICS URL")
        if res_uid and feed:
            key = (res_uid, feed)
            by_feed[key].append(record)
            print(f"   Added to existing_records: key=({res_uid}, {feed})")
            print(f"     Record ID: {fields.get('ID')}, Status: {fields.get('Status')}")
    
    return dict(by_feed)

def simulate_processed_uid_url_pairs(ics_uids, property_id, feed_url):
    """Simulate what processed_uid_url_pairs would contain"""
    processed = set()
    
    print(f"\n🔍 SIMULATING processed_uid_url_pairs creation:")
    for ics_uid in ics_uids:
        composite_uid = f"{ics_uid}_{property_id}"
        pair = (composite_uid, feed_url)
        processed.add(pair)
        print(f"   Added: ({composite_uid}, {feed_url})")
    
    return processed

def main():
    # Initialize Airtable
    api = Api(os.getenv('PROD_AIRTABLE_API_KEY'))
    base = api.base(os.getenv('PROD_AIRTABLE_BASE_ID'))
    reservations_table = base.table('Reservations')
    
    # The specific feed we're testing
    test_url = "https://www.airbnb.com.au/calendar/ical/33374849.ics?s=5b15ff2b078140ad2cb1ea3ef5a261a6"
    property_id = "recVu3YtfTaoK3siK"
    
    print("=" * 80)
    print("DETAILED REMOVAL LOGIC DEBUG FOR RECORD 37717")
    print("=" * 80)
    
    # Step 1: Get current ICS UIDs
    print(f"\n1. CURRENT ICS FEED CONTENT:")
    current_ics_uids = fetch_current_ics_uids(test_url)
    print(f"   Current UIDs in feed: {len(current_ics_uids)}")
    for uid in current_ics_uids:
        print(f"     - {uid}")
    
    # Step 2: Simulate existing_records (how the real code builds it)
    print(f"\n2. SIMULATING existing_records DICTIONARY:")
    existing_records = simulate_get_records_by_uid_feed(reservations_table, test_url)
    
    # Step 3: Simulate processed_uid_url_pairs
    print(f"\n3. SIMULATING processed_uid_url_pairs:")
    processed_uid_url_pairs = simulate_processed_uid_url_pairs(current_ics_uids, property_id, test_url)
    
    # Step 4: Exact removal logic simulation
    print(f"\n4. REMOVAL LOGIC EXECUTION:")
    
    # Get all UIDs for this feed URL (exact code from line 1278)
    feed_keys = [(uid, feed_url) for uid, feed_url in existing_records.keys() if feed_url == test_url]
    print(f"   feed_keys: {len(feed_keys)} keys found:")
    for i, (uid, feed_url) in enumerate(feed_keys):
        print(f"     {i+1}. ({uid}, {feed_url})")
    
    # Find pairs that exist in Airtable but weren't in this feed (exact code from line 1281)
    missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
    print(f"\n   missing_keys: {len(missing_keys)} keys should be removed:")
    for i, (uid, feed_url) in enumerate(missing_keys):
        print(f"     {i+1}. ({uid}, {feed_url})")
    
    # Check each missing key for removal conditions
    print(f"\n5. REMOVAL CONDITIONS CHECK:")
    today_iso = date.today().isoformat()
    print(f"   Today: {today_iso}")
    
    for uid, feed_url in missing_keys:
        print(f"\n   Checking missing key: {uid}")
        records = existing_records.get((uid, feed_url), [])
        active_records = [r for r in records if r["fields"].get("Status") in ("New", "Modified")]
        
        print(f"     Total records: {len(records)}")
        print(f"     Active records: {len(active_records)}")
        
        for rec in active_records:
            fields = rec["fields"]
            checkout = fields.get("Check-out Date", "")
            record_id = fields.get("ID")
            
            print(f"     Record {record_id}:")
            print(f"       Status: {fields.get('Status')}")
            print(f"       Checkout: {checkout}")
            print(f"       Checkout < today? {checkout < today_iso}")
            
            if checkout < today_iso:
                print(f"       ❌ WOULD BE SKIPPED - checkout date is in past")
                continue
            
            # Check duplicate detection logic
            property_ids = fields.get("Property ID", [])
            if property_ids:
                record_property_id = property_ids[0]
                record_checkin = fields.get("Check-in Date", "")
                record_checkout = fields.get("Check-out Date", "")
                record_entry_type = fields.get("Entry Type", "")
                
                duplicate_key = (record_property_id, record_checkin, record_checkout, record_entry_type)
                print(f"       Duplicate key: {duplicate_key}")
                
                # For this specific case, no current events exist with these dates
                print(f"       No current events match these dates")
                print(f"       ✅ SHOULD BE REMOVED - no duplicate match, future date")
            else:
                print(f"       ✅ SHOULD BE REMOVED - no property ID check needed")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY:")
    print(f"Total existing records: {len(existing_records)}")
    print(f"Total feed keys: {len(feed_keys)}")
    print(f"Total missing keys (should be removed): {len(missing_keys)}")
    print(f"If missing_keys > 0 and conditions pass, removal should occur")

if __name__ == "__main__":
    main()