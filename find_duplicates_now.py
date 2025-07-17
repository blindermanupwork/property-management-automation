#!/usr/bin/env python3
import sys
sys.path.append('/home/opc/automation')

from src.automation.config_prod import ProdConfig
from pyairtable import Api
from collections import defaultdict

config = ProdConfig()
api = Api(config.get_airtable_api_key())
base = api.base(config.get_airtable_base_id())
table = base.table('Reservations')

# Find exact duplicates - same property and same check-in date
property_date_groups = defaultdict(list)
count = 0

print("Scanning for duplicates in New records...")

for page in table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Status', 'Reservation UID']):
    for record in page:
        count += 1
        if count % 1000 == 0:
            print(f'Processed {count} records...', file=sys.stderr)
        
        fields = record['fields']
        status = fields.get('Status', '')
        if status != 'New':
            continue
            
        prop_ids = fields.get('Property ID', [])
        checkin = fields.get('Check-in Date', '')
        checkout = fields.get('Check-out Date', '')
        uid = fields.get('Reservation UID', '')
        
        for prop_id in prop_ids:
            key = (prop_id, checkin, checkout)
            property_date_groups[key].append({
                'id': record['id'],
                'uid': uid,
                'status': status
            })

# Show duplicates
print('\nCURRENT DUPLICATES (New status only):')
duplicate_count = 0
duplicate_groups = 0

for key, records in property_date_groups.items():
    if len(records) > 1:
        duplicate_groups += 1
        prop_id, checkin, checkout = key
        print(f'\n{duplicate_groups}. Property {prop_id}, {checkin} to {checkout}: {len(records)} records')
        for r in records:
            print(f'   - {r["id"]} | {r["uid"]} | {r["status"]}')
        duplicate_count += len(records)

print(f'\nSUMMARY:')
print(f'- Total duplicate groups: {duplicate_groups}')
print(f'- Total duplicate records: {duplicate_count}')

if duplicate_count == 0:
    print('NO DUPLICATES FOUND in New records')