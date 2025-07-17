#!/usr/bin/env python3
"""Test to understand the same-day turnover issue"""

import sys
import os
sys.path.insert(0, '/home/opc/automation')

from datetime import datetime
from src.automation.config_wrapper import Config
from pyairtable import Api

# Initialize with production environment
os.environ['ENVIRONMENT'] = 'production'
# Reimport Config after setting environment
from src.automation.config_wrapper import Config
config = Config
api = Api(config.AIRTABLE_API_KEY)
base = api.base(config.AIRTABLE_BASE_ID)
table = base.table('Reservations')

# Find a record with the issue
print("Searching for records with same-day mismatch...")
records = table.all(
    formula="AND({Reservation UID}='4580366_recZBaV3gl4yPC15z', {Status}='Modified')",
    fields=['ID', 'Same-day Turnover', 'Status', 'Last Updated', 'Service Line Description']
)

for rec in records:
    fields = rec['fields']
    print(f"\nRecord ID: {fields.get('ID')}")
    print(f"Same-day Turnover: {fields.get('Same-day Turnover')} (type: {type(fields.get('Same-day Turnover'))})")
    print(f"Status: {fields.get('Status')}")
    print(f"Service Line: {fields.get('Service Line Description')}")
    print(f"Last Updated: {fields.get('Last Updated')}")

# Test creating a record with Same-day = True
print("\n\nTesting record creation with Same-day = True...")
test_fields = {
    'Entry Type': 'Reservation',
    'Service Type': 'Turnover',
    'Guest Name': 'TEST SAME DAY',
    'Check-in Date': '2025-12-25',
    'Check-out Date': '2025-12-26',
    'Property ID': ['recZBaV3gl4yPC15z'],
    'Entry Source': 'Test',
    'Reservation UID': 'TEST_SAMEDAY_123',
    'Status': 'New',
    'Same-day Turnover': True,
    'ICS URL': 'test',
}

print(f"Creating with Same-day Turnover = {test_fields['Same-day Turnover']} (type: {type(test_fields['Same-day Turnover'])})")

try:
    new_rec = table.create(test_fields)
    print(f"Created record ID: {new_rec['id']}")
    
    # Read it back
    check_rec = table.get(new_rec['id'])
    same_day_value = check_rec['fields'].get('Same-day Turnover')
    print(f"Read back Same-day Turnover = {same_day_value} (type: {type(same_day_value)})")
    
    # Clean up
    table.delete(new_rec['id'])
    print("Test record deleted")
    
except Exception as e:
    print(f"Error: {e}")