#!/usr/bin/env python3
"""
Production-ready job template finder using direct HCP API calls.
Uses the same API pattern as prod-hcp-sync.cjs for consistency.
"""

import os
import csv
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
log_dir = Path("/home/opc/automation/src/automation/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"job_template_finder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load production environment variables
from dotenv import load_dotenv
load_dotenv('/home/opc/automation/config/environments/prod/.env')

# HCP API Configuration
HCP_TOKEN = os.getenv('PROD_HCP_TOKEN')
if not HCP_TOKEN:
    logger.error("PROD_HCP_TOKEN not found in environment")
    exit(1)

HCP_BASE_URL = "https://api.housecallpro.com"
HCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Token {HCP_TOKEN}"
}

# Job categorization patterns (case-insensitive)
def is_turnover(desc: str) -> bool:
    """Check if job is a turnover."""
    desc_lower = desc.lower()
    # Must not contain inspection or return laundry
    if 'inspection' in desc_lower or 'return laundry' in desc_lower:
        return False
    # Check for turnover patterns
    patterns = [' ng ', 'next guest', 'sameday', 'same day', 'str same day', 'str next guest']
    return any(p in desc_lower for p in patterns)

def is_inspection(desc: str) -> bool:
    """Check if job is an inspection."""
    return 'inspection' in desc.lower()

def is_return_laundry(desc: str) -> bool:
    """Check if job is return laundry."""
    return 'return laundry' in desc.lower()

class HCPApiClient:
    """HCP API client with rate limiting and retry logic."""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = HCP_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Token {token}"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _handle_rate_limit(self, response: requests.Response, retry_count: int) -> Optional[float]:
        """Handle rate limiting and return wait time."""
        if response.status_code == 429:
            reset_header = response.headers.get('RateLimit-Reset')
            if reset_header:
                # Parse reset time and calculate wait
                try:
                    reset_time = int(reset_header)
                    wait_time = max(reset_time - int(time.time()), 1)
                except:
                    wait_time = 2 ** (retry_count + 1)
            else:
                wait_time = 2 ** (retry_count + 1)
            
            logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
            return wait_time
        return None
    
    def request(self, path: str, method: str = "GET", body: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """Make API request with retry logic."""
        url = f"{self.base_url}{path}"
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if method == "GET":
                    response = self.session.get(url, timeout=30)
                elif method == "POST":
                    response = self.session.post(url, json=body, timeout=30)
                else:
                    response = self.session.request(method, url, json=body, timeout=30)
                
                # Handle rate limiting
                wait_time = self._handle_rate_limit(response, retry_count)
                if wait_time:
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                
                # Success
                if response.status_code == 200:
                    return response.json()
                
                # Other errors
                if response.status_code == 404:
                    logger.debug(f"404 for {path}")
                    return None
                
                logger.error(f"API error {response.status_code}: {response.text[:200]}")
                retry_count += 1
                time.sleep(2 ** retry_count)
                
            except requests.exceptions.Timeout:
                logger.error(f"Timeout for {path}")
                retry_count += 1
                time.sleep(2 ** retry_count)
            except Exception as e:
                logger.error(f"Request error: {e}")
                retry_count += 1
                time.sleep(2 ** retry_count)
        
        return None
    
    def get_customer_jobs(self, customer_id: str, page_size: int = 100) -> List[Dict]:
        """Get all jobs for a customer."""
        all_jobs = []
        page = 1
        
        while True:
            path = f"/v1/jobs?customer_id={customer_id}&page={page}&page_size={page_size}"
            result = self.request(path)
            
            if not result or 'data' not in result:
                break
            
            jobs = result.get('data', [])
            all_jobs.extend(jobs)
            
            if not result.get('has_more', False):
                break
            
            page += 1
            time.sleep(0.5)  # Rate limiting between pages
        
        return all_jobs

def load_properties_csv(file_path: str) -> List[Dict]:
    """Load properties from CSV."""
    properties = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties

def find_templates_for_address(jobs: List[Dict], address_id: str) -> Dict[str, Optional[str]]:
    """Find job templates for a specific address."""
    templates = {
        'turnover': None,
        'inspection': None,
        'return_laundry': None
    }
    
    # Filter jobs for this address and active status
    address_jobs = [
        job for job in jobs 
        if job.get('address', {}).get('id') == address_id
        and job.get('work_status') not in ['canceled', 'deleted']
    ]
    
    if not address_jobs:
        return templates
    
    # Categorize jobs
    categorized = {
        'turnover': [],
        'inspection': [],
        'return_laundry': []
    }
    
    for job in address_jobs:
        desc = job.get('description', '')
        
        # Priority: Return Laundry > Inspection > Turnover
        if is_return_laundry(desc):
            categorized['return_laundry'].append(job)
        elif is_inspection(desc):
            categorized['inspection'].append(job)
        elif is_turnover(desc):
            categorized['turnover'].append(job)
    
    # Get most recent of each type
    for job_type, job_list in categorized.items():
        if job_list:
            # Sort by created_at descending
            job_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            templates[job_type] = job_list[0].get('id')
            
            # Log the job we found
            job = job_list[0]
            logger.info(f"    Found {job_type}: {templates[job_type]} - {job.get('description', '')[:50]}...")
    
    return templates

def process_properties_by_customer(properties: List[Dict], api_client: HCPApiClient) -> List[Dict]:
    """Process properties grouped by customer for efficiency."""
    # Group properties by customer
    customer_groups = {}
    for prop in properties:
        customer_id = prop.get('HCP Customer ID')
        if customer_id and prop.get('HCP Address ID'):
            if customer_id not in customer_groups:
                customer_groups[customer_id] = []
            customer_groups[customer_id].append(prop)
    
    logger.info(f"Processing {len(customer_groups)} unique customers")
    
    # Process each customer
    for idx, (customer_id, customer_props) in enumerate(customer_groups.items(), 1):
        logger.info(f"\nProcessing customer {idx}/{len(customer_groups)}: {customer_id}")
        
        # Get all jobs for this customer
        jobs = api_client.get_customer_jobs(customer_id)
        logger.info(f"  Found {len(jobs)} total jobs for customer")
        
        if not jobs:
            continue
        
        # Process each property for this customer
        for prop in customer_props:
            property_name = prop.get('Property Name', 'Unknown')
            address_id = prop.get('HCP Address ID')
            
            if not address_id:
                continue
            
            # Skip if already has all templates
            if (prop.get('Turnover Job Template ID') and 
                prop.get('Inspection Job Template ID') and 
                prop.get('Return Laundry Job Template ID')):
                logger.info(f"  Skipping {property_name} - already has all templates")
                continue
            
            logger.info(f"  Processing property: {property_name}")
            
            # Find templates for this address
            templates = find_templates_for_address(jobs, address_id)
            
            # Update property
            if templates['turnover']:
                prop['Turnover Job Template ID'] = templates['turnover']
            if templates['inspection']:
                prop['Inspection Job Template ID'] = templates['inspection']
            if templates['return_laundry']:
                prop['Return Laundry Job Template ID'] = templates['return_laundry']
        
        # Rate limiting between customers
        time.sleep(1.0)
    
    return properties

def save_results(properties: List[Dict], output_dir: Path, timestamp: str) -> Path:
    """Save updated properties and generate reports."""
    # Save updated properties
    output_file = output_dir / f"Prod_Airtable_Properties_Updated_{timestamp}.csv"
    
    if properties:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=properties[0].keys())
            writer.writeheader()
            writer.writerows(properties)
    
    # Generate summary
    total = len(properties)
    has_turnover = sum(1 for p in properties if p.get('Turnover Job Template ID'))
    has_inspection = sum(1 for p in properties if p.get('Inspection Job Template ID'))
    has_return_laundry = sum(1 for p in properties if p.get('Return Laundry Job Template ID'))
    has_all = sum(1 for p in properties 
                  if p.get('Turnover Job Template ID') and 
                     p.get('Inspection Job Template ID') and 
                     p.get('Return Laundry Job Template ID'))
    
    summary = f"""Job Template Extraction Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
=====================================
Total Properties: {total}

Templates Found:
- Turnover: {has_turnover}/{total} ({has_turnover/total*100:.1f}%)
- Inspection: {has_inspection}/{total} ({has_inspection/total*100:.1f}%)
- Return Laundry: {has_return_laundry}/{total} ({has_return_laundry/total*100:.1f}%)

Complete (all 3 types): {has_all}/{total} ({has_all/total*100:.1f}%)

Output: {output_file}
"""
    
    # Save summary
    summary_file = output_dir / f"job_template_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    # Generate missing report
    missing = [p for p in properties 
               if not p.get('Turnover Job Template ID') or 
                  not p.get('Inspection Job Template ID') or 
                  not p.get('Return Laundry Job Template ID')]
    
    if missing:
        missing_file = output_dir / f"missing_templates_{timestamp}.csv"
        with open(missing_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Property Name', 'Customer ID', 'Address ID', 'Missing Types'])
            
            for prop in missing:
                missing_types = []
                if not prop.get('Turnover Job Template ID'):
                    missing_types.append('Turnover')
                if not prop.get('Inspection Job Template ID'):
                    missing_types.append('Inspection')
                if not prop.get('Return Laundry Job Template ID'):
                    missing_types.append('Return Laundry')
                
                writer.writerow([
                    prop.get('Property Name', ''),
                    prop.get('HCP Customer ID', ''),
                    prop.get('HCP Address ID', ''),
                    ', '.join(missing_types)
                ])
    
    logger.info(f"\n{summary}")
    print(summary)
    
    return output_file

def main():
    """Main execution."""
    start_time = time.time()
    logger.info("Starting production job template finder...")
    logger.info(f"Using HCP API Token: {'*' * 10}{HCP_TOKEN[-4:]}")
    
    # Initialize API client
    api_client = HCPApiClient(HCP_TOKEN)
    
    # Load properties
    input_file = "/home/opc/automation/export/Prod_Airtable_Properties.csv"
    properties = load_properties_csv(input_file)
    logger.info(f"Loaded {len(properties)} properties")
    
    # Process properties
    properties = process_properties_by_customer(properties, api_client)
    
    # Save results
    output_dir = Path("/home/opc/automation/export")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = save_results(properties, output_dir, timestamp)
    
    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed:.1f} seconds")
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()