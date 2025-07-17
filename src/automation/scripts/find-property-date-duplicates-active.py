#!/usr/bin/env python3
"""
Find cases where the same property and dates have multiple different UIDs 
that are all in active statuses (New/Modified/Removed).

This catches situations where:
- Same property
- Same check-in and check-out dates
- Different UIDs
- Multiple records with active statuses

This violates the business rule that there should only be one active reservation
for a given property and date range.
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.automation.config_wrapper import Config
from pyairtable import Api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def find_property_date_duplicates_active(fix=False):
    """Find properties with multiple active UIDs for same dates."""
    
    # Initialize Airtable
    api = Api(Config.get_airtable_api_key())
    base = api.base(Config.get_airtable_base_id())
    table = base.table('Reservations')
    
    logging.info(f"Searching for property/date duplicates with multiple active UIDs...")
    
    # Get all records with active statuses
    formula = "OR({Status} = 'New', {Status} = 'Modified', {Status} = 'Removed')"
    
    active_records = table.all(formula=formula)
    logging.info(f"Found {len(active_records)} total active records")
    
    # Group by (property_id, checkin, checkout, entry_type)
    records_by_key = defaultdict(list)
    
    for record in active_records:
        fields = record['fields']
        
        # Get property ID
        property_ids = fields.get('Property ID', [])
        if not property_ids:
            continue
        property_id = property_ids[0]
        
        # Get dates
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        entry_type = fields.get('Entry Type', 'Reservation')
        
        if not (checkin and checkout):
            continue
        
        # Create key
        key = (property_id, checkin, checkout, entry_type)
        records_by_key[key].append(record)
    
    # Find keys with multiple different UIDs
    duplicates = {}
    total_duplicate_records = 0
    
    for key, records in records_by_key.items():
        if len(records) > 1:
            # Check if they have different UIDs
            uids = set(r['fields'].get('Reservation UID', '') for r in records)
            if len(uids) > 1:
                duplicates[key] = records
                total_duplicate_records += len(records)
    
    logging.info(f"\nFound {len(duplicates)} property/date combinations with multiple active UIDs")
    logging.info(f"Total duplicate records involved: {total_duplicate_records}")
    
    # Show details for each duplicate group
    updates_to_make = []
    
    for key, records in sorted(duplicates.items(), key=lambda x: (x[0][1], x[0][0])):  # Sort by date, then property
        property_id, checkin, checkout, entry_type = key
        
        # Get property name from first record
        property_name = records[0]['fields'].get('HCP Address (from Property ID)', ['Unknown'])[0]
        
        logging.info(f"\n{'='*60}")
        logging.info(f"Property: {property_name} ({property_id})")
        logging.info(f"Dates: {checkin} to {checkout}")
        logging.info(f"Entry Type: {entry_type}")
        logging.info(f"Active records: {len(records)} with {len(set(r['fields'].get('Reservation UID', '') for r in records))} different UIDs")
        
        # Sort by Last Updated (newest first), then by ID (highest first)
        records.sort(key=lambda r: (
            r['fields'].get('Last Updated', ''),
            -r['fields'].get('ID', 0)
        ), reverse=True)
        
        # Group by UID to show the problem clearly
        by_uid = defaultdict(list)
        for record in records:
            uid = record['fields'].get('Reservation UID', 'NO_UID')
            by_uid[uid].append(record)
        
        logging.info(f"\nUIDs found:")
        keep_record = records[0]  # Keep the most recent overall
        
        for uid, uid_records in by_uid.items():
            logging.info(f"  UID: {uid}")
            for record in uid_records:
                fields = record['fields']
                is_keeper = (record['id'] == keep_record['id'])
                marker = "KEEP" if is_keeper else "FIX"
                
                logging.info(f"    [{marker}] ID {fields.get('ID')}: Status={fields.get('Status')}, "
                            f"Source={fields.get('Entry Source', 'Unknown')}, "
                            f"Updated={fields.get('Last Updated', 'Unknown')}")
                
                if not is_keeper:
                    updates_to_make.append({
                        'id': record['id'],
                        'current_status': fields.get('Status'),
                        'record_id': fields.get('ID'),
                        'uid': uid
                    })
    
    # Summary
    logging.info(f"\n{'='*60}")
    logging.info(f"SUMMARY:")
    logging.info(f"Total property/date combinations with issues: {len(duplicates)}")
    logging.info(f"Total records that need fixing: {len(updates_to_make)}")
    
    if fix and updates_to_make:
        logging.info(f"\nFixing {len(updates_to_make)} records by marking them as Old...")
        
        # Update in batches
        batch_size = 10
        for i in range(0, len(updates_to_make), batch_size):
            batch = updates_to_make[i:i+batch_size]
            batch_updates = []
            
            for update in batch:
                batch_updates.append({
                    'id': update['id'],
                    'fields': {
                        'Status': 'Old',
                        'Last Updated': datetime.now().isoformat()
                    }
                })
            
            table.batch_update(batch_updates)
            logging.info(f"  Updated batch {i//batch_size + 1}/{(len(updates_to_make) + batch_size - 1)//batch_size}")
        
        logging.info("✅ All duplicates fixed!")
    elif not fix and updates_to_make:
        logging.info("\n💡 To fix these issues, run with --fix flag")
    else:
        logging.info("\n✅ No property/date duplicates with multiple active UIDs found!")
    
    return len(duplicates), len(updates_to_make)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Find property/date combinations with multiple active UIDs'
    )
    parser.add_argument('--fix', action='store_true', 
                        help='Fix the duplicates by marking older records as Old')
    args = parser.parse_args()
    
    find_property_date_duplicates_active(fix=args.fix)