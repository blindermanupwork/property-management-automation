#!/usr/bin/env python3
"""
Diagnose why 433 records were incorrectly removed
"""

import sys
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from pyairtable import Api

def analyze_recent_removals():
    """Check what was recently marked as removed"""
    
    config = Config
    api = Api(config.get_airtable_token())
    
    # Get production base
    base_id = config.get_airtable_base_id()
    table = api.table(base_id, "Reservations")
    
    print("🔍 ANALYZING RECENT REMOVALS")
    print("="*80)
    
    # Find records marked as "Removed" today
    from datetime import date
    today_str = date.today().isoformat()
    
    formula = f"AND({{Status}} = 'Removed', DATESTR({{Last Updated}}) = '{today_str}')"
    removed_today = table.all(
        formula=formula,
        fields=["ID", "Reservation UID", "Check-in Date", "Check-out Date", 
               "Property ID", "Entry Type", "Last Updated", "ICS URL"]
    )
    
    print(f"Found {len(removed_today)} records marked as Removed today")
    
    if len(removed_today) == 0:
        print("No removals found for today")
        return
    
    # Analyze patterns
    print("\n1. SAMPLE OF REMOVED RECORDS:")
    for i, record in enumerate(removed_today[:10]):
        fields = record["fields"]
        uid = fields.get("Reservation UID", "")
        property_ids = fields.get("Property ID", [])
        property_id = property_ids[0] if property_ids else "NO_PROPERTY"
        composite_uid = f"{uid}_{property_id}" if property_id != "NO_PROPERTY" else uid
        
        print(f"  {i+1}. ID: {fields.get('ID')}")
        print(f"     UID: {uid}")
        print(f"     Property ID: {property_id}")
        print(f"     Composite UID: {composite_uid}")
        print(f"     Dates: {fields.get('Check-in Date')} to {fields.get('Check-out Date')}")
        print(f"     Type: {fields.get('Entry Type')}")
        print(f"     Feed: {fields.get('ICS URL', 'NO_FEED')[:80]}...")
        print()
    
    # Check if any of these UIDs still exist in feeds
    print("\n2. CHECKING IF THESE UIDS STILL EXIST AS 'New' RECORDS:")
    unique_uids = set()
    for record in removed_today:
        uid = record["fields"].get("Reservation UID", "")
        if uid:
            unique_uids.add(uid)
    
    print(f"   Checking {len(unique_uids)} unique UIDs...")
    
    # Look for New/Modified records with same UIDs
    for uid in list(unique_uids)[:5]:  # Check first 5
        formula = f"AND({{Reservation UID}} = '{uid}', OR({{Status}} = 'New', {{Status}} = 'Modified'))"
        still_active = table.all(formula=formula, fields=["ID", "Status", "Property ID"])
        
        if still_active:
            print(f"   ⚠️  UID {uid[:30]}... still has ACTIVE records:")
            for rec in still_active:
                prop_ids = rec["fields"].get("Property ID", [])
                prop_id = prop_ids[0] if prop_ids else "NO_PROPERTY"
                print(f"       ID: {rec['fields'].get('ID')} - Property: {prop_id}")
        else:
            print(f"   ✓ UID {uid[:30]}... correctly has no active records")
    
    # Property analysis
    print("\n3. PROPERTY ANALYSIS:")
    property_counts = {}
    for record in removed_today:
        property_ids = record["fields"].get("Property ID", [])
        if property_ids:
            prop_id = property_ids[0]
            property_counts[prop_id] = property_counts.get(prop_id, 0) + 1
    
    print(f"   Removals affected {len(property_counts)} properties:")
    sorted_props = sorted(property_counts.items(), key=lambda x: x[1], reverse=True)
    for prop_id, count in sorted_props[:10]:
        print(f"   - {prop_id}: {count} removals")

if __name__ == "__main__":
    analyze_recent_removals()