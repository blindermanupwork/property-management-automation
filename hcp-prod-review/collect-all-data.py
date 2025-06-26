#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path

def merge_customer_pages():
    """Merge all customer page files into a single customers.json"""
    hcp_dir = Path('/home/opc/automation/hcp-prod-review/hcp-prod')
    all_customers = []
    
    # Read all customer page files
    for i in range(1, 9):  # 8 pages total
        page_file = hcp_dir / f'customers-page{i}.json'
        if page_file.exists():
            with open(page_file, 'r') as f:
                data = json.load(f)
                all_customers.extend(data.get('customers', []))
    
    # Save merged file
    with open(hcp_dir / 'customers.json', 'w') as f:
        json.dump(all_customers, f, indent=2)
    
    print(f"Merged {len(all_customers)} customers into customers.json")
    return all_customers

def create_customer_property_mapping(customers):
    """Create a mapping of customer names to their property addresses"""
    mapping = {}
    
    for customer in customers:
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        
        # Get service addresses only (not billing)
        service_addresses = []
        for addr in customer.get('addresses', []):
            if addr.get('type') == 'service':
                addr_str = addr.get('street', '')
                if addr.get('street_line_2'):
                    addr_str += f", {addr['street_line_2']}"
                addr_str += f", {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}"
                
                service_addresses.append({
                    'id': addr.get('id'),
                    'full_address': addr_str.strip(),
                    'street': addr.get('street'),
                    'street_line_2': addr.get('street_line_2'),
                    'city': addr.get('city'),
                    'state': addr.get('state'),
                    'zip': addr.get('zip')
                })
        
        if customer_name and service_addresses:
            mapping[customer_name] = {
                'customer_id': customer.get('id'),
                'email': customer.get('email'),
                'phone': customer.get('mobile_number'),
                'service_addresses': service_addresses,
                'address_count': len(service_addresses)
            }
    
    # Save mapping
    output_file = Path('/home/opc/automation/hcp-prod-review/hcp-prod/customer_property_mapping.json')
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    
    print(f"\nCreated mapping for {len(mapping)} customers with service addresses")
    
    # Print summary statistics
    total_addresses = sum(cust['address_count'] for cust in mapping.values())
    multi_property_customers = [name for name, data in mapping.items() if data['address_count'] > 1]
    
    print(f"Total service addresses: {total_addresses}")
    print(f"Customers with multiple properties: {len(multi_property_customers)}")
    
    if multi_property_customers:
        print("\nCustomers with multiple properties:")
        for name in sorted(multi_property_customers)[:10]:  # Show first 10
            count = mapping[name]['address_count']
            print(f"  - {name}: {count} properties")
        if len(multi_property_customers) > 10:
            print(f"  ... and {len(multi_property_customers) - 10} more")
    
    return mapping

if __name__ == "__main__":
    print("Processing HCP Production customer data...\n")
    
    # Merge customer pages
    customers = merge_customer_pages()
    
    # Create customer-property mapping
    mapping = create_customer_property_mapping(customers)
    
    print("\nProcessing complete!")
    print(f"Files saved in: /home/opc/automation/hcp-prod-review/hcp-prod/")