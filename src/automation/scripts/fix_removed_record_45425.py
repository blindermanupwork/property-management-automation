#!/usr/bin/env python3
"""
Fix incorrectly removed record 45425
This record was marked as removed but is still active in the ICS feed
"""
import os
import sys
from datetime import datetime
from pyairtable import Api
import pytz

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_record_45425():
    """Fix the incorrectly removed record"""
    
    # Production base
    base_id = 'appZzebEIqCU5R9ER'
    table_id = 'tblaPnk0jxF47xWhL'
    
    # Get API key
    api_key = os.environ.get('AIRTABLE_API_KEY')
    if not api_key:
        print("ERROR: AIRTABLE_API_KEY not found in environment")
        return False
    
    api = Api(api_key)
    base = api.base(base_id)
    table = base.table(table_id)
    
    print("Searching for record 45425...")
    
    # Find the removed record
    records = table.all(formula="AND({ID}=45425, {Status}='Removed')")
    
    if not records:
        print("ERROR: Record 45425 with status 'Removed' not found")
        return False
    
    record = records[0]
    record_id = record['id']
    fields = record['fields']
    
    print(f"\nFound record:")
    print(f"  Record ID: {record_id}")
    print(f"  UID: {fields.get('Reservation UID')}")
    print(f"  Property: {fields.get('HCP Address (from Property ID)', ['Unknown'])[0]}")
    print(f"  Check-in: {fields.get('Check-in Date')}")
    print(f"  Check-out: {fields.get('Check-out Date')}")
    print(f"  Status: {fields.get('Status')}")
    print(f"  HCP Job: {fields.get('Service Job ID')}")
    
    # Update the record back to Modified (or New if it was never modified)
    arizona_tz = pytz.timezone('America/Phoenix')
    now = datetime.now(arizona_tz)
    
    updates = {
        'Status': 'Modified',  # Restore to active status
        'Last Updated': now.isoformat(sep=' ', timespec='seconds'),
        'Service Sync Details': fields.get('Service Sync Details', '') + 
                               f"\n\n**RESTORED** - Record incorrectly marked as removed, restored to active status - {now.strftime('%b %d, %I:%M %p')}"
    }
    
    # Clear removal tracking fields if they exist
    if 'Missing Count' in fields:
        updates['Missing Count'] = 0
    if 'Missing Since' in fields:
        updates['Missing Since'] = None
    
    print(f"\nUpdating record to restore active status...")
    
    try:
        table.update(record_id, updates)
        print("✅ SUCCESS: Record 45425 has been restored to active status")
        
        # Also check if there are any 'Old' versions that should be cleaned up
        old_records = table.all(formula=f"AND({{Reservation UID}}='{fields.get('Reservation UID')}', {{Status}}='Old')")
        if old_records:
            print(f"\nNote: Found {len(old_records)} old versions of this reservation that may need cleanup")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR updating record: {e}")
        return False


if __name__ == "__main__":
    fix_record_45425()