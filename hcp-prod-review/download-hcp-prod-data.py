#!/usr/bin/env python3

import json
import os
import sys
import time
from pathlib import Path

# Add the parent directory to the system path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.hcp_mcp_client import HCPClient

def download_all_customers(client, output_dir):
    """Download all customers from HCP with pagination"""
    customers = []
    page = 1
    page_size = 50  # Smaller page size to avoid token limits
    
    while True:
        print(f"Fetching customers page {page}...")
        try:
            response = client.list_customers(page=page, page_size=page_size)
            
            if 'customers' in response:
                customers.extend(response['customers'])
                print(f"  Added {len(response['customers'])} customers (total: {len(customers)})")
                
                # Check if we have more pages
                if response.get('page', 0) >= response.get('total_pages', 1):
                    break
                    
                page += 1
                time.sleep(0.5)  # Rate limiting
            else:
                print(f"Error: Unexpected response format")
                break
                
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    # Save to file
    output_file = output_dir / 'customers.json'
    with open(output_file, 'w') as f:
        json.dump(customers, f, indent=2)
    
    print(f"\nSaved {len(customers)} customers to {output_file}")
    return customers

def download_all_jobs(client, output_dir):
    """Download all jobs from HCP with pagination"""
    jobs = []
    page = 1
    page_size = 20  # Even smaller for jobs due to more data
    
    while True:
        print(f"Fetching jobs page {page}...")
        try:
            response = client.list_jobs(page=page, per_page=page_size)
            
            if 'jobs' in response:
                jobs.extend(response['jobs'])
                print(f"  Added {len(response['jobs'])} jobs (total: {len(jobs)})")
                
                # Check if we have more pages
                if response.get('page', 0) >= response.get('total_pages', 1):
                    break
                    
                page += 1
                time.sleep(0.5)  # Rate limiting
            else:
                print(f"Error: Unexpected response format")
                break
                
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    # Save to file
    output_file = output_dir / 'jobs.json'
    with open(output_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    print(f"\nSaved {len(jobs)} jobs to {output_file}")
    return jobs

def create_customer_property_mapping(customers, output_dir):
    """Create a mapping of customer names to their property addresses"""
    mapping = {}
    
    for customer in customers:
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        
        addresses = []
        for addr in customer.get('addresses', []):
            if addr.get('type') == 'service':
                addr_str = addr.get('street', '')
                if addr.get('street_line_2'):
                    addr_str += f", {addr['street_line_2']}"
                addr_str += f", {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}"
                addresses.append({
                    'id': addr.get('id'),
                    'full_address': addr_str.strip(),
                    'street': addr.get('street'),
                    'street_line_2': addr.get('street_line_2'),
                    'city': addr.get('city'),
                    'state': addr.get('state'),
                    'zip': addr.get('zip')
                })
        
        if customer_name and addresses:
            mapping[customer_name] = {
                'customer_id': customer.get('id'),
                'addresses': addresses
            }
    
    # Save mapping
    output_file = output_dir / 'customer_property_mapping.json'
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nCreated mapping for {len(mapping)} customers")
    return mapping

if __name__ == "__main__":
    # Initialize client for production HCP
    client = HCPClient(environment='prod')
    
    # Create output directory
    output_dir = Path('/home/opc/automation/hcp-prod-review/hcp-prod')
    output_dir.mkdir(exist_ok=True)
    
    print("Starting HCP Production data download...\n")
    
    # Download customers
    customers = download_all_customers(client, output_dir)
    
    # Download jobs
    jobs = download_all_jobs(client, output_dir)
    
    # Create customer-property mapping
    mapping = create_customer_property_mapping(customers, output_dir)
    
    print("\nDownload complete!")
    print(f"Files saved in: {output_dir}")