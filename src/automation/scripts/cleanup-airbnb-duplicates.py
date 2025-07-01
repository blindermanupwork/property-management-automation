#!/usr/bin/env python3
"""
Clean up Airbnb duplicate reservations that have different UIDs but same property/dates.

This handles the specific case where multiple ICS feeds contained the same Airbnb event
with different property IDs, causing race condition duplicates.

Duplicates are identified by having the same:
- Property ID  
- Check-in Date
- Check-out Date
- Entry Type

For each set of duplicates, keeps the newest record (by ID) and marks others as "Old".
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from pyairtable import Api
from src.automation.config_wrapper import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_property_date_duplicates(table, status_filter=None):
    """Find all duplicate reservations based on property and dates only (ignoring UID)."""
    logger.info("Fetching all reservations from Airtable...")
    
    # Build filter formula - always exclude Old records
    formula_parts = ["NOT({Status} = 'Old')"]
    if status_filter:
        formula_parts.append(f"{{Status}} = '{status_filter}'")
    
    formula = f"AND({', '.join(formula_parts)})"
    
    # Fetch all records
    all_records = table.all(formula=formula)
    logger.info(f"Found {len(all_records)} total reservations (excluding Old status)")
    
    # Group by property/date key (excluding UID)
    duplicate_groups = defaultdict(list)
    
    for record in all_records:
        fields = record['fields']
        
        # Skip if missing required fields
        if not all(key in fields for key in ['Property ID', 'Check-in Date', 'Check-out Date']):
            continue
            
        # Build duplicate key WITHOUT Reservation UID
        prop_id = fields.get('Property ID', [''])[0] if fields.get('Property ID') else ''
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        entry_type = fields.get('Entry Type', 'Reservation')
        
        # Skip if missing critical fields
        if not (prop_id and checkin and checkout):
            continue
            
        key = (prop_id, checkin, checkout, entry_type)
        duplicate_groups[key].append(record)
    
    # Filter to only groups with duplicates
    duplicates = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
    
    # Additional filtering for Airbnb-specific duplicates
    airbnb_duplicates = {}
    for key, records in duplicates.items():
        # Check if any have Airbnb UIDs (they often contain specific patterns)
        uids = [r['fields'].get('Reservation UID', '') for r in records]
        # If different UIDs, this is likely our race condition case
        if len(set(uids)) > 1:
            airbnb_duplicates[key] = records
    
    logger.info(f"Found {len(airbnb_duplicates)} groups of property/date duplicates with different UIDs")
    
    return airbnb_duplicates

def mark_duplicates_as_old(table, duplicates, dry_run=True):
    """Mark older duplicate records as 'Old' status."""
    updates_to_make = []
    
    for key, records in duplicates.items():
        prop_id, checkin, checkout, entry_type = key
        
        # Sort by ID (newest first) - higher ID = newer record
        sorted_records = sorted(records, key=lambda r: r['fields'].get('ID', 0), reverse=True)
        
        logger.info(f"\nDuplicate group for {entry_type} at property {prop_id}:")
        logger.info(f"  Check-in: {checkin}, Check-out: {checkout}")
        logger.info(f"  Found {len(records)} duplicate records with different UIDs:")
        
        for i, record in enumerate(sorted_records):
            fields = record['fields']
            record_id = record['id']
            airtable_id = fields.get('ID', 'Unknown')
            res_uid = fields.get('Reservation UID', 'Unknown')
            status = fields.get('Status', 'Unknown')
            last_updated = fields.get('Last Updated', 'Unknown')
            created_time = fields.get('Created Time', 'Unknown')
            
            if i == 0:
                logger.info(f"    [KEEP] ID: {airtable_id}, UID: {res_uid}, Status: {status}, Created: {created_time}")
            else:
                logger.info(f"    [MARK OLD] ID: {airtable_id}, UID: {res_uid}, Status: {status}, Created: {created_time}")
                updates_to_make.append({
                    'id': record_id,
                    'fields': {
                        'Status': 'Old',
                        'Last Updated': datetime.now().isoformat()
                    }
                })
    
    logger.info(f"\nTotal records to mark as Old: {len(updates_to_make)}")
    
    if not dry_run and updates_to_make:
        logger.info("Updating records...")
        # Update in batches of 10
        for i in range(0, len(updates_to_make), 10):
            batch = updates_to_make[i:i+10]
            table.batch_update(batch)
            logger.info(f"  Updated batch {i//10 + 1} ({len(batch)} records)")
        
        logger.info("✅ All duplicates marked as Old!")
    elif dry_run:
        logger.info("DRY RUN - No changes made. Use --execute to apply changes.")
    else:
        logger.info("No updates needed.")
    
    return len(updates_to_make)

def main():
    parser = argparse.ArgumentParser(description='Clean up Airbnb duplicate reservations with different UIDs')
    parser.add_argument('--env', choices=['dev', 'prod'], default='prod',
                        help='Environment to clean (default: prod)')
    parser.add_argument('--status', help='Filter by status (e.g., "New")')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be updated without making changes (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform the updates (overrides --dry-run)')
    
    args = parser.parse_args()
    
    # Determine if we're doing a dry run
    dry_run = not args.execute
    
    # Load environment configuration
    os.environ['ENVIRONMENT'] = 'development' if args.env == 'dev' else 'production'
    
    # Get Airtable credentials
    api_key = Config.get_airtable_api_key()
    base_id = Config.get_airtable_base_id()
    table_name = Config.get_airtable_table_name('reservations')
    
    logger.info(f"Environment: {args.env}")
    logger.info(f"Base ID: {base_id}")
    logger.info(f"Table: {table_name}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    if args.status:
        logger.info(f"Status filter: {args.status}")
    
    # Connect to Airtable
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    # Find duplicates
    duplicates = find_property_date_duplicates(table, args.status)
    
    if not duplicates:
        logger.info("No property/date duplicates with different UIDs found!")
        return
    
    # Mark duplicates as old
    updated_count = mark_duplicates_as_old(table, duplicates, dry_run)
    
    if updated_count > 0:
        logger.info(f"\n{'Would update' if dry_run else 'Updated'} {updated_count} records total")

if __name__ == '__main__':
    main()