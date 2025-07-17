#!/usr/bin/env python3
"""
Find all Airtable IDs that were incorrectly marked as "Removed" during the UID bug incident
"""

import sys
from pathlib import Path
import os

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from pyairtable import Api

def find_removed_ids():
    """
    Find all record IDs that were incorrectly marked as Removed during incident
    """
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    
    # Re-import to get prod config
    from src.automation.config_wrapper import get_config
    config = get_config()
    
    api = Api(config.get_airtable_api_key())
    base_id = config.get_airtable_base_id()
    table = api.table(base_id, "Reservations")
    
    print("🔍 FINDING INCORRECTLY REMOVED RECORDS")
    print("="*80)
    
    # Target records marked as Removed on July 11, 2025 (all hours during incident)
    formula = """AND(
        {Status} = 'Removed',
        DATESTR({Last Updated}) = '2025-07-11'
    )"""
    
    print("Searching for records marked as Removed on incident date...")
    print("Date: 2025-07-11 (all hours)")
    
    removed_records = table.all(
        formula=formula,
        fields=["ID", "Reservation UID", "Status", "Last Updated"]
    )
    
    print(f"\nFound {len(removed_records)} records marked as Removed during incident")
    
    if len(removed_records) == 0:
        print("No records found to restore")
        return []
    
    # Extract Airtable IDs for the batch script
    airtable_ids = []
    record_ids = []  # The actual record IDs for API calls
    
    for record in removed_records:
        airtable_id = record["fields"].get("ID")
        record_id = record["id"]  # The record ID for API calls
        
        if airtable_id and record_id:
            airtable_ids.append(airtable_id)
            record_ids.append(record_id)
    
    print(f"\nCollected {len(airtable_ids)} valid record IDs")
    
    # Write IDs to file for the batch script
    ids_file = "/home/opc/automation/removed_record_ids.txt"
    with open(ids_file, "w") as f:
        for record_id in record_ids:
            f.write(f"{record_id}\n")
    
    print(f"Record IDs written to: {ids_file}")
    
    # Also write Airtable IDs for reference
    airtable_ids_file = "/home/opc/automation/removed_airtable_ids.txt"
    with open(airtable_ids_file, "w") as f:
        for airtable_id in airtable_ids:
            f.write(f"{airtable_id}\n")
    
    print(f"Airtable IDs written to: {airtable_ids_file}")
    
    # Show sample of what will be restored
    print(f"\nSample records to be restored:")
    for i, record in enumerate(removed_records[:10]):
        fields = record["fields"]
        print(f"  {i+1}. ID: {fields.get('ID')}")
        print(f"     UID: {fields.get('Reservation UID', '')[:60]}...")
        print(f"     Last Updated: {fields.get('Last Updated')}")
    
    if len(removed_records) > 10:
        print(f"  ... and {len(removed_records) - 10} more records")
    
    return record_ids

if __name__ == "__main__":
    record_ids = find_removed_ids()
    print(f"\n✅ Found {len(record_ids)} records to restore")
    print("Next: Run batch_restore_records.py to restore them all")