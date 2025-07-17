#\!/usr/bin/env python3
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

print("🔍 Searching for Mayes property reservations...")

# Get all records for this property
all_records = []
page_num = 1
for page in table.iterate(page_size=100, fields=['Property ID', 'Check-in Date', 'Check-out Date', 'Status', 'Reservation UID', 'Last Updated', 'ICS URL']):
    print(f"Processing page {page_num}...")
    for record in page:
        fields = record['fields']
        prop_ids = fields.get('Property ID', [])
        if 'recRQSv5kFaVKAXdj' in prop_ids:
            all_records.append(record)
    page_num += 1

print(f"\n📊 Found {len(all_records)} total records for Mayes property")

# Group by dates
date_groups = defaultdict(list)
for record in all_records:
    fields = record['fields']
    checkin = fields.get('Check-in Date', '')
    checkout = fields.get('Check-out Date', '')
    key = (checkin, checkout)
    date_groups[key].append(record)

# Find duplicates
duplicate_groups = [(k, v) for k, v in date_groups.items() if len(v) > 1]
print(f"\n🚨 Found {len(duplicate_groups)} date ranges with multiple records")

# Show top 10 duplicate groups
for i, ((checkin, checkout), records) in enumerate(duplicate_groups[:10]):
    print(f"\n{i+1}. Dates: {checkin} to {checkout} ({len(records)} records)")
    for rec in sorted(records, key=lambda r: r['fields'].get('Last Updated', ''), reverse=True):
        status = rec['fields'].get('Status', 'Unknown')
        uid = rec['fields'].get('Reservation UID', 'No UID')
        updated = rec['fields'].get('Last Updated', 'Unknown')
        print(f"   - [{status}] {rec['id']}  < /dev/null |  UID: {uid[:40]}... | Updated: {updated}")

# Count by status
status_counts = defaultdict(int)
for record in all_records:
    status = record['fields'].get('Status', 'Unknown')
    status_counts[status] += 1

print(f"\n📈 Record counts by status:")
for status, count in sorted(status_counts.items()):
    print(f"   - {status}: {count}")

