# Webhook Processing - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Webhook Processing system, including CloudMailin email processing, HousecallPro job status updates, security authentication, environment separation, and automated response handling.

## Core Business Purpose

The Webhook Processing system enables real-time communication between external services and the automation platform. It provides secure, authenticated endpoints for receiving data updates, processing payloads, and triggering appropriate system responses while maintaining complete environment separation and comprehensive error handling.

## Business Workflows

### 1. CloudMailin Email Webhook Processing

#### **Email-to-Webhook Conversion Flow**
**Endpoint**: `/webhooks/csv-email`
**Business Logic for iTrip Email Processing**:
```python
def process_cloudmailin_email_webhook(payload):
    """Process incoming email webhook from CloudMailin"""
    
    # Email validation - Only process iTrip checkout reports
    sender = payload.get('envelope', {}).get('from', '').lower()
    subject = payload.get('subject', '').lower()
    
    # Business Rule: Only process iTrip checkout reports
    if 'itrip' not in sender or 'checkouts report' not in subject:
        return {
            'status': 'ignored',
            'reason': 'Email not from iTrip or not checkout report',
            'action': 'No processing required'
        }
    
    # Extract email metadata
    received_date = payload.get('date')
    sender_email = payload.get('from')
    attachments = payload.get('attachments', [])
    
    if not attachments:
        return {
            'status': 'warning',
            'reason': 'iTrip email without attachments',
            'action': 'Manual verification required'
        }
    
    # Process each attachment
    processed_files = []
    for attachment in attachments:
        filename = attachment.get('name', '')
        content_b64 = attachment.get('content', '')
        
        # Business Rule: Only process CSV files
        if not filename.lower().endswith('.csv'):
            continue
            
        # Decode and save to both environments
        csv_content = base64.b64decode(content_b64)
        
        # Save to both dev and prod for processing
        for environment in ['development', 'production']:
            file_path = save_csv_attachment(filename, csv_content, environment)
            processed_files.append({
                'filename': filename,
                'environment': environment,
                'path': file_path,
                'size': len(csv_content)
            })
    
    return {
        'status': 'success',
        'files_processed': len(processed_files),
        'environments_updated': ['development', 'production'],
        'next_step': 'CSV processor will handle files automatically'
    }
```

#### **CSV File Handling and Environment Distribution**
**Business Rules for Multi-Environment Processing**:
```python
def save_csv_attachment(filename, content, environment):
    """Save CSV attachment to environment-specific directory"""
    
    # Environment-specific directory mapping
    directory_mapping = {
        'development': '/home/opc/automation/src/automation/scripts/CSV_process_development/',
        'production': '/home/opc/automation/src/automation/scripts/CSV_process_production/'
    }
    
    target_directory = directory_mapping[environment]
    
    # Generate unique filename to prevent conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(target_directory, unique_filename)
    
    # Save file with proper permissions
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Set file permissions for processing
    os.chmod(file_path, 0o644)
    
    return {
        'file_path': file_path,
        'environment': environment,
        'processing_status': 'ready_for_csv_processor',
        'expected_processing': 'Next 4-hour automation cycle'
    }
```

### 2. HousecallPro Webhook Processing

#### **Environment-Specific Webhook Routing**
**Business Logic for Development vs Production Separation**:
```python
# Webhook endpoint configuration
WEBHOOK_ENDPOINTS = {
    'development': {
        'url': 'https://servativ.themomentcatchers.com/webhooks/hcp-dev',
        'port': 5001,
        'service': 'webhook-dev',
        'airtable_base': 'app67yWFv0hKdl6jM',
        'log_file': 'webhook_development.log',
        'source': 'Boris HCP account (development)'
    },
    'production': {
        'url': 'https://servativ.themomentcatchers.com/webhooks/hcp',
        'port': 5000,
        'service': 'webhook',
        'airtable_base': 'appZzebEIqCU5R9ER',
        'log_file': 'webhook.log',
        'source': '3rd party HCP account (forwarded)'
    }
}

def determine_webhook_environment(request_path):
    """Determine target environment based on webhook path"""
    if '/webhooks/hcp-dev' in request_path:
        return 'development'
    elif '/webhooks/hcp' in request_path:
        return 'production'
    else:
        raise ValueError(f"Unknown webhook path: {request_path}")
```

#### **Dual Authentication System**
**Business Logic for HCP and Forwarded Webhook Authentication**:
```python
def authenticate_webhook_request(request, payload_bytes):
    """Authenticate webhook request using dual authentication system"""
    
    # Method 1: Direct HCP signature verification
    hcp_signature = request.headers.get('X-HousecallPro-Signature')
    hcp_timestamp = request.headers.get('X-HousecallPro-Timestamp')
    
    if hcp_signature and hcp_timestamp:
        if verify_hcp_signature(payload_bytes, hcp_timestamp, hcp_signature):
            return {
                'authenticated': True,
                'method': 'hcp_signature',
                'source': 'Direct HCP webhook'
            }
    
    # Method 2: Servativ forwarding authentication
    internal_auth = request.headers.get('X-Internal-Auth')
    
    if internal_auth == SERVATIV_WEBHOOK_SECRET:
        return {
            'authenticated': True,
            'method': 'forwarding_auth',
            'source': 'Servativ forwarded webhook'
        }
    
    # Authentication failed
    return {
        'authenticated': False,
        'attempted_methods': ['hcp_signature', 'forwarding_auth'],
        'error': 'No valid authentication found'
    }

def verify_hcp_signature(payload_bytes, timestamp, signature):
    """Verify HCP HMAC-SHA256 signature"""
    # Reconstruct signed content
    if timestamp:
        raw_content = timestamp.encode() + b"." + payload_bytes
    else:
        raw_content = payload_bytes
    
    # Calculate expected signature
    expected_signature = hmac.new(
        HCP_WEBHOOK_SECRET.encode(),
        raw_content,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures safely
    return hmac.compare_digest(expected_signature, signature)
```

#### **Job Status Update Processing**
**Business Logic for HCP Job Status Synchronization**:
```python
def handle_job_status_update(job_data, webhook_environment):
    """Process job status updates from HCP webhooks"""
    
    job_id = job_data.get('id')
    work_status = job_data.get('work_status', '')
    customer_data = job_data.get('customer', {})
    
    # Find matching Airtable reservation
    matching_record = find_reservation_by_job_id(job_id, webhook_environment)
    
    if not matching_record:
        # Attempt automatic job reconciliation
        reconciliation_result = attempt_job_reconciliation(job_data, webhook_environment)
        if reconciliation_result['success']:
            matching_record = reconciliation_result['matched_record']
        else:
            return {
                'status': 'orphaned_job',
                'job_id': job_id,
                'reason': 'No matching reservation found',
                'action': 'Manual review required'
            }
    
    # Map HCP work status to Airtable job status
    job_status = map_work_status_to_job_status(work_status)
    
    # Determine update significance (reduced noise strategy)
    significant_statuses = ["In Progress", "Completed", "Canceled"]
    is_significant_change = job_status in significant_statuses
    
    # Prepare update fields
    update_fields = {
        'Service Job Status': job_status,
        'Last Updated': datetime.now().isoformat()
    }
    
    # Only update Service Sync Details for significant changes
    if is_significant_change:
        arizona_timestamp = format_arizona_timestamp()
        sync_message = f"Job {job_status.lower()} - {arizona_timestamp}"
        update_fields['Service Sync Details'] = sync_message
    
    # Execute Airtable update
    update_result = update_airtable_record(
        matching_record['id'],
        update_fields,
        webhook_environment
    )
    
    return {
        'status': 'success',
        'job_id': job_id,
        'job_status': job_status,
        'significant_change': is_significant_change,
        'airtable_updated': update_result['success']
    }

def map_work_status_to_job_status(work_status):
    """Map HCP work status to Airtable job status values"""
    status_mapping = {
        'needs_scheduling': 'Unscheduled',
        'scheduled': 'Scheduled',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'canceled': 'Canceled',
        'on_hold': 'On Hold'
    }
    
    work_status_lower = work_status.lower()
    
    # Check for partial matches
    for hcp_status, airtable_status in status_mapping.items():
        if hcp_status.replace('_', ' ') in work_status_lower:
            return airtable_status
    
    # Default fallback
    return 'Unknown'
```

#### **Schedule Synchronization Processing**
**Business Logic for Schedule Mismatch Detection**:
```python
def handle_schedule_update(job_data, webhook_environment, is_rescheduled=False):
    """Process schedule updates and detect sync mismatches"""
    
    job_id = job_data.get('id')
    schedule_data = job_data.get('schedule', {})
    hcp_scheduled_start = schedule_data.get('scheduled_start')
    
    # Find matching reservation
    matching_record = find_reservation_by_job_id(job_id, webhook_environment)
    if not matching_record:
        return handle_orphaned_schedule_update(job_data, webhook_environment)
    
    # Extract Airtable service time
    airtable_service_time = matching_record['fields'].get('Final Service Time')
    
    if not airtable_service_time or not hcp_scheduled_start:
        return handle_incomplete_schedule_data(job_id, matching_record)
    
    # Parse timestamps with timezone handling
    hcp_datetime = parse_hcp_timestamp(hcp_scheduled_start)
    airtable_datetime = parse_airtable_timestamp(airtable_service_time)
    
    # Convert both to Arizona timezone for comparison
    hcp_arizona = convert_to_arizona_timezone(hcp_datetime)
    airtable_arizona = convert_to_arizona_timezone(airtable_datetime)
    
    # Compare dates and times
    date_match = hcp_arizona.date() == airtable_arizona.date()
    time_match = abs((hcp_arizona - airtable_arizona).total_seconds()) <= 1800  # 30-minute tolerance
    
    # Determine sync status
    if date_match and time_match:
        sync_status = "Synced"
        alert_message = None  # Clear any existing schedule alerts
    elif not date_match:
        sync_status = "Wrong Date"
        alert_message = build_date_mismatch_message(airtable_arizona, hcp_arizona)
    else:
        sync_status = "Wrong Time"
        alert_message = build_time_mismatch_message(airtable_arizona, hcp_arizona)
    
    # Update Airtable with sync status
    update_fields = {
        'Schedule Sync Status': sync_status,
        'Last Schedule Check': datetime.now().isoformat()
    }
    
    # Schedule Sync Details: Alert field - only populated when schedules are mismatched
    if alert_message:
        update_fields['Schedule Sync Details'] = alert_message
    else:
        update_fields['Schedule Sync Details'] = None  # Clear alert when synced
    
    # Service Sync Details: Activity log - always updated
    arizona_timestamp = format_arizona_timestamp()
    activity_message = f"Schedule {'rescheduled' if is_rescheduled else 'updated'}: {sync_status} - {arizona_timestamp}"
    update_fields['Service Sync Details'] = activity_message
    
    return update_airtable_record(matching_record['id'], update_fields, webhook_environment)

def build_time_mismatch_message(airtable_time, hcp_time):
    """Build user-friendly time mismatch message"""
    airtable_formatted = format_arizona_time(airtable_time)
    hcp_formatted = format_arizona_time(hcp_time)
    arizona_timestamp = format_arizona_timestamp()
    
    return f"Airtable shows {airtable_formatted} but HCP shows {hcp_formatted} - {arizona_timestamp}"

def build_date_mismatch_message(airtable_time, hcp_time):
    """Build user-friendly date mismatch message"""
    airtable_date = format_arizona_date(airtable_time)
    hcp_date = format_arizona_date(hcp_time)
    arizona_timestamp = format_arizona_timestamp()
    
    return f"Airtable shows {airtable_date} but HCP shows {hcp_date} - {arizona_timestamp}"
```

### 3. Automatic Job Reconciliation

#### **Orphaned Job Detection and Matching**
**Business Logic for Linking Unassigned HCP Jobs**:
```python
def attempt_job_reconciliation(job_data, webhook_environment):
    """Automatically match orphaned HCP jobs to existing reservations"""
    
    # Extract job characteristics for matching
    customer_id = job_data.get('customer', {}).get('id')
    address_id = job_data.get('address', {}).get('id')
    scheduled_start = job_data.get('schedule', {}).get('scheduled_start')
    
    if not all([customer_id, address_id, scheduled_start]):
        return {
            'success': False,
            'reason': 'Insufficient job data for reconciliation',
            'missing_fields': [f for f in ['customer_id', 'address_id', 'scheduled_start'] 
                             if not job_data.get(f.split('_')[0], {}).get(f.split('_')[1] if '_' in f else 'id')]
        }
    
    job_datetime = parse_hcp_timestamp(scheduled_start)
    
    # Define search window (1 hour before/after)
    search_start = (job_datetime - timedelta(hours=1)).isoformat()
    search_end = (job_datetime + timedelta(hours=1)).isoformat()
    
    # Find reservations without job IDs in time window
    candidate_reservations = find_unlinked_reservations_in_window(
        search_start, search_end, webhook_environment
    )
    
    # Match based on property (customer/address combination)
    for reservation in candidate_reservations:
        property_mapping = get_property_hcp_mapping(reservation)
        
        if (property_mapping['hcp_customer_id'] == customer_id and 
            property_mapping['hcp_address_id'] == address_id):
            
            # Found match - link job to reservation
            link_result = link_job_to_reservation(
                job_data['id'], reservation['id'], webhook_environment
            )
            
            if link_result['success']:
                return {
                    'success': True,
                    'matched_record': reservation,
                    'job_id': job_data['id'],
                    'reservation_id': reservation['id'],
                    'match_criteria': 'property_and_timing'
                }
    
    return {
        'success': False,
        'reason': 'No matching reservation found',
        'candidates_found': len(candidate_reservations),
        'search_window': f"{search_start} to {search_end}"
    }

def find_unlinked_reservations_in_window(start_time, end_time, environment):
    """Find reservations without job IDs in specified time window"""
    
    # Airtable formula for finding unlinked reservations
    filter_formula = f"""AND(
        NOT({{Service Job ID}}),
        NOT({{Status}} = 'Old'),
        {{Entry Type}} = 'Reservation',
        DATETIME_PARSE({{Final Service Time}}) >= DATETIME_PARSE('{start_time}'),
        DATETIME_PARSE({{Final Service Time}}) <= DATETIME_PARSE('{end_time}')
    )"""
    
    airtable_base = get_airtable_base(environment)
    
    return airtable_base.table('Reservations').all(
        formula=filter_formula,
        max_records=100
    )
```

### 4. Security and Rate Limiting

#### **Request Validation and Security Measures**
**Business Logic for Webhook Security**:
```python
def validate_webhook_request(request):
    """Comprehensive webhook request validation"""
    
    validation_results = {
        'valid': True,
        'security_checks': [],
        'warnings': [],
        'errors': []
    }
    
    # Payload size validation
    content_length = request.headers.get('Content-Length', '0')
    try:
        payload_size = int(content_length)
        if payload_size > SECURITY_CONFIG['MAX_PAYLOAD_SIZE']:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Payload too large: {payload_size} bytes")
    except ValueError:
        validation_results['warnings'].append("Invalid Content-Length header")
    
    # Content type validation
    content_type = request.headers.get('Content-Type', '')
    if 'application/json' not in content_type:
        validation_results['warnings'].append(f"Unexpected content type: {content_type}")
    
    # User agent analysis
    user_agent = request.headers.get('User-Agent', '')
    if 'HousecallPro' in user_agent:
        validation_results['security_checks'].append('Recognized HCP user agent')
    elif user_agent:
        validation_results['warnings'].append(f"Unknown user agent: {user_agent}")
    
    # Rate limiting check
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)
    rate_limit_status = check_rate_limit(client_ip)
    
    if rate_limit_status['exceeded']:
        validation_results['valid'] = False
        validation_results['errors'].append('Rate limit exceeded')
    
    validation_results['security_checks'].append(f"Rate limit: {rate_limit_status['requests']}/{rate_limit_status['limit']}")
    
    return validation_results

SECURITY_CONFIG = {
    'MAX_PAYLOAD_SIZE': 2097152,    # 2MB limit
    'SIGNATURE_TOLERANCE': 300,     # 5 minutes for timestamp validation
    'RATE_LIMIT_REQUESTS': 30,      # 30 requests per minute
    'RATE_LIMIT_WINDOW': 60,        # 60 seconds
    'ALWAYS_RETURN_200': True       # Prevent webhook disabling
}
```

#### **Asynchronous Processing with Rate Limiting**
**Business Logic for Queue-Based Processing**:
```python
class WebhookProcessor:
    """Asynchronous webhook processor with rate limiting"""
    
    def __init__(self):
        self.webhook_queue = queue.Queue(maxsize=1000)
        self.rate_limiter = RateLimiter(max_per_second=5)  # Airtable API limit
        self.worker_thread = threading.Thread(target=self.process_webhook_queue)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def enqueue_webhook(self, webhook_data):
        """Add webhook to processing queue"""
        try:
            # Add webhook with metadata
            queue_item = {
                'webhook_data': webhook_data,
                'received_at': datetime.now().isoformat(),
                'environment': webhook_data.get('environment'),
                'source_ip': webhook_data.get('source_ip'),
                'retry_count': 0
            }
            
            self.webhook_queue.put(queue_item, timeout=5)
            
            return {
                'queued': True,
                'queue_size': self.webhook_queue.qsize(),
                'estimated_processing': 'Within 30 seconds'
            }
            
        except queue.Full:
            return {
                'queued': False,
                'reason': 'Queue at capacity',
                'action': 'Webhook processing overloaded'
            }
    
    def process_webhook_queue(self):
        """Worker thread for processing webhooks from queue"""
        while True:
            try:
                # Get webhook from queue with timeout
                queue_item = self.webhook_queue.get(timeout=60)
                
                # Apply rate limiting
                self.rate_limiter.wait()
                
                # Process webhook
                processing_result = self.process_single_webhook(queue_item)
                
                # Handle retry logic
                if not processing_result['success'] and queue_item['retry_count'] < 3:
                    queue_item['retry_count'] += 1
                    # Re-queue with exponential backoff
                    time.sleep(2 ** queue_item['retry_count'])
                    self.webhook_queue.put(queue_item)
                
                # Mark task complete
                self.webhook_queue.task_done()
                
            except queue.Empty:
                # Normal timeout - continue waiting
                continue
            except Exception as error:
                logger.error(f"Webhook processing error: {error}")
                # Continue processing other webhooks
                continue
```

### 5. Error Handling and Response Patterns

#### **Graceful Error Handling Strategy**
**Business Logic for Maintaining Webhook Reliability**:
```python
def handle_webhook_error(error, webhook_context):
    """Handle webhook processing errors gracefully"""
    
    error_response = {
        'status': 'success',  # Always return success to prevent webhook disabling
        'processed': False,
        'error_logged': True,
        'timestamp': datetime.now().isoformat()
    }
    
    error_classification = classify_error(error)
    
    if error_classification['type'] == 'authentication':
        error_response.update({
            'reason': 'Authentication failed',
            'action': 'Check webhook authentication configuration',
            'severity': 'high'
        })
        
    elif error_classification['type'] == 'validation':
        error_response.update({
            'reason': 'Payload validation failed',
            'action': 'Check webhook payload format',
            'severity': 'medium'
        })
        
    elif error_classification['type'] == 'airtable':
        error_response.update({
            'reason': 'Airtable update failed',
            'action': 'Retry automatically or manual intervention',
            'severity': 'medium'
        })
        
    elif error_classification['type'] == 'system':
        error_response.update({
            'reason': 'System error',
            'action': 'Alert system administrator',
            'severity': 'high'
        })
    
    # Log error with context
    log_webhook_error(error, webhook_context, error_classification)
    
    # Send alerts for high severity errors
    if error_response['severity'] == 'high':
        send_admin_alert(error, webhook_context)
    
    return error_response

def classify_error(error):
    """Classify error type for appropriate handling"""
    error_str = str(error).lower()
    
    if 'signature' in error_str or 'authentication' in error_str:
        return {'type': 'authentication', 'retryable': False}
    elif 'payload' in error_str or 'validation' in error_str:
        return {'type': 'validation', 'retryable': False}
    elif 'airtable' in error_str or 'api' in error_str:
        return {'type': 'airtable', 'retryable': True}
    else:
        return {'type': 'system', 'retryable': True}
```

## Critical Business Rules

### Webhook Authentication Rules
1. **Dual Authentication**: Support both HCP signatures and forwarding authentication
2. **Signature Validation**: HMAC-SHA256 with timestamp tolerance of 5 minutes
3. **Always Return 200**: Prevent webhook providers from disabling endpoints
4. **Rate Limiting**: Maximum 30 requests per minute per IP address

### Environment Separation Rules
1. **Endpoint Isolation**: Separate URLs and ports for dev vs production
2. **Data Isolation**: Environment-specific Airtable bases and log files
3. **Service Separation**: Independent systemd services for each environment
4. **CSV Distribution**: Email attachments saved to both environments

### Processing Priority Rules
1. **Significant Status Changes**: Only update sync details for In Progress, Completed, Canceled
2. **Schedule Alerts**: Alert field only populated when schedules are mismatched
3. **Activity Logging**: Service sync details continuously updated for all operations
4. **Reconciliation**: Automatic job linking based on property and timing

### Update Strategy Rules
1. **HCP-Sourced Records**: Only update records with Entry Source = "HCP" or existing Job ID
2. **Timestamp Comparison**: 30-minute tolerance for schedule sync validation
3. **Arizona Timezone**: All timestamps displayed in Arizona timezone
4. **Queue Processing**: Maximum 5 Airtable API calls per second

### Error Handling Rules
1. **Graceful Degradation**: Continue processing even with partial failures
2. **Retry Logic**: Maximum 3 retries with exponential backoff
3. **Error Classification**: Different handling based on error type
4. **Admin Alerts**: High severity errors trigger immediate notifications

## Error Handling Patterns

### Authentication Errors
- Invalid signatures logged with full context for debugging
- Forwarding authentication failures indicate configuration issues
- Missing authentication headers suggest integration problems

### Processing Errors
- Airtable API failures trigger automatic retry with backoff
- Record not found errors initiate reconciliation procedures
- Validation failures logged for pattern analysis

### System Errors
- Queue overflow indicates processing capacity issues
- Worker thread failures trigger service restart procedures
- Critical errors escalated to administrative notification

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Webhook Processing business logic
**Primary Code**: Webhook handlers and authentication systems