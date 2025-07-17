#!/usr/bin/env python3
"""Trace the Same-day Turnover issue through the CSV processing flow"""

import os
os.environ['ENVIRONMENT'] = 'production'

from pyairtable import Api
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Load production environment variables
from dotenv import load_dotenv
load_dotenv('/home/opc/automation/config/environments/prod/.env')

# Initialize
api_key = os.getenv('PROD_AIRTABLE_API_KEY')
base_id = os.getenv('PROD_AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)
table = base.table('Reservations')

# Look for the specific UID
uid = '4580366_recZBaV3gl4yPC15z'
formula = f"{{Reservation UID}}='{uid}'"

print(f"\nSearching for all records with UID: {uid}")
records = table.all(formula=formula, max_records=10)

print(f"Found {len(records)} records")

# Sort by ID to see chronological order
sorted_records = sorted(records, key=lambda r: r['fields'].get('ID', 0))

for i, rec in enumerate(sorted_records):
    fields = rec['fields']
    print(f"\n--- Record {i+1} ---")
    print(f"Airtable ID: {rec['id']}")
    print(f"ID: {fields.get('ID')}")
    print(f"Status: {fields.get('Status')}")
    print(f"Same-day Turnover: {fields.get('Same-day Turnover')} (type: {type(fields.get('Same-day Turnover'))})")
    print(f"Service Line: {fields.get('Service Line Description')}")
    print(f"Last Updated: {fields.get('Last Updated')}")
    print(f"Check-in: {fields.get('Check-in Date')}")
    print(f"Check-out: {fields.get('Check-out Date')}")

# Now check if there's a pattern - look for the creation record
print("\n\nAnalyzing the history...")
if len(sorted_records) >= 2:
    newest = sorted_records[0]['fields']
    older = sorted_records[1]['fields']
    
    print(f"Newest record has Same-day = {newest.get('Same-day Turnover')}")
    print(f"Older record has Same-day = {older.get('Same-day Turnover')}")
    
    if newest.get('Same-day Turnover') != older.get('Same-day Turnover'):
        print("\n⚠️ SAME-DAY FLAG CHANGED BETWEEN RECORDS!")