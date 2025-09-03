#!/usr/bin/env python3
"""
Find ALL reservation records where:
1. They have a Service Job ID
2. Final Service Date != Checkout Date
"""

import requests
import json
import os
from datetime import datetime, date

# Airtable config
AIRTABLE_BASE_ID = "appZzebEIqCU5R9ER"
AIRTABLE_TABLE_ID = "tblaPnk0jxF47xWhL"
AIRTABLE_API_KEY = "REDACTED_PROD_API_KEY"

def get_all_records_with_job_ids():
    """Get all records that have Service Job ID"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    
    all_records = []
    params = {
        "filterByFormula": "AND(NOT({Service Job ID} = ''), NOT({Scheduled Service Time} = ''), NOT({Check-out Date} = ''))",
        "pageSize": 100
    }
    
    while True:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        records = data.get('records', [])
        
        if not records:
            break
            
        all_records.extend(records)
        print(f"Fetched {len(records)} records (total: {len(all_records)})")
        
        # Check for next page
        offset = data.get('offset')
        if not offset:
            break
        params['offset'] = offset
    
    return all_records

def find_mismatches(records):
    """Find records where Scheduled Service Date != Checkout Date and checkout is today or future"""
    mismatches = []
    today = date.today()
    
    for record in records:
        fields = record.get('fields', {})
        
        airtable_id = fields.get('ID')
        checkout_date = fields.get('Check-out Date')
        scheduled_service_time = fields.get('Scheduled Service Time')
        service_job_id = fields.get('Service Job ID')
        
        if not all([airtable_id, checkout_date, scheduled_service_time, service_job_id]):
            continue
        
        # Parse checkout date to compare with today
        try:
            checkout_date_obj = datetime.strptime(checkout_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            continue
        
        # Only process if checkout is today or in the future
        if checkout_date_obj < today:
            continue
        
        # Extract date from Scheduled Service Time (remove time portion)
        if 'T' in scheduled_service_time:
            service_date = scheduled_service_time.split('T')[0]
        else:
            service_date = scheduled_service_time
        
        # Compare dates
        if checkout_date != service_date:
            mismatches.append({
                'airtable_id': airtable_id,
                'checkout_date': checkout_date,
                'service_date': service_date,
                'service_job_id': service_job_id
            })
    
    return mismatches

def main():
    print("Finding records with Service Job IDs where Scheduled Service Date != Checkout Date")
    print("(Filtered for checkout dates TODAY and FUTURE only)")
    print("=" * 80)
    
    # Get all records
    print("Fetching all records with Service Job IDs...")
    all_records = get_all_records_with_job_ids()
    print(f"Total records with Service Job IDs: {len(all_records)}")
    
    # Find mismatches
    print("\nAnalyzing for date mismatches...")
    mismatches = find_mismatches(all_records)
    
    if not mismatches:
        print("No mismatches found!")
        return
    
    print(f"\nFound {len(mismatches)} mismatched records:")
    
    # Output comma-separated IDs
    ids = [str(m['airtable_id']) for m in mismatches]
    print(f"\nAirtable IDs: {','.join(ids)}")
    
    # Output details
    print(f"\nDetails:")
    for i, match in enumerate(mismatches, 1):
        print(f"{i}. ID: {match['airtable_id']} | Checkout: {match['checkout_date']} | Scheduled: {match['service_date']}")

if __name__ == "__main__":
    main()