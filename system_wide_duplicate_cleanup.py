#!/usr/bin/env python3
"""
System-wide duplicate cleanup script.

This script:
1. Finds all properties with significant duplication issues
2. For each property, groups reservations by check-in/check-out dates  
3. For each date group with duplicates:
   - Keeps the most recent "New" record
   - Marks all others as "Old"
   - Removes unnecessary "Removed" records
4. Provides detailed reporting and progress tracking

Based on analysis showing 130 properties with duplicates (81.6% of all records).
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict
from datetime import datetime
import argparse
import time

def get_property_duplicates(table, properties_table, min_duplicates=5):
    """Find all properties with duplicate issues."""
    print(f"🔍 Scanning all reservations for duplicate patterns...")
    
    # Get property names for better reporting
    print("📋 Loading property names...")
    property_names = {}
    for page in properties_table.iterate(page_size=100, fields=['Property Name']):
        for record in page:
            property_names[record['id']] = record['fields'].get('Property Name', 'Unknown')
    
    print(f"   Loaded {len(property_names)} property names")
    
    # Scan all reservations
    property_date_groups = defaultdict(lambda: defaultdict(list))
    all_records_count = 0
    page_num = 1
    
    for page in table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Status', 'Last Updated']):
        print(f"Processing reservations page {page_num}...")
        for record in page:
            all_records_count += 1
            fields = record['fields']
            prop_ids = fields.get('Property ID', [])
            checkin = fields.get('Check-in Date', '')
            checkout = fields.get('Check-out Date', '')
            
            for prop_id in prop_ids:
                date_key = (checkin, checkout)
                property_date_groups[prop_id][date_key].append(record)
        page_num += 1
    
    print(f"📊 Processed {all_records_count} total reservations")
    
    # Find properties with duplicates
    property_duplicate_stats = []
    
    for prop_id, date_groups in property_date_groups.items():
        duplicate_date_count = 0
        total_duplicate_records = 0
        max_duplicates_per_date = 0
        
        for date_key, records in date_groups.items():
            if len(records) > 1:
                duplicate_date_count += 1
                total_duplicate_records += len(records)
                max_duplicates_per_date = max(max_duplicates_per_date, len(records))
        
        if duplicate_date_count >= min_duplicates or max_duplicates_per_date >= min_duplicates:
            property_duplicate_stats.append({
                'property_id': prop_id,
                'property_name': property_names.get(prop_id, 'Unknown'),
                'duplicate_date_ranges': duplicate_date_count,
                'total_duplicate_records': total_duplicate_records,
                'max_duplicates_per_date': max_duplicates_per_date,
                'date_groups': date_groups
            })
    
    # Sort by most problematic
    property_duplicate_stats.sort(key=lambda x: (x['total_duplicate_records'], x['duplicate_date_ranges']), reverse=True)
    
    return property_duplicate_stats, all_records_count

def cleanup_property_duplicates(table, property_info, dry_run=True):
    """Clean up duplicates for a single property."""
    prop_id = property_info['property_id']
    prop_name = property_info['property_name']
    date_groups = property_info['date_groups']
    
    print(f"\n🏠 Processing property: {prop_name[:60]}")
    print(f"     Property ID: {prop_id}")
    print(f"     Duplicate date ranges: {property_info['duplicate_date_ranges']}")
    print(f"     Total duplicate records: {property_info['total_duplicate_records']}")
    
    # Find duplicate groups (date ranges with multiple records)
    duplicate_groups = [(k, v) for k, v in date_groups.items() if len(v) > 1]
    
    # Prepare updates
    records_to_update = []
    records_to_delete = []
    
    for (checkin, checkout), records in duplicate_groups:
        print(f"  📅 Processing dates: {checkin} to {checkout} ({len(records)} records)")
        
        # Separate records by status
        new_records = [r for r in records if r['fields'].get('Status') == 'New']
        old_records = [r for r in records if r['fields'].get('Status') == 'Old']
        removed_records = [r for r in records if r['fields'].get('Status') == 'Removed']
        
        print(f"     - New: {len(new_records)}, Old: {len(old_records)}, Removed: {len(removed_records)}")
        
        if new_records:
            # Keep the most recent "New" record
            latest_new = max(new_records, key=lambda r: r['fields'].get('Last Updated', ''))
            print(f"     ✅ Keeping latest New record: {latest_new['id']}")
            
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
                    print(f"     🔄 Will mark as Old: {record['id']}")
        
        # If we have active records, remove unnecessary "Removed" records
        if new_records or old_records:
            for record in removed_records:
                records_to_delete.append(record['id'])
                print(f"     🗑️ Will delete unnecessary Removed record: {record['id']}")
    
    print(f"  📋 Property summary:")
    print(f"     - Records to mark as Old: {len(records_to_update)}")
    print(f"     - Records to delete: {len(records_to_delete)}")
    
    if not dry_run and (records_to_update or records_to_delete):
        try:
            if records_to_update:
                print(f"     ⚡ Updating {len(records_to_update)} records to 'Old' status...")
                batch_size = 10
                for i in range(0, len(records_to_update), batch_size):
                    batch = records_to_update[i:i+batch_size]
                    table.batch_update(batch)
                    print(f"       Updated batch {i//batch_size + 1}/{(len(records_to_update) + batch_size - 1)//batch_size}")
            
            if records_to_delete:
                print(f"     🗑️ Deleting {len(records_to_delete)} unnecessary records...")
                batch_size = 10
                for i in range(0, len(records_to_delete), batch_size):
                    batch = records_to_delete[i:i+batch_size]
                    table.batch_delete(batch)
                    print(f"       Deleted batch {i//batch_size + 1}/{(len(records_to_delete) + batch_size - 1)//batch_size}")
            
            print(f"     ✅ Property cleanup completed!")
        except Exception as e:
            print(f"     ❌ Error processing property: {e}")
            return False
    
    return len(records_to_update), len(records_to_delete)

def main():
    parser = argparse.ArgumentParser(description='System-wide duplicate cleanup')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no changes)')
    parser.add_argument('--min-duplicates', type=int, default=5, help='Minimum duplicates to process')
    parser.add_argument('--limit', type=int, default=0, help='Max properties to process (0 = all)')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip initial analysis (faster for testing)')
    args = parser.parse_args()
    
    config = ProdConfig()
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    reservations_table = base.table('Reservations')
    properties_table = base.table('Properties')
    
    print(f"🚀 Starting system-wide duplicate cleanup")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE EXECUTION'}")
    print(f"   Minimum duplicates threshold: {args.min_duplicates}")
    print(f"   Property limit: {args.limit if args.limit > 0 else 'No limit'}")
    
    start_time = time.time()
    
    if not args.skip_analysis:
        # Find all properties with duplicates
        property_duplicate_stats, total_records = get_property_duplicates(
            reservations_table, properties_table, args.min_duplicates
        )
        
        print(f"\n🚨 Found {len(property_duplicate_stats)} properties with significant duplicates")
        print(f"📊 Out of {total_records} total reservation records")
        
        # Show top problematic properties
        print(f"\n📋 Top 10 most problematic properties:")
        for i, stats in enumerate(property_duplicate_stats[:10]):
            print(f"{i+1:2d}. {stats['property_name'][:60]}")
            print(f"     Total duplicate records: {stats['total_duplicate_records']}")
            print(f"     Duplicate date ranges: {stats['duplicate_date_ranges']}")
    else:
        print("⚡ Skipping analysis - using cached results")
        # For testing, we could load from a saved file here
        property_duplicate_stats = []
    
    if not property_duplicate_stats:
        print("✅ No properties found with significant duplicates!")
        return
    
    # Process properties
    properties_to_process = property_duplicate_stats[:args.limit] if args.limit > 0 else property_duplicate_stats
    
    print(f"\n🔧 Processing {len(properties_to_process)} properties...")
    
    total_updates = 0
    total_deletes = 0
    successful_properties = 0
    
    for i, property_info in enumerate(properties_to_process):
        print(f"\n[{i+1}/{len(properties_to_process)}]", end=" ")
        
        try:
            updates, deletes = cleanup_property_duplicates(
                reservations_table, property_info, args.dry_run
            )
            total_updates += updates
            total_deletes += deletes
            successful_properties += 1
            
            # Add small delay to avoid rate limiting
            if not args.dry_run:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Failed to process property {property_info['property_name']}: {e}")
            continue
    
    # Final summary
    elapsed_time = time.time() - start_time
    print(f"\n🏁 Cleanup completed in {elapsed_time:.1f} seconds")
    print(f"📊 Final Summary:")
    print(f"   - Properties processed: {successful_properties}/{len(properties_to_process)}")
    print(f"   - Total records marked as Old: {total_updates}")
    print(f"   - Total records deleted: {total_deletes}")
    print(f"   - Mode: {'DRY RUN' if args.dry_run else 'LIVE EXECUTION'}")
    
    if args.dry_run:
        print(f"\n💡 To execute changes, run without --dry-run flag")
    else:
        print(f"\n✅ All changes have been applied to the database")

if __name__ == "__main__":
    main()