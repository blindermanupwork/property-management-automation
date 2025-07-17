#!/usr/bin/env python3
"""
Download HCP Service Line Content Script
Downloads all current HCP job service line items and stores them in Airtable
Production environment only
"""

import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timezone
from pathlib import Path
from pyairtable import Api
import json

# Add parent directories to path
automation_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(automation_root))

try:
    from src.automation.config_prod import ProdConfig
except ImportError:
    # Alternative path when run from different context
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from automation.config_prod import ProdConfig

class HCPServiceLineDownloader:
    def __init__(self):
        self.config = ProdConfig()
        
        # Initialize Airtable
        api_key = self.config.get_airtable_api_key()
        base_id = self.config.get_airtable_base_id()
        self.api = Api(api_key)
        self.base = self.api.base(base_id)
        self.table = self.base.table('Reservations')
        
        # HCP API configuration
        self.hcp_token = os.environ.get('PROD_HCP_TOKEN')
        if not self.hcp_token:
            raise ValueError("PROD_HCP_TOKEN environment variable not set")
            
        self.hcp_base_url = 'https://api.housecallpro.com'
        self.hcp_headers = {
            'Authorization': f'Token {self.hcp_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'no_line_items': 0,
            'errors': 0,
            'exact_match': 0,
            'user_content': 0,
            'missing_job': 0
        }
        
        self.comparisons = []
        self.dry_run = False
        
    async def get_hcp_job_line_item(self, session, job_id):
        """Fetch the first line item (service line) from HCP job"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Need to call the line_items endpoint specifically
                async with session.get(
                    f'{self.hcp_base_url}/jobs/{job_id}/line_items',
                    headers=self.hcp_headers
                ) as response:
                    if response.status == 404:
                        return None, "Job not found in HCP"
                    elif response.status == 429:
                        # Rate limited - wait and retry
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 2 ** retry_count  # Exponential backoff
                            await asyncio.sleep(wait_time)
                            continue
                        return None, "Rate limited after retries"
                    elif response.status != 200:
                        return None, f"HCP API error: {response.status}"
                        
                    data = await response.json()
                    
                    # Get the line items array from the response
                    line_items = data.get('data', []) if isinstance(data, dict) else []
                    if not line_items:
                        return None, "No line items found"
                        
                    # Return the name of the first line item
                    return line_items[0].get('name', ''), None
                    
            except Exception as e:
                return None, f"Error: {str(e)}"
    
    def compare_service_lines(self, system_line, hcp_line):
        """Compare system generated vs actual HCP content"""
        if not system_line or not hcp_line:
            return "missing_data"
            
        # Clean up for comparison
        system_clean = system_line.strip()
        hcp_clean = hcp_line.strip()
        
        if system_clean == hcp_clean:
            return "exact_match"
        elif hcp_clean.startswith(system_clean):
            # HCP has additional content at the end
            return "user_addition"
        elif system_clean in hcp_clean:
            # System content is somewhere in HCP line
            return "user_modification"
        else:
            # Significant differences
            return "major_difference"
    
    async def process_downloads(self):
        """Process all reservations and download HCP service lines"""
        print(f"\n🔄 Starting HCP Service Line Download for PRODUCTION")
        print(f"⏰ Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Fetch all reservations with HCP Job IDs
        formula = 'AND({Service Job ID} != "", {Job Status} != "Canceled")'
        fields = [
            'Service Job ID',
            'Service Line Description',
            'HCP Service Line Current',
            'Property ID',
            'Service Type',
            'Check-out Date'
        ]
        
        print("\n📊 Fetching all active jobs from Airtable...")
        records = []
        for page in self.table.iterate(formula=formula, fields=fields):
            for record in page:
                records.append({
                    'id': record['id'],
                    **record['fields']
                })
        
        self.stats['total'] = len(records)
        print(f"   Found {len(records)} jobs to process")
        
        # Process in batches
        async with aiohttp.ClientSession() as session:
            batch_size = 5  # Reduced from 10 to avoid rate limits
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(records)-1)//batch_size + 1}")
                
                tasks = []
                for record in batch:
                    job_id = record['Service Job ID']
                    task = self.process_single_job(session, record)
                    tasks.append(task)
                
                # Process batch
                await asyncio.gather(*tasks)
                
                # Rate limit pause between batches
                if i + batch_size < len(records):
                    await asyncio.sleep(2)  # Increased from 1 to 2 seconds
        
        # Generate report
        self.generate_report()
    
    async def process_single_job(self, session, record):
        """Process a single job record"""
        job_id = record['Service Job ID']
        property_name = record.get('Property ID', ['Unknown'])[0] if record.get('Property ID') else 'Unknown'
        
        print(f"   Processing job {job_id} for {property_name}...", end='')
        
        # Get current HCP content
        hcp_line, error = await self.get_hcp_job_line_item(session, job_id)
        
        if error:
            if "not found" in error.lower():
                self.stats['missing_job'] += 1
                print(f" ❌ {error}")
            elif "No line items" in error:
                self.stats['no_line_items'] += 1
                print(f" ⚠️  {error}")
            else:
                self.stats['errors'] += 1
                print(f" ❌ {error}")
            return
        
        # Update Airtable with current HCP content
        try:
            if not self.dry_run:
                self.table.update(record['id'], {
                    'HCP Service Line Current': hcp_line
                })
            self.stats['success'] += 1
            
            # Compare with system generated
            system_line = record.get('Service Line Description', '')
            comparison = self.compare_service_lines(system_line, hcp_line)
            
            if comparison == "exact_match":
                self.stats['exact_match'] += 1
                print(" ✅ Match")
            elif comparison in ["user_addition", "user_modification"]:
                self.stats['user_content'] += 1
                print(" ✏️  User content detected")
                
                # Store interesting comparisons
                if len(self.comparisons) < 20:  # Keep first 20 examples
                    self.comparisons.append({
                        'job_id': job_id,
                        'property': property_name,
                        'system': system_line,
                        'hcp': hcp_line,
                        'type': comparison
                    })
            else:
                print(" ✅ Updated")
                
        except Exception as e:
            self.stats['errors'] += 1
            print(f" ❌ Airtable error: {str(e)}")
    
    def generate_report(self):
        """Generate summary report"""
        print("\n" + "="*60)
        print("📊 HCP Service Line Download Report")
        print("="*60)
        print(f"Total jobs processed: {self.stats['total']}")
        print(f"✅ Successfully updated: {self.stats['success']}")
        print(f"🔍 Exact matches: {self.stats['exact_match']}")
        print(f"✏️  User content detected: {self.stats['user_content']}")
        print(f"⚠️  No line items found: {self.stats['no_line_items']}")
        print(f"🚫 Jobs not found in HCP: {self.stats['missing_job']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        if self.comparisons:
            print("\n📝 Sample User Content Detected:")
            print("-" * 60)
            
            for comp in self.comparisons[:10]:  # Show first 10
                print(f"\nJob: {comp['job_id']} ({comp['property']})")
                print(f"System: {comp['system']}")
                print(f"HCP:    {comp['hcp']}")
                
                # Highlight the difference
                if comp['type'] == 'user_addition':
                    user_part = comp['hcp'][len(comp['system']):].strip()
                    print(f"User added: '{user_part}'")
        
        # Save detailed report
        report_path = self.config.get_logs_dir() / f'hcp_service_line_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump({
                'stats': self.stats,
                'comparisons': self.comparisons,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")

async def main(dry_run=False):
    """Main entry point"""
    downloader = HCPServiceLineDownloader()
    downloader.dry_run = dry_run
    await downloader.process_downloads()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Download HCP service line content to Airtable')
    parser.add_argument('--dry-run', action='store_true', help='Run without updating Airtable')
    args = parser.parse_args()
    
    print("🚀 HCP Service Line Downloader - Production Only")
    print("This script will download all current HCP service line content")
    print("and store it in the 'HCP Service Line Current' field in Airtable.")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No Airtable updates will be made")
    else:
        print("\nMake sure you've added the field to Airtable first!")
        response = input("\nProceed? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    asyncio.run(main(args.dry_run))