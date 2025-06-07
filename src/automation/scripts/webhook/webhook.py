# secure_webhook_app.py
import os
import hmac
import hashlib
import json
import pytz
import uuid
import time
import sys
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

# File handler with MST
file_handler = logging.FileHandler(str(Config.get_logs_dir() / "webhook.log"))
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
SERVATIV_WEBHOOK_SECRET = "sk_servativ_webhook_7f4d9b2e8a3c1f6d"

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
    logger.info("✅ Airtable connection initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize Airtable: {e}")
    exit(1)

# Arizona timezone
ARIZONA_TZ = pytz.timezone('America/Phoenix')

# --- Utility and helper functions ---

def get_arizona_time():
    return datetime.now(timezone.utc).astimezone(ARIZONA_TZ)

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
    """Find reservation record by HCP job ID"""
    try:
        results = reservations_table.all(
            formula=f"{{Service Job ID}} = '{job_id}'",
            fields=["Reservation UID", "Service Job ID", "Status", "Job Status", "Entry Source"]
        )
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
        now = get_arizona_time().isoformat()
        return reservations_table.update(record_id, {
            "Sync Date and Time": now,
            "Sync Details": details
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
        update_sync_info(record_id, f"Updated job status to {job_status}")
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
        update_sync_info(record_id, f"Updated assignee to: {assignee or '(empty)'}")
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
        sync_details = "Rescheduled job" if is_rescheduled else "Updated schedule"
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
        update_sync_info(record_id, f"Appointment {appointment_id} discarded, job unscheduled")
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
        update_sync_info(record_id, f"Appointment {appointment_id} scheduled, assignee: {assignee or '(empty)'}")
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
        
        update_data = {
            "Service Appointment ID": appointment_id,
            "Assignee": assignee,
            "Scheduled Service Time": start_time
        }
        
        logger.info(f"📋 Appointment ID: {appointment_id}")
        logger.info(f"👤 Assignee: {assignee or '(empty)'}")
        logger.info(f"⏰ Rescheduled start: {start_time or '(empty)'}")
        
        result = reservations_table.update(record_id, update_data)
        update_sync_info(record_id, f"Appointment {appointment_id} rescheduled, assignee: {assignee or '(empty)'}")
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
        update_sync_info(record_id, f"Pros assigned to appointment {appointment_id}: {assignee or '(empty)'}")
        logger.info(f"✅ Pros assigned to appointment {appointment_id} for record: {record_id}")
        return result
    except Exception as e:
        logger.error(f"Error handling pros assigned: {e}")
        return None

def handle_appointment_pros_unassigned(appointment_data, existing_record):
    """Handle pros unassigned from appointment events"""
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
        update_sync_info(record_id, f"Pros unassigned from appointment {appointment_id}, remaining: {assignee or '(none)'}")
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
        
        # Content-Type check for webhook endpoint
        if request.endpoint == 'hcp_webhook' and request.method == 'POST':
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
    """Main HCP webhook handler"""
    client_ip = get_client_ip()
    logger.info(f"📥 Webhook received from {client_ip}")
    
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

# --- Error handlers ---

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 200

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 200

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Forbidden"}), 200

@app.errorhandler(413)
def payload_too_large(error):
    return jsonify({"error": "Payload too large"}), 200

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({"error": "Rate limit exceeded"}), 200

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 200

# --- Main entrypoint ---

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