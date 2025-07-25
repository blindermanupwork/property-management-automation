#!/usr/bin/env python3
"""
Test script to process a single ICS feed - specifically the Mayes Lodgify feed
This will help debug why the hybrid duplicate detection isn't working
"""

import sys
import os
sys.path.insert(0, '/home/opc/automation')

from src.automation.config_prod import ProdConfig as Config
from pyairtable import Table
import logging
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/test_mayes_ics.log')
    ]
)

def test_mayes_feed():
    """Test processing the Mayes Lodgify feed"""
    
    config = Config()
    AIRTABLE_API_KEY = config.get_airtable_api_key()
    AIRTABLE_BASE_ID = config.get_airtable_base_id()
    
    # Mayes Lodgify feed URL
    feed_url = "https://www.lodgify.com/oh/9f78ed10-1a08-4a32-9920-48fe2ac5ddcf.ics"
    property_id = "recRQSv5kFaVKAXdj"  # Mayes property ID
    
    logging.info(f"Testing Mayes Lodgify feed: {feed_url}")
    logging.info(f"Property ID: {property_id}")
    
    # Download the ICS content
    logging.info("Downloading ICS feed...")
    response = requests.get(feed_url)
    if response.status_code != 200:
        logging.error(f"Failed to download feed: {response.status_code}")
        return
    
    ics_content = response.text
    logging.info(f"Downloaded {len(ics_content)} bytes")
    
    # Save to file for inspection
    with open('/tmp/mayes_lodgify.ics', 'w') as f:
        f.write(ics_content)
    logging.info("Saved ICS content to /tmp/mayes_lodgify.ics")
    
    # Check current Airtable records
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, "Reservations")
    
    logging.info("\n🔍 Checking existing reservations for this property...")
    
    # Get all records for this property
    formula = f"{{Property ID}} = '{property_id}'"
    all_property_records = table.all(formula=formula)
    
    logging.info(f"Found {len(all_property_records)} total records for Mayes property")
    
    # Check for Aug 2-3 reservations
    aug_records = []
    for rec in all_property_records:
        fields = rec['fields']
        if fields.get('Check-in Date') == '2025-08-02' and fields.get('Check-out Date') == '2025-08-03':
            aug_records.append(rec)
            logging.info(f"\n  Aug 2-3 Record:")
            logging.info(f"    ID: {rec['id']}")
            logging.info(f"    UID: {fields.get('Reservation UID', 'N/A')}")
            logging.info(f"    Status: {fields.get('Status', 'N/A')}")
            logging.info(f"    Entry Type: {fields.get('Entry Type', 'N/A')}")
            logging.info(f"    ICS URL: {fields.get('ICS URL', 'N/A')}")
    
    if not aug_records:
        logging.warning("❌ No records found for Aug 2-3, 2025!")
    
    # Parse ICS content to check what's in the feed
    logging.info("\n📅 Parsing ICS content...")
    
    # Simple parse to find Aug 2-3 event
    lines = ics_content.split('\n')
    in_event = False
    current_event = {}
    
    for line in lines:
        line = line.strip()
        if line == 'BEGIN:VEVENT':
            in_event = True
            current_event = {}
        elif line == 'END:VEVENT':
            in_event = False
            # Check if this is Aug 2-3
            if current_event.get('DTSTART') == '20250802' and current_event.get('DTEND') == '20250803':
                logging.info("\n✅ Found Aug 2-3 event in ICS feed:")
                for k, v in current_event.items():
                    logging.info(f"    {k}: {v}")
        elif in_event and ':' in line:
            key, value = line.split(':', 1)
            if ';' in key:
                key = key.split(';')[0]
            current_event[key] = value
    
    # Now let's trace what would happen with the hybrid logic
    logging.info("\n🔍 Simulating hybrid duplicate detection...")
    
    # The new UID from the feed
    new_uid = "ceb333d7-2b77-4138-a8b1-634b9ffe7672"
    
    # Check if any existing records would match by property+dates+type
    for rec in all_property_records:
        fields = rec['fields']
        if (fields.get('Check-in Date') == '2025-08-02' and 
            fields.get('Check-out Date') == '2025-08-03' and
            fields.get('Entry Type') == 'Reservation' and
            fields.get('Status') in ('New', 'Modified')):
            logging.info(f"\n🎯 Found potential hybrid match:")
            logging.info(f"    Record ID: {rec['id']}")
            logging.info(f"    Current UID: {fields.get('Reservation UID', 'N/A')}")
            logging.info(f"    Status: {fields.get('Status', 'N/A')}")
            logging.info(f"    Would update UID from {fields.get('Reservation UID', 'N/A')} to {new_uid}")

if __name__ == "__main__":
    test_mayes_feed()