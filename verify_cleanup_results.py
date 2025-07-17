#!/usr/bin/env python3
"""
Verification script to check the results of our duplicate cleanup.
Compares before/after statistics to show improvement.
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict

def main():
    config = ProdConfig()
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    reservations_table = base.table('Reservations')
    
    print(f"🔍 Verifying cleanup results...")
    
    # Scan all reservations
    property_date_groups = defaultdict(lambda: defaultdict(list))
    status_counts = defaultdict(int)
    all_records_count = 0
    page_num = 1
    
    for page in reservations_table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Status']):
        print(f"Processing page {page_num}...", end='\r')
        for record in page:
            all_records_count += 1
            fields = record['fields']
            status = fields.get('Status', 'Unknown')
            status_counts[status] += 1
            
            prop_ids = fields.get('Property ID', [])
            checkin = fields.get('Check-in Date', '')
            checkout = fields.get('Check-out Date', '')
            
            for prop_id in prop_ids:
                date_key = (checkin, checkout)
                property_date_groups[prop_id][date_key].append(record)
        page_num += 1
    
    print(f"\n📊 Current Database Status:")
    print(f"   - Total records: {all_records_count}")
    for status, count in sorted(status_counts.items()):
        print(f"   - {status}: {count}")
    
    # Find remaining duplicates
    properties_with_duplicates = 0
    total_duplicate_date_ranges = 0
    total_duplicate_records = 0
    
    for prop_id, date_groups in property_date_groups.items():
        duplicate_date_count = 0
        duplicate_record_count = 0
        
        for date_key, records in date_groups.items():
            if len(records) > 1:
                duplicate_date_count += 1
                duplicate_record_count += len(records)
        
        if duplicate_date_count > 0:
            properties_with_duplicates += 1
            total_duplicate_date_ranges += duplicate_date_count
            total_duplicate_records += duplicate_record_count
    
    print(f"\n🎯 Duplicate Analysis:")
    print(f"   - Properties with duplicates: {properties_with_duplicates}")
    print(f"   - Total duplicate date ranges: {total_duplicate_date_ranges}")
    print(f"   - Total duplicate records: {total_duplicate_records}")
    print(f"   - Percentage of duplicates: {(total_duplicate_records/all_records_count)*100:.1f}%")
    
    # Show improvement (comparing to our earlier analysis)
    print(f"\n📈 Improvement Summary:")
    print(f"   - Before cleanup: 130+ properties had duplicates")
    print(f"   - After cleanup: {properties_with_duplicates} properties have duplicates")
    print(f"   - Before cleanup: ~81.6% of records were duplicates")
    print(f"   - After cleanup: {(total_duplicate_records/all_records_count)*100:.1f}% of records are duplicates")
    
    if properties_with_duplicates == 0:
        print(f"\n🎉 SUCCESS: All duplicate issues have been resolved!")
    else:
        print(f"\n💡 Remaining duplicates may be legitimate (different sources, etc.)")

if __name__ == "__main__":
    main()