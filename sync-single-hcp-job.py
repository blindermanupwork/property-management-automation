#!/usr/bin/env python3
"""
Sync a single HCP job to Airtable
Usage: python3 sync-single-hcp-job.py --job-id 38096 --env dev
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import pytz
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from src.automation.config_wrapper import Config

# Import pyairtable
try:
    from pyairtable import Api
except ImportError:
    print("Please install pyairtable: pip3 install pyairtable")
    sys.exit(1)

# Import requests for HCP API
try:
    import requests
except ImportError:
    print("Please install requests: pip3 install requests")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_hcp_job(job_id, hcp_token):
    """Fetch job details from HCP"""
    url = f'https://api.housecallpro.com/jobs/{job_id}'
    headers = {
        'Authorization': f'Token {hcp_token}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HCP API error: {e}")
        logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return None
    except Exception as e:
        logger.error(f"Error fetching HCP job: {e}")
        return None

def find_matching_reservation(airtable_base, job_data):
    """Find the Airtable reservation that matches this HCP job"""
    # Extract customer and property information
    customer_id = job_data.get('customer', {}).get('id')
    address = job_data.get('address', {})
    scheduled_start = job_data.get('schedule', {}).get('scheduled_start')
    
    if not customer_id or not address or not scheduled_start:
        logger.error("Missing required job data for matching")
        return None
    
    # Convert scheduled time to match Airtable format
    job_datetime = datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
    
    # Search for reservations
    reservations_table = airtable_base.table('Reservations')
    
    # Try to find by existing job ID first
    formula = f"{{Service Job ID}} = '{job_data['id']}'"
    existing = reservations_table.all(formula=formula)
    if existing:
        logger.info(f"Found existing reservation with job ID: {existing[0]['id']}")
        return existing[0]
    
    # If not found, try to match by property and time
    # This would require more complex matching logic based on your specific needs
    logger.warning("No existing reservation found with this job ID")
    logger.info(f"Job details: Customer {customer_id}, Address {address.get('street')}, Time {scheduled_start}")
    
    return None

def update_reservation_with_job(airtable_base, reservation, job_data):
    """Update the Airtable reservation with HCP job data"""
    reservations_table = airtable_base.table('Reservations')
    
    # Extract job information
    job_id = job_data['id']
    job_status = job_data.get('work_status', 'unknown')
    scheduled_time = job_data.get('schedule', {}).get('scheduled_start')
    
    # Map HCP status to Airtable status
    status_map = {
        'needs scheduling': 'Unscheduled',
        'scheduled': 'Scheduled',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'canceled': 'Canceled'
    }
    
    airtable_status = status_map.get(job_status.lower(), job_status)
    
    # Prepare update fields
    update_fields = {
        'Service Job ID': job_id,
        'Job Status': airtable_status,
        'Sync Status': 'Synced',
        'Sync Date and Time': datetime.now().isoformat()
    }
    
    if scheduled_time:
        update_fields['Scheduled Service Time'] = scheduled_time
    
    # Check for appointments
    appointments = job_data.get('appointments', [])
    if appointments:
        update_fields['Service Appointment ID'] = appointments[0]['id']
    
    # Update the reservation
    try:
        reservations_table.update(reservation['id'], update_fields)
        logger.info(f"Successfully updated reservation {reservation['id']} with job {job_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update reservation: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Sync a single HCP job to Airtable')
    parser.add_argument('--job-id', required=True, help='HCP Job ID to sync')
    parser.add_argument('--env', choices=['dev', 'prod'], default='dev', help='Environment')
    
    args = parser.parse_args()
    
    # Load environment configuration
    if args.env == 'prod':
        from dotenv import load_dotenv
        load_dotenv('/home/opc/automation/config/environments/prod/.env')
        airtable_api_key = os.getenv('PROD_AIRTABLE_API_KEY')
        airtable_base_id = os.getenv('PROD_AIRTABLE_BASE_ID')
        hcp_token = os.getenv('PROD_HCP_TOKEN')
        env_name = 'PRODUCTION'
    else:
        from dotenv import load_dotenv
        load_dotenv('/home/opc/automation/config/environments/dev/.env')
        airtable_api_key = os.getenv('DEV_AIRTABLE_API_KEY')
        airtable_base_id = os.getenv('DEV_AIRTABLE_BASE_ID')
        hcp_token = os.getenv('DEV_HCP_TOKEN')
        env_name = 'DEVELOPMENT'
    
    if not all([airtable_api_key, airtable_base_id, hcp_token]):
        logger.error(f"Missing required {env_name} environment variables")
        sys.exit(1)
    
    logger.info(f"Syncing HCP job {args.job_id} in {env_name} environment")
    
    # Initialize APIs
    api = Api(airtable_api_key)
    base = api.base(airtable_base_id)
    
    # Fetch HCP job
    logger.info(f"Fetching job {args.job_id} from HCP...")
    job_data = get_hcp_job(args.job_id, hcp_token)
    
    if not job_data:
        logger.error("Failed to fetch job from HCP")
        sys.exit(1)
    
    logger.info(f"Found job: {job_data.get('invoice_number', 'N/A')} - Status: {job_data.get('work_status')}")
    
    # Find matching reservation
    reservation = find_matching_reservation(base, job_data)
    
    if reservation:
        # Update the reservation
        success = update_reservation_with_job(base, reservation, job_data)
        if success:
            logger.info("✅ Successfully synced job to Airtable")
        else:
            logger.error("❌ Failed to sync job to Airtable")
            sys.exit(1)
    else:
        logger.warning("No matching reservation found in Airtable")
        logger.info("You may need to run the full reconciliation script to match orphaned jobs")
        sys.exit(1)

if __name__ == '__main__':
    main()