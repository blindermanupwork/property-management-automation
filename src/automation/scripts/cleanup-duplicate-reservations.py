#!/usr/bin/env python3
"""
Clean up duplicate reservations in Airtable by marking older duplicates as "Old".

Duplicates are identified by having the same:
- Property ID
- Check-in Date
- Check-out Date
- Entry Type
- Reservation UID

For each set of duplicates, keeps the newest record (by ID) and marks others as "Old".
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from pyairtable import Api

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_duplicate_reservations(table, status_filter=None):
    """Find all duplicate reservations based on key fields."""
    logger.info("Fetching all reservations from Airtable...")
    
    # Build filter formula - always exclude Old records
    formula_parts = ["NOT({Status} = 'Old')"]
    if status_filter:
        formula_parts.append(f"{{Status}} = '{status_filter}'")
    
    formula = f"AND({', '.join(formula_parts)})"
    
    # Fetch all records
    all_records = table.all(formula=formula)
    logger.info(f"Found {len(all_records)} total reservations (excluding Old status)")
    
    # Group by duplicate key
    duplicate_groups = defaultdict(list)
    
    for record in all_records:
        fields = record['fields']
        
        # Skip if missing required fields
        if not all(key in fields for key in ['Property ID', 'Check-in Date', 'Check-out Date']):
            continue
            
        # Build duplicate key
        prop_id = fields.get('Property ID', [''])[0] if fields.get('Property ID') else ''
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        entry_type = fields.get('Entry Type', 'Reservation')
        res_uid = fields.get('Reservation UID', '')
        
        # Skip if missing critical fields
        if not (prop_id and checkin and checkout):
            continue
            
        key = (prop_id, checkin, checkout, entry_type, res_uid)
        duplicate_groups[key].append(record)
    
    # Filter to only groups with duplicates
    duplicates = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
    
    logger.info(f"Found {len(duplicates)} groups of duplicates")
    
    return duplicates

def mark_duplicates_as_old(table, duplicates, dry_run=True):
    """Mark older duplicate records as 'Old' status."""
    updates_to_make = []
    
    for key, records in duplicates.items():
        prop_id, checkin, checkout, entry_type, res_uid = key
        
        # Sort by ID (newest first) - higher ID = newer record
        sorted_records = sorted(records, key=lambda r: r['fields'].get('ID', 0), reverse=True)
        
        logger.info(f"\nDuplicate group for {entry_type} at property {prop_id}:")
        logger.info(f"  Check-in: {checkin}, Check-out: {checkout}")
        logger.info(f"  Reservation UID: {res_uid}")
        logger.info(f"  Found {len(records)} duplicate records:")
        
        for i, record in enumerate(sorted_records):
            fields = record['fields']
            record_id = record['id']
            airtable_id = fields.get('ID', 'Unknown')
            status = fields.get('Status', 'Unknown')
            last_updated = fields.get('Last Updated', 'Unknown')
            
            if i == 0:
                logger.info(f"    ✓ KEEP: ID {airtable_id} (Record: {record_id}) - Status: {status}, Updated: {last_updated}")
            else:
                # Skip if already marked as Old
                if status == 'Old':
                    logger.info(f"    ⏭️  SKIP: ID {airtable_id} (Record: {record_id}) - Already Old, Updated: {last_updated}")
                else:
                    logger.info(f"    ✗ MARK OLD: ID {airtable_id} (Record: {record_id}) - Status: {status}, Updated: {last_updated}")
                    
                    if not dry_run:
                        updates_to_make.append({
                            'id': record_id,
                            'fields': {'Status': 'Old'}
                        })
    
    if dry_run:
        logger.info(f"\n🔍 DRY RUN: Would mark {sum(len(v)-1 for v in duplicates.values())} records as 'Old'")
    else:
        if updates_to_make:
            logger.info(f"\n🔄 Updating {len(updates_to_make)} records...")
            
            # Update in batches of 10
            for i in range(0, len(updates_to_make), 10):
                batch = updates_to_make[i:i+10]
                table.batch_update(batch)
                logger.info(f"  Updated batch {i//10 + 1} ({len(batch)} records)")
            
            logger.info(f"✅ Successfully marked {len(updates_to_make)} duplicate records as 'Old'")
        else:
            logger.info("\n✅ No updates needed")

def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate reservations in Airtable')
    parser.add_argument('--env', choices=['dev', 'prod'], default='prod',
                        help='Environment to clean (default: prod)')
    parser.add_argument('--status', help='Filter by status (e.g., "New")')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be updated without making changes (default: True)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform the updates (overrides --dry-run)')
    
    args = parser.parse_args()
    
    # Override dry-run if execute is specified
    dry_run = not args.execute
    
    # Load environment variables
    if args.env == 'dev':
        env_path = '/home/opc/automation/config/environments/dev/.env'
    else:
        env_path = '/home/opc/automation/config/environments/prod/.env'
    
    load_dotenv(env_path)
    
    # Get Airtable credentials
    if args.env == 'dev':
        api_key = os.getenv('DEV_AIRTABLE_API_KEY')
        base_id = os.getenv('DEV_AIRTABLE_BASE_ID', 'app67yWFv0hKdl6jM')
    else:
        api_key = os.getenv('PROD_AIRTABLE_API_KEY')
        base_id = os.getenv('PROD_AIRTABLE_BASE_ID', 'appZzebEIqCU5R9ER')
    
    if not api_key:
        logger.error("AIRTABLE_API_KEY not found in environment")
        return 1
    
    logger.info(f"🔧 Running duplicate cleanup for {args.env.upper()} environment")
    logger.info(f"📊 Base ID: {base_id}")
    logger.info(f"🔍 Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    
    # Connect to Airtable
    api = Api(api_key)
    base = api.base(base_id)
    table = base.table('Reservations')
    
    # Find duplicates
    duplicates = find_duplicate_reservations(table, args.status)
    
    if not duplicates:
        logger.info("\n✅ No duplicates found!")
        return 0
    
    # Mark duplicates as old
    mark_duplicates_as_old(table, duplicates, dry_run)
    
    if dry_run:
        logger.info("\n💡 To execute these changes, run with --execute flag")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())