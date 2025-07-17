#!/usr/bin/env python3
"""
Find orphaned ICS records that have mismatched UIDs and are stuck in 'New' status.
These are records that won't be marked as 'Old' by the ICS processor because their UIDs
don't match what's currently in the ICS feed.
"""

import os
import sys
from datetime import datetime, date
from pyairtable import Api
from dotenv import load_dotenv

# Load production environment
load_dotenv('/home/opc/automation/config/environments/prod/.env')

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
    
    # Create a map of ICS URLs to property IDs
    url_to_properties = {}
    for feed in ics_feeds:
        url = feed['fields'].get('ICS URL')
        prop_ids = feed['fields'].get('Property Name', [])
        if url and prop_ids:
            url_to_properties[url] = prop_ids
    
    print(f"Found {len(url_to_properties)} active ICS feeds")
    
    # Fetch all reservations with 'New' status
    print("\nFetching all 'New' status reservations...")
    new_reservations = reservations_table.all(
        formula="{Status} = 'New'",
        fields=['ID', 'Reservation UID', 'ICS URL', 'Property ID', 'Check-in Date', 
                'Check-out Date', 'Entry Type', 'Last Updated', 'Entry Source']
    )
    
    print(f"Found {len(new_reservations)} reservations with 'New' status")
    
    # Group reservations by ICS URL
    reservations_by_url = {}
    for res in new_reservations:
        fields = res['fields']
        ics_url = fields.get('ICS URL')
        if ics_url:
            if ics_url not in reservations_by_url:
                reservations_by_url[ics_url] = []
            reservations_by_url[ics_url].append(res)
    
    # Analyze potential orphans
    print("\nAnalyzing potential orphaned records...")
    print("=" * 80)
    
    orphaned_records = []
    today = date.today().isoformat()
    
    for url, reservations in reservations_by_url.items():
        if url not in url_to_properties:
            # This ICS URL is not in active feeds
            for res in reservations:
                fields = res['fields']
                checkout = fields.get('Check-out Date', '')
                if checkout >= today:  # Only care about future reservations
                    orphaned_records.append(res)
                    print(f"\nOrphaned Record Found:")
                    print(f"  ID: {fields.get('ID')}")
                    print(f"  Record ID: {res['id']}")
                    print(f"  UID: {fields.get('Reservation UID')}")
                    print(f"  Property: {fields.get('Property ID', ['Unknown'])[0]}")
                    print(f"  Dates: {fields.get('Check-in Date')} to {fields.get('Check-out Date')}")
                    print(f"  ICS URL: {url}")
                    print(f"  Last Updated: {fields.get('Last Updated')}")
                    print(f"  Entry Source: {fields.get('Entry Source')}")
                    print(f"  Reason: ICS feed is no longer active")
        else:
            # Check for UID pattern mismatches
            for res in reservations:
                fields = res['fields']
                uid = fields.get('Reservation UID', '')
                checkout = fields.get('Check-out Date', '')
                
                if checkout < today:
                    continue
                
                # Check if this looks like a composite UID with wrong base
                if '_rec' in uid:
                    base_uid = uid.split('_')[0]
                    # Check if any other record has same property/dates but different base UID
                    prop_ids = fields.get('Property ID', [])
                    if prop_ids:
                        prop_id = prop_ids[0]
                        checkin = fields.get('Check-in Date')
                        checkout = fields.get('Check-out Date')
                        
                        # Look for other records with same property/dates
                        for other_res in reservations:
                            if other_res['id'] == res['id']:
                                continue
                            other_fields = other_res['fields']
                            other_prop_ids = other_fields.get('Property ID', [])
                            if (other_prop_ids and other_prop_ids[0] == prop_id and
                                other_fields.get('Check-in Date') == checkin and
                                other_fields.get('Check-out Date') == checkout):
                                
                                other_uid = other_fields.get('Reservation UID', '')
                                if '_rec' in other_uid:
                                    other_base_uid = other_uid.split('_')[0]
                                    if base_uid != other_base_uid:
                                        orphaned_records.append(res)
                                        print(f"\nOrphaned Record Found (UID Mismatch):")
                                        print(f"  ID: {fields.get('ID')}")
                                        print(f"  Record ID: {res['id']}")
                                        print(f"  UID: {uid}")
                                        print(f"  Base UID: {base_uid}")
                                        print(f"  Property: {prop_id}")
                                        print(f"  Dates: {checkin} to {checkout}")
                                        print(f"  Conflicting ID: {other_fields.get('ID')}")
                                        print(f"  Conflicting UID: {other_uid}")
                                        print(f"  Last Updated: {fields.get('Last Updated')}")
                                        print(f"  Entry Source: {fields.get('Entry Source')}")
                                        break
    
    print(f"\n{'=' * 80}")
    print(f"Total orphaned records found: {len(orphaned_records)}")
    
    if orphaned_records:
        print("\nThese records will remain in 'New' status indefinitely because:")
        print("1. Their UIDs don't match any current ICS feed events")
        print("2. The ICS processor only marks records as 'Old' if it previously saw their UID")
        print("3. These are likely from CSV imports, manual entries, or Airbnb UID changes")
        
        # Group by property for summary
        by_property = {}
        for rec in orphaned_records:
            prop_ids = rec['fields'].get('Property ID', ['Unknown'])
            prop = prop_ids[0] if prop_ids else 'Unknown'
            if prop not in by_property:
                by_property[prop] = 0
            by_property[prop] += 1
        
        print(f"\nOrphaned records by property:")
        for prop, count in sorted(by_property.items(), key=lambda x: x[1], reverse=True):
            print(f"  {prop}: {count} records")

if __name__ == "__main__":
    main()