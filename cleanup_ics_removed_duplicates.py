#!/usr/bin/env python3
"""
Cleanup duplicate ICS records with "Removed" status.

This script:
1. Finds all reservations with "Removed" status
2. Groups them by property and dates
3. Identifies duplicates where active records exist
4. Marks unnecessary "Removed" records as "Old"
"""

import os
import sys
from datetime import datetime
from collections import defaultdict
import argparse

# Add project root to path
sys.path.append('/home/opc/automation')

from src.automation.config_wrapper import Config
from pyairtable import Api

def main():
    parser = argparse.ArgumentParser(description='Cleanup duplicate ICS removed records')
    parser.add_argument('--env', choices=['dev', 'prod'], default='prod', help='Environment')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
    parser.add_argument('--property-id', help='Specific property ID to clean (optional)')
    args = parser.parse_args()
    
    # Setup configuration
    if args.env == 'prod':
        from src.automation.config_prod import ProdConfig
        config = ProdConfig()
        api = Api(config.get_airtable_api_key())
        base = api.base(config.get_airtable_base_id())
    else:
        from src.automation.config_dev import DevConfig
        config = DevConfig()
        api = Api(config.get_airtable_api_key())
        base = api.base(config.get_airtable_base_id())
    
    table = base.table('Reservations')
    
    print(f"🔍 Searching for duplicate ICS records in {args.env} environment...")
    
    # Get all reservations with relevant fields
    fields = ['Property ID', 'Check-in Date', 'Check-out Date', 'Status', 
              'Entry Type', 'Reservation UID', 'Last Updated', 'ICS URL']
    
    if args.property_id:
        # Filter for specific property
        formula = f"FIND('{args.property_id}', {{Property ID}})"
    else:
        formula = None
    
    all_records = table.all(fields=fields, formula=formula)
    print(f"📊 Found {len(all_records)} total records")
    
    # Group records by property + dates
    groups = defaultdict(list)
    for record in all_records:
        fields = record['fields']
        property_id = fields.get('Property ID', ['Unknown'])[0] if fields.get('Property ID') else 'Unknown'
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        
        key = (property_id, checkin, checkout)
        groups[key].append(record)
    
    # Find groups with duplicates
    duplicate_groups = []
    removed_to_mark_old = []
    
    for key, records in groups.items():
        if len(records) > 1:
            # Check if we have both active and removed records
            statuses = [r['fields'].get('Status', '') for r in records]
            has_removed = 'Removed' in statuses
            has_active = any(s in ['New', 'Modified'] for s in statuses)
            
            if has_removed:
                duplicate_groups.append((key, records))
                
                # If we have active records, mark all "Removed" records as "Old"
                if has_active:
                    for record in records:
                        if record['fields'].get('Status') == 'Removed':
                            removed_to_mark_old.append(record)
    
    print(f"\n🚨 Found {len(duplicate_groups)} groups with duplicates involving 'Removed' status")
    
    # Show details for each duplicate group
    for (property_id, checkin, checkout), records in duplicate_groups[:10]:  # Show first 10
        print(f"\n📍 Property: {property_id}, Dates: {checkin} to {checkout}")
        for record in sorted(records, key=lambda r: r['fields'].get('Last Updated', '')):
            status = record['fields'].get('Status', 'Unknown')
            uid = record['fields'].get('Reservation UID', 'No UID')
            last_updated = record['fields'].get('Last Updated', 'Unknown')
            print(f"   - {status}: {uid[:50]}... (Updated: {last_updated})")
    
    if len(duplicate_groups) > 10:
        print(f"\n... and {len(duplicate_groups) - 10} more duplicate groups")
    
    # Mark unnecessary "Removed" records as "Old"
    print(f"\n🧹 Found {len(removed_to_mark_old)} 'Removed' records to mark as 'Old'")
    
    if not args.dry_run and removed_to_mark_old:
        print("\n⚡ Updating records...")
        batch_size = 10
        for i in range(0, len(removed_to_mark_old), batch_size):
            batch = removed_to_mark_old[i:i+batch_size]
            updates = []
            for record in batch:
                updates.append({
                    'id': record['id'],
                    'fields': {
                        'Status': 'Old',
                        'Last Updated': datetime.now().isoformat()
                    }
                })
            table.batch_update(updates)
            print(f"   Updated batch {i//batch_size + 1}/{(len(removed_to_mark_old) + batch_size - 1)//batch_size}")
        
        print(f"\n✅ Successfully marked {len(removed_to_mark_old)} records as 'Old'")
    elif args.dry_run:
        print("\n🔸 DRY RUN - No changes made")
        print(f"Would mark {len(removed_to_mark_old)} records as 'Old'")
    
    # Additional analysis - properties with most duplicates
    property_duplicate_counts = defaultdict(int)
    for (property_id, _, _), records in duplicate_groups:
        property_duplicate_counts[property_id] += 1
    
    print("\n📊 Properties with most duplicate groups:")
    for prop_id, count in sorted(property_duplicate_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   - {prop_id}: {count} duplicate groups")

if __name__ == "__main__":
    main()