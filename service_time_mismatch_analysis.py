#!/usr/bin/env python3
"""
Script to find Airtable records where Final Service Time != Check-out Date
and the record has a Service Job ID.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Import airtable-prod MCP functions
def get_airtable_records_with_service_jobs():
    """Get all records with Service Job ID and compare Final Service Time vs Check-out Date"""
    
    # Since we can't directly call MCP from Python, we'll use a different approach
    # This is a conceptual script - in practice we'd need to implement the MCP calls
    
    mismatched_records = []
    
    # Sample data from the MCP response we saw earlier
    # In a real implementation, we'd paginate through all records
    sample_records = [
        {
            "id": "rec01wrOHDBjyopU7",
            "Check-out Date": "2025-07-27",
            "Final Service Time": "2025-07-27T17:00:00.000Z",
            "Service Job ID": "job_06e49f5b6e49474b835c5ac07ce190a5"
        },
        {
            "id": "rec05wFybE3ej75EN", 
            "Check-out Date": "2025-08-09",
            "Final Service Time": "2025-08-09T17:00:00.000Z",
            "Service Job ID": "job_672bdda438a44dc18cc81afebc2136bf"
        },
        {
            "id": "rec07qYBsqAJQR4iu",
            "Check-out Date": "2025-06-30", 
            "Final Service Time": "2025-06-30T17:15:00.000Z",
            "Service Job ID": "job_8718427afc9348d994f96343ebe0d0cf"
        }
        # ... more records would be processed here
    ]
    
    for record in sample_records:
        checkout_date = record.get("Check-out Date")
        final_service_time = record.get("Final Service Time")
        service_job_id = record.get("Service Job ID")
        
        if not all([checkout_date, final_service_time, service_job_id]):
            continue
            
        # Extract date from Final Service Time
        service_date = final_service_time.split('T')[0] if 'T' in final_service_time else final_service_time
        
        # Compare dates
        if checkout_date != service_date:
            mismatched_records.append({
                'airtable_id': record['id'],
                'checkout_date': checkout_date,
                'final_service_time': final_service_time,
                'service_job_id': service_job_id
            })
    
    return mismatched_records

if __name__ == "__main__":
    print("Analyzing service time mismatches...")
    mismatched = get_airtable_records_with_service_jobs()
    
    if mismatched:
        print("\nFound mismatched records:")
        ids = [record['airtable_id'] for record in mismatched]
        print(','.join(ids))
        
        print(f"\nDetails for {len(mismatched)} records:")
        for record in mismatched:
            print(f"ID: {record['airtable_id']} | Checkout: {record['checkout_date']} | Service: {record['final_service_time']}")
    else:
        print("No mismatched records found in sample data")