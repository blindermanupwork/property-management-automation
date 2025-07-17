#!/usr/bin/env python3
"""
Find all current duplicates in Airtable Reservations table.
Identifies records with same Property ID + Check-in + Check-out + Entry Type.
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict
from datetime import datetime
import argparse

def find_all_duplicates(table, properties_table):
    """Find all duplicate reservations grouped by property/dates/type."""
    
    print("🔍 Scanning for duplicate reservations...")
    
    # Get property names for better reporting
    print("📋 Loading property names...")
    property_names = {}
    for page in properties_table.iterate(page_size=100, fields=['Property Name']):
        for record in page:
            property_names[record['id']] = record['fields'].get('Property Name', 'Unknown')
    
    print(f"   Loaded {len(property_names)} property names")
    
    # Group reservations by property/dates/type
    duplicate_groups = defaultdict(list)
    all_records = []
    active_records = 0
    total_records = 0
    
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
            
            # Only consider active records (New/Modified)
            if status in ['New', 'Modified']:
                active_records += 1
                prop_ids = fields.get('Property ID', [])
                checkin = fields.get('Check-in Date', '')
                checkout = fields.get('Check-out Date', '')
                entry_type = fields.get('Entry Type', '')
                
                for prop_id in prop_ids:
                    # Create unique key for grouping (NOT including Entry Source)
                    key = (prop_id, checkin, checkout, entry_type)
                    duplicate_groups[key].append(record)
            
            all_records.append(record)
    
    print(f"\n📈 Scan complete:")
    print(f"   - Total records: {total_records:,}")
    print(f"   - Active records (New/Modified/Removed): {active_records:,}")
    print(f"   - Unique combinations: {len(duplicate_groups):,}")
    
    # Find actual duplicates (groups with more than 1 record)
    actual_duplicates = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
    
    # Calculate statistics
    total_duplicate_records = sum(len(records) for records in actual_duplicates.values())
    
    print(f"\n🚨 Duplicate Summary:")
    print(f"   - Groups with duplicates: {len(actual_duplicates):,}")
    print(f"   - Total duplicate records: {total_duplicate_records:,}")
    print(f"   - Average duplicates per group: {total_duplicate_records/len(actual_duplicates):.1f}" if actual_duplicates else "")
    
    # Group by property for analysis
    property_stats = defaultdict(lambda: {'groups': 0, 'records': 0, 'examples': []})
    
    for (prop_id, checkin, checkout, entry_type), records in actual_duplicates.items():
        property_stats[prop_id]['groups'] += 1
        property_stats[prop_id]['records'] += len(records)
        if len(property_stats[prop_id]['examples']) < 3:  # Keep first 3 examples
            property_stats[prop_id]['examples'].append({
                'dates': f"{checkin} to {checkout}",
                'type': entry_type,
                'count': len(records),
                'statuses': [r['fields'].get('Status', 'Unknown') for r in records],
                'sources': list(set([r['fields'].get('Entry Source', 'Unknown') for r in records])),
                'uids': [r['fields'].get('Reservation UID', 'No UID') for r in records]
            })
    
    # Sort by most problematic properties
    sorted_properties = sorted(
        [(prop_id, stats) for prop_id, stats in property_stats.items()],
        key=lambda x: (x[1]['records'], x[1]['groups']),
        reverse=True
    )
    
    return {
        'total_records': total_records,
        'active_records': active_records,
        'duplicate_groups': actual_duplicates,
        'property_stats': sorted_properties,
        'property_names': property_names
    }

def print_detailed_report(results):
    """Print detailed duplicate report."""
    
    duplicate_groups = results['duplicate_groups']
    property_stats = results['property_stats']
    property_names = results['property_names']
    
    print("\n" + "="*80)
    print("🏠 TOP PROPERTIES WITH DUPLICATES")
    print("="*80)
    
    # Show top 20 properties
    for i, (prop_id, stats) in enumerate(property_stats[:20]):
        prop_name = property_names.get(prop_id, 'Unknown')
        print(f"\n{i+1}. {prop_name}")
        print(f"   Property ID: {prop_id}")
        print(f"   Duplicate groups: {stats['groups']}")
        print(f"   Total duplicate records: {stats['records']}")
        print(f"   Examples:")
        for example in stats['examples']:
            sources_str = '/'.join(example['sources']) if example['sources'] else 'Unknown'
            print(f"      - {example['dates']} ({example['type']}/{sources_str}): {example['count']} records")
            print(f"        Statuses: {', '.join(example['statuses'])}")
            for uid in example['uids'][:3]:  # Show first 3 UIDs
                print(f"        • {uid}")
    
    # Show some specific duplicate examples
    print("\n" + "="*80)
    print("📋 SAMPLE DUPLICATE DETAILS")
    print("="*80)
    
    examples_shown = 0
    for (prop_id, checkin, checkout, entry_type), records in duplicate_groups.items():
        if examples_shown >= 10:
            break
        
        prop_name = property_names.get(prop_id, 'Unknown')
        print(f"\n🔍 Property: {prop_name}")
        print(f"   Dates: {checkin} to {checkout}")
        print(f"   Entry Type: {entry_type}")
        print(f"   Duplicate Count: {len(records)}")
        print("   Records:")
        
        for record in records:
            fields = record['fields']
            print(f"      - ID: {record['id']}")
            print(f"        UID: {fields.get('Reservation UID', 'No UID')}")
            # Guest name not available in this table
            print(f"        Source: {fields.get('Entry Source', 'Unknown')}")
            print(f"        Status: {fields.get('Status', 'Unknown')}")
            print(f"        Updated: {fields.get('Last Updated', 'Unknown')}")
        
        examples_shown += 1

def main():
    parser = argparse.ArgumentParser(description='Find all duplicates in Airtable')
    parser.add_argument('--env', choices=['dev', 'prod'], default='prod', help='Environment')
    parser.add_argument('--export', help='Export results to JSON file')
    args = parser.parse_args()
    
    # Setup configuration
    if args.env == 'dev':
        from src.automation.config_dev import DevConfig
        config = DevConfig()
    else:
        config = ProdConfig()
    
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    reservations_table = base.table('Reservations')
    properties_table = base.table('Properties')
    
    print(f"🚀 Analyzing duplicates in {args.env.upper()} environment")
    print(f"   Base ID: {config.get_airtable_base_id()}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find duplicates
    results = find_all_duplicates(reservations_table, properties_table)
    
    # Print report
    print_detailed_report(results)
    
    # Export if requested
    if args.export:
        import json
        # Convert to serializable format
        export_data = {
            'metadata': {
                'environment': args.env,
                'timestamp': datetime.now().isoformat(),
                'total_records': results['total_records'],
                'active_records': results['active_records'],
                'duplicate_groups': len(results['duplicate_groups']),
                'total_duplicate_records': sum(len(v) for v in results['duplicate_groups'].values())
            },
            'property_summary': [
                {
                    'property_id': prop_id,
                    'property_name': results['property_names'].get(prop_id, 'Unknown'),
                    'duplicate_groups': stats['groups'],
                    'duplicate_records': stats['records'],
                    'examples': stats['examples']
                }
                for prop_id, stats in results['property_stats'][:50]  # Top 50
            ]
        }
        
        with open(args.export, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"\n💾 Results exported to {args.export}")

if __name__ == "__main__":
    main()