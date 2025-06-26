# secure_webhook_app.py
import os
import hmac
import hashlib
import json
import pytz
import uuid
import time
import sys
import base64
import threading
import queue
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, request, abort, jsonify
from pyairtable import Table
import logging

# Import the automation config
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.automation.config_wrapper import Config

# ── Configure logging with MST timezone ──────────────────────────────
# MST timezone for logging
mst_log = pytz.timezone('America/Phoenix')
class MSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=mst_log)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Configure logger with MST timestamps
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Remove any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# File handler with MST - use environment-specific log file
environment = os.environ.get('ENVIRONMENT', 'production')
log_filename = f"webhook_{environment}.log" if environment == 'development' else "webhook.log"
file_handler = logging.FileHandler(str(Config.get_logs_dir() / log_filename))
file_handler.setFormatter(MSTFormatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)

# Console handler with MST
console_handler = logging.StreamHandler()
console_handler.setFormatter(MSTFormatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(console_handler)

# ── Configuration ───────────────────────────────────────────────────────────
# Use Config class for environment variables

# Environment variables using Config
AIRTABLE_API_KEY = Config.get_airtable_api_key()
AIRTABLE_BASE_ID = Config.get_airtable_base_id()
AIRTABLE_TABLE_NAME = Config.get_airtable_table_name('reservations')
AIRTABLE_PROPERTIES_TABLE = Config.get_airtable_table_name('properties')
HCP_WEBHOOK_SECRET = os.environ.get("HCP_WEBHOOK_SECRET")
SERVATIV_WEBHOOK_SECRET = os.environ.get("SERVATIV_WEBHOOK_SECRET")

# Validate required configuration
missing_config = Config.validate_config()
if missing_config or not HCP_WEBHOOK_SECRET:
    logger.error(f"❌ Missing required configuration: {missing_config + (['HCP_WEBHOOK_SECRET'] if not HCP_WEBHOOK_SECRET else [])}")
    exit(1)

# Security configuration - made optional and with sensible defaults
SECURITY_CONFIG = {
    'MAX_PAYLOAD_SIZE': int(os.environ.get('MAX_PAYLOAD_SIZE', '2097152')),  # 2MB
    'SIGNATURE_TOLERANCE': int(os.environ.get('SIGNATURE_TOLERANCE', '300')),  # 5 minutes
    'ENABLE_IP_WHITELIST': os.environ.get('ENABLE_IP_WHITELIST', 'false').lower() == 'true',
    'ALLOWED_IPS': [ip.strip() for ip in os.environ.get('ALLOWED_IPS', '').split(',') if ip.strip()],
    'REQUIRE_HTTPS': os.environ.get('REQUIRE_HTTPS', 'false').lower() == 'true',
}

# Flask app setup
app = Flask(__name__)

# Optional: Add ProxyFix only if behind a proxy
if os.environ.get('BEHIND_PROXY', 'false').lower() == 'true':
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
        logger.info("✅ ProxyFix enabled")
    except ImportError:
        logger.warning("⚠️ ProxyFix not available, install werkzeug")

# Optional: Rate limiting (only if flask-limiter is available)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["3000 per minute"],  # More generous default
        storage_uri="memory://",
        headers_enabled=True
    )
    limiter.init_app(app)
    RATE_LIMITING_ENABLED = True
    logger.info("✅ Rate limiting enabled")
except ImportError:
    RATE_LIMITING_ENABLED = False
    logger.warning("⚠️ Rate limiting disabled - install flask-limiter for rate limiting")

# Initialize Airtable API and tables
try:
    reservations_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    properties_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_PROPERTIES_TABLE)
    customers_table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, Config.get_airtable_table_name('customers'))
    logger.info("✅ Airtable connection initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Airtable: {e}")
    exit(1)

# Job reconciliation will be initialized after all functions are defined

# Arizona timezone
ARIZONA_TZ = pytz.timezone('America/Phoenix')

# --- Async webhook processing with rate limiting ---
# Queue for webhook processing
webhook_queue = queue.Queue(maxsize=1000)

# Rate limiter for Airtable API calls (5 requests per second max)
class RateLimiter:
    def __init__(self, max_per_second=5):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_call = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        with self.lock:
            now = time.time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_call = time.time()

# Global rate limiter for Airtable
airtable_rate_limiter = RateLimiter(max_per_second=5)

def process_webhook_async(webhook_data):
    """Process webhook data asynchronously"""
    try:
        event_type = webhook_data.get("event", "unknown")
        
        # Handle appointment events
        if event_type.startswith("job.appointment."):
            appointment_data = webhook_data.get("appointment", {})
            if not appointment_data:
                return
            
            job_id = appointment_data.get("job_id")
            if not job_id:
                return
            
            # Rate limit before Airtable call
            airtable_rate_limiter.wait_if_needed()
            existing_record = find_reservation_by_job_id(job_id)
            if not existing_record:
                logger.warning(f"⚠️ No matching reservation found for job ID: {job_id}")
                return
            
            if not should_update_record(existing_record):
                return
            
            # Rate limit before each Airtable update
            airtable_rate_limiter.wait_if_needed()
            
            # Handle specific appointment events
            if event_type == "job.appointment.appointment_discarded":
                handle_appointment_discarded(appointment_data, existing_record)
            elif event_type == "job.appointment.scheduled":
                handle_appointment_scheduled(appointment_data, existing_record)
            elif event_type == "job.appointment.rescheduled":
                handle_appointment_rescheduled(appointment_data, existing_record)
            elif event_type == "job.appointment.appointment_pros_assigned":
                handle_appointment_pros_assigned(appointment_data, existing_record)
            elif event_type == "job.appointment.appointment_pros_unassigned":
                handle_appointment_pros_unassigned(appointment_data, existing_record)
            
            logger.info(f"✅ Successfully processed {event_type} for job {job_id}")
            
        else:
            # Handle regular job events
            job_data = webhook_data.get("job", {})
            if not job_data:
                return
            
            job_id = job_data.get("id")
            if not job_id:
                return
            
            # Rate limit before Airtable call
            airtable_rate_limiter.wait_if_needed()
            existing_record = find_reservation_by_job_id(job_id)
            if existing_record and should_update_record(existing_record):
                # Rate limit before updates
                airtable_rate_limiter.wait_if_needed()
                
                # Update job status if present
                if "work_status" in job_data:
                    handle_status_update(job_data, existing_record)
                
                # Update employee assignment
                handle_employee_assignment(job_data, existing_record)
                
                # Update scheduling
                is_rescheduled = event_type == "job.rescheduled"
                handle_scheduling(job_data, existing_record, is_rescheduled)
                
                logger.info(f"✅ Successfully processed {event_type} for job {job_id}")
            elif not existing_record:
                logger.warning(f"⚠️ No matching reservation found for job ID: {job_id}")
                
    except Exception as e:
        logger.error(f"❌ Error in async webhook processing: {str(e)}", exc_info=True)

def webhook_worker():
    """Worker thread that processes webhooks from the queue"""
    logger.info("🚀 Webhook worker thread started")
    while True:
        try:
            # Get webhook data from queue (blocks until available)
            webhook_data = webhook_queue.get(timeout=60)  # 60 second timeout
            
            # Route to appropriate processor based on source
            if webhook_data.get("_source") == "supabase":
                # Remove the marker before processing
                webhook_data.pop("_source", None)
                process_supabase_webhook_async(webhook_data)
            else:
                # Regular HCP webhook
                process_webhook_async(webhook_data)
            
            # Mark task as done
            webhook_queue.task_done()
            
        except queue.Empty:
            # No webhooks for 60 seconds, just continue
            continue
        except Exception as e:
            logger.error(f"❌ Error in webhook worker: {str(e)}", exc_info=True)

# Start the worker thread
worker_thread = threading.Thread(target=webhook_worker, daemon=True)
worker_thread.start()
logger.info("✅ Async webhook processing enabled")

# --- Utility and helper functions ---

def get_arizona_time():
    return datetime.now(timezone.utc).astimezone(ARIZONA_TZ)

def format_datetime_for_display(iso_string):
    """Format ISO datetime string for display in Arizona time"""
    if not iso_string:
        return "(no time)"
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        az_dt = dt.astimezone(ARIZONA_TZ)
        return az_dt.strftime("%b %d at %-I:%M %p")
    except:
        return iso_string

def get_client_ip():
    """Get the real client IP, accounting for proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def check_ip_whitelist():
    """Check if client IP is in whitelist (if enabled)"""
    if not SECURITY_CONFIG['ENABLE_IP_WHITELIST'] or not SECURITY_CONFIG['ALLOWED_IPS']:
        return True
    
    client_ip = get_client_ip()
    try:
        import ipaddress
        client_ip_obj = ipaddress.ip_address(client_ip)
        for allowed_ip in SECURITY_CONFIG['ALLOWED_IPS']:
            try:
                if '/' in allowed_ip:
                    # CIDR notation
                    if client_ip_obj in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                else:
                    # Exact IP match
                    if str(client_ip_obj) == allowed_ip:
                        return True
            except ValueError:
                logger.warning(f"Invalid IP/CIDR in whitelist: {allowed_ip}")
                continue
        return False
    except Exception as e:
        logger.error(f"IP validation error: {e}")
        return True  # Fail open for security check errors

def validate_payload_size():
    """Check if payload size is within limits"""
    content_length = request.content_length
    if content_length and content_length > SECURITY_CONFIG['MAX_PAYLOAD_SIZE']:
        return False
    return True

def validate_timestamp(timestamp):
    """Validate webhook timestamp (if provided)"""
    if not timestamp:
        return True  # Allow missing timestamps for compatibility
    try:
        webhook_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - webhook_time) > SECURITY_CONFIG['SIGNATURE_TOLERANCE']:
            logger.warning(f"Timestamp outside tolerance: {abs(current_time - webhook_time)}s")
            return False
        return True
    except (ValueError, TypeError):
        logger.warning(f"Invalid timestamp format: {timestamp}")
        return True  # Fail open for timestamp issues

def is_servativ_forwarded(request) -> bool:
    """Check if request is forwarded from Servativ"""
    auth_header = request.headers.get("X-Internal-Auth", "")
    return auth_header == SERVATIV_WEBHOOK_SECRET

def verify_signature(payload: bytes, timestamp: str, sig: str) -> bool:
    """Verify webhook signature"""
    try:
        if not sig:
            logger.warning("No signature provided")
            return False
            
        # Validate timestamp if provided
        if timestamp and not validate_timestamp(timestamp):
            return False
            
        # Create expected signature
        if timestamp:
            raw = timestamp.encode() + b"." + payload
        else:
            raw = payload
            
        expected = hmac.new(HCP_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False

def should_update_record(existing_record):
    """Check if record should be updated based on entry source"""
    service_job_id = existing_record.get("fields", {}).get("Service Job ID", "")
    if service_job_id:
        logger.info(f"✅ Allowing HCP update - record has Service Job ID: {service_job_id}")
        return True
    entry_source = existing_record.get("fields", {}).get("Entry Source", "")
    if entry_source != "HCP":
        logger.warning(f"⚠️ Skipping update - no Service Job ID and Entry Source is: {entry_source}")
        return False
    return True

def find_reservation_by_job_id(job_id):
    """Find reservation record by HCP job ID, excluding Old status"""
    try:
        # Rate limit is handled by the caller in async processing
        # Only process records that are NOT Old status
        results = reservations_table.all(
            formula=f"AND({{Service Job ID}} = '{job_id}', {{Status}} != 'Old')",
            fields=["Reservation UID", "Service Job ID", "Status", "Job Status", "Entry Source"]
        )
        if results:
            # Log which record we're updating for debugging
            record = results[0]
            status = record.get('fields', {}).get('Status', '')
            logger.info(f"Found record with Status='{status}' for job {job_id}")
        return results[0] if results else None
    except Exception as e:
        logger.error(f"Error finding reservation by job ID {job_id}: {e}")
        return None

def format_employee_names(employees):
    """Format employee names from HCP data"""
    if not employees:
        return ""
    return ", ".join([f"{emp.get('first_name', '')} {emp.get('last_name', '')}" for emp in employees])

def update_sync_info(record_id, details):
    """Update sync information for a record"""
    try:
        # Get current UTC time for Airtable (it expects UTC)
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        # Use environment-specific field names
        field_name = "Service Sync Details" if environment == 'development' else "Sync Details"
        return reservations_table.update(record_id, {
            "Sync Date and Time": now,
            field_name: details
        })
    except Exception as e:
        logger.error(f"Error updating sync info for record {record_id}: {e}")

def map_work_status_to_job_status(work_status):
    """Map HCP work status to our job status"""
    if not work_status:
        return ""
    work_status = work_status.lower()
    if "complete" in work_status:
        return "Completed"
    elif "cancel" in work_status:
        return "Canceled"
    elif "unscheduled" in work_status:
        return "Unscheduled"
    elif "needs scheduling" in work_status:
        return "Unscheduled"
    elif "scheduled" in work_status:
        return "Scheduled"
    elif "in progress" in work_status:
        return "In Progress"
    return work_status

# --- Business Logic Handlers ---

def handle_status_update(job_data, existing_record):
    """Handle job status updates"""
    try:
        record_id = existing_record.get("id")
        work_status = job_data.get("work_status", "")
        job_status = map_work_status_to_job_status(work_status)
        
        update_data = {"Job Status": job_status}
        work_timestamps = job_data.get("work_timestamps", {})
        update_data["On My Way Time"] = work_timestamps.get("on_my_way_at")
        update_data["Job Started Time"] = work_timestamps.get("started_at") 
        update_data["Job Completed Time"] = work_timestamps.get("completed_at")
        
        result = reservations_table.update(record_id, update_data)
        # Use clearer messages for dev environment
        if environment == 'development':
            sync_details = f"✅ Updated HCP job status to \"{job_status}\""
        else:
            sync_details = f"Updated job status to {job_status}"
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Updated status for record {record_id}: {job_status}")
        return result
    except Exception as e:
        logger.error(f"Error handling status update: {e}")
        return None

def handle_employee_assignment(job_data, existing_record):
    """Handle employee assignment updates"""
    try:
        employees = job_data.get("assigned_employees", [])
        assignee = format_employee_names(employees)
        if not employees:
            assignee = None
        record_id = existing_record.get("id")
        result = reservations_table.update(record_id, {"Assignee": assignee})
        # Use clearer messages for dev environment
        if environment == 'development':
            sync_details = f"✅ Updated HCP assignee to: {assignee or '(unassigned)'}"
        else:
            sync_details = f"Updated assignee to: {assignee or '(empty)'}"
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Updated assignee for record {record_id}: {assignee or '(empty)'}")
        return result
    except Exception as e:
        logger.error(f"Error handling employee assignment: {e}")
        return None

def handle_scheduling(job_data, existing_record, is_rescheduled=False):
    """Handle scheduling updates"""
    try:
        record_id = existing_record.get("id")
        schedule_data = job_data.get("schedule", {})
        scheduled_start = schedule_data.get("scheduled_start")
        update_data = {"Scheduled Service Time": scheduled_start}
        result = reservations_table.update(record_id, update_data)
        # Use clearer messages for dev environment
        logger.info(f"DEBUG: Environment is '{environment}' (type: {type(environment)})")
        if environment == 'development':
            if is_rescheduled:
                sync_details = "✅ Rescheduled HCP job schedule"
            else:
                sync_details = "✅ Updated HCP job schedule"
        else:
            sync_details = "Rescheduled job" if is_rescheduled else "Updated schedule"
        logger.info(f"DEBUG: Setting sync_details to: '{sync_details}'")
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Updated schedule for record {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling scheduling: {e}")
        return None

def format_appointment_employee_names(dispatched_employees):
    """Format employee names from appointment data"""
    if not dispatched_employees:
        return ""
    return ", ".join([f"{emp.get('first_name', '')} {emp.get('last_name', '')}" for emp in dispatched_employees])

def handle_appointment_discarded(appointment_data, existing_record):
    """Handle appointment discarded events"""
    try:
        logger.info("Processing job.appointment.appointment_discarded webhook")
        job_id = appointment_data.get("job_id", "")
        appointment_id = appointment_data.get("id", "")
        
        record_id = existing_record.get("id")
        update_data = {
            "Job Status": "Unscheduled",
            "Service Appointment ID": None,
            "On My Way Time": None,
            "Job Started Time": None,
            "Job Completed Time": None,
            "Scheduled Service Time": None,
            "Assignee": None
        }
        
        result = reservations_table.update(record_id, update_data)
        # Use clearer messages for dev environment
        if environment == 'development':
            sync_details = f"⚠️ HCP appointment {appointment_id} discarded, job unscheduled"
        else:
            sync_details = f"Appointment {appointment_id} discarded, job unscheduled"
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Appointment {appointment_id} discarded for record: {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling appointment discarded: {e}")
        return None

def handle_appointment_scheduled(appointment_data, existing_record):
    """Handle appointment scheduled events"""
    try:
        logger.info("Processing job.appointment.scheduled webhook")
        job_id = appointment_data.get("job_id", "")
        appointment_id = appointment_data.get("id", "")
        
        record_id = existing_record.get("id")
        dispatched_employees = appointment_data.get("dispatched_employees", [])
        assignee = format_appointment_employee_names(dispatched_employees)
        start_time = appointment_data.get("start_time")
        
        update_data = {
            "Service Appointment ID": appointment_id,
            "Assignee": assignee,
            "Job Status": "Scheduled",
            "Scheduled Service Time": start_time
        }
        
        logger.info(f"📋 Appointment ID: {appointment_id}")
        logger.info(f"👤 Assignee: {assignee or '(empty)'}")
        logger.info(f"⏰ Scheduled start: {start_time or '(empty)'}")
        
        result = reservations_table.update(record_id, update_data)
        # Use clearer messages for dev environment
        if environment == 'development':
            sync_details = f"✅ Appointment scheduled: {format_datetime_for_display(start_time)}, assignee: {assignee or '(unassigned)'}"
        else:
            sync_details = f"Appointment {appointment_id} scheduled, assignee: {assignee or '(empty)'}"
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Appointment {appointment_id} scheduled for record: {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling appointment scheduled: {e}")
        return None

def handle_appointment_rescheduled(appointment_data, existing_record):
    """Handle appointment rescheduled events"""
    try:
        logger.info("Processing job.appointment.rescheduled webhook")
        job_id = appointment_data.get("job_id", "")
        appointment_id = appointment_data.get("id", "")
        
        record_id = existing_record.get("id")
        dispatched_employees = appointment_data.get("dispatched_employees", [])
        assignee = format_appointment_employee_names(dispatched_employees)
        start_time = appointment_data.get("start_time")
        
        logger.info(f"📋 Appointment ID: {appointment_id}")
        logger.info(f"👤 Assignee: {assignee or '(empty)'}")
        logger.info(f"⏰ Rescheduled start: {start_time or '(empty)'}")
        
        # Check what actually changed BEFORE updating
        if environment == 'development':
            # Check what actually changed
            old_assignee = existing_record.get('fields', {}).get('Assignee', '')
            old_time = existing_record.get('fields', {}).get('Scheduled Service Time', '')
            
            # Check if we recently processed an assignee webhook
            last_sync_details = existing_record.get('fields', {}).get('Service Sync Details', '')
            recently_updated_assignee = ('Assignee updated:' in last_sync_details or 
                                       'assignees removed' in last_sync_details or
                                       'Assignee removed' in last_sync_details)
            
            logger.info(f"🔍 Comparing - Old assignee: '{old_assignee}', New assignee: '{assignee}'")
            logger.info(f"🔍 Last sync details: '{last_sync_details[:50]}...'")
            logger.info(f"🔍 Recently updated assignee: {recently_updated_assignee}")
            
            assignee_changed = str(old_assignee).strip() != str(assignee or '').strip()
            
            # Compare times more accurately
            time_changed = False
            try:
                if old_time and start_time:
                    old_dt = datetime.fromisoformat(old_time.replace('Z', '+00:00'))
                    new_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    # Consider times different if they differ by more than 1 minute
                    time_changed = abs((old_dt - new_dt).total_seconds()) > 60
                elif old_time != start_time:
                    time_changed = True
            except:
                time_changed = str(old_time) != str(start_time)
            
            # Skip update if this appears to be a duplicate from assignee change
            # (HCP sends rescheduled webhook after pros_unassigned/assigned)
            if recently_updated_assignee and not time_changed:
                logger.info(f"Skipping duplicate rescheduled webhook after recent assignee change")
                return None  # Don't update, the assignee webhook already handled it
            
            if assignee_changed and not time_changed:
                logger.info(f"Skipping duplicate rescheduled webhook after assignee change")
                return None  # Don't update, the assignee webhook already handled it
            
            if time_changed:
                if assignee:
                    sync_details = f"✅ Schedule updated: {format_datetime_for_display(start_time)}, assignee: {assignee}"
                else:
                    sync_details = f"✅ Schedule updated: {format_datetime_for_display(start_time)} (no assignee)"
            else:
                # No real changes, skip this update
                logger.info(f"No actual changes detected in rescheduled webhook")
                return None
        else:
            sync_details = f"Appointment {appointment_id} rescheduled, assignee: {assignee or '(empty)'}"
        
        # Now update Airtable with the changes
        update_data = {
            "Service Appointment ID": appointment_id,
            "Assignee": assignee,
            "Scheduled Service Time": start_time
        }
        
        result = reservations_table.update(record_id, update_data)
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Appointment {appointment_id} rescheduled for record: {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling appointment rescheduled: {e}")
        return None

def handle_appointment_pros_assigned(appointment_data, existing_record):
    """Handle pros assigned to appointment events"""
    try:
        logger.info("Processing job.appointment.appointment_pros_assigned webhook")
        job_id = appointment_data.get("job_id", "")
        appointment_id = appointment_data.get("id", "")
        
        record_id = existing_record.get("id")
        dispatched_employees = appointment_data.get("dispatched_employees", [])
        assignee = format_appointment_employee_names(dispatched_employees)
        
        update_data = {
            "Service Appointment ID": appointment_id,
            "Assignee": assignee
        }
        
        logger.info(f"📋 Appointment ID: {appointment_id}")
        logger.info(f"👤 New assignee: {assignee or '(empty)'}")
        
        result = reservations_table.update(record_id, update_data)
        # Use clearer messages for dev environment
        if environment == 'development':
            sync_details = f"✅ Assignee updated: {assignee or '(none)'}"
        else:
            sync_details = f"Pros assigned to appointment {appointment_id}: {assignee or '(empty)'}"
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Pros assigned to appointment {appointment_id} for record: {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling pros assigned: {e}")
        return None

def handle_appointment_pros_unassigned(appointment_data, existing_record):
    """Handle pros unassigned from appointment events
    
    Note: HCP often sends two webhooks when changing assignees:
    1. appointment_pros_unassigned - removing old assignee
    2. appointment_pros_assigned - adding new assignee
    This results in two separate Service Sync Details updates.
    """
    try:
        logger.info("Processing job.appointment.appointment_pros_unassigned webhook")
        job_id = appointment_data.get("job_id", "")
        appointment_id = appointment_data.get("id", "")
        
        record_id = existing_record.get("id")
        dispatched_employees = appointment_data.get("dispatched_employees", [])
        assignee = format_appointment_employee_names(dispatched_employees)
        if not dispatched_employees:
            assignee = None
            
        update_data = {
            "Service Appointment ID": appointment_id,
            "Assignee": assignee
        }
        
        logger.info(f"📋 Appointment ID: {appointment_id}")
        logger.info(f"👤 Remaining assignee: {assignee or '(none)'}")
        
        result = reservations_table.update(record_id, update_data)
        # Use clearer messages for dev environment
        if environment == 'development':
            if assignee:
                # There are still some assignees remaining
                sync_details = f"⚠️ Assignee removed, remaining: {assignee}"
            else:
                # All assignees removed
                sync_details = f"⚠️ All assignees removed"
        else:
            sync_details = f"Pros unassigned from appointment {appointment_id}, remaining: {assignee or '(none)'}"
        update_sync_info(record_id, sync_details)
        logger.info(f"✅ Pros unassigned from appointment {appointment_id} for record: {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling pros unassigned: {e}")
        return None

# --- Security middleware ---

@app.before_request
def security_checks():
    """Perform security checks before processing requests"""
    try:
        # Skip security checks for health endpoint
        if request.endpoint == 'health_check':
            return
            
        # For webhook endpoints, NEVER abort - just log issues
        if request.endpoint in ['hcp_webhook', 'csv_email_webhook']:
            # HTTPS check (log only)
            if SECURITY_CONFIG['REQUIRE_HTTPS']:
                if not request.is_secure and request.headers.get('X-Forwarded-Proto', '') != 'https':
                    logger.warning(f"⚠️ HTTPS required but got HTTP from {get_client_ip()} - allowing anyway")
            
            # IP whitelist check (log only)
            if SECURITY_CONFIG['ENABLE_IP_WHITELIST'] and not check_ip_whitelist():
                logger.warning(f"⚠️ IP not in whitelist: {get_client_ip()} - allowing anyway")
            
            # Payload size check (log only)
            if not validate_payload_size():
                logger.warning(f"⚠️ Payload too large from {get_client_ip()} - allowing anyway")
            
            # Content-Type check (log only)
            if request.method == 'POST':
                content_type = request.content_type
                if content_type and 'application/json' not in content_type:
                    logger.warning(f"⚠️ Invalid content type: {content_type} - allowing anyway")
            
            # Always allow webhooks through
            return
            
        # For non-webhook endpoints, enforce security
        # HTTPS enforcement (only if enabled)
        if SECURITY_CONFIG['REQUIRE_HTTPS']:
            if not request.is_secure and request.headers.get('X-Forwarded-Proto', '') != 'https':
                logger.warning(f"HTTPS required - rejecting HTTP request from {get_client_ip()}")
                abort(400)  # Bad Request - HTTPS required
        
        # IP whitelist (only if enabled)
        if SECURITY_CONFIG['ENABLE_IP_WHITELIST'] and not check_ip_whitelist():
            logger.warning(f"IP not in whitelist: {get_client_ip()}")
            abort(403)
        
        # Payload size check
        if not validate_payload_size():
            logger.warning(f"Payload too large from {get_client_ip()}")
            abort(413)
        
        # Content-Type check for other endpoints
        if request.method == 'POST':
            content_type = request.content_type
            if content_type and 'application/json' not in content_type:
                logger.warning(f"Invalid content type: {content_type}")
                abort(400)
                
    except Exception as e:
        logger.error(f"Error in security checks: {e}")
        # Don't abort on security check errors, just log them

# --- Main webhook route ---

@app.route("/webhooks/hcp", methods=["POST"])
def hcp_webhook():
    """Main HCP webhook handler - ALWAYS returns 200"""
    try:
        client_ip = get_client_ip()
        logger.info(f"📥 Webhook received from {client_ip}")
    except Exception as e:
        # Even if we can't get client IP, continue
        client_ip = "unknown"
        logger.error(f"Error getting client IP: {e}")
    
    try:
        payload = request.get_data()
        timestamp = request.headers.get("Api-Timestamp", "")
        signature = request.headers.get("Api-Signature", "")
        
        # Parse JSON
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logger.warning(f"Invalid JSON payload: {e}")
            return jsonify({"error": "Invalid JSON"}), 200
        
        # Ping test
        if data == {"foo": "bar"}:
            logger.info("✅ Ping test successful")
            return jsonify({"status": "success", "message": "Ping received"}), 200
        
        # Check if this is a forwarded request from Servativ
        is_forwarded = is_servativ_forwarded(request)
        if is_forwarded:
            logger.info(f"✅ Verified forwarded webhook from Servativ - Event: {data.get('event', 'unknown')}")
        else:
            # Verify signature for direct HCP webhooks
            if not verify_signature(payload, timestamp, signature):
                logger.warning(f"❌ Invalid webhook signature from {client_ip}")
                return jsonify({"status": "success", "message": "Webhook received"}), 200
        
        event_type = data.get("event", "unknown")
        logger.info(f"✅ Verified webhook - Event: {event_type}")
        
        # Add webhook to processing queue instead of processing synchronously
        try:
            webhook_queue.put_nowait(data)
            logger.info(f"📤 Added webhook to queue - Event: {event_type}")
        except queue.Full:
            logger.error("❌ Webhook queue is full! Dropping webhook")
            return jsonify({"status": "error", "message": "Queue full"}), 200
        
        # Return immediately to avoid timeout
        return jsonify({"status": "success", "message": "Webhook queued"}), 200
        
        # OLD SYNCHRONOUS CODE BELOW (keeping for reference but it won't execute)
        # Handle appointment events differently than job events
        if event_type.startswith("job.appointment."):
            appointment_data = data.get("appointment", {})
            if not appointment_data:
                logger.warning("No appointment data in webhook")
                return jsonify({"status": "success", "message": "No appointment data"}), 200
            
            job_id = appointment_data.get("job_id")
            appointment_id = appointment_data.get("id")
            
            if not job_id:
                logger.warning("No job_id in appointment webhook")
                return jsonify({"status": "success", "message": "No job_id in appointment"}), 200
            
            logger.info(f"🔍 Processing appointment event - Job ID: {job_id}, Appointment ID: {appointment_id}")
            
            existing_record = find_reservation_by_job_id(job_id)
            if not existing_record:
                logger.warning(f"⚠️ No matching reservation found for job ID: {job_id}")
                return jsonify({"status": "success", "message": "No matching reservation"}), 200
            
            if not should_update_record(existing_record):
                return jsonify({"status": "success", "message": "Record update not allowed"}), 200
            
            # Handle specific appointment events
            if event_type == "job.appointment.appointment_discarded":
                handle_appointment_discarded(appointment_data, existing_record)
            elif event_type == "job.appointment.scheduled":
                handle_appointment_scheduled(appointment_data, existing_record)
            elif event_type == "job.appointment.rescheduled":
                handle_appointment_rescheduled(appointment_data, existing_record)
            elif event_type == "job.appointment.appointment_pros_assigned":
                handle_appointment_pros_assigned(appointment_data, existing_record)
            elif event_type == "job.appointment.appointment_pros_unassigned":
                handle_appointment_pros_unassigned(appointment_data, existing_record)
            else:
                logger.warning(f"⚠️ Unhandled appointment event: {event_type}")
            
            logger.info(f"✅ Successfully processed {event_type} for job {job_id}")
            
        else:
            # Handle regular job events
            job_data = data.get("job", {})
            if not job_data:
                logger.warning("No job data in webhook")
                return jsonify({"status": "success", "message": "No job data"}), 200
            
            job_id = job_data.get("id")
            if not job_id:
                logger.warning("No job_id in webhook")
                return jsonify({"status": "success", "message": "No job_id"}), 200
            
            logger.info(f"🔍 Processing job ID: {job_id}")
            
            existing_record = find_reservation_by_job_id(job_id)
            if existing_record and should_update_record(existing_record):
                # Update job status if present
                if "work_status" in job_data:
                    handle_status_update(job_data, existing_record)
                
                # Update employee assignment
                handle_employee_assignment(job_data, existing_record)
                
                # Update scheduling
                is_rescheduled = event_type == "job.rescheduled"
                handle_scheduling(job_data, existing_record, is_rescheduled)
                
                logger.info(f"✅ Successfully processed {event_type} for job {job_id}")
            elif not existing_record:
                logger.warning(f"⚠️ No matching reservation found for job ID: {job_id}")
        
        return jsonify({"status": "success", "message": "Webhook processed"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Processing failed"}), 200

# --- CSV Email webhook (CloudMailin) ---

def save_csv_attachment(filename, content, environment='development'):
    """Save CSV content to processing directory"""
    try:
        # Determine output directory based on environment
        if environment == 'production':
            output_dir = Path('/home/opc/automation/src/automation/scripts/CSV_process_production')
        else:
            output_dir = Path('/home/opc/automation/src/automation/scripts/CSV_process_development')
        
        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = filename.replace(' ', '_').replace('(', '').replace(')', '')
        unique_filename = f"{timestamp}_{safe_filename}"
        
        # Save file
        file_path = output_dir / unique_filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"✅ Saved CSV: {unique_filename} ({len(content)} bytes)")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to save CSV {filename}: {e}")
        return None

@app.route("/webhooks/csv-email", methods=["POST"])
def csv_email_webhook():
    """Handle incoming email webhook from CloudMailin for CSV attachments"""
    try:
        # CloudMailin sends multipart data, check for JSON in request
        if request.is_json:
            data = request.json
        else:
            # Handle multipart form data from CloudMailin
            data = {}
            if request.form:
                # Try to parse JSON from form fields
                for key, value in request.form.items():
                    if key in ['envelope', 'headers', 'attachments']:
                        try:
                            data[key] = json.loads(value) if isinstance(value, str) else value
                        except:
                            data[key] = value
                    else:
                        data[key] = value
            
            # Handle file uploads (attachments)
            if request.files:
                data['attachments'] = []
                for file_key, file_obj in request.files.items():
                    if file_obj.filename and file_obj.filename.endswith('.csv'):
                        content = file_obj.read()
                        data['attachments'].append({
                            'file_name': file_obj.filename,
                            'content_type': file_obj.content_type,
                            'content': base64.b64encode(content).decode('utf-8')
                        })
        
        # Log email details
        envelope = data.get('envelope', {})
        headers = data.get('headers', {})
        sender = envelope.get('from', headers.get('from', 'Unknown'))
        subject = headers.get('subject', 'No Subject')
        
        # Log email body for verification links/codes
        email_body = data.get('plain', '') or data.get('html', '') or ''
        
        logger.info(f"📧 Received email from {sender}: {subject}")
        
        # Check for verification content in any email
        if any(keyword in email_body.lower() for keyword in ['verification', 'verify', 'confirm', 'code', 'gmail.com/mail/confirm']):
            logger.info(f"🔍 VERIFICATION EMAIL DETECTED:")
            logger.info(f"📄 Email body content: {email_body[:1000]}...")  # Log first 1000 chars
        
        # Check if this is an iTrip email
        sender_lower = sender.lower() if sender else ''
        subject_lower = subject.lower() if subject else ''
        
        if 'itrip' not in sender_lower or 'checkouts report' not in subject_lower:
            # For non-iTrip emails, still log if they contain verification content
            if any(keyword in email_body.lower() for keyword in ['verification', 'verify', 'confirm', 'code']):
                logger.info(f"🔍 Non-iTrip email contains verification content - not skipping")
            else:
                logger.info(f"⏭️  Skipping non-iTrip email from {sender}")
                return jsonify({'status': 'ignored', 'reason': 'not iTrip email'}), 200
        
        # Process attachments
        attachments = data.get('attachments', [])
        saved_files = []
        
        for attachment in attachments:
            filename = attachment.get('file_name', 'unknown.csv')
            content_b64 = attachment.get('content', '')
            
            # Only process CSV files
            if not filename.lower().endswith('.csv'):
                logger.info(f"⏭️  Skipping non-CSV attachment: {filename}")
                continue
            
            try:
                # Decode base64 content
                content = base64.b64decode(content_b64)
                
                # Save to both environments (let CSV processor filter)
                for env in ['development', 'production']:
                    saved_path = save_csv_attachment(filename, content, env)
                    if saved_path:
                        saved_files.append(saved_path)
                
                logger.info(f"✅ Processed CSV attachment: {filename}")
                
            except Exception as e:
                logger.error(f"❌ Failed to process attachment {filename}: {e}")
        
        # Return success response
        response = {
            'status': 'success',
            'processed_files': len(saved_files),
            'files': saved_files
        }
        
        logger.info(f"🎉 Email processed successfully: {len(saved_files)} files saved")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ CSV email webhook error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 200

# --- Supabase webhook for images/data ---

def save_image_from_webhook(job_reference, image_url=None, image_data=None, filename=None):
    """Save image from Supabase webhook - either from URL or direct data"""
    try:
        import requests
        from pathlib import Path
        import uuid
        
        # Determine environment
        env_suffix = '_development' if environment == 'development' else '_production'
        
        # Create image storage directory
        image_dir = Path(f'/home/opc/automation/src/automation/images{env_suffix}')
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        if filename:
            # Sanitize provided filename
            safe_filename = filename.replace(' ', '_').replace('/', '_')
            final_filename = f"{timestamp}_{job_reference}_{unique_id}_{safe_filename}"
        else:
            # Default filename
            final_filename = f"{timestamp}_{job_reference}_{unique_id}.jpg"
        
        file_path = image_dir / final_filename
        
        # Save image based on source
        if image_url:
            # Download from URL
            logger.info(f"📥 Downloading image from URL: {image_url}")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save binary content
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
        elif image_data:
            # Save direct base64 data
            logger.info(f"💾 Saving image from base64 data")
            import base64
            
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            # Decode and save
            image_bytes = base64.b64decode(image_data)
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
        else:
            logger.error("❌ No image URL or data provided")
            return None
            
        logger.info(f"✅ Saved image: {final_filename}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to save image: {e}")
        return None

def process_supabase_webhook_async(webhook_data):
    """Process Supabase webhook data asynchronously"""
    try:
        # Extract key fields from webhook
        event_type = webhook_data.get("type", "unknown")
        record = webhook_data.get("record", {})
        old_record = webhook_data.get("old_record", {})
        
        # Job reference could be in various fields - check common patterns
        job_reference = (
            record.get("job_id") or 
            record.get("hcp_job_id") or 
            record.get("service_job_id") or
            record.get("reservation_uid") or
            record.get("reference_id")
        )
        
        if not job_reference:
            logger.warning("⚠️ No job reference found in Supabase webhook")
            return
            
        logger.info(f"🔍 Processing Supabase webhook - Event: {event_type}, Job Reference: {job_reference}")
        
        # Try to find reservation by various methods
        existing_record = None
        
        # First try by Service Job ID
        if job_reference.startswith("job_"):
            airtable_rate_limiter.wait_if_needed()
            existing_record = find_reservation_by_job_id(job_reference)
        
        # If not found, try by Reservation UID
        if not existing_record:
            airtable_rate_limiter.wait_if_needed()
            try:
                results = reservations_table.all(
                    formula=f"AND({{Reservation UID}} = '{job_reference}', {{Status}} != 'Old')",
                    fields=["Reservation UID", "Service Job ID", "Status", "Entry Source"]
                )
                existing_record = results[0] if results else None
            except Exception as e:
                logger.error(f"Error finding reservation by UID: {e}")
        
        if not existing_record:
            logger.warning(f"⚠️ No matching reservation found for reference: {job_reference}")
            return
            
        record_id = existing_record.get("id")
        
        # Process images if present
        images = record.get("images", [])
        image_urls = record.get("image_urls", [])
        saved_images = []
        
        # Handle array of images
        for idx, image in enumerate(images):
            if isinstance(image, dict):
                image_url = image.get("url")
                image_data = image.get("data")
                filename = image.get("filename", f"image_{idx}.jpg")
            else:
                # Assume it's direct image data
                image_url = None
                image_data = image
                filename = f"image_{idx}.jpg"
                
            saved_path = save_image_from_webhook(job_reference, image_url, image_data, filename)
            if saved_path:
                saved_images.append(saved_path)
        
        # Handle image URLs
        for idx, image_url in enumerate(image_urls):
            saved_path = save_image_from_webhook(job_reference, image_url=image_url, filename=f"url_image_{idx}.jpg")
            if saved_path:
                saved_images.append(saved_path)
        
        # Update Airtable with image information
        if saved_images:
            airtable_rate_limiter.wait_if_needed()
            
            # Store image paths in sync details for now
            # In production, you might want to add a dedicated field
            image_info = f"Images received from Supabase: {len(saved_images)} files"
            
            # Update sync details
            update_sync_info(record_id, f"Supabase webhook: {event_type}, {image_info}")
            
            # You could also update a dedicated field if it exists
            # For example: reservations_table.update(record_id, {"Image Paths": "\n".join(saved_images)})
            
            logger.info(f"✅ Processed Supabase webhook for job {job_reference}: {len(saved_images)} images")
        else:
            # Still update sync info even without images
            update_sync_info(record_id, f"Supabase webhook: {event_type}, no images")
            logger.info(f"✅ Processed Supabase webhook for job {job_reference}: no images")
            
    except Exception as e:
        logger.error(f"❌ Error in Supabase webhook processing: {str(e)}", exc_info=True)

@app.route("/webhooks/supabase", methods=["POST"])
def supabase_webhook():
    """Handle incoming webhook from Supabase with images/data - ALWAYS returns 200"""
    try:
        client_ip = get_client_ip()
        logger.info(f"📥 Supabase webhook received from {client_ip}")
    except Exception as e:
        client_ip = "unknown"
        logger.error(f"Error getting client IP: {e}")
    
    try:
        payload = request.get_data()
        signature = request.headers.get("X-Supabase-Signature", "")
        
        # Get Supabase webhook secret from env
        SUPABASE_WEBHOOK_SECRET = os.environ.get("SUPABASE_WEBHOOK_SECRET", "")
        
        # Parse JSON
        try:
            data = request.get_json(force=True)
        except Exception as e:
            logger.warning(f"Invalid JSON payload: {e}")
            return jsonify({"error": "Invalid JSON"}), 200
        
        # Ping test
        if data == {"foo": "bar"}:
            logger.info("✅ Supabase ping test successful")
            return jsonify({"status": "success", "message": "Ping received"}), 200
        
        # Check if this is a forwarded request from Servativ
        is_forwarded = is_servativ_forwarded(request)
        if is_forwarded:
            logger.info(f"✅ Verified forwarded Supabase webhook from Servativ")
        elif SUPABASE_WEBHOOK_SECRET:
            # Verify Supabase signature if secret is configured
            # Supabase uses HMAC-SHA256 with format: sha256=<hex_digest>
            if signature.startswith("sha256="):
                expected = "sha256=" + hmac.new(
                    SUPABASE_WEBHOOK_SECRET.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(expected, signature):
                    logger.warning(f"❌ Invalid Supabase webhook signature from {client_ip}")
                    return jsonify({"status": "success", "message": "Webhook received"}), 200
            else:
                logger.warning(f"⚠️ Supabase signature format unexpected: {signature[:20]}...")
        else:
            logger.warning("⚠️ SUPABASE_WEBHOOK_SECRET not configured - accepting webhook anyway")
        
        event_type = data.get("type", "unknown")
        logger.info(f"✅ Verified Supabase webhook - Event: {event_type}")
        
        # Add webhook to processing queue
        try:
            # Add a marker to distinguish Supabase webhooks
            data["_source"] = "supabase"
            webhook_queue.put_nowait(data)
            logger.info(f"📤 Added Supabase webhook to queue - Event: {event_type}")
        except queue.Full:
            logger.error("❌ Webhook queue is full! Dropping webhook")
            return jsonify({"status": "error", "message": "Queue full"}), 200
        
        # Return immediately to avoid timeout
        return jsonify({"status": "success", "message": "Webhook queued"}), 200
        
    except Exception as e:
        logger.error(f"❌ Supabase webhook error: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": "Processing failed"}), 200

# --- Health check ---

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Basic health check - try to connect to Airtable
        api.base(AIRTABLE_BASE_ID).table(AIRTABLE_TABLE_NAME).all(max_records=1)
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(mst_log).isoformat(),
            "version": "2.0.0",
            "features": {
                "rate_limiting": RATE_LIMITING_ENABLED,
                "ip_whitelist": SECURITY_CONFIG['ENABLE_IP_WHITELIST'],
                "https_required": SECURITY_CONFIG['REQUIRE_HTTPS']
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now(mst_log).isoformat(),
            "error": str(e)
        }), 500

# --- Error handlers - ALWAYS return 200 for webhooks ---

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"400 Bad Request caught - returning 200 anyway")
    return jsonify({"error": "Bad request", "status": "success"}), 200

@app.errorhandler(401)
def unauthorized(error):
    logger.warning(f"401 Unauthorized caught - returning 200 anyway")
    return jsonify({"error": "Unauthorized", "status": "success"}), 200

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"403 Forbidden caught - returning 200 anyway")
    return jsonify({"error": "Forbidden", "status": "success"}), 200

@app.errorhandler(413)
def payload_too_large(error):
    logger.warning(f"413 Payload Too Large caught - returning 200 anyway")
    return jsonify({"error": "Payload too large", "status": "success"}), 200

@app.errorhandler(429)
def rate_limit_exceeded(error):
    logger.warning(f"429 Rate Limit caught - returning 200 anyway")
    return jsonify({"error": "Rate limit exceeded", "status": "success"}), 200

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Server Error caught - returning 200 anyway: {error}")
    return jsonify({"error": "Internal server error", "status": "success"}), 200

@app.errorhandler(Exception)
def handle_exception(error):
    """Catch-all exception handler - ALWAYS returns 200"""
    logger.error(f"Unhandled exception caught - returning 200 anyway: {type(error).__name__}: {str(error)}")
    return jsonify({"error": "Server error", "status": "success", "message": "Exception handled"}), 200

# --- Main entrypoint ---

# Initialize job reconciliation now that all functions are defined
try:
    from webhook_reconciliation import integrate_reconciliation
    # Pass the current module's globals for proper integration
    current_module = type(sys)('webhook_module')
    current_module.__dict__.update(globals())
    current_module.reservations_table = reservations_table
    current_module.properties_table = properties_table
    current_module.customers_table = customers_table
    current_module.process_webhook_async = process_webhook_async
    current_module.find_reservation_by_job_id = find_reservation_by_job_id
    current_module.update_sync_info = update_sync_info
    current_module.environment = environment
    integrate_reconciliation(current_module)
    logger.info(f"✅ Job reconciliation enabled for {environment} environment")
except Exception as e:
    logger.warning(f"⚠️ Job reconciliation not available: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting secure webhook server...")
    logger.info(f"📊 Rate limiting: {'Enabled' if RATE_LIMITING_ENABLED else 'Disabled'}")
    logger.info(f"🔒 HTTPS required: {SECURITY_CONFIG['REQUIRE_HTTPS']}")
    logger.info(f"🌐 IP whitelist: {'Enabled' if SECURITY_CONFIG['ENABLE_IP_WHITELIST'] else 'Disabled'}")
    logger.info(f"📦 Max payload: {SECURITY_CONFIG['MAX_PAYLOAD_SIZE']} bytes")

    # Determine port and environment based on PORT env var
    port = int(os.environ.get('PORT', 5000))
    env_name = Config.environment_name
    
    logger.info(f"🌍 Environment: {env_name}")
    logger.info(f"🔌 Port: {port}")
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        threaded=True
    )