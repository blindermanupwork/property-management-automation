#!/usr/bin/env python3
"""
Cleanup duplicate reservations using correct logic:
- Unique constraint: Property ID + Check-in Date + Check-out Date + Entry Type
- Only consider New/Modified/Removed statuses (not Old)
- Keep the most recently updated record as active
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from src.automation.config_dev import DevConfig
from pyairtable import Api
from collections import defaultdict
from datetime import datetime
import argparse
import time
import json

def find_duplicates_to_clean(table, properties_table):
    """Find duplicates using correct logic."""
    
    print("🔍 Finding duplicates to clean...")
    
    # Get property names for better reporting
    print("📋 Loading property names...")
    property_names = {}
    for page in properties_table.iterate(page_size=100, fields=['Property Name']):
        for record in page:
            property_names[record['id']] = record['fields'].get('Property Name', 'Unknown')
    
    # Group records by correct unique constraint
    duplicate_groups = defaultdict(list)
    total_records = 0
    active_records = 0
    
    print("\n📊 Analyzing reservations...")
    fields_to_fetch = [
        'Property ID', 'Check-in Date', 'Check-out Date', 
        'Entry Type', 'Status', 'Reservation UID',
        'Entry Source', 'Last Updated'
    ]
    
    for page in table.iterate(page_size=100, fields=fields_to_fetch):
        for record in page:
            total_records += 1
            fields = record['fields']
            status = fields.get('Status', '')
            
            # Only consider active statuses (not Old)
            if status in ['New', 'Modified', 'Removed']:
                active_records += 1
                prop_ids = fields.get('Property ID', [])
                checkin = fields.get('Check-in Date', '')
                checkout = fields.get('Check-out Date', '')
                entry_type = fields.get('Entry Type', '')
                
                for prop_id in prop_ids:
                    # Key does NOT include Entry Source
                    key = (prop_id, checkin, checkout, entry_type)
                    duplicate_groups[key].append(record)
    
    print(f"\n📈 Analysis complete:")
    print(f"   - Total records: {total_records:,}")
    print(f"   - Active records (New/Modified/Removed): {active_records:,}")
    print(f"   - Unique combinations: {len(duplicate_groups):,}")
    
    # Find actual duplicates
    duplicates_to_fix = {}
    stats = {
        'groups_with_duplicates': 0,
        'total_duplicate_records': 0,
        'new_duplicates': 0,
        'modified_duplicates': 0,
        'removed_duplicates': 0,
        'mixed_status_groups': 0
    }
    
    for key, records in duplicate_groups.items():
        if len(records) > 1:
            stats['groups_with_duplicates'] += 1
            stats['total_duplicate_records'] += len(records)
            
            # Analyze status distribution
            status_counts = defaultdict(int)
            for r in records:
                status = r['fields'].get('Status', '')
                status_counts[status] += 1
            
            # Count different status types
            if status_counts['New'] > 0:
                stats['new_duplicates'] += status_counts['New'] - 1  # All but one are duplicates
            if status_counts['Modified'] > 0:
                stats['modified_duplicates'] += status_counts['Modified'] - 1
            if status_counts['Removed'] > 0 and (status_counts['New'] > 0 or status_counts['Modified'] > 0):
                stats['removed_duplicates'] += status_counts['Removed']  # All removed if active exists
            
            if len(status_counts) > 1:
                stats['mixed_status_groups'] += 1
            
            duplicates_to_fix[key] = {
                'records': records,
                'status_counts': dict(status_counts),
                'property_name': property_names.get(key[0], 'Unknown')
            }
    
    print(f"\n🚨 Duplicates found:")
    print(f"   - Groups with duplicates: {stats['groups_with_duplicates']:,}")
    print(f"   - Total duplicate records: {stats['total_duplicate_records']:,}")
    print(f"   - Excess New records: {stats['new_duplicates']:,}")
    print(f"   - Excess Modified records: {stats['modified_duplicates']:,}")
    print(f"   - Unnecessary Removed records: {stats['removed_duplicates']:,}")
    print(f"   - Groups with mixed statuses: {stats['mixed_status_groups']:,}")
    
    return duplicates_to_fix, stats, property_names

def plan_cleanup(duplicates_to_fix):
    """Plan which records to keep and which to update/delete."""
    
    cleanup_plan = {
        'records_to_mark_old': [],
        'records_to_delete': [],
        'records_to_keep': [],
        'property_summary': defaultdict(lambda: {'mark_old': 0, 'delete': 0, 'keep': 0})
    }
    
    for (prop_id, checkin, checkout, entry_type), group_info in duplicates_to_fix.items():
        records = group_info['records']
        prop_name = group_info['property_name']
        
        # Separate by status
        new_records = [r for r in records if r['fields'].get('Status') == 'New']
        modified_records = [r for r in records if r['fields'].get('Status') == 'Modified']
        removed_records = [r for r in records if r['fields'].get('Status') == 'Removed']
        
        # Determine which record to keep
        keeper = None
        
        # Priority: Modified > New > Removed (by most recent)
        if modified_records:
            keeper = max(modified_records, key=lambda r: r['fields'].get('Last Updated', ''))
        elif new_records:
            keeper = max(new_records, key=lambda r: r['fields'].get('Last Updated', ''))
        elif removed_records:
            # If only removed records, keep the most recent
            keeper = max(removed_records, key=lambda r: r['fields'].get('Last Updated', ''))
        
        if keeper:
            cleanup_plan['records_to_keep'].append(keeper)
            cleanup_plan['property_summary'][prop_id]['keep'] += 1
            
            # Mark all others based on their status
            for record in records:
                if record['id'] != keeper['id']:
                    if record['fields'].get('Status') == 'Removed':
                        # Delete unnecessary Removed records if we have an active record
                        if keeper['fields'].get('Status') in ['New', 'Modified']:
                            cleanup_plan['records_to_delete'].append(record)
                            cleanup_plan['property_summary'][prop_id]['delete'] += 1
                        else:
                            # Keep removed if keeper is also removed (mark as old)
                            cleanup_plan['records_to_mark_old'].append(record)
                            cleanup_plan['property_summary'][prop_id]['mark_old'] += 1
                    else:
                        # Mark duplicate New/Modified as Old
                        cleanup_plan['records_to_mark_old'].append(record)
                        cleanup_plan['property_summary'][prop_id]['mark_old'] += 1
    
    return cleanup_plan

def print_cleanup_plan(cleanup_plan, property_names, limit=10):
    """Print a summary of the cleanup plan."""
    
    print("\n" + "="*80)
    print("🧹 CLEANUP PLAN SUMMARY")
    print("="*80)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   - Records to keep active: {len(cleanup_plan['records_to_keep']):,}")
    print(f"   - Records to mark as Old: {len(cleanup_plan['records_to_mark_old']):,}")
    print(f"   - Records to delete: {len(cleanup_plan['records_to_delete']):,}")
    
    # Sort properties by most affected
    sorted_properties = sorted(
        cleanup_plan['property_summary'].items(),
        key=lambda x: x[1]['mark_old'] + x[1]['delete'],
        reverse=True
    )
    
    print(f"\n🏠 Top {limit} Most Affected Properties:")
    for i, (prop_id, counts) in enumerate(sorted_properties[:limit]):
        if i >= limit:
            break
        prop_name = property_names.get(prop_id, 'Unknown')
        total_actions = counts['mark_old'] + counts['delete']
        print(f"\n{i+1}. {prop_name}")
        print(f"   Property ID: {prop_id}")
        print(f"   Keep active: {counts['keep']}")
        print(f"   Mark as Old: {counts['mark_old']}")
        print(f"   Delete: {counts['delete']}")
        print(f"   Total actions: {total_actions}")
    
    # Show some examples
    print(f"\n📋 Sample Records to Process:")
    print("\nRecords to mark as Old (first 5):")
    for record in cleanup_plan['records_to_mark_old'][:5]:
        fields = record['fields']
        print(f"   - {record['id']}: {fields.get('Reservation UID', 'No UID')} ({fields.get('Status')})")
    
    print("\nRecords to delete (first 5):")
    for record in cleanup_plan['records_to_delete'][:5]:
        fields = record['fields']
        print(f"   - {record['id']}: {fields.get('Reservation UID', 'No UID')} ({fields.get('Status')})")

def create_backup(cleanup_plan, backup_file):
    """Create a CSV backup of records that will be modified."""
    import csv
    
    print(f"\n💾 Creating backup to {backup_file}...")
    
    with open(backup_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'Record ID', 'Action', 'Reservation UID', 'Property ID', 
            'Check-in Date', 'Check-out Date', 'Entry Type', 'Entry Source',
            'Status', 'Last Updated', 'Full Record JSON'
        ])
        
        # Write records to mark as old
        for record in cleanup_plan['records_to_mark_old']:
            fields = record['fields']
            writer.writerow([
                record['id'],
                'MARK_AS_OLD',
                fields.get('Reservation UID', ''),
                ','.join(fields.get('Property ID', [])),
                fields.get('Check-in Date', ''),
                fields.get('Check-out Date', ''),
                fields.get('Entry Type', ''),
                fields.get('Entry Source', ''),
                fields.get('Status', ''),
                fields.get('Last Updated', ''),
                json.dumps(record)
            ])
        
        # Write records to delete
        for record in cleanup_plan['records_to_delete']:
            fields = record['fields']
            writer.writerow([
                record['id'],
                'DELETE',
                fields.get('Reservation UID', ''),
                ','.join(fields.get('Property ID', [])),
                fields.get('Check-in Date', ''),
                fields.get('Check-out Date', ''),
                fields.get('Entry Type', ''),
                fields.get('Entry Source', ''),
                fields.get('Status', ''),
                fields.get('Last Updated', ''),
                json.dumps(record)
            ])
    
    print(f"   ✅ Backed up {len(cleanup_plan['records_to_mark_old']) + len(cleanup_plan['records_to_delete'])} records")

def execute_cleanup(table, cleanup_plan, dry_run=True, backup_file=None):
    """Execute the cleanup plan."""
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        return
    
    # Create backup first
    if backup_file:
        create_backup(cleanup_plan, backup_file)
    
    print("\n🚀 Executing cleanup...")
    
    # Mark records as Old in batches
    if cleanup_plan['records_to_mark_old']:
        print(f"\n📝 Marking {len(cleanup_plan['records_to_mark_old'])} records as Old...")
        
        updates = []
        for record in cleanup_plan['records_to_mark_old']:
            updates.append({
                'id': record['id'],
                'fields': {
                    'Status': 'Old',
                    'Last Updated': datetime.now().isoformat()
                }
            })
        
        # Process in batches of 10
        batch_size = 10
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            try:
                table.batch_update(batch)
                print(f"   Batch {i//batch_size + 1}/{(len(updates) + batch_size - 1)//batch_size} completed")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   ❌ Error updating batch: {e}")
    
    # Delete records in batches
    if cleanup_plan['records_to_delete']:
        print(f"\n🗑️  Deleting {len(cleanup_plan['records_to_delete'])} unnecessary records...")
        
        record_ids = [r['id'] for r in cleanup_plan['records_to_delete']]
        
        # Process in batches of 10
        batch_size = 10
        for i in range(0, len(record_ids), batch_size):
            batch = record_ids[i:i+batch_size]
            try:
                table.batch_delete(batch)
                print(f"   Batch {i//batch_size + 1}/{(len(record_ids) + batch_size - 1)//batch_size} completed")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"   ❌ Error deleting batch: {e}")
    
    print("\n✅ Cleanup completed!")

def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate reservations')
    parser.add_argument('--env', choices=['dev', 'prod'], default='prod', help='Environment')
    parser.add_argument('--execute', action='store_true', help='Execute cleanup (default is dry run)')
    parser.add_argument('--limit', type=int, default=20, help='Max properties to show in summary')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()
    
    # Setup configuration
    if args.env == 'dev':
        config = DevConfig()
    else:
        config = ProdConfig()
    
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    reservations_table = base.table('Reservations')
    properties_table = base.table('Properties')
    
    print(f"🚀 Duplicate Cleanup - {args.env.upper()} Environment")
    print(f"   Base ID: {config.get_airtable_base_id()}")
    print(f"   Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find duplicates
    duplicates_to_fix, stats, property_names = find_duplicates_to_clean(
        reservations_table, properties_table
    )
    
    if not duplicates_to_fix:
        print("\n✅ No duplicates found!")
        return
    
    # Plan cleanup
    cleanup_plan = plan_cleanup(duplicates_to_fix)
    
    # Show plan
    print_cleanup_plan(cleanup_plan, property_names, args.limit)
    
    # Execute if requested
    if args.execute:
        print("\n" + "="*80)
        print("⚠️  EXECUTING CLEANUP")
        print("="*80)
        
        if args.yes:
            response = 'yes'
        else:
            response = input("\nAre you sure you want to proceed? Type 'yes' to continue: ")
        
        if response.lower() == 'yes':
            # Generate backup filename with timestamp
            backup_file = f"duplicate_cleanup_backup_{args.env}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            execute_cleanup(reservations_table, cleanup_plan, dry_run=False, backup_file=backup_file)
        else:
            print("\n❌ Cleanup cancelled")
    else:
        print("\n💡 To execute cleanup, run with --execute flag")

if __name__ == "__main__":
    main()