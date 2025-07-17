#!/usr/bin/env python3
"""
Analyze duplicate detection logic for ICS sync
"""

import json
import requests
from datetime import datetime

# Production Airtable settings
AIRTABLE_API_KEY = "patxCGJzJxxfzjJJa.9cea1db97c962feb693f89e97733d88a7cf07e31a013b4a20c6f12c11fefaa0e"
BASE_ID = "appZzebEIqCU5R9ER"
TABLE_ID = "tblaPnk0jxF47xWhL"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def get_records_for_property_dates(property_id, checkin, checkout):
    """Get all records for a property with specific dates"""
    formula = f"AND({{Property ID}}='{property_id}', {{Check-in Date}}='{checkin}', {{Check-out Date}}='{checkout}')"
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_ID}"
    params = {
        "filterByFormula": formula,
        "fields[]": ["ID", "Status", "Reservation UID", "Check-in Date", "Check-out Date", "Last Updated"]
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()["records"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def main():
    print("="*80)
    print("DUPLICATE DETECTION ANALYSIS")
    print("="*80)
    
    # Property and dates from record 37717
    property_id = "recVu3YtfTaoK3siK"
    checkin = "2025-07-20"
    checkout = "2025-08-18"
    
    print(f"\n1. Searching for all records with:")
    print(f"   Property: {property_id}")
    print(f"   Check-in: {checkin}")
    print(f"   Check-out: {checkout}")
    
    records = get_records_for_property_dates(property_id, checkin, checkout)
    
    print(f"\n2. Found {len(records)} records:")
    for rec in records:
        fields = rec["fields"]
        uid = fields.get("Reservation UID", "N/A")
        base_uid = uid.split("_")[0] if "_" in uid else uid
        print(f"\n   Record ID: {fields.get('ID')}")
        print(f"   Status: {fields.get('Status')}")
        print(f"   Full UID: {uid}")
        print(f"   Base UID: {base_uid}")
        print(f"   Last Updated: {fields.get('Last Updated')}")
    
    print("\n3. DUPLICATE DETECTION ISSUE:")
    print("   The ICS processor should detect that these are the same reservation")
    print("   because they have the same property/dates but different UIDs.")
    print("   This should prevent the old record from being marked as 'Removed'.")
    
    print("\n4. CURRENT FEED ANALYSIS:")
    print("   Feed has 3 events, one of which is the SAME reservation with new UID")
    print("   Old UID: 1418fb94e984-a6b8c8bea2d3e211eb681e0caa686cf8@airbnb.com")
    print("   New UID: 1418fb94e984-9d7bd29cff405425b4abc5f366d0402c@airbnb.com")
    
    print("\n5. WHY DUPLICATE DETECTION FAILED:")
    print("   The duplicate_detected_dates set is only populated when status='Duplicate_Ignored'")
    print("   But when processing the new UID, it creates a NEW record instead of detecting duplicate")
    print("   So the duplicate key is never added to duplicate_detected_dates")
    print("   Therefore, during removal, it doesn't skip the old record")

if __name__ == "__main__":
    main()