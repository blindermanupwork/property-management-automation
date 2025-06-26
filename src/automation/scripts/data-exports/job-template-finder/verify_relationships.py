#!/usr/bin/env python3
"""
Verify customer-property relationships and correct any issues.
Also merges customer data with property data for complete records.
"""

import os
import sys
import csv
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parents[4]))
from src.automation.config_prod import ConfigProd

# Setup logging
log_dir = Path("/home/opc/automation/src/automation/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"verify_relationships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HCP API Configuration
HCP_API_KEY = os.getenv('HCP_API_KEY_PROD')
HCP_BASE_URL = "https://api.housecallpro.com"
HCP_HEADERS = {
    "Authorization": f"Bearer {HCP_API_KEY}",
    "Content-Type": "application/json"
}

def load_csv(file_path: str) -> List[Dict]:
    """Load CSV file."""
    records = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def make_api_request(url: str, retry_count: int = 0) -> Optional[Dict]:
    """Make API request with retry logic."""
    try:
        response = requests.get(url, headers=HCP_HEADERS)
        
        if response.status_code == 429:
            reset_time = response.headers.get('RateLimit-Reset')
            if reset_time:
                wait_time = max(int(reset_time) - int(time.time()), 1)
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return make_api_request(url, retry_count)
        
        if response.status_code != 200:
            if retry_count < 3:
                time.sleep(2 ** retry_count)
                return make_api_request(url, retry_count + 1)
            return None
        
        return response.json()
    except Exception as e:
        logger.error(f"Request error: {e}")
        return None

def verify_customer(customer_id: str) -> Optional[Dict]:
    """Verify customer exists and get details."""
    url = f"{HCP_BASE_URL}/v1/customers/{customer_id}"
    data = make_api_request(url)
    return data.get('data') if data else None

def verify_address_belongs_to_customer(customer_id: str, address_id: str) -> bool:
    """Verify that an address belongs to a customer."""
    customer = verify_customer(customer_id)
    if not customer:
        return False
    
    addresses = customer.get('addresses', [])
    for addr in addresses:
        if addr.get('id') == address_id:
            return True
    return False

def find_correct_customer_for_address(address_id: str, properties: List[Dict]) -> Optional[str]:
    """Find the correct customer ID for an address by checking other properties."""
    # Look for other properties with the same address
    for prop in properties:
        if prop.get('HCP Address ID') == address_id:
            customer_id = prop.get('HCP Customer ID')
            if customer_id and verify_address_belongs_to_customer(customer_id, address_id):
                return customer_id
    return None

def merge_customer_property_data(properties: List[Dict], customers: List[Dict]) -> List[Dict]:
    """Merge customer data into property records."""
    # Create customer lookup
    customer_lookup = {c['HCP Customer ID']: c for c in customers if c.get('HCP Customer ID')}
    
    for prop in properties:
        customer_id = prop.get('HCP Customer ID')
        if customer_id and customer_id in customer_lookup:
            customer = customer_lookup[customer_id]
            # Add customer details to property
            prop['Customer First Name'] = customer.get('First Name', '')
            prop['Customer Last Name'] = customer.get('Last Name', '')
            prop['Customer Email'] = customer.get('Email', '')
            prop['Customer Mobile'] = customer.get('Mobile Number', '')
    
    return properties

def verify_and_correct_relationships(properties: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """Verify all customer-property relationships and correct issues."""
    corrections = []
    verified_count = 0
    error_count = 0
    
    for idx, prop in enumerate(properties, 1):
        property_name = prop.get('Property Name', 'Unknown')
        customer_id = prop.get('HCP Customer ID', '')
        address_id = prop.get('HCP Address ID', '')
        
        if not customer_id or not address_id:
            continue
        
        logger.info(f"Verifying {idx}/{len(properties)}: {property_name}")
        
        # Verify relationship
        if verify_address_belongs_to_customer(customer_id, address_id):
            verified_count += 1
            prop['Relationship Verified'] = 'Yes'
        else:
            error_count += 1
            prop['Relationship Verified'] = 'No'
            
            # Try to find correct customer
            correct_customer = find_correct_customer_for_address(address_id, properties)
            if correct_customer:
                corrections.append({
                    'Property Name': property_name,
                    'Address ID': address_id,
                    'Old Customer ID': customer_id,
                    'New Customer ID': correct_customer,
                    'Status': 'Corrected'
                })
                prop['HCP Customer ID'] = correct_customer
                prop['Relationship Verified'] = 'Corrected'
            else:
                corrections.append({
                    'Property Name': property_name,
                    'Address ID': address_id,
                    'Old Customer ID': customer_id,
                    'New Customer ID': '',
                    'Status': 'Unable to correct'
                })
        
        time.sleep(0.5)  # Rate limiting
    
    logger.info(f"\nVerification complete: {verified_count} verified, {error_count} errors")
    return properties, corrections

def save_corrections_report(corrections: List[Dict], output_path: str):
    """Save corrections report."""
    if not corrections:
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Property Name', 'Address ID', 'Old Customer ID', 'New Customer ID', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(corrections)

def main():
    """Main execution."""
    logger.info("Starting relationship verification...")
    
    # Load data
    properties = load_csv("/home/opc/automation/export/Prod_Airtable_Properties.csv")
    customers = load_csv("/home/opc/automation/export/Prod_Airtable_Customers.csv")
    
    logger.info(f"Loaded {len(properties)} properties and {len(customers)} customers")
    
    # Verify and correct relationships
    properties, corrections = verify_and_correct_relationships(properties)
    
    # Merge customer data
    properties = merge_customer_property_data(properties, customers)
    
    # Save results
    output_dir = Path("/home/opc/automation/export")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save corrected properties
    properties_output = output_dir / f"Prod_Properties_Verified_{timestamp}.csv"
    with open(properties_output, 'w', newline='', encoding='utf-8') as f:
        if properties:
            fieldnames = list(properties[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(properties)
    
    # Save corrections report
    if corrections:
        corrections_output = output_dir / f"Relationship_Corrections_{timestamp}.csv"
        save_corrections_report(corrections, str(corrections_output))
        logger.info(f"Found {len(corrections)} relationship issues. See {corrections_output}")
    
    logger.info(f"Verification complete. Results saved to {properties_output}")

if __name__ == "__main__":
    main()