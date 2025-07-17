#!/usr/bin/env python3
"""
Fix Tab2 blocks that were incorrectly marked as "Removed" - change them to "Old".
"Removed" implies they were deleted from the source, but they're actually just duplicates.
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

def fix_removed_status(dry_run=True):
    """Change Tab2 blocks from Removed to Old status."""
    
    # Initialize Airtable
    api = Api(Config.get_airtable_api_key())
    base = api.base(Config.get_airtable_base_id())
    table = base.table('Reservations')
    
    logging.info(f"Fixing Tab2 blocks marked as Removed in {'DRY RUN' if dry_run else 'EXECUTE'} mode...")
    
    # Find all Tab2 blocks with Status = "Removed"
    formula = "AND({ICS URL} = 'csv_evolve_blocks', {Entry Type} = 'Block', {Status} = 'Removed')"
    removed_blocks = table.all(formula=formula)
    
    logging.info(f"Found {len(removed_blocks)} Tab2 blocks marked as 'Removed'")
    
    if not removed_blocks:
        logging.info("No blocks to fix!")
        return
    
    # Show what we found
    logging.info("\nBlocks to change from 'Removed' to 'Old':")
    for block in removed_blocks:
        fields = block['fields']
        property_name = fields.get('HCP Address (from Property ID)', ['Unknown'])[0]
        dates = f"{fields.get('Check-in Date')} - {fields.get('Check-out Date')}"
        uid = fields.get('Reservation UID', 'No UID')
        logging.info(f"  ID {fields.get('ID')}: {property_name} | {dates} | UID: {uid}")
    
    if not dry_run:
        logging.info(f"\nUpdating {len(removed_blocks)} records...")
        
        # Update in batches
        batch_size = 10
        for i in range(0, len(removed_blocks), batch_size):
            batch = removed_blocks[i:i+batch_size]
            updates = []
            
            for block in batch:
                updates.append({
                    'id': block['id'],
                    'fields': {
                        'Status': 'Old',
                        'Last Updated': datetime.now().isoformat()
                    }
                })
            
            table.batch_update(updates)
            logging.info(f"  Updated batch {i//batch_size + 1}/{(len(removed_blocks) + batch_size - 1)//batch_size}")
        
        logging.info("✅ All 'Removed' statuses changed to 'Old'!")
    else:
        logging.info(f"\n💡 This will change {len(removed_blocks)} records from 'Removed' to 'Old'")
        logging.info("To execute these changes, run with --execute flag")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fix Tab2 blocks marked as Removed')
    parser.add_argument('--execute', action='store_true', help='Actually perform the update (default is dry run)')
    args = parser.parse_args()
    
    fix_removed_status(dry_run=not args.execute)