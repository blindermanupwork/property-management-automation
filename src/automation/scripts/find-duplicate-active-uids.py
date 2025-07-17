#!/usr/bin/env python3
"""
Find reservations where the same UID has multiple active statuses (New/Modified/Removed).
This violates the rule that only one record per UID should be active at a time.
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

def find_duplicate_active_uids(specific_ids=None):
    """Find UIDs that have multiple active records."""
    
    # Initialize Airtable
    api = Api(Config.get_airtable_api_key())
    base = api.base(Config.get_airtable_base_id())
    table = base.table('Reservations')
    
    logging.info(f"Searching for duplicate active UIDs...")
    
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
    duplicates = {}
    specific_found = set()
    
    for uid, records in records_by_uid.items():
        if len(records) > 1:
            duplicates[uid] = records
            
            # Check if any of our specific IDs are in this group
            if specific_ids:
                for record in records:
                    if record['fields'].get('ID') in specific_ids:
                        specific_found.add(record['fields'].get('ID'))
    
    logging.info(f"\nFound {len(duplicates)} UIDs with multiple active records")
    
    # Show details for each duplicate
    for uid, records in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
        logging.info(f"\nUID: {uid}")
        logging.info(f"  Active records: {len(records)}")
        
        # Sort by Last Updated
        records.sort(key=lambda r: r['fields'].get('Last Updated', ''), reverse=True)
        
        for record in records:
            fields = record['fields']
            logging.info(f"    - ID {fields.get('ID')}: Status={fields.get('Status')}, "
                        f"Dates={fields.get('Check-in Date')} to {fields.get('Check-out Date')}, "
                        f"Property={fields.get('HCP Address (from Property ID)', ['Unknown'])[0]}, "
                        f"Updated={fields.get('Last Updated')}")
    
    # Report on specific IDs if requested
    if specific_ids:
        logging.info(f"\n{'='*60}")
        logging.info(f"Specific IDs requested: {specific_ids}")
        logging.info(f"Found in duplicate groups: {specific_found}")
        not_found = set(specific_ids) - specific_found
        if not_found:
            logging.info(f"Not found in duplicate groups: {not_found}")
            logging.info("These may have already been fixed or don't have duplicates")

if __name__ == "__main__":
    # Check for the specific IDs mentioned by the user
    specific_ids = [36853, 36855, 36856, 36858]
    find_duplicate_active_uids(specific_ids)