#!/usr/bin/env python3
"""
Find records that were incorrectly marked as "Old" during the cleanup.
A record was incorrectly marked if there's no other "New" record with the same:
- Property ID
- Check-in Date  
- Check-out Date
- Entry Type
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict

config = ProdConfig()
api = Api(config.get_airtable_api_key())
base = api.base(config.get_airtable_base_id())
table = base.table('Reservations')

print("🔍 Finding records incorrectly marked as 'Old' during cleanup...")

# Get all records marked "Old" on July 17 around 7 AM (the cleanup time)
cleanup_old_records = []
print("📋 Loading records marked 'Old' during cleanup timeframe...")

for page in table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Entry Type', 'Status', 'Last Updated', 'Reservation UID']):
    for record in page:
        fields = record['fields']
        status = fields.get('Status', '')
        last_updated = fields.get('Last Updated', '')
        
        # Check if marked Old on July 17 around 7 AM
        if (status == 'Old' and '2025-07-17T07:' in last_updated):
            cleanup_old_records.append({
                'id': record['id'],
                'property_ids': fields.get('Property ID', []),
                'checkin': fields.get('Check-in Date', ''),
                'checkout': fields.get('Check-out Date', ''),
                'entry_type': fields.get('Entry Type', ''),
                'uid': fields.get('Reservation UID', ''),
                'last_updated': last_updated
            })

print(f"Found {len(cleanup_old_records)} records marked 'Old' during cleanup")

# Get all current "New" records to check for duplicates
print("📋 Loading all current 'New' records...")
current_new_records = []

for page in table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Entry Type', 'Status']):
    for record in page:
        fields = record['fields']
        status = fields.get('Status', '')
        
        if status == 'New':
            current_new_records.append({
                'id': record['id'],
                'property_ids': fields.get('Property ID', []),
                'checkin': fields.get('Check-in Date', ''),
                'checkout': fields.get('Check-out Date', ''),
                'entry_type': fields.get('Entry Type', '')
            })

print(f"Found {len(current_new_records)} current 'New' records")

# Create lookup for current "New" records
new_lookup = defaultdict(list)
for record in current_new_records:
    for prop_id in record['property_ids']:
        key = (prop_id, record['checkin'], record['checkout'], record['entry_type'])
        new_lookup[key].append(record)

# Find incorrectly marked "Old" records
incorrectly_marked = []
correctly_marked = []

print("\n🔍 Analyzing cleanup records...")

for old_record in cleanup_old_records:
    # Check if there's a "New" record with same property/dates/type
    has_new_duplicate = False
    
    for prop_id in old_record['property_ids']:
        key = (prop_id, old_record['checkin'], old_record['checkout'], old_record['entry_type'])
        if key in new_lookup:
            has_new_duplicate = True
            break
    
    if has_new_duplicate:
        correctly_marked.append(old_record)
    else:
        incorrectly_marked.append(old_record)

print(f"\n📊 ANALYSIS RESULTS:")
print(f"   - Correctly marked as 'Old' (has duplicate 'New' record): {len(correctly_marked)}")
print(f"   - INCORRECTLY marked as 'Old' (no duplicate 'New' record): {len(incorrectly_marked)}")

if incorrectly_marked:
    print(f"\n🚨 INCORRECTLY MARKED RECORDS (should be restored to 'New'):")
    for i, record in enumerate(incorrectly_marked[:10]):  # Show first 10
        print(f"{i+1:3d}. {record['id']} | {record['property_ids']} | {record['checkin']} to {record['checkout']} | {record['entry_type']} | {record['uid']}")
    
    if len(incorrectly_marked) > 10:
        print(f"     ... and {len(incorrectly_marked) - 10} more")
    
    print(f"\n💡 RECOMMENDATION:")
    print(f"   Restore these {len(incorrectly_marked)} records to 'New' status")
    print(f"   They were incorrectly marked 'Old' and have no current duplicates")
else:
    print(f"\n✅ ALL RECORDS WERE CORRECTLY MARKED!")
    print(f"   Every 'Old' record has a corresponding 'New' duplicate")

print(f"\n📋 Summary:")
print(f"   - Total cleanup records analyzed: {len(cleanup_old_records)}")
print(f"   - Safe to restore: {len(incorrectly_marked)}")
print(f"   - Should remain 'Old': {len(correctly_marked)}")