#!/usr/bin/env python3
"""
Clean up specific Airbnb event duplicates in production that were created before the race condition fix.
These are records with the same event ID across multiple properties where jobs were never created.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
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

def find_problematic_event_records(table, event_id):
    """Find all records with a specific Airbnb event ID that have no jobs created."""
    logger.info(f"Searching for records with event ID: {event_id}")
    
    # Search for records with this event ID that are not created and not old
    formula = f"AND(SEARCH('{event_id}', {{Reservation UID}}), {{Sync Status}} = 'Not Created', NOT({{Status}} = 'Old'))"
    
    records = table.all(formula=formula)
    logger.info(f"Found {len(records)} records with event ID {event_id} that have no jobs created")
    
    # Group by property to understand the scope
    properties = {}
    for record in records:
        fields = record['fields']
        prop_id = fields.get('Property ID', ['Unknown'])[0] if fields.get('Property ID') else 'Unknown'
        prop_address = fields.get('HCP Address (from Property ID)', ['Unknown'])[0] if fields.get('HCP Address (from Property ID)') else 'Unknown'
        properties[prop_id] = prop_address
    
    logger.info(f"These records span {len(properties)} different properties")
    
    return records

def mark_records_as_old(table, records, dry_run=True):
    """Mark records as Old status."""
    if not records:
        logger.info("No records to update")
        return 0
    
    logger.info(f"\nRecords to mark as Old:")
    for record in records:
        fields = record['fields']
        record_id = fields.get('ID', 'Unknown')
        prop_address = fields.get('HCP Address (from Property ID)', ['Unknown'])[0] if fields.get('HCP Address (from Property ID)') else 'Unknown'
        res_uid = fields.get('Reservation UID', 'Unknown')
        logger.info(f"  ID: {record_id} - {prop_address}")
        logger.info(f"    UID: {res_uid}")
    
    if dry_run:
        logger.info(f"\nDRY RUN - Would mark {len(records)} records as Old")
    else:
        logger.info(f"\nMarking {len(records)} records as Old...")
        
        # Update in batches of 10
        updates = []
        for record in records:
            updates.append({
                'id': record['id'],
                'fields': {
                    'Status': 'Old',
                    'Last Updated': datetime.now().isoformat()
                }
            })
        
        for i in range(0, len(updates), 10):
            batch = updates[i:i+10]
            table.batch_update(batch)
            logger.info(f"  Updated batch {i//10 + 1} ({len(batch)} records)")
        
        logger.info("✅ All records marked as Old!")
    
    return len(records)

def main():
    parser = argparse.ArgumentParser(description='Clean up specific Airbnb event duplicates in production')
    parser.add_argument('--event-id', default='7f662ec65913-0b965d9f7508e0072385e2a838679d2c',
                        help='Airbnb event ID to clean up')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be updated without making changes (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform the updates (overrides --dry-run)')
    
    args = parser.parse_args()
    
    # Determine if we're doing a dry run
    dry_run = not args.execute
    
    # Force production environment
    os.environ['ENVIRONMENT'] = 'production'
    
    # Get production Airtable credentials directly
    from dotenv import load_dotenv
    env_path = '/home/opc/automation/config/environments/prod/.env'
    load_dotenv(env_path)
    
    api_key = os.getenv('PROD_AIRTABLE_API_KEY')
    base_id = 'appZzebEIqCU5R9ER'  # Production base ID
    table_name = 'Reservations'
    
    logger.info("=" * 60)
    logger.info("PRODUCTION Airbnb Event Cleanup")
    logger.info("=" * 60)
    logger.info(f"Base ID: {base_id}")
    logger.info(f"Table: {table_name}")
    logger.info(f"Event ID: {args.event_id}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.info("=" * 60)
    
    # Connect to Airtable
    api = Api(api_key)
    table = api.table(base_id, table_name)
    
    # Find problematic records
    records = find_problematic_event_records(table, args.event_id)
    
    if not records:
        logger.info("\nNo problematic records found!")
        return
    
    # Mark them as old
    updated_count = mark_records_as_old(table, records, dry_run)
    
    if dry_run and updated_count > 0:
        logger.info("\n⚠️  To execute these changes, run with --execute flag")

if __name__ == '__main__':
    main()