#!/usr/bin/env python3
"""
Find job templates using HCP MCP tools for better performance.
Uses list_jobs with filters instead of customer-specific endpoints that often 404.
"""

import os
import csv
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import logging
import subprocess
import re

# Setup logging
log_dir = Path("/home/opc/automation/src/automation/logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"job_template_mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Job patterns
TURNOVER_PATTERNS = [" ng ", "next guest", "sameday", "same day", "STR SAME DAY", "STR Next Guest"]
INSPECTION_KEYWORDS = ["inspection"]
RETURN_LAUNDRY_KEYWORDS = ["return laundry"]

def load_properties_csv(file_path: str) -> List[Dict]:
    """Load properties from CSV."""
    properties = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties

def run_mcp_command(tool_name: str, params: Dict) -> Optional[Dict]:
    """Run MCP command and return result."""
    cmd = [
        "node",
        "/home/opc/automation/tools/mcp-client.js",
        tool_name,
        json.dumps(params)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            logger.error(f"MCP command failed: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Error running MCP command: {e}")
        return None

def categorize_job_description(description: str) -> Optional[str]:
    """Categorize job based on description."""
    desc_lower = description.lower()
    
    # Priority: Return Laundry > Inspection > Turnover
    for keyword in RETURN_LAUNDRY_KEYWORDS:
        if keyword in desc_lower:
            return 'return_laundry'
    
    for keyword in INSPECTION_KEYWORDS:
        if keyword in desc_lower:
            return 'inspection'
    
    # Turnover must NOT contain inspection or return laundry
    if 'inspection' not in desc_lower and 'return laundry' not in desc_lower:
        for pattern in TURNOVER_PATTERNS:
            if pattern in desc_lower:
                return 'turnover'
    
    return None

def process_batch_properties(properties_batch: List[Dict]) -> Dict[str, Dict[str, str]]:
    """Process a batch of properties to find job templates."""
    # Collect all unique customer IDs in this batch
    customer_ids = list(set(p['HCP Customer ID'] for p in properties_batch if p.get('HCP Customer ID')))
    
    # Results storage: address_id -> {turnover, inspection, return_laundry}
    results = {}
    
    # Process each customer
    for customer_id in customer_ids:
        logger.info(f"Fetching jobs for customer {customer_id}")
        
        # Use list_jobs with customer filter (avoids 404 issues)
        params = {
            "customer_id": customer_id,
            "per_page": 100,
            "scheduled_start_min": (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        }
        
        # Use a direct API call instead of MCP for now
        cmd = f"""curl -s -X GET 'https://api.housecallpro.com/v1/jobs?customer_id={customer_id}&per_page=100' \
            -H 'Authorization: Bearer {os.getenv("HCP_API_KEY_PROD")}' \
            -H 'Content-Type: application/json'"""
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                jobs = data.get('data', [])
                
                logger.info(f"Found {len(jobs)} jobs for customer {customer_id}")
                
                # Process jobs by address
                for prop in properties_batch:
                    if prop.get('HCP Customer ID') != customer_id:
                        continue
                        
                    address_id = prop.get('HCP Address ID')
                    if not address_id:
                        continue
                    
                    # Initialize results for this address
                    if address_id not in results:
                        results[address_id] = {
                            'turnover': None,
                            'inspection': None,
                            'return_laundry': None
                        }
                    
                    # Find jobs for this address
                    address_jobs = [
                        job for job in jobs 
                        if job.get('address', {}).get('id') == address_id
                        and job.get('work_status') not in ['canceled', 'deleted']
                    ]
                    
                    # Categorize jobs
                    categorized = {
                        'turnover': [],
                        'inspection': [],
                        'return_laundry': []
                    }
                    
                    for job in address_jobs:
                        job_type = categorize_job_description(job.get('description', ''))
                        if job_type:
                            categorized[job_type].append(job)
                    
                    # Get most recent of each type
                    for job_type, job_list in categorized.items():
                        if job_list:
                            # Sort by created_at descending
                            job_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                            results[address_id][job_type] = job_list[0].get('id')
                            logger.debug(f"Found {job_type} for {address_id}: {job_list[0].get('id')}")
            
            else:
                logger.error(f"API call failed for customer {customer_id}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error processing customer {customer_id}: {e}")
        
        # Rate limiting
        time.sleep(0.5)
    
    return results

def update_properties_with_templates(properties: List[Dict], templates: Dict[str, Dict[str, str]]) -> List[Dict]:
    """Update properties with found templates."""
    for prop in properties:
        address_id = prop.get('HCP Address ID')
        if address_id and address_id in templates:
            template_data = templates[address_id]
            
            if template_data.get('turnover'):
                prop['Turnover Job Template ID'] = template_data['turnover']
            if template_data.get('inspection'):
                prop['Inspection Job Template ID'] = template_data['inspection']
            if template_data.get('return_laundry'):
                prop['Return Laundry Job Template ID'] = template_data['return_laundry']
    
    return properties

def main():
    """Main execution."""
    logger.info("Starting MCP-based job template finder...")
    
    # Load properties
    input_file = "/home/opc/automation/export/Prod_Airtable_Properties.csv"
    properties = load_properties_csv(input_file)
    logger.info(f"Loaded {len(properties)} properties")
    
    # Process in batches of 10 customers at a time
    batch_size = 10
    all_templates = {}
    
    # Group properties by customer
    customer_props = {}
    for prop in properties:
        customer_id = prop.get('HCP Customer ID')
        if customer_id:
            if customer_id not in customer_props:
                customer_props[customer_id] = []
            customer_props[customer_id].append(prop)
    
    # Process in batches
    customer_ids = list(customer_props.keys())
    total_batches = (len(customer_ids) + batch_size - 1) // batch_size
    
    for i in range(0, len(customer_ids), batch_size):
        batch_num = i // batch_size + 1
        batch_customers = customer_ids[i:i + batch_size]
        batch_properties = []
        
        for cid in batch_customers:
            batch_properties.extend(customer_props[cid])
        
        logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch_customers)} customers)")
        
        # Process this batch
        batch_templates = process_batch_properties(batch_properties)
        all_templates.update(batch_templates)
    
    # Update properties with templates
    properties = update_properties_with_templates(properties, all_templates)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"/home/opc/automation/export/Prod_Airtable_Properties_Templates_{timestamp}.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if properties:
            fieldnames = list(properties[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(properties)
    
    # Generate summary
    total = len(properties)
    has_turnover = sum(1 for p in properties if p.get('Turnover Job Template ID'))
    has_inspection = sum(1 for p in properties if p.get('Inspection Job Template ID'))
    has_return_laundry = sum(1 for p in properties if p.get('Return Laundry Job Template ID'))
    
    summary = f"""
Job Template Summary
===================
Total Properties: {total}
Turnover Templates Found: {has_turnover} ({has_turnover/total*100:.1f}%)
Inspection Templates Found: {has_inspection} ({has_inspection/total*100:.1f}%)
Return Laundry Templates Found: {has_return_laundry} ({has_return_laundry/total*100:.1f}%)

Output: {output_file}
"""
    
    logger.info(summary)
    print(summary)

if __name__ == "__main__":
    main()