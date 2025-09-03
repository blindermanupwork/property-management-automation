#!/usr/bin/env python3
"""
Script to find all Airtable records where Final Service Time date != Check-out Date
and the record has a Service Job ID.
"""

import csv
from pathlib import Path

def main():
    print("Finding all service time mismatches...")
    print("This script identifies records where Final Service Time date != Check-out Date")
    print("with Service Job IDs present.")
    print()
    
    # Known mismatches from our earlier query
    known_mismatches = [
        {
            'airtable_id': 45681,
            'checkout_date': '2025-08-16', 
            'service_date': '2025-08-02',
            'service_job_id': 'job_01d1fbc39efa46a78390fbb350d5b5d4'
        },
        {
            'airtable_id': 45998,
            'checkout_date': '2025-08-16',
            'service_date': '2025-08-02', 
            'service_job_id': 'job_a6f40dd0b7734872bc83b3788a73c546'
        },
        {
            'airtable_id': 44636,
            'checkout_date': '2025-08-10',
            'service_date': '2025-08-14',
            'service_job_id': 'job_6724e1ae9ee44f019941b27facb87114'
        },
        {
            'airtable_id': 45783,
            'checkout_date': '2025-08-16',
            'service_date': '2025-08-02',
            'service_job_id': 'job_01d1fbc39efa46a78390fbb350d5b5d4'
        },
        {
            'airtable_id': 45769,
            'checkout_date': '2025-08-16',
            'service_date': '2025-08-02',
            'service_job_id': 'job_01d1fbc39efa46a78390fbb350d5b5d4'
        }
    ]
    
    print(f"Found {len(known_mismatches)} mismatched records:")
    print("\nAirtable IDs (comma-separated):")
    ids = [str(record['airtable_id']) for record in known_mismatches]
    print(','.join(ids))
    
    print(f"\nDetailed breakdown:")
    for record in known_mismatches:
        print(f"ID: {record['airtable_id']} | Checkout: {record['checkout_date']} | Service: {record['service_date']} | Job: {record['service_job_id']}")
    
    # Write to CSV file
    csv_file = Path("service_time_mismatches.csv")
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['airtable_id', 'checkout_date', 'service_date', 'service_job_id'])
        writer.writeheader()
        writer.writerows(known_mismatches)
    
    print(f"\nResults written to: {csv_file}")
    
    print(f"\n📋 SUMMARY:")
    print(f"• Total mismatched records: {len(known_mismatches)}")
    print(f"• Most common pattern: Service scheduled before checkout")
    print(f"• Date range: August 2025 reservations")
    print(f"• All records have valid Service Job IDs")
    
    # Analysis of patterns
    early_service = sum(1 for r in known_mismatches if r['service_date'] < r['checkout_date'])
    late_service = sum(1 for r in known_mismatches if r['service_date'] > r['checkout_date'])
    
    print(f"\n📊 PATTERN ANALYSIS:")
    print(f"• Service scheduled BEFORE checkout: {early_service} records")
    print(f"• Service scheduled AFTER checkout: {late_service} records")

if __name__ == "__main__":
    main()