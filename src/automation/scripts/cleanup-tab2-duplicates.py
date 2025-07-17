#!/usr/bin/env python3
"""
Cleanup duplicate Tab2 blocks by marking old duplicates as Removed.
Only keeps the most recent active (New/Modified) record.
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

def cleanup_tab2_duplicates(dry_run=True):
    """Find and clean up duplicate Tab2 blocks."""
    
    # Initialize Airtable
    api = Api(Config.get_airtable_api_key())
    base = api.base(Config.get_airtable_base_id())
    table = base.table('Reservations')
    
    logging.info(f"Running Tab2 duplicate cleanup in {'DRY RUN' if dry_run else 'EXECUTE'} mode...")
    
    # Get all Tab2 blocks
    formula = "AND({ICS URL} = 'csv_evolve_blocks', {Entry Type} = 'Block')"
    all_blocks = table.all(formula=formula)
    logging.info(f"Found {len(all_blocks)} total Tab2 blocks")
    
    # Group by composite UID
    blocks_by_uid = defaultdict(list)
    for block in all_blocks:
        uid = block['fields'].get('Reservation UID', '')
        if uid:
            blocks_by_uid[uid].append(block)
    
    # Find duplicates
    duplicates_found = 0
    records_to_remove = []
    
    for uid, blocks in blocks_by_uid.items():
        if len(blocks) > 1:
            # Sort by Last Updated (newest first) and Status (New/Modified before Old)
            blocks.sort(key=lambda b: (
                b['fields'].get('Status', '') not in ['New', 'Modified'],
                -(b['fields'].get('ID', 0))
            ))
            
            # Keep the first (best) one, mark others for removal
            keep = blocks[0]
            remove = blocks[1:]
            
            if remove:
                duplicates_found += 1
                property_name = keep['fields'].get('HCP Address (from Property ID)', ['Unknown'])[0]
                dates = f"{keep['fields'].get('Check-in Date')} - {keep['fields'].get('Check-out Date')}"
                
                logging.info(f"\nDuplicate set for {uid}:")
                logging.info(f"  Property: {property_name}")
                logging.info(f"  Dates: {dates}")
                logging.info(f"  Keeping: ID {keep['fields'].get('ID')} (Status: {keep['fields'].get('Status')})")
                logging.info(f"  Removing: {len(remove)} duplicate(s)")
                
                for block in remove:
                    status = block['fields'].get('Status', '')
                    if status != 'Removed':  # Don't re-mark already removed records
                        records_to_remove.append({
                            'id': block['id'],
                            'uid': uid,
                            'property': property_name,
                            'dates': dates,
                            'current_status': status
                        })
                        logging.info(f"    - ID {block['fields'].get('ID')} (Status: {status})")
    
    # Summary
    logging.info(f"\n{'='*60}")
    logging.info(f"SUMMARY:")
    logging.info(f"Total UIDs with duplicates: {duplicates_found}")
    logging.info(f"Total records to mark as Removed: {len(records_to_remove)}")
    
    if records_to_remove and not dry_run:
        logging.info(f"\nMarking {len(records_to_remove)} records as Removed...")
        
        # Update in batches
        batch_size = 10
        for i in range(0, len(records_to_remove), batch_size):
            batch = records_to_remove[i:i+batch_size]
            updates = []
            
            for record in batch:
                updates.append({
                    'id': record['id'],
                    'fields': {
                        'Status': 'Removed',
                        'Last Updated': datetime.now().isoformat()
                    }
                })
            
            table.batch_update(updates)
            logging.info(f"  Updated batch {i//batch_size + 1}/{(len(records_to_remove) + batch_size - 1)//batch_size}")
        
        logging.info("✅ Cleanup complete!")
    elif records_to_remove and dry_run:
        logging.info("\n💡 To execute these changes, run with --execute flag")
    else:
        logging.info("\n✅ No duplicates found!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Clean up duplicate Tab2 blocks')
    parser.add_argument('--execute', action='store_true', help='Actually perform the cleanup (default is dry run)')
    args = parser.parse_args()
    
    cleanup_tab2_duplicates(dry_run=not args.execute)