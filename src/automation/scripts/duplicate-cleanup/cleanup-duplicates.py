#!/usr/bin/env python3
"""
Comprehensive Duplicate Cleanup Script with CSV Export
======================================================
Groups reservations by property, then by check-in/check-out dates and entry type.
Keeps the latest record from each group based on Last Updated timestamp.

Features:
- Dry run mode by default (use --execute to actually fix)
- Can target specific properties by name or Airtable ID
- Exports detailed CSV reports for easy reading
- Organized folder structure with dated exports
- Groups by property for clear visibility
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import logging
import argparse
import json
import csv
import os

# Add parent directories to path for imports
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import config
from src.automation.config_wrapper import Config
from pyairtable import Api

# Set up logging to both file and console
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class DuplicateCleanup:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.config = Config
        self.api = Api(self.config.get_airtable_api_key())
        self.base = self.api.base(self.config.get_airtable_base_id())
        self.reservations_table = self.base.table('Reservations')
        self.properties_table = self.base.table('Properties')
        self.property_names = {}
        self.timestamp = datetime.now()
        self.export_dir = Path(__file__).parent / 'exports'
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.load_property_names()
        
    def load_property_names(self):
        """Load all property names for better reporting."""
        logging.info("Loading property names...")
        for record in self.properties_table.all(fields=['Property Name']):
            prop_name = record['fields'].get('Property Name', '')
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
            
    def find_duplicates_by_property(self, target_property=None, entry_types=None):
        """Find all duplicates grouped by property."""
        logging.info("Fetching all active reservations...")
        
        # Build formula based on entry types
        base_formula = "AND(NOT({Status} = 'Old'), NOT({Status} = 'Removed'))"
        
        if entry_types and entry_types != ['both']:
            type_conditions = []
            if 'reservation' in entry_types:
                type_conditions.append("{Entry Type} = 'Reservation'")
            if 'block' in entry_types:
                type_conditions.append("{Entry Type} = 'Block'")
            if type_conditions:
                type_formula = f"OR({', '.join(type_conditions)})"
                formula = f"AND({base_formula}, {type_formula})"
            else:
                formula = base_formula
        else:
            formula = base_formula
        
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
                            'last_updated': keep_record['fields'].get('Last Updated') or keep_record['fields'].get('Sync Date and Time', 'Unknown'),
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
                            'last_updated': rem_record['fields'].get('Last Updated') or rem_record['fields'].get('Sync Date and Time', 'Unknown'),
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
        
    def get_export_filename(self, duplicate_report, target_property=None):
        """Generate appropriate filename based on dry run/execute and target."""
        # Generate dynamic timestamp
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%-m-%-d-%y %I%M%p").lower()
        action = "Analyze" if self.dry_run else "Executed"
        
        # Determine environment (Production or Development)
        env = "Prod" if self.config.is_production else "Dev"
        
        if target_property and len(duplicate_report) == 1:
            # Get the actual property name from the report
            prop_data = next(iter(duplicate_report.values()))
            prop_name = prop_data['property_name']
            # Clean property name for filename
            clean_name = "".join(c for c in prop_name if c.isalnum() or c in (' ', '-')).strip()
            # Truncate if too long
            if len(clean_name) > 50:
                clean_name = clean_name[:50].strip()
            filename = f"{env} {action} {date_str} {clean_name}.csv"
        else:
            filename = f"{env} {action} {date_str} ALL.csv"
            
        return self.export_dir / filename
        
    def export_consolidated_csv(self, duplicate_report, target_property=None):
        """Export a single consolidated CSV with all duplicate information."""
        export_file = self.get_export_filename(duplicate_report, target_property)
        
        with open(export_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Headers with Action in column 1
            writer.writerow([
                'Action', 'Property Name', 'Airtable ID',
                'Check-in', 'Check-out', 'Entry Type', 
                'UID', 'Source', 'Status', 'Last Updated', 'Has HCP Job'
            ])
            
            for prop_id, prop_data in duplicate_report.items():
                for dup in prop_data['duplicates']:
                    # Write the kept record
                    keep = dup['keep']
                    writer.writerow([
                        'KEEP',
                        prop_data['property_name'],
                        keep['airtable_id'],
                        dup['checkin'],
                        dup['checkout'],
                        dup['entry_type'],
                        keep['uid'],
                        keep['source'],
                        keep['status'],
                        keep['last_updated'],
                        'Yes' if keep['has_job'] else 'No'
                    ])
                    
                    # Write the removed records
                    for rem in dup['remove']:
                        writer.writerow([
                            'DROP',
                            prop_data['property_name'],
                            rem['airtable_id'],
                            dup['checkin'],
                            dup['checkout'],
                            dup['entry_type'],
                            rem['uid'],
                            rem['source'],
                            rem['status'],
                            rem['last_updated'],
                            'Yes' if rem['has_job'] else 'No'
                        ])
        
        logging.info(f"Exported consolidated report to {export_file}")
        return export_file
        
    def print_summary(self, duplicate_report, total_duplicates, total_to_remove, export_file):
        """Print a summary of duplicates found."""
        print("\n" + "="*80)
        print("DUPLICATE CLEANUP SUMMARY")
        print("="*80)
        print(f"Properties with duplicates: {len(duplicate_report)}")
        print(f"Total duplicate records: {total_duplicates}")
        print(f"Records to remove: {total_to_remove}")
        print(f"Records to keep: {total_duplicates - total_to_remove}")
        
        print("\n" + "-"*80)
        print("EXPORT FILE:")
        print("-"*80)
        print(f"📁 {export_file}")
        
    def execute_cleanup(self, duplicate_report, target_property=None):
        """Actually perform the cleanup by marking duplicates as Old."""
        if self.dry_run:
            logging.info("DRY RUN - No changes will be made")
            return 0, 0
            
        logging.info("EXECUTING cleanup...")
        updated_count = 0
        failed_count = 0
        
        # Collect all records to update
        records_to_update = []
        for prop_id, prop_data in duplicate_report.items():
            for dup in prop_data['duplicates']:
                for rem in dup['remove']:
                    records_to_update.append({
                        'id': rem['id'],
                        'fields': {'Status': 'Old'}
                    })
        
        # Process in batches of 100
        batch_size = 100
        total_records = len(records_to_update)
        logging.info(f"Processing {total_records} records in batches of {batch_size}...")
        
        for i in range(0, total_records, batch_size):
            batch = records_to_update[i:i+batch_size]
            batch_end = min(i+batch_size, total_records)
            logging.info(f"Processing batch {i//batch_size + 1}: records {i+1}-{batch_end} of {total_records}")
            
            try:
                # Batch update using Airtable's batch update method
                results = self.reservations_table.batch_update(batch)
                updated_count += len(batch)
                logging.info(f"✅ Batch update successful: {len(batch)} records")
            except Exception as e:
                failed_count += len(batch)
                logging.error(f"❌ Batch update failed: {e}")
                # Try individual updates as fallback
                logging.info("Attempting individual updates for failed batch...")
                for record in batch:
                    try:
                        self.reservations_table.update(record['id'], record['fields'])
                        updated_count += 1
                        failed_count -= 1
                        logging.info(f"✅ Individual update successful: {record['id']}")
                    except Exception as individual_e:
                        logging.error(f"❌ Individual update failed for {record['id']}: {individual_e}")
        
        logging.info(f"✅ Cleanup complete! Updated {updated_count} records, {failed_count} failures")
        return updated_count, failed_count
        
def main():
    parser = argparse.ArgumentParser(description='Clean up duplicate reservations by property')
    parser.add_argument('--execute', action='store_true', help='Execute the cleanup (default is dry-run)')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt (use with --execute)')
    parser.add_argument('--property', type=str, help='Target specific property by name or Airtable ID')
    parser.add_argument('--entry-type', type=str, choices=['reservation', 'block', 'both'], 
                        default='both', help='Filter by entry type (default: both)')
    
    args = parser.parse_args()
    
    cleanup = DuplicateCleanup(dry_run=not args.execute)
    
    # Parse entry types
    if args.entry_type == 'both':
        entry_types = ['reservation', 'block']
    else:
        entry_types = [args.entry_type]
    
    # Find duplicates
    duplicate_report, total_duplicates, total_to_remove = cleanup.find_duplicates_by_property(
        target_property=args.property,
        entry_types=entry_types
    )
    
    if not duplicate_report:
        print("\n✅ No duplicates found!")
        return
        
    # Export consolidated report
    export_file = cleanup.export_consolidated_csv(duplicate_report, target_property=args.property)
    
    # Print summary
    cleanup.print_summary(duplicate_report, total_duplicates, total_to_remove, export_file)
    
    # Execute if requested
    if args.execute:
        print("\n" + "="*80)
        if args.force:
            print("⚠️  Force mode enabled - executing cleanup without confirmation")
            response = 'yes'
        else:
            response = input("⚠️  Are you sure you want to mark these duplicates as Old? (yes/no): ")
        
        if response.lower() == 'yes':
            updated, failed = cleanup.execute_cleanup(duplicate_report, target_property=args.property)
            if updated > 0:
                print(f"\n✅ Successfully updated {updated} records to Old status")
            if failed > 0:
                print(f"⚠️  Failed to update {failed} records")
        else:
            print("Cleanup cancelled.")
    else:
        print("\n" + "="*80)
        print("This was a DRY RUN. To execute the cleanup, run with --execute")
        print("="*80)

if __name__ == '__main__':
    main()