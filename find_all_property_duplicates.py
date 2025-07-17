#!/usr/bin/env python3
"""
Find all properties with significant duplication issues.

This script:
1. Scans all reservations in the production Airtable
2. Groups by property and dates
3. Identifies properties with excessive duplicates
4. Reports the top problematic properties
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict
import argparse

def main():
    parser = argparse.ArgumentParser(description='Find all property duplicates')
    parser.add_argument('--min-duplicates', type=int, default=5, help='Minimum duplicates to report')
    parser.add_argument('--limit', type=int, default=20, help='Max properties to show')
    args = parser.parse_args()
    
    config = ProdConfig()
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    reservations_table = base.table('Reservations')
    properties_table = base.table('Properties')
    
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
    
    for page in reservations_table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Status', 'Last Updated']):
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
        
        if duplicate_date_count >= args.min_duplicates or max_duplicates_per_date >= args.min_duplicates:
            property_duplicate_stats.append({
                'property_id': prop_id,
                'property_name': property_names.get(prop_id, 'Unknown'),
                'duplicate_date_ranges': duplicate_date_count,
                'total_duplicate_records': total_duplicate_records,
                'max_duplicates_per_date': max_duplicates_per_date,
                'total_records': len([r for date_records in date_groups.values() for r in date_records])
            })
    
    # Sort by most problematic
    property_duplicate_stats.sort(key=lambda x: (x['total_duplicate_records'], x['duplicate_date_ranges']), reverse=True)
    
    print(f"\n🚨 Found {len(property_duplicate_stats)} properties with significant duplicates\n")
    
    # Show top problematic properties
    for i, stats in enumerate(property_duplicate_stats[:args.limit]):
        print(f"{i+1:2d}. {stats['property_name'][:60]}")
        print(f"     Property ID: {stats['property_id']}")
        print(f"     Total Records: {stats['total_records']}")
        print(f"     Duplicate Date Ranges: {stats['duplicate_date_ranges']}")
        print(f"     Total Duplicate Records: {stats['total_duplicate_records']}")
        print(f"     Max Duplicates per Date: {stats['max_duplicates_per_date']}")
        print()
    
    if len(property_duplicate_stats) > args.limit:
        print(f"... and {len(property_duplicate_stats) - args.limit} more properties with duplicates")
    
    # Show overall statistics
    total_duplicate_records = sum(s['total_duplicate_records'] for s in property_duplicate_stats)
    total_duplicate_dates = sum(s['duplicate_date_ranges'] for s in property_duplicate_stats)
    
    print(f"\n📈 Overall Statistics:")
    print(f"   - Properties with duplicates: {len(property_duplicate_stats)}")
    print(f"   - Total duplicate date ranges: {total_duplicate_dates}")
    print(f"   - Total duplicate records: {total_duplicate_records}")
    print(f"   - Percentage of all records: {(total_duplicate_records/all_records_count)*100:.1f}%")

if __name__ == "__main__":
    main()