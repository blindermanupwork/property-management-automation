#!/usr/bin/env python3
"""
Test script to verify iTrip same-day turnover detection fix
Tests both the logic and actual Airtable records
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from pyairtable import Api

# Add parent directories to path
automation_root = Path(__file__).resolve().parent
sys.path.insert(0, str(automation_root))

from src.automation.config_prod import ProdConfig

def test_sameday_logic():
    """Test the same-day detection logic"""
    print("🧪 Testing Same-Day Detection Logic")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Same day - checkout and next guest same date',
            'checkout': '2025-08-09',
            'itrip_next': '2025-08-09',
            'expected': True
        },
        {
            'name': 'Not same day - next guest day after',
            'checkout': '2025-08-09',
            'itrip_next': '2025-08-10',
            'expected': False
        },
        {
            'name': 'Not same day - next guest 3 days later',
            'checkout': '2025-08-09',
            'itrip_next': '2025-08-12',
            'expected': False
        }
    ]
    
    for test in test_cases:
        checkout = datetime.fromisoformat(test['checkout'])
        next_checkin = datetime.fromisoformat(test['itrip_next'])
        
        # Compare dates only (ignore time)
        checkout_date_only = checkout.date()
        next_checkin_date_only = next_checkin.date()
        
        is_same_day = checkout_date_only == next_checkin_date_only
        
        status = "✅ PASS" if is_same_day == test['expected'] else "❌ FAIL"
        print(f"\n{status} {test['name']}")
        print(f"   Checkout: {test['checkout']}")
        print(f"   iTrip Next: {test['itrip_next']}")
        print(f"   Same day? {is_same_day} (expected: {test['expected']})")

def check_production_records():
    """Check actual production records that were fixed"""
    print("\n\n🔍 Checking Production Records")
    print("=" * 50)
    
    config = ProdConfig()
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    table = base.table('Reservations')
    
    # Check records 45604 and 45605
    record_ids = [45604, 45605]
    
    for record_id in record_ids:
        print(f"\n📋 Checking Record ID: {record_id}")
        
        # Get record by ID
        formula = f"{{ID}} = {record_id}"
        records = table.all(formula=formula)
        
        if not records:
            print(f"   ❌ Record not found")
            continue
            
        record = records[0]
        fields = record['fields']
        
        # Extract key fields
        checkout = fields.get('Check-out Date', 'N/A')
        itrip_next = fields.get('iTrip Next Guest Date', 'N/A')
        same_day_checkbox = fields.get('Same-day Turnover', False)
        service_line = fields.get('Service Line Description', 'N/A')
        entry_source = fields.get('Entry Source', 'N/A')
        
        print(f"   Entry Source: {entry_source}")
        print(f"   Check-out Date: {checkout}")
        print(f"   iTrip Next Guest Date: {itrip_next}")
        print(f"   Same-day Turnover Checkbox: {same_day_checkbox}")
        print(f"   Service Line: {service_line}")
        
        # Verify the fix worked
        if entry_source == 'iTrip' and checkout == itrip_next:
            if same_day_checkbox and 'SAME DAY' in service_line:
                print(f"   ✅ VERIFIED: Same-day correctly detected and service line updated")
            else:
                print(f"   ❌ ISSUE: Should be same-day but not correctly marked")
        else:
            print(f"   ℹ️  Not a same-day iTrip scenario")

def find_more_test_cases():
    """Find more iTrip records with same-day scenarios"""
    print("\n\n🔎 Finding More iTrip Same-Day Test Cases")
    print("=" * 50)
    
    config = ProdConfig()
    api = Api(config.get_airtable_api_key())
    base = api.base(config.get_airtable_base_id())
    table = base.table('Reservations')
    
    # Find iTrip records where checkout = itrip next guest date
    formula = "AND({Entry Source} = 'iTrip', {iTrip Next Guest Date} != '', {Service Job ID} != '')"
    records = table.all(formula=formula, max_records=20)
    
    same_day_count = 0
    
    print(f"\nFound {len(records)} iTrip records with jobs and next guest dates")
    
    for record in records:
        fields = record['fields']
        checkout = fields.get('Check-out Date', '')
        itrip_next = fields.get('iTrip Next Guest Date', '')
        
        if checkout and itrip_next and checkout == itrip_next:
            same_day_count += 1
            record_id = fields.get('ID', 'Unknown')
            same_day_checkbox = fields.get('Same-day Turnover', False)
            service_line = fields.get('Service Line Description', 'N/A')
            
            status = "✅" if (same_day_checkbox and 'SAME DAY' in service_line) else "❌"
            
            print(f"\n{status} Record {record_id}:")
            print(f"   Checkout & iTrip Next: {checkout}")
            print(f"   Same-day Checkbox: {same_day_checkbox}")
            print(f"   Service Line: {service_line[:50]}...")
    
    print(f"\n📊 Summary: Found {same_day_count} same-day iTrip scenarios")

if __name__ == '__main__':
    print("🚀 iTrip Same-Day Fix Verification Test")
    print("=" * 70)
    
    # Run all tests
    test_sameday_logic()
    check_production_records()
    find_more_test_cases()
    
    print("\n\n✅ Test completed!")