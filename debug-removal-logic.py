#!/usr/bin/env python3
"""
Debug script to test the exact removal logic for record 37717.
This will simulate what the ICS processor should be doing.
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

def main():
    # Initialize Airtable
    api = Api(os.getenv('PROD_AIRTABLE_API_KEY'))
    base = api.base(os.getenv('PROD_AIRTABLE_BASE_ID'))
    reservations_table = base.table('Reservations')
    
    # The specific feed we're testing
    test_url = "https://www.airbnb.com.au/calendar/ical/33374849.ics?s=5b15ff2b078140ad2cb1ea3ef5a261a6"
    property_id = "recVu3YtfTaoK3siK"
    
    print("=" * 80)
    print("DEBUGGING REMOVAL LOGIC FOR RECORD 37717")
    print("=" * 80)
    
    # Step 1: Get current ICS UIDs
    print(f"\n1. FETCHING CURRENT ICS FEED:")
    print(f"   URL: {test_url}")
    current_ics_uids = fetch_current_ics_uids(test_url)
    print(f"   Current UIDs in feed: {len(current_ics_uids)}")
    for uid in current_ics_uids:
        print(f"     - {uid}")
    
    # Step 2: Simulate get_records_by_uid_feed for this specific feed
    print(f"\n2. FETCHING EXISTING AIRTABLE RECORDS:")
    all_records = reservations_table.all(
        formula=f"{{ICS URL}} = '{test_url}'",
        fields=['ID', 'Reservation UID', 'ICS URL', 'Status', 'Check-in Date', 'Check-out Date', 'Entry Type', 'Property ID']
    )
    
    print(f"   Found {len(all_records)} records for this feed")
    
    # Build existing_records dictionary like the real code
    existing_records = defaultdict(list)
    for record in all_records:
        fields = record.get("fields", {})
        res_uid = fields.get("Reservation UID")
        feed = fields.get("ICS URL")
        if res_uid and feed:
            existing_records[(res_uid, feed)].append(record)
            print(f"     Record ID {fields.get('ID')}: UID='{res_uid}', Status={fields.get('Status')}")
    
    # Step 3: Simulate processed_uid_url_pairs (what would be created from current ICS)
    print(f"\n3. SIMULATING PROCESSED_UID_URL_PAIRS:")
    processed_uid_url_pairs = set()
    for ics_uid in current_ics_uids:
        composite_uid = f"{ics_uid}_{property_id}"
        processed_uid_url_pairs.add((composite_uid, test_url))
        print(f"     Processed: {composite_uid}")
    
    # Step 4: Simulate removal detection logic
    print(f"\n4. REMOVAL DETECTION LOGIC:")
    
    # Get all UIDs for this feed URL (like the real code)
    feed_keys = [(uid, feed_url) for uid, feed_url in existing_records.keys() if feed_url == test_url]
    print(f"   Feed keys found: {len(feed_keys)}")
    for uid, feed_url in feed_keys:
        print(f"     - {uid}")
    
    # Find missing keys (like the real code)
    missing_keys = [pair for pair in feed_keys if pair not in processed_uid_url_pairs]
    print(f"\n   Missing keys (should be removed): {len(missing_keys)}")
    for uid, feed_url in missing_keys:
        print(f"     - {uid}")
    
    # Step 5: Check each missing key
    print(f"\n5. CHECKING REMOVAL CONDITIONS:")
    today_iso = date.today().isoformat()
    print(f"   Today: {today_iso}")
    
    for uid, feed_url in missing_keys:
        print(f"\n   Checking UID: {uid}")
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
                print(f"       ❌ SKIPPED - checkout date is in past")
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
                
                # Simulate duplicate_detected_dates (would contain current ICS event dates)
                duplicate_detected_dates = set()
                for ics_uid in current_ics_uids:
                    # For this test, we know the current event is July 20 - Aug 18
                    duplicate_detected_dates.add((property_id, "2025-07-20", "2025-08-18", "Reservation"))
                
                print(f"       Duplicate detected dates: {duplicate_detected_dates}")
                
                if duplicate_key in duplicate_detected_dates:
                    print(f"       ❌ SKIPPED - matches duplicate detection")
                    continue
                else:
                    print(f"       ✅ WOULD BE REMOVED - no duplicate match")
            else:
                print(f"       ✅ WOULD BE REMOVED - no property ID check")

if __name__ == "__main__":
    main()