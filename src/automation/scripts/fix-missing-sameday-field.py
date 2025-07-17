#!/usr/bin/env python3
"""
Fix missing Same-day Turnover field for iTrip reservations.

This script finds iTrip reservations where the CSV indicates same-day turnover
but the Airtable field is not set, and updates them.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(env_path)

# Airtable configuration
DEV_BASE_ID = "app67yWFv0hKdl6jM"
PROD_BASE_ID = "appZzebEIqCU5R9ER"
RESERVATIONS_TABLE_ID = "tblaPnk0jxF47xWhL"

def get_airtable_api_key(env='prod'):
    # Use absolute paths
    if env == 'dev':
        # Load dev environment
        dev_env_path = '/home/opc/automation/config/environments/dev/.env'
        load_dotenv(dev_env_path, override=True)
        return os.environ.get("DEV_AIRTABLE_API_KEY")
    else:
        # Load prod environment
        prod_env_path = '/home/opc/automation/config/environments/prod/.env'
        load_dotenv(prod_env_path, override=True)
        return os.environ.get("PROD_AIRTABLE_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def find_and_fix_sameday_issues(base_id, env='prod', dry_run=True):
    """Find and fix reservations with missing same-day turnover field."""
    
    # Initialize Airtable
    api_key = get_airtable_api_key(env)
    if not api_key:
        logging.error(f"No API key found for {env} environment!")
        return
    
    logging.info(f"Using API key: {api_key[:10]}...{api_key[-4:]}")
    
    api = Api(api_key)
    base = api.base(base_id)
    table = base.table(RESERVATIONS_TABLE_ID)
    
    # Query for iTrip reservations that might have same-day issues
    formula = "AND({Entry Source} = 'iTrip', {Status} = 'Modified', {Service Line Description} = 'Turnover STR Next Guest Unknown')"
    
    logging.info(f"Searching for potentially affected iTrip reservations...")
    records = table.all(formula=formula)
    
    issues_found = []
    
    for record in records:
        fields = record['fields']
        record_id = record['id']
        uid = fields.get('Reservation UID', 'Unknown')
        
        # Check if iTrip Report Info contains "Same Day?" = Yes
        itrip_info = fields.get('iTrip Report Info', '')
        
        # Look for same-day indicator in various formats
        is_same_day_in_csv = False
        if 'Same Day?' in itrip_info:
            # Extract the line with Same Day?
            for line in itrip_info.split('\n'):
                if 'Same Day?' in line:
                    # Check if it's followed by Yes
                    if ',Yes,' in line or ', Yes,' in line or '"Yes"' in line:
                        is_same_day_in_csv = True
                        break
        
        # Check if Same-day Turnover field is missing or False
        same_day_field = fields.get('Same-day Turnover', False)
        
        if is_same_day_in_csv and not same_day_field:
            issues_found.append({
                'id': record_id,
                'uid': uid,
                'checkout': fields.get('Check-out Date', 'Unknown'),
                'property': fields.get('HCP Address (from Property ID)', ['Unknown'])[0] if fields.get('HCP Address (from Property ID)') else 'Unknown'
            })
            
            logging.info(f"Found issue: {uid} - Checkout {fields.get('Check-out Date')} - {fields.get('HCP Address (from Property ID)', ['Unknown'])[0] if fields.get('HCP Address (from Property ID)') else 'Unknown'}")
    
    if not issues_found:
        logging.info("No issues found!")
        return
    
    logging.info(f"\nFound {len(issues_found)} reservations with missing same-day turnover field")
    
    if dry_run:
        logging.info("\nDRY RUN - No changes will be made")
        logging.info("\nAffected reservations:")
        for issue in issues_found:
            logging.info(f"  - {issue['uid']} | Checkout: {issue['checkout']} | Property: {issue['property']}")
        logging.info("\nRun with --execute to fix these issues")
    else:
        logging.info("\nFixing issues...")
        
        # Update records in batches
        updates = []
        for issue in issues_found:
            updates.append({
                'id': issue['id'],
                'fields': {'Same-day Turnover': True}
            })
        
        # Process in batches of 10
        for i in range(0, len(updates), 10):
            batch = updates[i:i+10]
            try:
                table.batch_update(batch)
                logging.info(f"Updated batch {i//10 + 1}/{(len(updates) + 9)//10}")
            except Exception as e:
                logging.error(f"Error updating batch: {e}")
        
        logging.info(f"\nSuccessfully updated {len(issues_found)} records")

def main():
    parser = argparse.ArgumentParser(description='Fix missing Same-day Turnover field for iTrip reservations')
    parser.add_argument('--env', choices=['dev', 'prod'], required=True, help='Environment to run against')
    parser.add_argument('--execute', action='store_true', help='Actually perform the fixes (default is dry run)')
    
    args = parser.parse_args()
    
    # Determine base ID
    base_id = DEV_BASE_ID if args.env == 'dev' else PROD_BASE_ID
    
    logging.info(f"Running against {args.env.upper()} environment (Base ID: {base_id})")
    
    find_and_fix_sameday_issues(base_id, env=args.env, dry_run=not args.execute)

if __name__ == '__main__':
    main()