#!/usr/bin/env python3
"""
Cleanup script for Mayes property duplicate records.

This script:
1. Finds all reservations for the Mayes property (recRQSv5kFaVKAXdj)
2. Groups them by check-in/check-out dates
3. For each date group with duplicates:
   - Keeps the most recent "New" record
   - Marks all others as "Old"
   - Removes unnecessary "Removed" records
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict
from datetime import datetime
import argparse

def main():
    parser = argparse.ArgumentParser(description='Cleanup Mayes property duplicates')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
    parser.add_argument('--property-id', default='recRQSv5kFaVKAXdj', help='Property ID to clean')
    args = parser.parse_args()
    
    config = ProdConfig()
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    table = base.table('Reservations')
    
    print(f"🔍 Searching for duplicates for property {args.property_id}...")
    
    # Get all records for this property
    all_records = []
    page_num = 1
    for page in table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Status', 'Reservation UID', 'Last Updated', 'ICS URL', 'Entry Type']):
        print(f"Processing page {page_num}...")
        for record in page:
            fields = record['fields']
            prop_ids = fields.get('Property ID', [])
            if args.property_id in prop_ids:
                all_records.append(record)
        page_num += 1
    
    print(f"📊 Found {len(all_records)} total records for this property")
    
    # Group by dates
    date_groups = defaultdict(list)
    for record in all_records:
        fields = record['fields']
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        key = (checkin, checkout)
        date_groups[key].append(record)
    
    # Find duplicate groups
    duplicate_groups = [(k, v) for k, v in date_groups.items() if len(v) > 1]
    print(f"\n🚨 Found {len(duplicate_groups)} date ranges with duplicates")
    
    # Prepare updates
    records_to_update = []
    records_to_delete = []
    
    for (checkin, checkout), records in duplicate_groups:
        print(f"\n📅 Processing dates: {checkin} to {checkout} ({len(records)} records)")
        
        # Separate records by status
        new_records = [r for r in records if r['fields'].get('Status') == 'New']
        old_records = [r for r in records if r['fields'].get('Status') == 'Old']
        removed_records = [r for r in records if r['fields'].get('Status') == 'Removed']
        
        print(f"   - New: {len(new_records)}, Old: {len(old_records)}, Removed: {len(removed_records)}")
        
        if new_records:
            # Keep the most recent "New" record
            latest_new = max(new_records, key=lambda r: r['fields'].get('Last Updated', ''))
            print(f"   ✅ Keeping latest New record: {latest_new['id']} (Updated: {latest_new['fields'].get('Last Updated', 'Unknown')})")
            
            # Mark all other "New" records as "Old"
            for record in new_records:
                if record['id'] != latest_new['id']:
                    records_to_update.append({
                        'id': record['id'],
                        'fields': {
                            'Status': 'Old',
                            'Last Updated': datetime.now().isoformat()
                        }
                    })
                    print(f"   🔄 Will mark as Old: {record['id']}")
        
        # If we have active records, remove unnecessary "Removed" records
        if new_records or old_records:
            for record in removed_records:
                records_to_delete.append(record['id'])
                print(f"   🗑️ Will delete unnecessary Removed record: {record['id']}")
    
    print(f"\n📋 Summary:")
    print(f"   - Records to mark as Old: {len(records_to_update)}")
    print(f"   - Records to delete: {len(records_to_delete)}")
    
    if not args.dry_run:
        if records_to_update:
            print(f"\n⚡ Updating {len(records_to_update)} records to 'Old' status...")
            batch_size = 10
            for i in range(0, len(records_to_update), batch_size):
                batch = records_to_update[i:i+batch_size]
                table.batch_update(batch)
                print(f"   Updated batch {i//batch_size + 1}/{(len(records_to_update) + batch_size - 1)//batch_size}")
        
        if records_to_delete:
            print(f"\n🗑️ Deleting {len(records_to_delete)} unnecessary records...")
            batch_size = 10
            for i in range(0, len(records_to_delete), batch_size):
                batch = records_to_delete[i:i+batch_size]
                table.batch_delete(batch)
                print(f"   Deleted batch {i//batch_size + 1}/{(len(records_to_delete) + batch_size - 1)//batch_size}")
        
        print(f"\n✅ Cleanup completed successfully!")
        
        # Show final counts
        final_counts = defaultdict(int)
        for record in all_records:
            if record['id'] not in records_to_delete:
                status = 'Old' if record['id'] in [u['id'] for u in records_to_update] else record['fields'].get('Status', 'Unknown')
                final_counts[status] += 1
        
        print(f"\n📈 Final record counts:")
        for status, count in sorted(final_counts.items()):
            print(f"   - {status}: {count}")
            
    else:
        print(f"\n🔸 DRY RUN - No changes made")

if __name__ == "__main__":
    main()