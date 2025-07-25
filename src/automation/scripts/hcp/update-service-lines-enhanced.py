#!/usr/bin/env python3
"""
HCP Service Line Update Script with Owner Detection
Updates service line descriptions for existing HCP jobs every 4 hours
Detects owner arrivals (blocks) and updates fields accordingly
Handles both development and production environments
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from pyairtable import Api
import aiohttp

# Add parent directories to path
automation_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(automation_root))

try:
    from src.automation.config_dev import DevConfig
    from src.automation.config_prod import ProdConfig
except ImportError:
    # Alternative path when run from different context
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from automation.config_dev import DevConfig
    from automation.config_prod import ProdConfig

class HCPServiceLineUpdater:
    def __init__(self, environment='development'):
        self.environment = environment
        # Select config based on environment
        if environment == 'production':
            self.config = ProdConfig()
        else:
            self.config = DevConfig()
        
        # Initialize Airtable
        api_key = self.config.get_airtable_api_key()
        base_id = self.config.get_airtable_base_id()
        self.api = Api(api_key)
        self.base = self.api.base(base_id)
        self.table = self.base.table('Reservations')
        
        # HCP API configuration
        hcp_token_key = 'PROD_HCP_TOKEN' if environment == 'production' else 'DEV_HCP_TOKEN'
        hcp_token = os.environ.get(hcp_token_key)
        
        self.hcp_base_url = 'https://api.housecallpro.com'
        self.hcp_headers = {
            'Authorization': f'Token {hcp_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
    def detect_owner_arrival(self, reservation, all_records):
        """
        Detect if an owner is arriving after this reservation checkout.
        Returns True if a block is checking in same day or next day.
        """
        check_out_date = reservation.get('Check-out Date')
        property_id = reservation.get('Property ID', [])
        
        if not check_out_date or not property_id:
            return False
            
        property_id_val = property_id[0] if isinstance(property_id, list) else property_id
        check_out = datetime.fromisoformat(check_out_date.replace('Z', '+00:00'))
        
        # Find all blocks at the same property
        blocks_at_property = []
        for record in all_records:
            # Skip if it's the same record or not a block
            if record['id'] == reservation['id']:
                continue
                
            entry_type = record.get('Entry Type')
            if entry_type != 'Block':
                continue
                
            # Check if same property
            rec_property_id = record.get('Property ID', [])
            if not rec_property_id:
                continue
                
            rec_property_id_val = rec_property_id[0] if isinstance(rec_property_id, list) else rec_property_id
            if rec_property_id_val != property_id_val:
                continue
                
            # Skip old/removed blocks
            status = record.get('Status', '')
            if status in ['Old', 'Removed']:
                continue
                
            check_in_date = record.get('Check-in Date')
            if check_in_date:
                blocks_at_property.append({
                    'check_in': datetime.fromisoformat(check_in_date.replace('Z', '+00:00')),
                    'record': record
                })
        
        # Sort blocks by check-in date
        blocks_at_property.sort(key=lambda x: x['check_in'])
        
        # Find the next block after checkout
        for block in blocks_at_property:
            if block['check_in'] >= check_out:
                # Calculate days between checkout and block check-in
                days_between = (block['check_in'].date() - check_out.date()).days
                
                if days_between <= 1:
                    print(f"   🏠 Owner arriving: Block checking in {days_between} day(s) after checkout")
                    return True
                else:
                    print(f"   📅 Block found but checking in {days_between} days later (not owner arriving)")
                    return False
        
        return False
    
    async def update_service_line(self, session, job_id, service_line_description):
        """Update a single HCP job's service line description"""
        try:
            # Get job details first
            async with session.get(
                f'{self.hcp_base_url}/jobs/{job_id}',
                headers=self.hcp_headers
            ) as response:
                if response.status != 200:
                    print(f"❌ Failed to get job {job_id}: {response.status}")
                    return False
                    
                job_data = await response.json()
                
            # Get the first line item (service line)
            if not job_data.get('line_items') or len(job_data['line_items']) == 0:
                print(f"⚠️  No line items found for job {job_id}")
                return False
                
            line_item = job_data['line_items'][0]
            line_item_id = line_item['id']
            
            # Update the line item with new description
            update_data = {
                'name': service_line_description,
                'description': line_item.get('description', ''),
                'unit_price': line_item['unit_price'],
                'quantity': line_item['quantity'],
                'kind': line_item['kind']
            }
            
            async with session.put(
                f'{self.hcp_base_url}/jobs/{job_id}/line_items/{line_item_id}',
                headers=self.hcp_headers,
                json=update_data
            ) as response:
                if response.status == 200:
                    print(f"✅ Updated job {job_id} service line")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to update job {job_id}: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error updating job {job_id}: {str(e)}")
            return False
    
    def build_service_line_description(self, record):
        """Build service line description following the same logic as Airtable automations"""
        # Get all needed fields
        # Extract service type - handle both object and string formats
        service_type_field = record.get('Service Type')
        if isinstance(service_type_field, dict) and service_type_field:
            service_type = service_type_field.get('name', 'Turnover')
        elif service_type_field:
            service_type = service_type_field
        else:
            service_type = 'Turnover'
        same_day = record.get('Same-day Turnover', False)
        # Check both Owner Arriving checkbox and Next Entry Is Block for backward compatibility
        is_owner_arriving = record.get('Owner Arriving', False) or record.get('Next Entry Is Block', False)
        custom_instructions = record.get('Custom Service Line Instructions', '').strip()
        check_in_date = record.get('Check-in Date')
        check_out_date = record.get('Check-out Date')
        
        # Check for iTrip Next Guest Date first
        itrip_next_guest_date = record.get('iTrip Next Guest Date')
        entry_source = record.get('Entry Source')
        
        # Use iTrip Next Guest Date if it's an iTrip reservation and the field is populated
        if entry_source == 'iTrip' and itrip_next_guest_date:
            next_guest_date = itrip_next_guest_date
            print(f"   📅 Using iTrip Next Guest Date: {itrip_next_guest_date}")
        else:
            next_guest_date = record.get('Next Guest Date')
        
        # Calculate if long-term guest
        is_long_term_guest = False
        if check_in_date and check_out_date:
            check_in = datetime.fromisoformat(check_in_date.replace('Z', '+00:00'))
            check_out = datetime.fromisoformat(check_out_date.replace('Z', '+00:00'))
            stay_duration_days = (check_out - check_in).days
            is_long_term_guest = stay_duration_days >= 14
        
        # Build base service name
        if same_day:
            base_svc_name = f"SAME DAY {service_type} STR"
        elif next_guest_date:
            next_date = datetime.fromisoformat(next_guest_date.replace('Z', '+00:00'))
            month = next_date.strftime('%B')
            day = next_date.day
            base_svc_name = f"{service_type} STR Next Guest {month} {day}"
        else:
            base_svc_name = f"{service_type} STR Next Guest Unknown"
        
        # Build service line with hierarchy
        parts = []
        
        # 1. Custom instructions (max 200 chars)
        if custom_instructions:
            if len(custom_instructions) > 200:
                custom_instructions = custom_instructions[:197] + '...'
            parts.append(custom_instructions)
        
        # 2. OWNER ARRIVING
        if is_owner_arriving:
            parts.append("OWNER ARRIVING")
        
        # 3. LONG TERM GUEST DEPARTING
        if is_long_term_guest:
            parts.append("LONG TERM GUEST DEPARTING")
        
        # 4. Base service name
        parts.append(base_svc_name)
        
        # Join all parts
        return " - ".join(parts) if len(parts) > 1 else parts[0]
    
    async def process_updates(self):
        """Process all reservations that need service line updates"""
        print(f"\n🔄 Starting HCP Service Line Updates with Owner Detection for {self.environment.upper()} environment")
        print(f"⏰ Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # First, get ALL records to detect owner arrivals
        all_formula = '{Entry Type} != ""'  # Get all entries
        all_fields = [
            'Entry Type',
            'Property ID',
            'Check-in Date',
            'Check-out Date',
            'Status'
        ]
        
        print("📊 Fetching all reservation and block records...")
        all_records = []
        for page in self.table.iterate(formula=all_formula, fields=all_fields):
            for record in page:
                all_records.append({
                    'id': record['id'],
                    **record['fields']
                })
        
        print(f"   Found {len(all_records)} total entries")
        
        # Now get all reservations with HCP Job IDs
        formula = 'AND({Service Job ID} != "", {Job Status} != "Canceled")'
        fields = [
            'Service Job ID',
            'Service Type',
            'Same-day Turnover',
            'Next Entry Is Block',
            'Owner Arriving',
            'Custom Service Line Instructions',
            'Check-in Date',
            'Check-out Date',
            'Next Guest Date',
            'iTrip Next Guest Date',
            'Entry Source',
            'Property ID',
            'Service Line Description',
            'Entry Type'
        ]
        
        # Fetch all active job records
        records = []
        for page in self.table.iterate(formula=formula, fields=fields):
            for record in page:
                records.append({
                    'id': record['id'],
                    **record['fields']
                })
        
        print(f"📊 Found {len(records)} active jobs to check")
        
        updates_needed = []
        owner_arrival_updates = []
        
        # Check which records need updates
        for record in records:
            # Detect owner arrival
            detected_owner_arriving = self.detect_owner_arrival(record, all_records)
            current_owner_arriving = record.get('Owner Arriving', False)
            
            # If owner arrival status changed, we need to update Airtable
            if detected_owner_arriving != current_owner_arriving:
                owner_arrival_updates.append({
                    'record_id': record['id'],
                    'property': record.get('Property ID', ['Unknown'])[0],
                    'owner_arriving': detected_owner_arriving
                })
                # Update the record dict so build_service_line_description uses the new value
                record['Owner Arriving'] = detected_owner_arriving
            
            current_description = record.get('Service Line Description', '')
            expected_description = self.build_service_line_description(record)
            
            if current_description != expected_description:
                updates_needed.append({
                    'record_id': record['id'],
                    'job_id': record['Service Job ID'],
                    'current': current_description,
                    'expected': expected_description,
                    'property': record.get('Property ID', ['Unknown'])[0]
                })
        
        # Update Owner Arriving fields in Airtable
        if owner_arrival_updates:
            print(f"\n🏠 Updating {len(owner_arrival_updates)} Owner Arriving fields in Airtable...")
            for update in owner_arrival_updates:
                print(f"   Property {update['property']}: Owner Arriving = {update['owner_arriving']}")
                self.table.update(
                    update['record_id'],
                    {'Owner Arriving': update['owner_arriving']}
                )
        
        print(f"\n🔍 Found {len(updates_needed)} jobs needing service line updates")
        
        if not updates_needed:
            print("✨ All service lines are up to date!")
            return
        
        # Update HCP jobs
        async with aiohttp.ClientSession() as session:
            update_tasks = []
            
            for update in updates_needed:
                print(f"\n📝 Updating job {update['job_id']} for property {update['property']}")
                print(f"   Current: {update['current']}")
                print(f"   New:     {update['expected']}")
                
                task = self.update_service_line(session, update['job_id'], update['expected'])
                update_tasks.append(task)
                
                # Process in batches of 10 to avoid rate limits
                if len(update_tasks) >= 10:
                    results = await asyncio.gather(*update_tasks)
                    update_tasks = []
                    await asyncio.sleep(1)  # Rate limit pause
            
            # Process remaining tasks
            if update_tasks:
                await asyncio.gather(*update_tasks)
        
        # Update Airtable records with new descriptions
        print("\n📊 Updating Airtable records with new service line descriptions...")
        for update in updates_needed:
            self.table.update(
                update['record_id'],
                {'Service Line Description': update['expected']}
            )
        
        print(f"\n✅ Service line update complete!")
        print(f"   - Updated {len(owner_arrival_updates)} Owner Arriving fields")
        print(f"   - Updated {len(updates_needed)} service line descriptions")
        
        # Output structured summary for automation controller
        total_count = len(records)  # Total jobs checked
        print(f"SERVICE_LINE_SUMMARY: OwnerArriving={len(owner_arrival_updates)}, ServiceLines={len(updates_needed)}, Total={total_count}")

async def main():
    parser = argparse.ArgumentParser(description='Update HCP service line descriptions with owner detection')
    parser.add_argument(
        '--env',
        choices=['development', 'production'],
        default='development',
        help='Environment to run in (default: development)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    
    args = parser.parse_args()
    
    updater = HCPServiceLineUpdater(environment=args.env)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        # TODO: Implement dry run logic
    else:
        await updater.process_updates()

if __name__ == '__main__':
    asyncio.run(main())