#!/usr/bin/env python3
"""
Find records with UID patterns that suggest they won't be handled by ICS processor.
Specifically looking for records like 37717 where the same property/dates have multiple UIDs.
"""

import os
from datetime import date
from pyairtable import Api
from dotenv import load_dotenv
from collections import defaultdict

# Load production environment
load_dotenv('/home/opc/automation/config/environments/prod/.env')

def main():
    # Initialize Airtable
    api = Api(os.getenv('PROD_AIRTABLE_API_KEY'))
    base = api.base(os.getenv('PROD_AIRTABLE_BASE_ID'))
    reservations_table = base.table('Reservations')
    
    print("Fetching all 'New' status reservations...")
    new_reservations = reservations_table.all(
        formula="{Status} = 'New'",
        fields=['ID', 'Reservation UID', 'ICS URL', 'Property ID', 'Check-in Date', 
                'Check-out Date', 'Entry Type', 'Last Updated', 'Entry Source',
                'HCP Address (from Property ID)']
    )
    
    print(f"Found {len(new_reservations)} reservations with 'New' status")
    
    # Group by property + dates to find duplicates
    by_property_dates = defaultdict(list)
    today = date.today().isoformat()
    
    for res in new_reservations:
        fields = res['fields']
        checkout = fields.get('Check-out Date', '')
        if checkout < today:
            continue
            
        prop_ids = fields.get('Property ID', [])
        if not prop_ids:
            continue
            
        prop_id = prop_ids[0]
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        entry_type = fields.get('Entry Type', '')
        
        key = (prop_id, checkin, checkout, entry_type)
        by_property_dates[key].append(res)
    
    print("\nLooking for properties with multiple 'New' records for same dates...")
    print("=" * 80)
    
    problematic_records = []
    
    for key, records in by_property_dates.items():
        if len(records) > 1:
            # Multiple records for same property/dates
            prop_id, checkin, checkout, entry_type = key
            
            # Extract unique base UIDs
            base_uids = set()
            for rec in records:
                uid = rec['fields'].get('Reservation UID', '')
                base_uid = uid.split('_')[0] if '_' in uid else uid
                base_uids.add(base_uid)
            
            if len(base_uids) > 1:
                # Different base UIDs = likely orphaned records
                print(f"\nProperty with conflicting UIDs:")
                print(f"  Property: {records[0]['fields'].get('HCP Address (from Property ID)', ['Unknown'])[0] if records[0]['fields'].get('HCP Address (from Property ID)') else prop_id}")
                print(f"  Dates: {checkin} to {checkout}")
                print(f"  Entry Type: {entry_type}")
                print(f"  Number of records: {len(records)}")
                
                # Sort by Last Updated to find which is older
                records_sorted = sorted(records, key=lambda r: r['fields'].get('Last Updated', ''))
                
                for i, rec in enumerate(records_sorted):
                    fields = rec['fields']
                    uid = fields.get('Reservation UID', '')
                    base_uid = uid.split('_')[0] if '_' in uid else uid
                    
                    print(f"\n  Record {i+1}:")
                    print(f"    ID: {fields.get('ID')}")
                    print(f"    Record ID: {rec['id']}")
                    print(f"    Full UID: {uid}")
                    print(f"    Base UID: {base_uid}")
                    print(f"    ICS URL: {fields.get('ICS URL', 'None')}")
                    print(f"    Last Updated: {fields.get('Last Updated')}")
                    print(f"    Entry Source: {fields.get('Entry Source')}")
                    
                    if i < len(records_sorted) - 1:
                        problematic_records.append(rec)
                        print(f"    ** LIKELY ORPHANED - older duplicate **")
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY:")
    print(f"Total likely orphaned records (older duplicates): {len(problematic_records)}")
    
    if problematic_records:
        print(f"\nThese {len(problematic_records)} records are likely orphaned because:")
        print("1. They have the same property/dates as newer records")
        print("2. They have different base UIDs (suggesting Airbnb changed the UID)")
        print("3. The ICS processor won't mark them as 'Old' because it only tracks UIDs it has seen")
        
        # Group by ICS URL
        by_ics_url = defaultdict(int)
        for rec in problematic_records:
            url = rec['fields'].get('ICS URL', 'No ICS URL')
            by_ics_url[url] += 1
        
        print("\nOrphaned records by ICS URL:")
        for url, count in sorted(by_ics_url.items(), key=lambda x: x[1], reverse=True):
            print(f"  {url}: {count} records")

if __name__ == "__main__":
    main()