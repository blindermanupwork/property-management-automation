#!/usr/bin/env python3
"""
Fix reservations where the same UID has multiple active statuses.
Keep the most recent and mark others as Old.
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

def fix_duplicate_active_uids(dry_run=True):
    """Fix UIDs that have multiple active records."""
    
    # Initialize Airtable
    api = Api(Config.get_airtable_api_key())
    base = api.base(Config.get_airtable_base_id())
    table = base.table('Reservations')
    
    logging.info(f"Fixing duplicate active UIDs in {'DRY RUN' if dry_run else 'EXECUTE'} mode...")
    
    # Get all records with active statuses
    formula = "OR({Status} = 'New', {Status} = 'Modified', {Status} = 'Removed')"
    
    active_records = table.all(formula=formula)
    logging.info(f"Found {len(active_records)} total active records")
    
    # Group by Reservation UID
    records_by_uid = defaultdict(list)
    for record in active_records:
        uid = record['fields'].get('Reservation UID', '')
        if uid:
            records_by_uid[uid].append(record)
    
    # Find UIDs with multiple active records
    updates_to_make = []
    
    for uid, records in records_by_uid.items():
        if len(records) > 1:
            # Sort by Last Updated (newest first), then by ID (highest first)
            records.sort(key=lambda r: (
                r['fields'].get('Last Updated', ''),
                -r['fields'].get('ID', 0)
            ), reverse=True)
            
            logging.info(f"\nUID: {uid}")
            logging.info(f"  Active records: {len(records)}")
            
            # Keep the first (most recent), mark others as Old
            keep = records[0]
            to_fix = records[1:]
            
            logging.info(f"  KEEP: ID {keep['fields'].get('ID')} (Status={keep['fields'].get('Status')}, Updated={keep['fields'].get('Last Updated')})")
            
            for record in to_fix:
                fields = record['fields']
                logging.info(f"  MARK OLD: ID {fields.get('ID')} (Status={fields.get('Status')}, Updated={fields.get('Last Updated')})")
                
                updates_to_make.append({
                    'id': record['id'],
                    'fields': {
                        'Status': 'Old',
                        'Last Updated': datetime.now().isoformat()
                    }
                })
    
    logging.info(f"\n{'='*60}")
    logging.info(f"Total records to mark as Old: {len(updates_to_make)}")
    
    if updates_to_make and not dry_run:
        logging.info("Updating records...")
        # Update in batches of 10
        for i in range(0, len(updates_to_make), 10):
            batch = updates_to_make[i:i+10]
            table.batch_update(batch)
            logging.info(f"  Updated batch {i//10 + 1} ({len(batch)} records)")
        
        logging.info("✅ All duplicates fixed!")
    elif dry_run and updates_to_make:
        logging.info("DRY RUN - No changes made. Use --execute to apply changes.")
    else:
        logging.info("✅ No duplicate active UIDs found!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fix duplicate active UIDs')
    parser.add_argument('--execute', action='store_true', help='Actually perform the fix (default is dry run)')
    args = parser.parse_args()
    
    fix_duplicate_active_uids(dry_run=not args.execute)