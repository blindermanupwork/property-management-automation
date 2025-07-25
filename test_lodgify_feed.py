#!/usr/bin/env python3
"""
Test script to debug Lodgify duplicate detection issue
Processes only the Mayes Lodgify feed
"""

import sys
import os
sys.path.insert(0, '/home/opc/automation')

from pyairtable import Table
from src.automation.config_prod import ProdConfig as Config
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_mayes_records():
    """Check the current state of Mayes records"""
    
    config = Config()
    AIRTABLE_API_KEY = config.get_airtable_api_key()
    AIRTABLE_BASE_ID = config.get_airtable_base_id()
    
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "Reservations")
    
    # Search for Mayes records
    print("\n🔍 Searching for Mayes Lodgify records...")
    
    # Get all records that might be related
    formula = "OR(FIND('44905', {Reservation UID}), FIND('44851', {Reservation UID}), FIND('44920', {Reservation UID}))"
    records = table.all(formula=formula)
    
    print(f"\nFound {len(records)} records:")
    for rec in records:
        fields = rec['fields']
        print(f"\nRecord ID: {rec['id']}")
        print(f"  UID: {fields.get('Reservation UID', 'N/A')}")
        print(f"  Status: {fields.get('Status', 'N/A')}")
        print(f"  Property: {fields.get('Property', 'N/A')}")
        print(f"  Check-in: {fields.get('Check-in Date', 'N/A')}")
        print(f"  Check-out: {fields.get('Check-out Date', 'N/A')}")
        print(f"  Entry Type: {fields.get('Entry Type', 'N/A')}")
        print(f"  ICS URL: {fields.get('ICS URL', 'N/A')}")
        
    # Also check by property and dates
    print("\n🔍 Checking for any records with same property and dates...")
    
    # You'll need to update this with the actual property ID and dates
    # property_formula = "AND({Property ID} = 'recXXX', {Check-in Date} = '2025-XX-XX')"
    
if __name__ == "__main__":
    check_mayes_records()