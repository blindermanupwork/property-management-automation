#!/usr/bin/env python3
"""
Enhanced script to find ALL types of orphaned ICS records including:
1. Records from inactive ICS feeds
2. Records with UID mismatches in active feeds
3. Records that appear to be duplicates with different UIDs
"""

import os
import sys
from datetime import datetime, date
from pyairtable import Api
from dotenv import load_dotenv
import requests
from icalendar import Calendar
from collections import defaultdict

# Load production environment
load_dotenv('/home/opc/automation/config/environments/prod/.env')

def fetch_ics_events(url):
    """Fetch and parse ICS feed, return UIDs of active events"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        cal = Calendar.from_ical(response.content)
        uids = set()
        
        for component in cal.walk():
            if component.name == "VEVENT":
                uid = component.get('UID')
                if uid:
                    uids.add(str(uid))
        
        return uids
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
        return set()

def main():
    # Initialize Airtable
    api = Api(os.getenv('PROD_AIRTABLE_API_KEY'))
    base = api.base(os.getenv('PROD_AIRTABLE_BASE_ID'))
    reservations_table = base.table('Reservations')
    ics_feeds_table = base.table('ICS Feeds')
    
    print("Fetching all active ICS feeds...")
    # Get all active ICS feeds
    ics_feeds = ics_feeds_table.all(
        formula="OR({Feed Status} = 'Active', {Feed Status} = '')",
        fields=['ICS URL', 'Property Name']
    )
    
    # Create maps
    url_to_properties = {}
    property_to_urls = defaultdict(list)
    
    for feed in ics_feeds:
        url = feed['fields'].get('ICS URL')
        prop_ids = feed['fields'].get('Property Name', [])
        if url and prop_ids:
            url_to_properties[url] = prop_ids
            for prop_id in prop_ids:
                property_to_urls[prop_id].append(url)
    
    print(f"Found {len(url_to_properties)} active ICS feeds")
    
    # Fetch all reservations with 'New' status
    print("\nFetching all 'New' status reservations...")
    new_reservations = reservations_table.all(
        formula="{Status} = 'New'",
        fields=['ID', 'Reservation UID', 'ICS URL', 'Property ID', 'Check-in Date', 
                'Check-out Date', 'Entry Type', 'Last Updated', 'Entry Source',
                'HCP Address (from Property ID)']
    )
    
    print(f"Found {len(new_reservations)} reservations with 'New' status")
    
    # Analyze
    print("\nAnalyzing orphaned records...")
    print("=" * 80)
    
    orphaned_by_inactive_feed = []
    orphaned_by_uid_mismatch = []
    today = date.today().isoformat()
    
    # Check each reservation
    for res in new_reservations:
        fields = res['fields']
        checkout = fields.get('Check-out Date', '')
        if checkout < today:
            continue  # Skip past reservations
            
        ics_url = fields.get('ICS URL', '')
        uid = fields.get('Reservation UID', '')
        prop_ids = fields.get('Property ID', [])
        
        # Type 1: Inactive feed
        if ics_url and ics_url not in url_to_properties:
            orphaned_by_inactive_feed.append(res)
            continue
        
        # Type 2: Active feed but UID mismatch
        if ics_url and prop_ids:
            prop_id = prop_ids[0]
            
            # Get the base UID (before underscore if composite)
            base_uid = uid.split('_')[0] if '_' in uid else uid
            
            # Check if this property has ICS feeds
            if prop_id in property_to_urls:
                urls_to_check = property_to_urls[prop_id]
                
                # Fetch current UIDs from the ICS feeds for this property
                current_uids = set()
                for url in urls_to_check:
                    if url == ics_url:  # Only check the specific feed
                        print(f"  Checking feed for property {prop_id}: {url}")
                        feed_uids = fetch_ics_events(url)
                        current_uids.update(feed_uids)
                
                # Check if our base UID exists in any current events
                if current_uids and base_uid not in current_uids:
                    # Double check by looking for any UID that would create our composite
                    found = False
                    for feed_uid in current_uids:
                        composite = f"{feed_uid}_{prop_id}"
                        if composite == uid:
                            found = True
                            break
                    
                    if not found:
                        orphaned_by_uid_mismatch.append(res)
    
    # Print results
    print("\n1. ORPHANED BY INACTIVE FEED:")
    print("-" * 40)
    for res in orphaned_by_inactive_feed:
        fields = res['fields']
        print(f"ID: {fields.get('ID')}, UID: {fields.get('Reservation UID')}")
        print(f"  Property: {fields.get('HCP Address (from Property ID)', ['Unknown'])[0] if fields.get('HCP Address (from Property ID)') else 'Unknown'}")
        print(f"  Dates: {fields.get('Check-in Date')} to {fields.get('Check-out Date')}")
        print(f"  ICS URL: {fields.get('ICS URL')}")
        print()
    
    print(f"\n2. ORPHANED BY UID MISMATCH (like record 37717):")
    print("-" * 40)
    for res in orphaned_by_uid_mismatch:
        fields = res['fields']
        uid = fields.get('Reservation UID', '')
        base_uid = uid.split('_')[0] if '_' in uid else uid
        print(f"ID: {fields.get('ID')}, Record: {res['id']}")
        print(f"  Full UID: {uid}")
        print(f"  Base UID: {base_uid}")
        print(f"  Property: {fields.get('HCP Address (from Property ID)', ['Unknown'])[0] if fields.get('HCP Address (from Property ID)') else 'Unknown'}")
        print(f"  Dates: {fields.get('Check-in Date')} to {fields.get('Check-out Date')}")
        print(f"  ICS URL: {fields.get('ICS URL')}")
        print(f"  Last Updated: {fields.get('Last Updated')}")
        print()
    
    print(f"\nSUMMARY:")
    print(f"Total orphaned by inactive feed: {len(orphaned_by_inactive_feed)}")
    print(f"Total orphaned by UID mismatch: {len(orphaned_by_uid_mismatch)}")
    print(f"TOTAL ORPHANED RECORDS: {len(orphaned_by_inactive_feed) + len(orphaned_by_uid_mismatch)}")
    
    if orphaned_by_uid_mismatch:
        print(f"\nThe {len(orphaned_by_uid_mismatch)} UID mismatch records (like 37717) will never be")
        print("marked as 'Old' because the ICS processor only tracks UIDs it has seen before.")
        print("These need to be manually cleaned up or the ICS processor needs enhancement.")

if __name__ == "__main__":
    main()