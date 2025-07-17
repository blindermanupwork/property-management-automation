# Error Handling & Recovery - Business Logic A-Z

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Complete alphabetical documentation of error handling business rules and implementation

---

## 🎯 **BUSINESS RULES BY ALPHABETICAL ORDER**

### **A - API Error Handling with Exponential Backoff**

**Condition**: When API calls receive rate limiting or transient errors  
**Action**: Implement exponential backoff retry strategy with maximum attempts  
**Implementation**: 
```javascript
// From hcp-sync scripts
async function hcp(path, method = 'GET', body = null) {
  const maxRetries = 3;
  let retry = 0;
  
  while (true) {
    const res = await fetch(`https://api.housecallpro.com${path}`, {
      method,
      headers: { 'Authorization': `Bearer ${HCP_TOKEN}` },
      body: body ? JSON.stringify(body) : undefined
    });
    
    if (res.status === 429 && retry < maxRetries) {
      retry++;
      const reset = res.headers.get('RateLimit-Reset');
      const wait = reset
        ? Math.max(new Date(reset) - new Date(), 1000)
        : 1000 * (2 ** retry);  // Exponential backoff: 2s, 4s, 8s
      console.log(`⏳ Rate limited, waiting ${wait / 1000}s...`);
      await new Promise(resolve => setTimeout(resolve, wait));
      continue;
    }
    return res;
  }
}
```
**Exception**: Critical API calls may have different retry strategies  
**Business Impact**: Prevents API quota exhaustion while maintaining service availability

### **B - Batch Operation Error Recovery**

**Condition**: When batch operations to Airtable fail  
**Action**: Implement batch collector with automatic flush and error handling  
**Implementation**:
```python
# From icsProcess.py
class BatchCollector:
    def flush(self):
        if not self.records:
            return
        try:
            if self.op == "update":
                unique = []
                seen_ids = set()
                for r in self.records:
                    if r["id"] not in seen_ids:
                        unique.append(r)
                        seen_ids.add(r["id"])
                self.table.batch_update(unique)
            else:
                self.table.batch_create([r["fields"] for r in self.records])
        except Exception as e:
            logging.error(f"Batch {self.op} error: {e}", exc_info=True)
        finally:
            self.records = []  # Always clear to prevent memory issues
```
**Exception**: Manual intervention may be required for persistent batch failures  
**Business Impact**: Ensures data consistency and prevents memory leaks during bulk operations

### **C - Configuration Validation with Clear Error Messages**

**Condition**: When required configuration is missing or invalid  
**Action**: Validate configuration early with specific remediation guidance  
**Implementation**:
```python
# From webhook.py
missing_config = Config.validate_config()
if missing_config or not HCP_WEBHOOK_SECRET:
    logger.error(f"❌ Missing required configuration: {missing_config + (['HCP_WEBHOOK_SECRET'] if not HCP_WEBHOOK_SECRET else [])}")
    exit(1)

# From controller.py
try:
    config_errors = config.validate_config()
    if config_errors:
        print("❌ Configuration validation failed:")
        for error in config_errors:
            print(f"   • {error}")
        print("\n💡 Please fix the configuration issues and try again.")
        sys.exit(1)
except Exception as e:
    self.logger.error(f"Configuration validation error: {str(e)}")
    sys.exit(1)
```
**Exception**: Force flag may bypass some validation in emergency situations  
**Business Impact**: Prevents execution with invalid configuration that could corrupt data

### **D - Data Integrity Validation Before Processing**

**Condition**: When processing CSV files with property links  
**Action**: Validate all required relationships exist before processing  
**Implementation**:
```python
# From csvProcess.py
def validate_property_links(reservations, property_table):
    """Validate that all properties in reservations exist in Property table"""
    missing_props = set()
    
    for res in reservations:
        prop_name = res.get("Property")
        if not prop_name:
            continue
            
        # Check if property exists
        formula = f"{{Name}} = '{prop_name}'"
        try:
            matches = property_table.all(formula=formula)
            if not matches:
                missing_props.add(prop_name)
        except Exception as e:
            logging.error(f"Error checking property {prop_name}: {e}")
            missing_props.add(prop_name)
    
    if missing_props:
        logging.error(
            f"❌ {len(missing_props)} reservation(s) missing Property mapping: "
            f"{', '.join(missing_props)}"
        )
        raise ValueError(f"Missing property links for {len(missing_props)} reservations")
```
**Exception**: Manual property creation may be allowed in development  
**Business Impact**: Prevents orphaned reservations without valid property associations

### **E - Exception Context Preservation**

**Condition**: When exceptions occur during processing  
**Action**: Preserve full context including stack traces and relevant data  
**Implementation**:
```python
# From controller.py
def run_automation(self, automation_name, automation_func, *args, **kwargs):
    try:
        result = automation_func(*args, **kwargs)
    except Exception as e:
        end_time = datetime.now(arizona_tz)
        duration = end_time - start_time
        error_details = f"Error after {duration.total_seconds():.1f}s: {str(e)}"
        
        print(f"❌ '{automation_name}' failed with error: {e}")
        print(f"📝 Traceback: {traceback.format_exc()}")
        
        # Update status with full error context
        self.update_automation_status(automation_name, False, error_details, start_time)
        
        # Log with full context
        self.logger.error(f"Automation '{automation_name}' failed", exc_info=True)
        return False
```
**Exception**: Production may limit stack trace exposure for security  
**Business Impact**: Enables effective troubleshooting and root cause analysis

### **F - Fallback Values for Missing Data**

**Condition**: When expected data fields are missing or null  
**Action**: Use sensible default values to prevent null reference errors  
**Implementation**:
```javascript
// From jobs.js
const serviceType = (serviceTypeObj && serviceTypeObj.name) ? serviceTypeObj.name : 'Turnover';
const customerName = (guestFirstName || '') + (guestLastName ? ' ' + guestLastName : '');

// From schedules.js
if (!nextGuestDate) {
    // Fall back to searching for next reservation
    const nextReservation = await findNextReservation(base, propertyLinks[0], checkOutDate);
    serviceName = nextReservation ? 
        `${serviceType} STR Next Guest ${month} ${day}` : 
        `${serviceType} STR Next Guest Unknown`;
}
```
**Exception**: Critical fields may require explicit values with no fallback  
**Business Impact**: Maintains system functionality even with incomplete data

### **G - Graceful Degradation for Component Failures**

**Condition**: When individual automation components fail  
**Action**: Continue processing other components to maintain partial functionality  
**Implementation**:
```python
# From controller.py
def run_full_automation(self):
    """Run all active automations in sequence"""
    results = {}
    
    for automation_name, automation_func in self.automations.items():
        try:
            if self.get_automation_status(automation_name):
                success = self.run_automation(automation_name, automation_func)
                results[automation_name] = success
            else:
                print(f"⏭️  '{automation_name}' is disabled in Airtable, skipping...")
                results[automation_name] = None
        except Exception as e:
            print(f"❌ Critical error in {automation_name}: {e}")
            results[automation_name] = False
            # Continue with next automation
    
    return results
```
**Exception**: Critical path automations may halt entire process on failure  
**Business Impact**: Maximizes system availability during partial failures

### **H - HTTP Error Response Handling**

**Condition**: When external HTTP requests fail  
**Action**: Handle specific HTTP errors with appropriate recovery strategies  
**Implementation**:
```python
# From icsProcess.py
async def fetch_ics(session, url):
    """Asynchronously fetches ICS content from a URL with comprehensive error handling"""
    try:
        async with session.get(url, timeout=15) as resp:
            if resp.status == 404:
                return url, False, None, "Feed not found (404)"
            elif resp.status == 403:
                return url, False, None, "Access forbidden (403)"
            elif resp.status >= 500:
                return url, False, None, f"Server error ({resp.status})"
            elif resp.status != 200:
                return url, False, None, f"HTTP {resp.status} - {resp.reason}"
                
            content = await resp.text()
            return url, True, content, None
            
    except asyncio.TimeoutError:
        return url, False, None, "Timeout after 15 seconds"
    except aiohttp.ClientError as e:
        return url, False, None, f"Network error: {str(e)}"
    except Exception as e:
        return url, False, None, f"Unexpected error: {str(e)}"
```
**Exception**: Critical feeds may have longer timeout or retry logic  
**Business Impact**: Provides detailed error information for troubleshooting feed issues

### **I - Input Validation with Early Exit**

**Condition**: When input data fails validation checks  
**Action**: Exit early with clear error messages before processing  
**Implementation**:
```python
# From csvProcess.py
def parse_row(raw, hdr_map):
    """Parse a row with comprehensive validation"""
    # Required field validation
    uid_raw = raw.get(hdr_map.get("UID", "UID"), "").strip()
    if not uid_raw:
        logging.warning("Row missing UID – skipped")
        return None
    
    # Date validation
    cin_raw = raw.get(hdr_map.get("Check-in Date", "Check-in Date"), "").strip()
    cout_raw = raw.get(hdr_map.get("Check-out Date", "Check-out Date"), "").strip()
    
    try:
        cin_date = parse(cin_raw).date()
        cout_date = parse(cout_raw).date()
    except Exception:
        logging.warning(f"Row with UID={uid_raw} has unparsable dates "
                        f"({cin_raw!r}, {cout_raw!r}) – skipped")
        return None
    
    # Logical validation
    if cout_date <= cin_date:
        logging.warning(f"Row with UID={uid_raw} has checkout <= checkin – skipped")
        return None
    
    return parsed_data
```
**Exception**: Some validation may be relaxed in development mode  
**Business Impact**: Prevents invalid data from corrupting system state

### **J - Job Creation Error Recovery**

**Condition**: When HousecallPro job creation fails  
**Action**: Log detailed error and mark record for manual intervention  
**Implementation**:
```javascript
// From jobs.js
try {
    const jobRes = await hcp('/jobs', 'POST', jobPayload);
    
    if (!jobRes.ok) {
        const errorText = await jobRes.text();
        console.error(`❌ Failed to create job: ${jobRes.status} - ${errorText}`);
        
        // Update Airtable with error status
        await base('Reservations').update(reservation.id, {
            'HCP Sync Status': `Error: ${jobRes.status}`,
            'Service Sync Details': `Job creation failed: ${errorText} - ${new Date().toLocaleString()}`
        });
        
        errorCount++;
        continue;
    }
    
    const job = await jobRes.json();
    console.log(`✅ Created job ${job.id} for ${resUID}`);
    
} catch (error) {
    console.error(`❌ Unexpected error creating job for ${resUID}: ${error.message}`);
    errorCount++;
}
```
**Exception**: Critical jobs may trigger immediate alerts  
**Business Impact**: Provides visibility into job creation failures for manual resolution

### **K - Kill Switch for Runaway Processes**

**Condition**: When processes exceed timeout thresholds  
**Action**: Implement timeout protection with process termination  
**Implementation**:
```python
# From evolveScrape.py
def second_tab_export(headless: bool, max_retries: int = 3):
    for attempt in range(max_retries):
        driver = None
        try:
            # Set page load timeout
            driver.set_page_load_timeout(60)
            
            # Perform export with timeout
            wait = WebDriverWait(driver, 30)
            download_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Download')]"))
            )
            
        except TimeoutException:
            log.error(f"Timeout waiting for element on attempt {attempt + 1}")
            if driver:
                driver.quit()
            continue
        except Exception as e:
            log.error(f"Unexpected error: {str(e)}")
        finally:
            if driver:
                driver.quit()
```
**Exception**: Critical processes may have extended timeouts  
**Business Impact**: Prevents resource exhaustion from hung processes

### **L - Logging with UTF-8 Error Handling**

**Condition**: When logging content with special characters  
**Action**: Handle encoding errors gracefully to prevent logging failures  
**Implementation**:
```python
# From csvProcess.py
# Console logger with UTF-8 error handling
stdout_utf8 = io.TextIOWrapper(
    sys.stdout.buffer,
    encoding="utf-8",
    errors="replace",  # Un-encodable chars → '?' so emit never fails
    line_buffering=True
)

console = logging.StreamHandler(stdout_utf8)
console.setLevel(logging.INFO)
console.setFormatter(ColoredFormatter(
    "%(log_color)s%(message)s",
    log_colors={
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
))
```
**Exception**: Critical error messages may use ASCII-only for compatibility  
**Business Impact**: Ensures logging system remains functional with international data

### **M - Memory Management in Batch Operations**

**Condition**: When processing large datasets that could exhaust memory  
**Action**: Implement batch processing with automatic memory cleanup  
**Implementation**:
```python
# From icsProcess.py
class BatchCollector:
    def __init__(self, table, op="create", batch_size=10):
        self.table = table
        self.op = op
        self.batch_size = batch_size
        self.records = []
    
    def add(self, record):
        self.records.append(record)
        if len(self.records) >= self.batch_size:
            self.flush()
    
    def flush(self):
        if not self.records:
            return
        try:
            # Process batch
            if self.op == "update":
                self.table.batch_update(self.records)
            else:
                self.table.batch_create([r["fields"] for r in self.records])
        finally:
            self.records = []  # Always clear to free memory
```
**Exception**: Critical operations may use smaller batch sizes  
**Business Impact**: Prevents out-of-memory errors during bulk data processing

### **N - Network Error Resilience**

**Condition**: When network requests fail due to connectivity issues  
**Action**: Implement retry logic with network-specific error handling  
**Implementation**:
```python
# From webhook.py
def get_airtable_record(job_id):
    """Get Airtable record with network error handling"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            url = f"{AIRTABLE_API_URL}/{AIRTABLE_BASE_ID}/Reservations"
            params = {
                'filterByFormula': f"{{HCP Job ID}} = '{job_id}'",
                'maxRecords': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
            time.sleep(retry_delay)
            retry_delay *= 2
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
            time.sleep(retry_delay)
            retry_delay *= 2
        except Exception as e:
            logger.error(f"Error getting record: {str(e)}")
            return None
    
    logger.error(f"Failed to get record after {max_retries} attempts")
    return None
```
**Exception**: Critical API calls may have different retry strategies  
**Business Impact**: Maintains service availability during transient network issues

### **O - Operation Status Tracking**

**Condition**: When automation operations complete or fail  
**Action**: Update operation status in Airtable for monitoring and alerting  
**Implementation**:
```python
# From controller.py
def update_automation_status(self, name, success, details="", start_time=None):
    """Update automation status in Airtable with comprehensive tracking"""
    try:
        records = self.automation_table.all(formula=f"{{Name}} = '{name}'")
        if records:
            update_fields = {
                "Last Run Status": "Success" if success else "Failed",
                "Last Run Details": details[:1000],  # Truncate long error messages
                "Last Run Date": datetime.now(self.arizona_tz).isoformat()
            }
            
            if start_time:
                duration = (datetime.now(self.arizona_tz) - start_time).total_seconds()
                update_fields["Last Run Duration (seconds)"] = duration
            
            self.automation_table.update(records[0]['id'], update_fields)
            
    except Exception as e:
        self.logger.error(f"Failed to update automation status: {e}")
        # Don't fail the automation due to status update failure
```
**Exception**: Status update failures don't halt automation execution  
**Business Impact**: Provides operational visibility without affecting core functionality

### **P - Partial Success Handling**

**Condition**: When batch operations partially succeed  
**Action**: Track and report both successes and failures  
**Implementation**:
```javascript
// From dev-hcp-sync.cjs
console.log('\n📊 Processing Summary:');
console.log(`✅ Successfully processed: ${successCount} reservations`);
console.log(`❌ Errors encountered: ${errorCount} reservations`);
console.log(`⏭️  Skipped (no action needed): ${skipCount} reservations`);
console.log(`🏠 Properties requiring HCP mapping: ${unmappedProperties.size}`);

if (errorCount > 0) {
    console.log('\n⚠️  Some reservations had errors. Check the Service Sync Details field for specifics.');
}

if (unmappedProperties.size > 0) {
    console.log('\n⚠️  The following properties need HCP customer mapping:');
    unmappedProperties.forEach(prop => console.log(`   - ${prop}`));
}
```
**Exception**: Critical operations may require 100% success rate  
**Business Impact**: Provides clear visibility into partial failures for remediation

### **Q - Queue-Based Error Isolation**

**Condition**: When webhook processing could block main thread  
**Action**: Use queue-based processing to isolate errors  
**Implementation**:
```python
# From webhook.py
def webhook_worker():
    """Worker thread for processing webhooks from queue"""
    while True:
        try:
            # Get webhook data from queue with timeout
            webhook_data = webhook_queue.get(timeout=60)
            
            try:
                process_webhook_async(webhook_data)
            except Exception as e:
                logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            finally:
                webhook_queue.task_done()
                
        except queue.Empty:
            # No webhooks for 60 seconds, just continue
            continue
        except Exception as e:
            logger.error(f"Worker thread error: {str(e)}", exc_info=True)
            time.sleep(5)  # Brief pause before continuing
```
**Exception**: Critical webhooks may bypass queue for immediate processing  
**Business Impact**: Prevents single webhook failure from blocking all webhook processing

### **R - Rate Limiting Protection**

**Condition**: When making multiple API calls that could exceed rate limits  
**Action**: Implement rate limiting to prevent API quota exhaustion  
**Implementation**:
```python
# From webhook.py
class RateLimiter:
    def __init__(self, calls_per_second=5):
        self.min_interval = 1.0 / calls_per_second
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

# Usage
rate_limiter = RateLimiter(calls_per_second=5)

def make_api_call():
    rate_limiter.wait_if_needed()
    # Make actual API call
```
**Exception**: Bulk operations may use different rate limits  
**Business Impact**: Prevents API service disruption and maintains good standing with providers

### **S - Security Error Sanitization**

**Condition**: When errors contain sensitive information  
**Action**: Sanitize error messages before logging or displaying  
**Implementation**:
```python
# From webhook.py
def sanitize_error_message(error_msg):
    """Remove sensitive information from error messages"""
    # Remove API keys
    error_msg = re.sub(r'pat[a-zA-Z0-9]{17,}', 'pat***', error_msg)
    # Remove bearer tokens
    error_msg = re.sub(r'Bearer [a-zA-Z0-9\-._~+/]+', 'Bearer ***', error_msg)
    # Remove webhook secrets
    error_msg = re.sub(r'whsec_[a-zA-Z0-9]+', 'whsec_***', error_msg)
    return error_msg

@app.route('/webhooks/hcp', methods=['POST'])
def handle_webhook():
    try:
        # Process webhook
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        safe_error = sanitize_error_message(str(e))
        logger.error(f"Webhook error: {safe_error}")
        # Never expose internal errors to external callers
        return jsonify({"status": "error", "message": "Internal error"}), 200
```
**Exception**: Development mode may show more detailed errors  
**Business Impact**: Prevents security breaches through error message exposure

### **T - Transaction Rollback for Data Consistency**

**Condition**: When multi-step operations fail partway through  
**Action**: Implement transaction-like behavior with rollback capability  
**Implementation**:
```python
# From icsProcess.py
def mark_all_as_old_and_clone(table, records, field_to_change, now_iso, status="Modified"):
    """Transaction-like operation to maintain data consistency"""
    batch_old = BatchCollector(table, op="update")
    created_record_id = None
    
    try:
        # Step 1: Mark all existing records as old
        for r in records:
            batch_old.add({
                "id": r["id"],
                "fields": {
                    "Status": {"name": "Old"},
                    "History Note": f"Marked old at {now_iso} due to {status.lower()}"
                }
            })
        batch_old.flush()
        
        # Step 2: Create new record
        cloned_fields = records[0]["fields"].copy()
        cloned_fields.update(field_to_change)
        created_record = table.create(cloned_fields)
        created_record_id = created_record['id']
        
        return created_record
        
    except Exception as e:
        logging.error(f"Transaction failed: {e}")
        # If we created a new record but failed later, delete it
        if created_record_id:
            try:
                table.delete(created_record_id)
            except:
                pass
        raise
```
**Exception**: Some operations may not support full rollback  
**Business Impact**: Maintains data consistency during complex multi-step operations

### **U - User-Friendly Error Messages**

**Condition**: When errors need to be displayed to users or in logs  
**Action**: Convert technical errors to actionable user messages  
**Implementation**:
```javascript
// From schedules.js
function getUserFriendlyError(error) {
    if (error.message.includes('UNKNOWN_FIELD_NAME')) {
        return 'Configuration error: Missing required field in Airtable. Please check your base schema.';
    } else if (error.message.includes('INVALID_PERMISSIONS')) {
        return 'Permission error: Please check your Airtable API key permissions.';
    } else if (error.message.includes('NOT_FOUND')) {
        return 'Record not found. It may have been deleted or the ID is incorrect.';
    } else if (error.message.includes('RATE_LIMITED')) {
        return 'Too many requests. Please wait a moment and try again.';
    } else {
        return `An error occurred: ${error.message}. Please contact support if this persists.`;
    }
}
```
**Exception**: Debug mode may show technical error details  
**Business Impact**: Enables users to understand and resolve issues independently

### **V - Validation Error Aggregation**

**Condition**: When multiple validation errors occur  
**Action**: Collect and report all validation errors together  
**Implementation**:
```python
# From config_dev.py
def validate_config(self) -> List[str]:
    """Validate configuration and return ALL errors"""
    errors = []
    
    # Check API key
    api_key = os.environ.get('DEV_AIRTABLE_API_KEY')
    if not api_key:
        errors.append("DEV_AIRTABLE_API_KEY is required for development")
    elif not api_key.startswith('pat'):
        errors.append("DEV_AIRTABLE_API_KEY should start with 'pat'")
    
    # Check base ID
    base_id = os.environ.get('DEV_AIRTABLE_BASE_ID')
    if not base_id:
        errors.append("DEV_AIRTABLE_BASE_ID is required for development")
    elif len(base_id) != 17:
        errors.append("DEV_AIRTABLE_BASE_ID should be 17 characters long")
    
    # Check HCP token
    hcp_token = os.environ.get('DEV_HCP_TOKEN')
    if not hcp_token:
        errors.append("DEV_HCP_TOKEN is required for HCP integration")
    
    # Return all errors at once
    return errors
```
**Exception**: Critical errors may halt validation early  
**Business Impact**: Allows fixing all configuration issues in one pass

### **W - Webhook Always-200 Response Strategy**

**Condition**: When webhook processing encounters any error  
**Action**: Always return HTTP 200 to prevent webhook service from disabling endpoint  
**Implementation**:
```python
# From webhook.py
@app.route('/webhooks/hcp', methods=['POST'])
def handle_webhook():
    """Handle HCP webhooks with always-200 response strategy"""
    try:
        # Verify webhook authenticity
        if not verify_webhook(request):
            logger.warning("Invalid webhook signature")
            return jsonify({"status": "invalid_signature"}), 200  # Still return 200
        
        # Process webhook
        payload = request.get_json()
        webhook_queue.put(payload)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        # Always return 200 to prevent webhook disabling
        return jsonify({"status": "error", "message": "Internal error"}), 200
```
**Exception**: Security violations may return different status codes  
**Business Impact**: Ensures webhook endpoint remains active even during errors

### **X - eXtended Error Context in Logs**

**Condition**: When errors occur during complex operations  
**Action**: Include extended context in error logs for effective debugging  
**Implementation**:
```python
# From controller.py
def run_automation(self, automation_name, automation_func, *args, **kwargs):
    """Run automation with comprehensive error context"""
    start_time = datetime.now(self.arizona_tz)
    context = {
        'automation': automation_name,
        'start_time': start_time.isoformat(),
        'environment': self.config.environment,
        'host': os.environ.get('HOSTNAME', 'unknown'),
        'args': args,
        'kwargs': {k: v for k, v in kwargs.items() if 'secret' not in k.lower()}
    }
    
    try:
        result = automation_func(*args, **kwargs)
        return result
    except Exception as e:
        context['error'] = str(e)
        context['error_type'] = type(e).__name__
        context['duration'] = (datetime.now(self.arizona_tz) - start_time).total_seconds()
        
        self.logger.error(
            f"Automation failed: {automation_name}",
            extra={'context': context},
            exc_info=True
        )
        raise
```
**Exception**: Production logs may exclude some sensitive context  
**Business Impact**: Enables rapid troubleshooting with full operational context

### **Y - Yielding Control During Long Operations**

**Condition**: When operations could block for extended periods  
**Action**: Implement async patterns or progress reporting to maintain responsiveness  
**Implementation**:
```python
# From icsProcess.py
async def process_feeds_async(feed_records):
    """Process feeds asynchronously to prevent blocking"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        for feed in feed_records:
            url = feed['fields'].get('URL', '').strip()
            if url:
                # Create task but don't await yet
                task = fetch_ics(session, url)
                tasks.append(task)
        
        # Process all feeds concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logging.error(f"Feed {i} failed: {str(result)}")
            else:
                # Process successful result
                pass
```
**Exception**: Critical operations may need synchronous processing  
**Business Impact**: Maintains system responsiveness during bulk operations

### **Z - Zero Data Loss Error Handling**

**Condition**: When errors occur during data processing  
**Action**: Ensure no data is lost by preserving failed records for manual review  
**Implementation**:
```python
# From csvProcess.py
def process_csv_files():
    """Process CSV files with zero data loss guarantee"""
    for fname in os.listdir(PROCESS_DIR):
        if not fname.endswith('.csv'):
            continue
            
        path = os.path.join(PROCESS_DIR, fname)
        done_path = os.path.join(DONE_DIR, fname)
        error_path = os.path.join(ERROR_DIR, fname)
        
        try:
            # Process file
            with open(path, newline="", encoding="utf-8-sig") as f:
                process_csv_data(f)
            
            # Move to done directory on success
            shutil.move(path, done_path)
            logging.info(f"✅ Moved {fname} to done directory")
            
        except Exception as e:
            logging.error(f"❌ Error processing {fname}: {e}", exc_info=True)
            # Move to error directory for manual review
            try:
                os.makedirs(ERROR_DIR, exist_ok=True)
                shutil.move(path, error_path)
                logging.info(f"📁 Moved {fname} to error directory for review")
            except:
                # If move fails, leave in process directory
                logging.error(f"⚠️  Could not move {fname}, leaving in process directory")
```
**Exception**: Temporary files may be cleaned up after processing  
**Business Impact**: Guarantees no data loss even during processing failures

---

## 🔧 **ERROR HANDLING PATTERNS SUMMARY**

### **Defensive Programming**
1. **Input Validation**: Validate all inputs before processing
2. **Null Checks**: Use fallback values for missing data
3. **Type Safety**: Verify data types before operations
4. **Boundary Checks**: Validate ranges and limits
5. **State Verification**: Ensure valid state before operations

### **Error Recovery Strategies**
1. **Retry with Backoff**: Exponential backoff for transient failures
2. **Circuit Breakers**: Prevent cascading failures
3. **Graceful Degradation**: Partial functionality during failures
4. **Rollback Capability**: Restore previous state on failure
5. **Manual Intervention**: Clear marking for human review

### **Operational Excellence**
1. **Comprehensive Logging**: Full context for troubleshooting
2. **Status Tracking**: Real-time operational visibility
3. **Error Metrics**: Track patterns and trends
4. **Alert Integration**: Notify on critical failures
5. **Documentation**: Clear error resolution procedures

---

*This business logic documentation provides comprehensive coverage of all error handling mechanisms, ensuring system resilience, data integrity, and operational visibility throughout the property management automation system.*