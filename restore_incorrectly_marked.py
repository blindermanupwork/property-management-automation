#!/usr/bin/env python3
"""
Restore records that were incorrectly marked as "Old" during cleanup.
For each group of incorrectly marked duplicates, restore only the most recent one to "New".
"""

import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict
from datetime import datetime

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

print("\n🔍 Analyzing cleanup records...")

for old_record in cleanup_old_records:
    # Check if there's a "New" record with same property/dates/type
    has_new_duplicate = False
    
    for prop_id in old_record['property_ids']:
        key = (prop_id, old_record['checkin'], old_record['checkout'], old_record['entry_type'])
        if key in new_lookup:
            has_new_duplicate = True
            break
    
    if not has_new_duplicate:
        incorrectly_marked.append(old_record)

print(f"Found {len(incorrectly_marked)} incorrectly marked records")

# Group incorrectly marked records by property/dates/type
print("\n🔍 Grouping incorrectly marked records...")
groups = defaultdict(list)

for record in incorrectly_marked:
    for prop_id in record['property_ids']:
        key = (prop_id, record['checkin'], record['checkout'], record['entry_type'])
        groups[key].append(record)

print(f"Found {len(groups)} unique property/date/type combinations")

# For each group, select the most recent record to restore
records_to_restore = []
total_in_groups = 0

for key, group_records in groups.items():
    total_in_groups += len(group_records)
    # Sort by last_updated descending and take the most recent
    most_recent = max(group_records, key=lambda r: r['last_updated'])
    records_to_restore.append(most_recent)
    
    prop_id, checkin, checkout, entry_type = key
    print(f"Group {prop_id} {checkin}-{checkout} {entry_type}: {len(group_records)} records → restoring {most_recent['id']}")

print(f"\n📊 RESTORATION PLAN:")
print(f"   - Total incorrectly marked records: {len(incorrectly_marked)}")
print(f"   - Grouped into {len(groups)} unique combinations")
print(f"   - Records to restore to 'New': {len(records_to_restore)}")
print(f"   - Records to leave as 'Old': {len(incorrectly_marked) - len(records_to_restore)}")

# Proceed with restoration
print(f"\n⚠️  Proceeding to restore {len(records_to_restore)} records to 'New' status")

if True:
    print(f"\n🔄 Restoring {len(records_to_restore)} records...")
    
    updates = []
    for record in records_to_restore:
        updates.append({
            'id': record['id'],
            'fields': {
                'Status': 'New',
                'Last Updated': datetime.now().isoformat()
            }
        })
    
    # Update in batches
    batch_size = 10
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        table.batch_update(batch)
        print(f"   Updated batch {i//batch_size + 1}/{(len(updates) + batch_size - 1)//batch_size}")
    
    print(f"\n✅ Successfully restored {len(records_to_restore)} records to 'New' status")
    print(f"📋 Summary:")
    print(f"   - Each property/date/type combination now has exactly 1 'New' record")
    print(f"   - Remaining duplicates stayed as 'Old' records")
    print(f"   - Fixed the cleanup script damage without recreating duplicate problem")
else:
    print("❌ Restoration cancelled")