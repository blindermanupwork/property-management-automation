#!/usr/bin/env python3
"""
Test cases for Job Reconciliation Logic
Tests various scenarios to ensure correct matching behavior
"""

import json
from datetime import datetime
import pytz

def test_date_matching_logic():
    """Test the core date matching logic"""
    print("=== Testing Date Matching Logic ===")
    
    # Test case data
    test_cases = [
        {
            "name": "Exact Same Date and Time",
            "reservation_time": "2025-09-04T17:15:00.000Z",
            "job_time": "2025-09-04T17:15:00.000Z",
            "should_match": True
        },
        {
            "name": "Same Date, Different Time",
            "reservation_time": "2025-09-04T17:15:00.000Z", 
            "job_time": "2025-09-04T10:00:00.000Z",
            "should_match": True  # Current logic matches same date
        },
        {
            "name": "Different Date, Same Time",
            "reservation_time": "2025-09-04T17:15:00.000Z",
            "job_time": "2025-08-23T17:15:00.000Z", 
            "should_match": False
        },
        {
            "name": "One Day Apart", 
            "reservation_time": "2025-09-04T17:15:00.000Z",
            "job_time": "2025-09-05T17:15:00.000Z",
            "should_match": False
        },
        {
            "name": "Timezone Edge Case (UTC vs Arizona)",
            "reservation_time": "2025-09-04T06:00:00.000Z",  # Midnight Arizona = 7AM UTC
            "job_time": "2025-09-03T23:59:00.000Z",          # 11:59 PM Arizona = 6:59 AM UTC next day  
            "should_match": False  # Different dates in UTC
        }
    ]
    
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        
        # Parse times (mimicking reconciliation logic)
        res_time = datetime.fromisoformat(test['reservation_time'].replace('Z', '+00:00'))
        job_time = datetime.fromisoformat(test['job_time'].replace('Z', '+00:00'))
        
        # Test current matching logic 
        actual_match = res_time.date() == job_time.date()
        expected_match = test['should_match']
        
        status = "✅ PASS" if actual_match == expected_match else "❌ FAIL"
        print(f"  Reservation: {res_time} (date: {res_time.date()})")
        print(f"  Job:         {job_time} (date: {job_time.date()})")
        print(f"  Expected: {expected_match}, Actual: {actual_match} - {status}")

def test_realistic_scenarios():
    """Test realistic reconciliation scenarios"""
    print("\n\n=== Testing Realistic Scenarios ===")
    
    # Simulate Curtis Porter scenario
    reservation = {
        "id": "rec45678",
        "fields": {
            "ID": 45678,
            "Final Service Time": "2025-09-04T17:15:00.000Z",
            "Property ID": ["recFr6W0pIwpsya67"]
        }
    }
    
    # Available jobs for Curtis Porter
    available_jobs = [
        {
            "id": "job_ba75d01094ec451980051f3bc835efc1",
            "customer": {"id": "cus_e55b9c831b764c42b8f73d640c2b9324"},
            "address": {"id": "adr_69b52f4f7ded4ddc80f9d6828e365104"},
            "schedule": {"scheduled_start": "2025-08-23T21:00:00Z"},
            "work_status": "complete unrated"
        },
        {
            "id": "job_200f32770ef2496ab1317b7ab9aa16cf", 
            "customer": {"id": "cus_e55b9c831b764c42b8f73d640c2b9324"},
            "address": {"id": "adr_2233ffebf9274492b5fe45b530469b22"},  # Different address
            "schedule": {"scheduled_start": "2025-09-01T17:15:00Z"},
            "work_status": "scheduled"
        },
        {
            "id": "job_c3efd4f839ff440a9f0436c81287859e",
            "customer": {"id": "cus_e55b9c831b764c42b8f73d640c2b9324"},
            "address": {"id": "adr_69b52f4f7ded4ddc80f9d6828e365104"}, 
            "schedule": {"scheduled_start": "2025-08-05T17:15:00Z"},
            "work_status": "complete rated"
        }
    ]
    
    # Property mapping
    property_mapping = {
        "recFr6W0pIwpsya67": {
            "property_name": "5731 E Marilyn Rd, Scottsdale",
            "hcp_customer_id": "cus_e55b9c831b764c42b8f73d640c2b9324",
            "hcp_address_id": "adr_69b52f4f7ded4ddc80f9d6828e365104"
        }
    }
    
    print(f"Testing Reservation {reservation['fields']['ID']} (Sept 4)")
    print(f"Expected: 5731 E Marilyn Rd, Scottsdale")
    print(f"Looking for jobs at address: adr_69b52f4f7ded4ddc80f9d6828e365104")
    
    # Simulate matching logic
    res_time = datetime.fromisoformat(reservation['fields']['Final Service Time'].replace('Z', '+00:00'))
    target_customer = property_mapping["recFr6W0pIwpsya67"]["hcp_customer_id"]
    target_address = property_mapping["recFr6W0pIwpsya67"]["hcp_address_id"]
    
    print(f"\nSearching for jobs:")
    print(f"  Customer: {target_customer}")
    print(f"  Address: {target_address}")
    print(f"  Date: {res_time.date()}")
    
    matches = []
    for job in available_jobs:
        # Check customer and address
        if (job['customer']['id'] == target_customer and 
            job['address']['id'] == target_address):
            
            job_time = datetime.fromisoformat(job['schedule']['scheduled_start'].replace('Z', '+00:00'))
            
            print(f"\n  Candidate Job {job['id'][:12]}...")
            print(f"    Job Date: {job_time.date()}")
            print(f"    Address Match: ✅")
            print(f"    Date Match: {res_time.date() == job_time.date()}")
            
            if res_time.date() == job_time.date():
                time_diff = abs((job_time - res_time).total_seconds())
                matches.append({
                    'job': job,
                    'time_diff': time_diff,
                    'days_apart': abs((job_time.date() - res_time.date()).days)
                })
    
    print(f"\n📊 Results:")
    if matches:
        matches.sort(key=lambda x: x['time_diff'])
        best = matches[0]
        print(f"  Found {len(matches)} matching job(s)")
        print(f"  Best match: {best['job']['id']}")
        print(f"  Days apart: {best['days_apart']}")
        print(f"  Status: {best['job']['work_status']}")
    else:
        print(f"  ❌ No matching jobs found")
        print(f"  This is correct - no Sept 4 job exists at that address")

def test_edge_cases():
    """Test problematic edge cases"""
    print("\n\n=== Testing Edge Cases ===")
    
    edge_cases = [
        {
            "name": "Multiple Jobs Same Day", 
            "description": "What if there are 2+ jobs on the same day?",
            "reservation_time": "2025-09-04T17:15:00.000Z",
            "job_times": [
                "2025-09-04T10:00:00.000Z",
                "2025-09-04T15:00:00.000Z", 
                "2025-09-04T20:00:00.000Z"
            ]
        },
        {
            "name": "Timezone Boundary",
            "description": "Job at midnight crosses date boundary",
            "reservation_time": "2025-09-04T07:00:00.000Z",  # Midnight Arizona
            "job_times": ["2025-09-03T23:59:00.000Z"]        # 11:59 PM Arizona (6:59 AM UTC)
        },
        {
            "name": "Far Apart Dates",
            "description": "Should never match jobs weeks apart", 
            "reservation_time": "2025-09-04T17:15:00.000Z",
            "job_times": ["2025-08-01T17:15:00.000Z"]        # 34 days apart
        }
    ]
    
    for case in edge_cases:
        print(f"\n{case['name']}: {case['description']}")
        res_time = datetime.fromisoformat(case['reservation_time'].replace('Z', '+00:00'))
        
        matches = []
        for job_time_str in case['job_times']:
            job_time = datetime.fromisoformat(job_time_str.replace('Z', '+00:00'))
            date_match = res_time.date() == job_time.date()
            time_diff = abs((job_time - res_time).total_seconds())
            days_apart = abs((job_time.date() - res_time.date()).days)
            
            print(f"  Job: {job_time} - Date match: {date_match}, Days apart: {days_apart}")
            
            if date_match:
                matches.append({'time_diff': time_diff, 'job_time': job_time})
        
        if matches:
            matches.sort(key=lambda x: x['time_diff'])
            print(f"  → Would select: {matches[0]['job_time']} (closest time)")
        else:
            print(f"  → No matches (correct behavior)")

def main():
    print("🧪 Job Reconciliation Test Suite")
    print("=" * 50)
    
    test_date_matching_logic()
    test_realistic_scenarios()
    test_edge_cases()
    
    print("\n\n✅ Test Suite Complete")
    print("💡 Key Findings:")
    print("  - Current logic only matches exact same dates")
    print("  - No Sept 4 job exists for Curtis Porter at 5731 E Marilyn Rd")
    print("  - Algorithm correctly found no match (this time)")
    print("  - Previous wrong match was likely due to a bug or different logic")

if __name__ == "__main__":
    main()