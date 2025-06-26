#!/usr/bin/env python3
"""
Update Service Line Description and Next Guest Date fields for all reservations.
This script processes all reservation records and updates their service information.

Usage:
    python update_service_fields.py              # Process all records
    python update_service_fields.py <ID>         # Test on single record by ID field value
    python update_service_fields.py --dev        # Force development environment
    python update_service_fields.py --prod       # Force production environment
    
Example:
    python update_service_fields.py 30777        # Test on record where ID field = 30777
    python update_service_fields.py --prod       # Process all records in production
    python update_service_fields.py 30777 --dev  # Test single record in development
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import argparse
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from airtable import Airtable
from dotenv import load_dotenv
import time

# Parse command line arguments
parser = argparse.ArgumentParser(description='Update Service Line Description and Next Guest Date fields')
parser.add_argument('id_value', nargs='?', help='Optional: Test on a specific record by ID field value (use "list" to see sample IDs)')
parser.add_argument('--batch-size', type=int, default=50, help='Number of records to process in parallel (default: 50)')
parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of parallel workers (default: 10)')
parser.add_argument('--dev', action='store_true', help='Force development environment')
parser.add_argument('--prod', action='store_true', help='Force production environment')
args = parser.parse_args()

# Airtable configuration - environment-aware
# Command line flags override environment variable
if args.prod:
    os.environ['ENVIRONMENT'] = 'production'
elif args.dev:
    os.environ['ENVIRONMENT'] = 'development'
else:
    # Default to development if not specified
    if 'ENVIRONMENT' not in os.environ:
        os.environ['ENVIRONMENT'] = 'development'

# Import Config after setting environment
from automation.config_wrapper import Config

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from automation.config_prod import ProdConfig
    config = ProdConfig()
    AIRTABLE_API_KEY = config.get_airtable_api_key()
    AIRTABLE_BASE_ID = config.get_airtable_base_id()
    print(f"Using PRODUCTION environment (API key: ...{AIRTABLE_API_KEY[-10:] if AIRTABLE_API_KEY else 'None'})")
else:
    from automation.config_dev import DevConfig
    config = DevConfig()
    AIRTABLE_API_KEY = config.get_airtable_api_key()
    AIRTABLE_BASE_ID = config.get_airtable_base_id()
    print(f"Using DEVELOPMENT environment (API key: ...{AIRTABLE_API_KEY[-10:] if AIRTABLE_API_KEY else 'None'})")

if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    print(f"\nError: Missing Airtable credentials for {ENVIRONMENT} environment")
    print("Please ensure your .env file contains:")
    if ENVIRONMENT == 'production':
        print("  PROD_AIRTABLE_API_KEY=your_prod_api_key")
        print("  PROD_AIRTABLE_BASE_ID=your_prod_base_id")
    else:
        print("  DEV_AIRTABLE_API_KEY=your_dev_api_key")
        print("  DEV_AIRTABLE_BASE_ID=your_dev_base_id")
    sys.exit(1)

# Initialize Airtable
reservations_table = Airtable(AIRTABLE_BASE_ID, 'Reservations', AIRTABLE_API_KEY)

# Thread-safe counters
update_lock = threading.Lock()
stats = {
    'updated': 0,
    'errors': 0,
    'skipped': 0
}

def format_date_for_service_line(date_str):
    """Format date as 'Month Day' (e.g., 'July 3')"""
    if not date_str:
        return None
    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    # Platform-independent way to format day without leading zero
    month = date_obj.strftime('%B')
    day = date_obj.day  # This gives us the day as an integer
    return f"{month} {day}"

def find_next_reservation(property_id, check_out_date, all_records):
    """Find the next reservation for a property after the check-out date"""
    property_reservations = []
    
    for record in all_records:
        fields = record['fields']
        
        # Skip if no property ID
        record_prop_ids = fields.get('Property ID', [])
        if not record_prop_ids or record_prop_ids[0] != property_id:
            continue
            
        # Check entry type
        entry_type = fields.get('Entry Type', {})
        if isinstance(entry_type, dict):
            entry_type = entry_type.get('name', '')
        if entry_type != 'Reservation':
            continue
            
        # Check status
        status = fields.get('Status', {})
        if isinstance(status, dict):
            status = status.get('name', '')
        if status == 'Old':
            continue
            
        # Check check-in date
        check_in = fields.get('Check-in Date')
        if not check_in:
            continue
            
        # Compare dates - for same-day turnovers, we want >= not just >
        if check_in < check_out_date:
            continue
            
        property_reservations.append({
            'record': record,
            'check_in': check_in
        })
    
    # Sort by check-in date
    property_reservations.sort(key=lambda x: x['check_in'])
    
    return property_reservations[0] if property_reservations else None

def process_single_record(id_value):
    """Process a single record for testing"""
    print(f"Testing on record with ID field: {id_value}")
    
    try:
        # Search for record by ID field
        print(f"Searching for record with ID = {id_value}...")
        
        # Try different formula formats
        # First try as a number (without quotes)
        formula = f"{{ID}} = {id_value}"
        print(f"Trying formula: {formula}")
        records = reservations_table.get_all(formula=formula)
        
        # If not found, try as text
        if not records:
            formula = f"{{ID}} = '{id_value}'"
            print(f"Trying formula: {formula}")
            records = reservations_table.get_all(formula=formula)
        
        if not records:
            print(f"Error: No record found with ID = {id_value}")
            return
        
        if len(records) > 1:
            print(f"Warning: Found {len(records)} records with ID = {id_value}, using first one")
        
        record = records[0]
        print(f"Found record: {record['id']} (Airtable ID)")
        
        # Get all records for next guest calculation
        print("Fetching all records for next guest calculation...")
        all_records = reservations_table.get_all()
        
        # Process just this one record
        process_record(record, all_records, 1, 1)
        
    except Exception as e:
        print(f"Error: {str(e)}")

def process_record(record, all_records, index, total, show_progress=True):
    """Process a single record"""
    try:
        record_id = record['id']
        fields = record['fields']
        
        # Get required fields
        property_ids = fields.get('Property ID', [])
        if not property_ids:
            if show_progress:
                print(f"[{index}/{total}] Skipping {record_id} - no property ID")
            with update_lock:
                stats['skipped'] += 1
            return
            
        property_id = property_ids[0]
        check_out_date = fields.get('Check-out Date')
        service_type = fields.get('Service Type', {})
        if isinstance(service_type, dict):
            service_type = service_type.get('name', 'Turnover')
        else:
            service_type = service_type or 'Turnover'
        
        same_day = fields.get('Same-day Turnover', False)
        
        # Current values
        current_next_guest = fields.get('Next Guest Date')
        current_service_line = fields.get('Service Line Description')
        
        if show_progress:
            print(f"\n[{index}/{total}] Processing {record_id}:")
            print(f"  Property ID: {property_id}")
            print(f"  Service Type: {service_type}")
            print(f"  Same-day: {same_day}")
            print(f"  Current Next Guest: {current_next_guest}")
            print(f"  Current Service Line: {current_service_line}")
        
        updates = {}
        
        # Always find next guest date (even for same-day turnovers)
        next_guest_date = None
        if check_out_date:
            next_res = find_next_reservation(property_id, check_out_date, all_records)
            if next_res:
                next_guest_date = next_res['check_in']
                if show_progress:
                    print(f"  Found next guest: {next_guest_date}")
            else:
                if show_progress:
                    print(f"  No next guest found")
        
        # Update Next Guest Date if needed (for both same-day and regular)
        if next_guest_date != current_next_guest:
            updates['Next Guest Date'] = next_guest_date
        
        # Build service line description
        if same_day:
            # Same day always just says "SAME DAY" regardless of next guest
            new_service_line = f"{service_type} STR SAME DAY"
        else:
            # Regular turnovers show next guest date in description
            if next_guest_date:
                formatted_date = format_date_for_service_line(next_guest_date)
                new_service_line = f"{service_type} STR Next Guest {formatted_date}"
            else:
                new_service_line = f"{service_type} STR Next Guest Unknown"
        
        # Update Service Line Description if needed
        if new_service_line != current_service_line:
            updates['Service Line Description'] = new_service_line
        
        # Apply updates if any
        if updates:
            if show_progress:
                print(f"  Updating with: {updates}")
            reservations_table.update(record_id, updates)
            if show_progress:
                print(f"  ✓ Updated successfully")
            with update_lock:
                stats['updated'] += 1
        else:
            if show_progress:
                print(f"  → No changes needed")
            with update_lock:
                stats['skipped'] += 1
            
    except Exception as e:
        if show_progress:
            print(f"  ✗ Error: {str(e)}")
        with update_lock:
            stats['errors'] += 1

def process_batch(batch, all_records, batch_num, total_batches):
    """Process a batch of records"""
    batch_size = len(batch)
    print(f"\n📦 Batch {batch_num}/{total_batches}: Processing {batch_size} records...")
    
    for i, record in enumerate(batch):
        # Show progress only for first and last record of batch
        show_progress = (i == 0 or i == batch_size - 1)
        process_record(record, all_records, i+1, batch_size, show_progress=show_progress)
        
        # Small delay to avoid rate limits
        if i < batch_size - 1:
            time.sleep(0.1)
    
    with update_lock:
        print(f"✅ Batch {batch_num}/{total_batches} complete - Updated: {stats['updated']}, Errors: {stats['errors']}, Skipped: {stats['skipped']}")

def process_records():
    """Process all reservation records with parallel batch processing"""
    print("Fetching all reservation records...")
    
    # Reset stats
    global stats
    stats = {'updated': 0, 'errors': 0, 'skipped': 0}
    
    # Get all records
    all_records = reservations_table.get_all()
    print(f"Found {len(all_records)} total records")
    
    # Filter for records that need processing
    records_to_process = []
    for record in all_records:
        fields = record['fields']
        
        # Check if it's a reservation
        entry_type = fields.get('Entry Type', {})
        if isinstance(entry_type, dict):
            entry_type = entry_type.get('name', '')
        
        if entry_type == 'Reservation':
            status = fields.get('Status', {})
            if isinstance(status, dict):
                status = status.get('name', '')
            
            if status != 'Old':
                records_to_process.append(record)
    
    print(f"Found {len(records_to_process)} reservations to process")
    print(f"Batch size: {args.batch_size}, Max workers: {args.max_workers}")
    
    # Split into batches
    batches = []
    for i in range(0, len(records_to_process), args.batch_size):
        batch = records_to_process[i:i + args.batch_size]
        batches.append(batch)
    
    print(f"Split into {len(batches)} batches")
    
    # Process batches in parallel
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = []
        for i, batch in enumerate(batches):
            future = executor.submit(process_batch, batch, all_records, i+1, len(batches))
            futures.append(future)
        
        # Wait for all batches to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Batch error: {str(e)}")
    
    # Final summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"🎉 Processing complete in {elapsed_time:.1f} seconds!")
    print(f"- ✅ Updated: {stats['updated']} records")
    print(f"- ❌ Errors: {stats['errors']} records")
    print(f"- ⏭️  Skipped: {stats['skipped']} records")
    print(f"- 📊 Total processed: {len(records_to_process)} records")
    print(f"- ⚡ Rate: {len(records_to_process)/elapsed_time:.1f} records/second")

def list_sample_ids():
    """List sample reservation IDs for testing"""
    print("Fetching sample reservation IDs...")
    try:
        # Get recent reservations
        formula = "{Entry Type} = 'Reservation'"
        records = reservations_table.get_all(formula=formula, max_records=10, sort=['ID'])
        
        print("\nSample reservation IDs:")
        print("-" * 40)
        for record in records:
            fields = record['fields']
            id_val = fields.get('ID', 'No ID')
            property_name = fields.get('Property ID', ['Unknown'])[0] if fields.get('Property ID') else 'Unknown'
            check_in = fields.get('Check-in Date', 'No date')
            print(f"ID: {id_val} - Property: {property_name} - Check-in: {check_in}")
        print("-" * 40)
        print("\nUse one of these IDs to test, e.g.:")
        if records and records[0]['fields'].get('ID'):
            print(f"python update_service_fields.py {records[0]['fields']['ID']}")
    except Exception as e:
        print(f"Error listing IDs: {str(e)}")

if __name__ == "__main__":
    print("Starting Service Field Update Script")
    print("=" * 50)
    print(f"Using Airtable Base: {AIRTABLE_BASE_ID}")
    
    try:
        if args.id_value:
            if args.id_value.lower() == 'list':
                # List sample IDs
                list_sample_ids()
            else:
                # Test on single record
                process_single_record(args.id_value)
        else:
            # Process all records
            process_records()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)