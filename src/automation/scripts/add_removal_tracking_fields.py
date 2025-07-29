#!/usr/bin/env python3
"""
Add removal tracking fields to Airtable Reservations table
"""
import os
import sys
from pyairtable import Api

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_tracking_fields(environment='prod'):
    """Add Missing Count, Missing Since, and Last Seen fields to Reservations table"""
    
    # Get the appropriate base ID
    if environment == 'prod':
        base_id = 'appZzebEIqCU5R9ER'
        print("Adding fields to PRODUCTION base")
    else:
        base_id = 'app67yWFv0hKdl6jM'
        print("Adding fields to DEVELOPMENT base")
    
    # Get API key
    api_key = os.environ.get('AIRTABLE_API_KEY')
    if not api_key:
        print("ERROR: AIRTABLE_API_KEY not found in environment")
        return False
    
    api = Api(api_key)
    base = api.base(base_id)
    
    # Table ID for Reservations
    table_id = 'tblaPnk0jxF47xWhL'
    
    print(f"\nAdding removal tracking fields to {environment} Reservations table...")
    
    # Field definitions
    fields_to_add = [
        {
            "name": "Missing Count",
            "type": "number",
            "options": {
                "precision": 0  # No decimal places
            },
            "description": "Number of consecutive syncs where this reservation was missing from ICS feed"
        },
        {
            "name": "Missing Since", 
            "type": "dateTime",
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "America/Phoenix"
            },
            "description": "Timestamp when reservation was first detected missing from ICS feed"
        },
        {
            "name": "Last Seen",
            "type": "dateTime", 
            "options": {
                "dateFormat": {"name": "us"},
                "timeFormat": {"name": "12hour"},
                "timeZone": "America/Phoenix"
            },
            "description": "Last timestamp when reservation was found in ICS feed"
        }
    ]
    
    # Note: Airtable API doesn't support creating fields directly
    # We'll need to use the MCP server instead
    print("\nTo add these fields, use the Airtable MCP server with these definitions:")
    for field in fields_to_add:
        print(f"\n- Field: {field['name']}")
        print(f"  Type: {field['type']}")
        print(f"  Description: {field['description']}")
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add removal tracking fields to Airtable")
    parser.add_argument('--env', choices=['dev', 'prod'], default='prod',
                        help='Environment to update (default: prod)')
    args = parser.parse_args()
    
    add_tracking_fields(args.env)