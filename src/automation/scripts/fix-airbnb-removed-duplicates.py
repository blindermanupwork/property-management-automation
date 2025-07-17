#!/usr/bin/env python3
"""
Fix Airbnb reservations that have duplicate "Removed" status.
There should never be two active records (New/Modified/Removed) with the same property and dates.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.automation.config_wrapper import Config
from pyairtable import Api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def fix_removed_duplicates(dry_run=True):
    """Fix records where there are duplicate Removed statuses for same property/dates."""
    
    # Initialize Airtable
    api = Api(Config.get_airtable_api_key())
    base = api.base(Config.get_airtable_base_id())
    table = base.table('Reservations')
    
    logging.info(f"Fixing duplicate Removed records in {'DRY RUN' if dry_run else 'EXECUTE'} mode...")
    
    # The specific IDs mentioned by the user
    target_ids = [36853, 36855, 36856, 36858]
    
    # Get these specific records
    formula = f"OR({', '.join([f'{{ID}} = {id}' for id in target_ids])})"
    target_records = table.all(formula=formula)
    
    logging.info(f"Found {len(target_records)} target records")
    
    # Group by property and dates to find duplicates
    duplicates_by_key = {}
    
    for record in target_records:
        fields = record['fields']
        property_ids = fields.get('Property ID', [])
        if not property_ids:
            continue
            
        property_id = property_ids[0]
        checkin = fields.get('Check-in Date')
        checkout = fields.get('Check-out Date')
        status = fields.get('Status')
        
        key = (property_id, checkin, checkout)
        
        if key not in duplicates_by_key:
            duplicates_by_key[key] = []
        
        duplicates_by_key[key].append({
            'record': record,
            'id': fields.get('ID'),
            'uid': fields.get('Reservation UID'),
            'status': status
        })
    
    # Now find ALL records with these same keys to understand the full picture
    for key, duplicate_info in duplicates_by_key.items():
        property_id, checkin, checkout = key
        
        # Find all records with same property and dates
        all_formula = (
            f"AND("
            f"{{Check-in Date}} = '{checkin}', "
            f"{{Check-out Date}} = '{checkout}'"
            f")"
        )
        
        all_matching = table.all(formula=all_formula)
        
        # Filter for same property
        same_property_records = []
        for rec in all_matching:
            rec_property_ids = rec['fields'].get('Property ID', [])
            if rec_property_ids and rec_property_ids[0] == property_id:
                same_property_records.append(rec)
        
        logging.info(f"\nProperty {property_id}, {checkin} to {checkout}:")
        logging.info(f"  Total records with same property/dates: {len(same_property_records)}")
        
        # Group by status
        by_status = {}
        for rec in same_property_records:
            status = rec['fields'].get('Status', 'Unknown')
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(rec)
        
        # Log status breakdown
        for status, recs in by_status.items():
            logging.info(f"  {status}: {len(recs)} records")
            for rec in recs:
                fields = rec['fields']
                logging.info(f"    - ID {fields.get('ID')}: UID={fields.get('Reservation UID')}")
        
        # Identify which "Removed" records should be changed to "Old"
        removed_records = by_status.get('Removed', [])
        if len(removed_records) > 1:
            # Keep the first one as Removed, mark others as Old
            to_fix = removed_records[1:]
            logging.info(f"  FIX: Will change {len(to_fix)} duplicate 'Removed' records to 'Old'")
        else:
            logging.info(f"  OK: Only one or zero 'Removed' records")
    
    # Now actually fix the duplicates
    if not dry_run:
        records_to_update = []
        
        # For each of our target records, check if it needs to be fixed
        for record in target_records:
            fields = record['fields']
            if fields.get('Status') == 'Removed':
                property_ids = fields.get('Property ID', [])
                if not property_ids:
                    continue
                    
                property_id = property_ids[0]
                checkin = fields.get('Check-in Date')
                checkout = fields.get('Check-out Date')
                uid = fields.get('Reservation UID')
                
                # Check if there's another Removed record with same property/dates but different UID
                check_formula = (
                    f"AND("
                    f"{{Check-in Date}} = '{checkin}', "
                    f"{{Check-out Date}} = '{checkout}', "
                    f"{{Status}} = 'Removed', "
                    f"{{Reservation UID}} != '{uid}'"
                    f")"
                )
                
                other_removed = table.all(formula=check_formula)
                
                # Filter for same property
                same_property_removed = []
                for rec in other_removed:
                    rec_property_ids = rec['fields'].get('Property ID', [])
                    if rec_property_ids and rec_property_ids[0] == property_id:
                        same_property_removed.append(rec)
                
                if same_property_removed:
                    # There's another Removed record, so this one should be Old
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {
                            'Status': 'Old',
                            'Last Updated': datetime.now().isoformat()
                        }
                    })
                    logging.info(f"Updating ID {fields.get('ID')} from Removed to Old")
        
        if records_to_update:
            logging.info(f"\nUpdating {len(records_to_update)} records...")
            table.batch_update(records_to_update)
            logging.info("✅ Updates complete!")
        else:
            logging.info("\n✅ No updates needed!")
    else:
        logging.info("\n💡 To execute these changes, run with --execute flag")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fix duplicate Removed Airbnb records')
    parser.add_argument('--execute', action='store_true', help='Actually perform the fix (default is dry run)')
    args = parser.parse_args()
    
    fix_removed_duplicates(dry_run=not args.execute)