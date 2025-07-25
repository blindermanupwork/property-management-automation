#!/usr/bin/env python3
"""
Comprehensive Duplicate Cleanup Script
=====================================
Groups reservations by property, then by check-in/check-out dates and entry type.
Keeps the latest record from each group based on Last Updated timestamp.

Features:
- Dry run mode by default (use --execute to actually fix)
- Can target specific properties by name or Airtable ID
- Exports detailed report of what will be kept/removed
- Groups by property for clear visibility
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import logging
import argparse
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.automation.config_prod import ProdConfig as Config
from pyairtable import Api

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DuplicateCleanup:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.config = Config()
        self.api = Api(self.config.get_airtable_api_key())
        self.base = self.api.base(self.config.get_airtable_base_id())
        self.reservations_table = self.base.table('Reservations')
        self.properties_table = self.base.table('Properties')
        self.property_names = {}
        self.load_property_names()
        
    def load_property_names(self):
        """Load all property names for better reporting."""
        logging.info("Loading property names...")
        for record in self.properties_table.all(fields=['Property Name']):
            prop_name = record['fields'].get('Property Name', '')
            # Just use property name
            display_name = prop_name
            self.property_names[record['id']] = display_name if display_name else f"Property {record['id']}"
        logging.info(f"Loaded {len(self.property_names)} property names")
        
    def get_property_display_name(self, prop_id):
        """Get a human-readable property name."""
        return self.property_names.get(prop_id, f"Unknown Property ({prop_id})")
        
    def parse_date(self, date_str):
        """Parse date string to datetime object for comparison."""
        if not date_str:
            return datetime.min.replace(tzinfo=None)
        try:
            # Handle ISO format with timezone
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                # Remove timezone info for consistent comparison
                return dt.replace(tzinfo=None)
            # Handle simple date format
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return datetime.min.replace(tzinfo=None)
            
    def find_duplicates_by_property(self, target_property=None):
        """Find all duplicates grouped by property."""
        logging.info("Fetching all active reservations...")
        
        # Only get active records (not Old or Removed)
        formula = "AND(NOT({Status} = 'Old'), NOT({Status} = 'Removed'))"
        
        all_records = self.reservations_table.all(formula=formula)
        logging.info(f"Found {len(all_records)} active records")
        
        # Group records by property
        property_groups = defaultdict(lambda: defaultdict(list))
        
        for record in all_records:
            fields = record['fields']
            prop_ids = fields.get('Property ID', [])
            checkin = fields.get('Check-in Date', '')
            checkout = fields.get('Check-out Date', '')
            entry_type = fields.get('Entry Type', '')
            
            # Skip if missing critical fields
            if not prop_ids or not checkin or not checkout:
                continue
                
            for prop_id in prop_ids:
                # Skip if targeting specific property and this isn't it
                if target_property:
                    prop_name = self.get_property_display_name(prop_id)
                    if target_property != prop_id and target_property.lower() not in prop_name.lower():
                        continue
                
                # Group key: checkin + checkout + entry_type
                group_key = (checkin, checkout, entry_type)
                property_groups[prop_id][group_key].append(record)
        
        # Find properties with duplicates
        duplicate_report = {}
        total_duplicates = 0
        total_to_remove = 0
        
        for prop_id, date_groups in property_groups.items():
            prop_duplicates = []
            
            for (checkin, checkout, entry_type), records in date_groups.items():
                if len(records) > 1:
                    # Sort by Last Updated (newest first), then by ID (highest first)
                    sorted_records = sorted(records, 
                                          key=lambda r: (
                                              self.parse_date(r['fields'].get('Last Updated', '')),
                                              r['fields'].get('ID', 0)
                                          ), 
                                          reverse=True)
                    
                    # Keep the first (newest), mark others for removal
                    keep_record = sorted_records[0]
                    remove_records = sorted_records[1:]
                    
                    duplicate_info = {
                        'checkin': checkin,
                        'checkout': checkout,
                        'entry_type': entry_type,
                        'total_records': len(records),
                        'keep': {
                            'id': keep_record['id'],
                            'airtable_id': keep_record['fields'].get('ID'),
                            'uid': keep_record['fields'].get('Reservation UID', 'NO_UID'),
                            'status': keep_record['fields'].get('Status'),
                            'source': keep_record['fields'].get('Entry Source'),
                            'last_updated': keep_record['fields'].get('Last Updated', 'Unknown'),
                            'guest': keep_record['fields'].get('Guest Name', 'Unknown'),
                            'has_job': bool(keep_record['fields'].get('Service Job ID'))
                        },
                        'remove': []
                    }
                    
                    for rem_record in remove_records:
                        duplicate_info['remove'].append({
                            'id': rem_record['id'],
                            'airtable_id': rem_record['fields'].get('ID'),
                            'uid': rem_record['fields'].get('Reservation UID', 'NO_UID'),
                            'status': rem_record['fields'].get('Status'),
                            'source': rem_record['fields'].get('Entry Source'),
                            'last_updated': rem_record['fields'].get('Last Updated', 'Unknown'),
                            'guest': rem_record['fields'].get('Guest Name', 'Unknown'),
                            'has_job': bool(rem_record['fields'].get('Service Job ID'))
                        })
                    
                    prop_duplicates.append(duplicate_info)
                    total_duplicates += len(records)
                    total_to_remove += len(remove_records)
            
            if prop_duplicates:
                duplicate_report[prop_id] = {
                    'property_name': self.get_property_display_name(prop_id),
                    'duplicate_groups': len(prop_duplicates),
                    'duplicates': prop_duplicates
                }
        
        return duplicate_report, total_duplicates, total_to_remove
        
    def export_report(self, duplicate_report, filename='duplicate_report.json'):
        """Export detailed duplicate report to JSON file."""
        with open(filename, 'w') as f:
            json.dump(duplicate_report, f, indent=2)
        logging.info(f"Exported detailed report to {filename}")
        
    def print_summary(self, duplicate_report, total_duplicates, total_to_remove):
        """Print a summary of duplicates found."""
        print("\n" + "="*80)
        print("DUPLICATE CLEANUP SUMMARY")
        print("="*80)
        print(f"Properties with duplicates: {len(duplicate_report)}")
        print(f"Total duplicate records: {total_duplicates}")
        print(f"Records to remove: {total_to_remove}")
        print(f"Records to keep: {total_duplicates - total_to_remove}")
        
        print("\n" + "-"*80)
        print("PROPERTIES WITH DUPLICATES:")
        print("-"*80)
        
        for prop_id, prop_data in duplicate_report.items():
            print(f"\n📍 {prop_data['property_name']} ({prop_id})")
            print(f"   Duplicate groups: {prop_data['duplicate_groups']}")
            
            for dup in prop_data['duplicates']:
                print(f"\n   📅 {dup['checkin']} to {dup['checkout']} - {dup['entry_type']}")
                print(f"      Total records: {dup['total_records']}")
                print(f"      ✅ KEEP: ID {dup['keep']['airtable_id']} - {dup['keep']['guest']} ({dup['keep']['source']})")
                print(f"         Updated: {dup['keep']['last_updated']}")
                if dup['keep']['has_job']:
                    print(f"         🔧 Has HCP Job")
                
                for rem in dup['remove']:
                    print(f"      ❌ REMOVE: ID {rem['airtable_id']} - {rem['guest']} ({rem['source']})")
                    print(f"         Updated: {rem['last_updated']}")
                    if rem['has_job']:
                        print(f"         ⚠️  Has HCP Job (will be preserved)")
        
    def execute_cleanup(self, duplicate_report):
        """Actually perform the cleanup by marking duplicates as Old."""
        if self.dry_run:
            logging.info("DRY RUN - No changes will be made")
            return
            
        logging.info("EXECUTING cleanup...")
        updated_count = 0
        
        for prop_id, prop_data in duplicate_report.items():
            for dup in prop_data['duplicates']:
                for rem in dup['remove']:
                    try:
                        # Update record to Old status
                        self.reservations_table.update(rem['id'], {'Status': 'Old'})
                        updated_count += 1
                        logging.info(f"Updated record {rem['id']} (ID: {rem['airtable_id']}) to Old status")
                    except Exception as e:
                        logging.error(f"Failed to update record {rem['id']}: {e}")
        
        logging.info(f"✅ Cleanup complete! Updated {updated_count} records to Old status")
        
def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate reservations by property')
    parser.add_argument('--execute', action='store_true', help='Execute the cleanup (default is dry-run)')
    parser.add_argument('--property', type=str, help='Target specific property by name or Airtable ID')
    parser.add_argument('--export', type=str, default='duplicate_report.json', help='Export report filename')
    
    args = parser.parse_args()
    
    cleanup = DuplicateCleanup(dry_run=not args.execute)
    
    # Find duplicates
    duplicate_report, total_duplicates, total_to_remove = cleanup.find_duplicates_by_property(
        target_property=args.property
    )
    
    if not duplicate_report:
        print("\n✅ No duplicates found!")
        return
        
    # Export report
    cleanup.export_report(duplicate_report, args.export)
    
    # Print summary
    cleanup.print_summary(duplicate_report, total_duplicates, total_to_remove)
    
    # Execute if requested
    if args.execute:
        print("\n" + "="*80)
        response = input("⚠️  Are you sure you want to mark these duplicates as Old? (yes/no): ")
        if response.lower() == 'yes':
            cleanup.execute_cleanup(duplicate_report)
        else:
            print("Cleanup cancelled.")
    else:
        print("\n" + "="*80)
        print("This was a DRY RUN. To execute the cleanup, run with --execute")
        print("="*80)

if __name__ == '__main__':
    main()