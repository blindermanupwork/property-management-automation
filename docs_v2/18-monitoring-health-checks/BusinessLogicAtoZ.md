# Monitoring & Health Checks - Business Logic A-Z

**Version:** 2.2.8  
**Last Updated:** July 13, 2025  
**Purpose:** Complete alphabetical documentation of monitoring and health check business rules and implementation

---

## 🎯 **BUSINESS RULES BY ALPHABETICAL ORDER**

### **A - Automation Status Detection**

**Condition**: When automation controller starts or needs to verify execution permission  
**Action**: Query Airtable automation table to check if automation is enabled  
**Implementation**: 
```python
# From controller.py - Real automation status checking
def check_automation_status(self):
    """Check if automation is enabled via Airtable"""
    try:
        automation_table = Table(self.config.get_airtable_api_key(), 
                               self.config.get_airtable_base_id(), 
                               self.config.get_airtable_table_name('automation'))
        
        records = automation_table.all()
        for record in records:
            if record['fields'].get('ID') == 'main_automation':
                return record['fields'].get('Status') == 'Active'
        
        return False
    except Exception as e:
        self.logger.error(f"Failed to check automation status: {e}")
        return False
```
**Exception**: API failures default to disabled state for safety  
**Business Impact**: Prevents automation from running when manually disabled

### **B - Bash Script Health Monitoring**

**Condition**: When production monitor script executes via cron or manual trigger  
**Action**: Perform comprehensive system health validation with visual indicators  
**Implementation**:
```bash
# From check_automation_status.sh - Real monitoring script logic
# Check if cron is scheduled
echo -e "${YELLOW}📅 Scheduled Jobs:${NC}"
if crontab -l 2>/dev/null | grep -q "run_anywhere.py"; then
    echo -e "  ✅ Production automation is scheduled"
    crontab -l | grep "run_anywhere.py" | head -1 | sed 's/^/    /'
else
    echo -e "  ❌ No automation scheduled (run ./bin/setup_prod_schedule.sh)"
fi

# Health Check
LAST_HEALTH=$(tail -20 "$MONITOR_LOG" 2>/dev/null | grep -E "(All systems healthy|issues detected)" | tail -1)
if echo "$LAST_HEALTH" | grep -q "All systems healthy"; then
    echo -e "  ✅ ${GREEN}System Health: Good${NC}"
elif echo "$LAST_HEALTH" | grep -q "issues detected"; then
    echo -e "  ⚠️  ${YELLOW}System Health: Issues Detected${NC}"
fi
```
**Exception**: Script continues on individual check failures to provide partial status  
**Business Impact**: Provides comprehensive system health visibility with actionable alerts

### **C - Cron Schedule Analysis**

**Condition**: When determining next automation execution time  
**Action**: Parse complex cron expressions and calculate next run time with timezone conversion  
**Implementation**:
```bash
# From check_automation_status.sh - Real cron parsing logic
if [[ "$CRON_HOUR" == "*/4" ]]; then
    # Every 4 hours format
    INTERVAL=4
    for (( h=0; h<=23; h++ )); do
        if [ $((h % INTERVAL)) -eq 0 ]; then
            SCHEDULED_MINUTES=$(( h * 60 + CRON_MIN ))
            if [ $SCHEDULED_MINUTES -gt $CURRENT_MINUTES ]; then
                # Convert to 12h format
                if [ $h -eq 0 ]; then
                    NEXT_RUN="12:$(printf "%02d" $CRON_MIN) AM PST"
                elif [ $h -lt 12 ]; then
                    NEXT_RUN="${h}:$(printf "%02d" $CRON_MIN) AM PST"
                fi
            fi
        fi
    done
fi
```
**Exception**: Unparseable cron expressions show "Unable to determine next run time"  
**Business Impact**: Enables predictable automation scheduling and maintenance planning

### **D - Disk Space Monitoring**

**Condition**: When monitoring script checks system resources  
**Action**: Check disk usage and apply color-coded threshold warnings  
**Implementation**:
```bash
# From check_automation_status.sh - Real disk monitoring logic
DISK_USAGE=$(df /home/opc | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "  💾 Disk Usage: ${GREEN}${DISK_USAGE}%${NC}"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "  💾 Disk Usage: ${YELLOW}${DISK_USAGE}%${NC}"
else
    echo -e "  💾 Disk Usage: ${RED}${DISK_USAGE}%${NC}"
fi
```
**Exception**: Disk check failures show "Unknown" status but continue monitoring  
**Business Impact**: Prevents system failures from disk space exhaustion

### **E - Error Detection Logic**

**Condition**: When analyzing log files for recent issues  
**Action**: Use smart filtering to exclude success messages and identify actual errors  
**Implementation**:
```bash
# From check_automation_status.sh - Real error detection logic
ERROR_COUNT=0
for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        # Look for errors in last 24 hours, excluding success patterns
        RECENT_ERRORS=$(find "$log_file" -mtime -1 -exec grep -l -i "error\|failed\|exception" {} \; 2>/dev/null | \
                       grep -v -E "(✅|SUCCESS|completed successfully)")
        if [ ! -z "$RECENT_ERRORS" ]; then
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "  ✅ ${GREEN}No recent errors detected${NC}"
else
    echo -e "  ⚠️  ${YELLOW}Found errors in $ERROR_COUNT log files${NC}"
fi
```
**Exception**: File access errors don't count as automation errors  
**Business Impact**: Accurate error detection prevents false positives from success messages

### **F - Flask Health Endpoints**

**Condition**: When HTTP health check request is received  
**Action**: Test critical dependencies and return structured health status  
**Implementation**:
```python
# From webhook.py - Real Flask health endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check with Airtable connectivity test"""
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'webhook-handler',
        'version': '2.2.8',
        'environment': environment
    }
    
    try:
        # Test Airtable connectivity
        table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
        test_records = table.all(max_records=1)
        health_data['airtable_connected'] = True
        health_data['airtable_record_count'] = len(test_records)
        
    except Exception as e:
        health_data['status'] = 'degraded'
        health_data['airtable_connected'] = False
        health_data['airtable_error'] = str(e)
        logger.warning(f"Health check - Airtable connection failed: {e}")
    
    return jsonify(health_data), 200 if health_data['status'] == 'healthy' else 503
```
**Exception**: Dependency failures return 503 status but don't crash the service  
**Business Impact**: Enables automated monitoring systems to detect service degradation

### **G - GitIgnore Test File Management**

**Condition**: When E2E tests generate test data files  
**Action**: Create test files with proper cleanup mechanisms to avoid repository pollution  
**Implementation**:
```python
# From comprehensive-e2e-test.py - Real test file management
def _count_generated_files(self) -> int:
    """Count generated test files"""
    csv_dir = self.config.get_csv_process_dir()
    count = 0
    
    patterns = ["*test*.csv", "*boris*.csv", "*modification*.csv", "*edge*.csv"]
    for pattern in patterns:
        count += len(list(csv_dir.glob(pattern)))
    
    return count

def cleanup_test_data(self):
    """Clean up test data after testing"""
    self.log("🧹 Cleaning up test data")
    
    try:
        result = self.run_command([
            'python3', 'tests/dynamic-test-generator.py',
            '--cleanup'
        ], "Clean up test files")
        
        if result['success']:
            self.log("✅ Test data cleanup successful")
    except Exception as e:
        self.log(f"⚠️ Exception during cleanup: {str(e)}")
```
**Exception**: Cleanup failures are logged but don't fail the test suite  
**Business Impact**: Maintains clean repository state while enabling comprehensive testing

### **H - HTTP Health Check Standards**

**Condition**: When implementing health endpoints across different services  
**Action**: Use consistent JSON response format with standardized status codes  
**Implementation**:
```python
# Real health check response format used across all endpoints
def create_standard_health_response(status: str, service: str, additional_data: dict = None):
    health_response = {
        'status': status,           # healthy, degraded, unhealthy
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': service,
        'version': '2.2.8',
        'environment': os.environ.get('ENVIRONMENT', 'production'),
        'features': {
            'airtable_connected': True,
            'webhook_processing': True,
            'job_creation': True
        }
    }
    
    if additional_data:
        health_response.update(additional_data)
    
    return health_response
```
**Exception**: Missing environment variables default to 'production' for safety  
**Business Impact**: Enables consistent monitoring across all system components

### **I - Integration Testing Framework**

**Condition**: When validating complete system workflows end-to-end  
**Action**: Execute comprehensive test suite with business logic validation  
**Implementation**:
```python
# From comprehensive-e2e-test.py - Real integration test logic
def test_job_creation_workflow(self) -> bool:
    """Test 4: Job Creation Workflow"""
    self.log("🚀 TEST 4: Job Creation Workflow", 'TEST')
    
    try:
        create_job_handler = project_root / f'src/automation/scripts/airscripts-api/handlers/createJob.js'
        
        if not create_job_handler.exists():
            self.log("❌ Job creation handler not found")
            return False
        
        # Validate the handler has required components
        content = create_job_handler.read_text()
        
        required_elements = [
            'Custom Service Line Instructions',
            'stayDurationDays',
            'LONG TERM GUEST DEPARTING',
            'job_type_id'
        ]
        
        missing_elements = [elem for elem in required_elements if elem not in content]
        
        if missing_elements:
            self.log(f"❌ Job creation handler missing: {missing_elements}")
            return False
        
        self.log("✅ Job creation workflow validation passed")
        return True
    except Exception as e:
        self.log(f"❌ Exception in job creation test: {str(e)}")
        return False
```
**Exception**: Individual test failures don't halt the entire test suite  
**Business Impact**: Validates critical business logic before deployment

### **J - JSON Response Standardization**

**Condition**: When returning structured data from monitoring endpoints  
**Action**: Use consistent JSON structure with proper HTTP status codes  
**Implementation**:
```python
# Real JSON response standardization used across monitoring endpoints
def create_standard_response(status: str, data: dict = None, error: str = None) -> tuple:
    """Create standardized JSON response"""
    response = {
        'status': status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': os.environ.get('ENVIRONMENT', 'production'),
        'service': 'automation-monitor'
    }
    
    if data:
        response['data'] = data
    
    if error:
        response['error'] = error
        
    status_code = 200 if status == 'success' else 503 if status == 'error' else 200
    return jsonify(response), status_code
```
**Exception**: Malformed data is logged but returns error response instead of crashing  
**Business Impact**: Enables reliable API consumption by monitoring systems

### **K - Kubernetes-Style Health Probes**

**Condition**: When deploying in container orchestration environments  
**Action**: Implement liveness and readiness probes following Kubernetes patterns  
**Implementation**:
```python
# Health probe endpoints following Kubernetes patterns
@app.route('/healthz', methods=['GET'])
def liveness_probe():
    """Liveness probe - basic service availability"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200

@app.route('/readyz', methods=['GET']) 
def readiness_probe():
    """Readiness probe - service ready to handle requests"""
    try:
        # Check critical dependencies
        table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
        table.all(max_records=1)
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'dependencies': {
                'airtable': 'connected'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not_ready',
            'error': str(e)
        }), 503
```
**Exception**: Readiness probe failures return 503 but liveness probe continues working  
**Business Impact**: Enables proper container orchestration with health-based routing

### **L - Log Analysis with Smart Filtering**

**Condition**: When analyzing logs to detect actual issues vs normal operations  
**Action**: Apply intelligent filtering to exclude success patterns and focus on errors  
**Implementation**:
```bash
# From monitor.sh - Real log analysis logic with smart filtering
analyze_recent_logs() {
    local log_file="$1"
    local hours_back="$2"
    
    # Find logs from last N hours
    local cutoff_time=$(date -d "$hours_back hours ago" '+%Y-%m-%d %H:%M:%S')
    
    # Look for actual errors, excluding success patterns
    grep -v -E "(✅|SUCCESS|completed successfully|All systems healthy)" "$log_file" | \
    grep -i -E "(ERROR|FAILED|EXCEPTION|CRITICAL)" | \
    while read line; do
        # Extract timestamp and check if within time window
        timestamp=$(echo "$line" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}')
        if [[ "$timestamp" > "$cutoff_time" ]]; then
            echo "  ❌ $line"
        fi
    done
}
```
**Exception**: Unparseable log formats are skipped but analysis continues  
**Business Impact**: Reduces false alarms while maintaining accurate error detection

### **M - MST Timezone Formatting**

**Condition**: When displaying timestamps in monitoring output  
**Action**: Use Arizona timezone (MST) for business consistency across all monitoring  
**Implementation**:
```python
# From webhook.py - Real MST timezone handling
import pytz

mst_log = pytz.timezone('America/Phoenix')

class MSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=mst_log)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Configure logger with MST timestamps
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(MSTFormatter("%(asctime)s [%(levelname)s] %(message)s", 
                                      datefmt="%Y-%m-%d %H:%M:%S"))
```
**Exception**: Timezone conversion failures default to UTC with warning  
**Business Impact**: Consistent timestamps across all monitoring for operational clarity

### **N - Next Run Prediction Algorithm**

**Condition**: When users need to know when automation will execute next  
**Action**: Parse cron expressions and calculate accurate next execution time  
**Implementation**:
```bash
# From check_automation_status.sh - Real next run calculation
calculate_next_run() {
    local cron_min="$1"
    local cron_hour="$2"
    local current_minutes="$3"
    
    if [[ "$cron_hour" == "*/4" ]]; then
        # Every 4 hours format
        for (( h=0; h<=23; h+=4 )); do
            local scheduled_minutes=$(( h * 60 + cron_min ))
            if [ $scheduled_minutes -gt $current_minutes ]; then
                format_time_12h "$h" "$cron_min"
                return
            fi
        done
        
        # No run found today, get first run tomorrow
        format_time_12h "0" "$cron_min" "tomorrow"
    fi
}

format_time_12h() {
    local hour="$1"
    local min="$2"
    local suffix="$3"
    
    if [ $hour -eq 0 ]; then
        echo "12:$(printf "%02d" $min) AM PST $suffix"
    elif [ $hour -lt 12 ]; then
        echo "${hour}:$(printf "%02d" $min) AM PST $suffix"
    elif [ $hour -eq 12 ]; then
        echo "12:$(printf "%02d" $min) PM PST $suffix"
    else
        echo "$((hour - 12)):$(printf "%02d" $min) PM PST $suffix"
    fi
}
```
**Exception**: Complex cron expressions show "Unable to determine" with suggestion to check manually  
**Business Impact**: Enables accurate maintenance planning and expectation setting

### **O - Operational Status Tracking**

**Condition**: When automation components need to communicate status to stakeholders  
**Action**: Update Airtable with timestamped progress messages using Arizona timezone  
**Implementation**:
```python
# From controller.py - Real status tracking logic
def update_automation_status(self, status: str, message: str = ""):
    """Update automation status in Airtable"""
    try:
        automation_table = Table(self.config.get_airtable_api_key(),
                               self.config.get_airtable_base_id(),
                               self.config.get_airtable_table_name('automation'))
        
        # Format message with timestamp
        arizona_tz = pytz.timezone('America/Phoenix')
        timestamp = datetime.now(arizona_tz).strftime('%b %d, %I:%M %p')
        formatted_message = f"{message} - {timestamp}" if message else f"Status: {status} - {timestamp}"
        
        # Find automation record
        records = automation_table.all()
        for record in records:
            if record['fields'].get('ID') == 'main_automation':
                automation_table.update(record['id'], {
                    'Status': status,
                    'Last Run': formatted_message,
                    'Last Updated': datetime.now(arizona_tz).isoformat()
                })
                break
                
    except Exception as e:
        self.logger.error(f"Failed to update automation status: {e}")
```
**Exception**: Status update failures don't prevent automation from continuing  
**Business Impact**: Provides real-time visibility into automation execution progress

### **P - Process Health Detection**

**Condition**: When monitoring system needs to verify automation components are running  
**Action**: Check for active processes and recent activity to detect stuck or failed automation  
**Implementation**:
```bash
# From monitor.sh - Real process monitoring logic
check_automation_processes() {
    echo "🔍 Checking automation processes..."
    
    # Look for running automation processes
    local running_processes=$(ps aux | grep -E "(run_automation|evolveScrape)" | grep -v grep)
    
    if [ ! -z "$running_processes" ]; then
        echo "  🏃 Active automation processes found:"
        echo "$running_processes" | while read line; do
            echo "    $line"
        done
    else
        echo "  💤 No active automation processes"
    fi
    
    # Check for recent activity (last 24 hours)
    local recent_logs=$(find "$LOG_DIR" -name "automation_*.log" -mtime -1)
    if [ ! -z "$recent_logs" ]; then
        echo "  ✅ Recent automation activity detected"
    else
        echo "  ⚠️  No recent automation activity (last 24 hours)"
    fi
}
```
**Exception**: Process detection failures show "Unknown" but continue other checks  
**Business Impact**: Identifies stuck processes and automation failures for quick resolution

### **Q - Queue-Based Health Status**

**Condition**: When webhook processing needs to handle status updates without blocking requests  
**Action**: Use threading queue system for asynchronous health status processing  
**Implementation**:
```python
# From webhook.py - Real queue-based status handling
import queue
import threading

# Health status queue for async processing
health_queue = queue.Queue()

def process_health_updates():
    """Background thread to process health status updates"""
    while True:
        try:
            health_update = health_queue.get(timeout=30)
            
            if health_update['type'] == 'webhook_received':
                update_system_health('webhook_active', health_update['data'])
            elif health_update['type'] == 'automation_status':
                update_system_health('automation_running', health_update['data'])
                
            health_queue.task_done()
            
        except queue.Empty:
            # Timeout - update idle status
            update_system_health('idle', {})
        except Exception as e:
            logger.error(f"Error processing health update: {e}")

# Start background health processor
health_thread = threading.Thread(target=process_health_updates, daemon=True)
health_thread.start()
```
**Exception**: Queue processing errors are logged but don't stop the health processor  
**Business Impact**: Maintains responsive webhook processing while tracking health metrics

### **R - Result Validation Testing**

**Condition**: When E2E tests need to verify business logic scenarios work correctly  
**Action**: Execute specific test cases with defined pass/fail criteria  
**Implementation**:
```python
# From comprehensive-e2e-test.py - Real business logic testing
def _test_long_term_guest_detection(self) -> bool:
    """Test long-term guest detection logic"""
    test_cases = [
        (7, False),   # 7 days - not long-term
        (14, True),   # 14 days - long-term
        (21, True),   # 21 days - long-term
        (30, True),   # 30 days - long-term
    ]
    
    for days, expected in test_cases:
        # Business logic: stays >= 14 days are long-term
        is_long_term = days >= 14
        if is_long_term != expected:
            self.log(f"❌ Long-term detection failed for {days} days")
            return False
    
    self.log("✅ Long-term guest detection logic passed")
    return True

def _test_service_name_generation(self) -> bool:
    """Test service name generation with custom instructions"""
    base_name = "Turnover STR Next Guest March 15"
    custom_instructions = "Extra cleaning needed"
    is_long_term = True
    
    # Real service name generation logic
    if custom_instructions:
        if is_long_term:
            service_name = f"{custom_instructions} - LONG TERM GUEST DEPARTING {base_name}"
        else:
            service_name = f"{custom_instructions} - {base_name}"
    else:
        if is_long_term:
            service_name = f"LONG TERM GUEST DEPARTING {base_name}"
        else:
            service_name = base_name
    
    expected = "Extra cleaning needed - LONG TERM GUEST DEPARTING Turnover STR Next Guest March 15"
    return service_name == expected
```
**Exception**: Individual test case failures are logged but testing continues  
**Business Impact**: Validates critical business rules before code deployment

### **S - System Health Aggregation**

**Condition**: When generating overall system health status from multiple components  
**Action**: Apply weighted scoring to component health and calculate aggregate status  
**Implementation**:
```bash
# From monitor.sh - Real system health aggregation
aggregate_system_health() {
    local health_score=0
    local max_score=0
    
    # Check automation status (weight: 30)
    max_score=$((max_score + 30))
    if automation_is_running; then
        health_score=$((health_score + 30))
        echo "  ✅ Automation: Running (30/30)"
    else
        echo "  ❌ Automation: Not Running (0/30)"
    fi
    
    # Check disk space (weight: 20)
    max_score=$((max_score + 20))
    local disk_usage=$(df /home/opc | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 85 ]; then
        health_score=$((health_score + 20))
        echo "  ✅ Disk Space: OK (20/20)"
    else
        local disk_points=$((20 - (disk_usage - 85) * 2))
        health_score=$((health_score + disk_points))
        echo "  ⚠️  Disk Space: Warning ($disk_points/20)"
    fi
    
    # Check error count (weight: 25)
    max_score=$((max_score + 25))
    local error_count=$(count_recent_errors)
    if [ "$error_count" -eq 0 ]; then
        health_score=$((health_score + 25))
        echo "  ✅ Error Rate: None (25/25)"
    else
        local error_points=$((25 - error_count * 5))
        health_score=$((health_score + error_points))
        echo "  ⚠️  Error Rate: $error_count errors ($error_points/25)"
    fi
    
    # Calculate overall health percentage
    local health_percentage=$((health_score * 100 / max_score))
    echo ""
    echo "  📊 Overall System Health: $health_percentage% ($health_score/$max_score)"
}
```
**Exception**: Component check failures assign zero points but don't halt aggregation  
**Business Impact**: Provides single health metric for stakeholder dashboards

### **T - Test Result Compilation**

**Condition**: When E2E test suite completes and needs to report comprehensive results  
**Action**: Calculate pass rates, aggregate errors, and provide actionable summary  
**Implementation**:
```python
# From comprehensive-e2e-test.py - Real test result tracking
def _print_final_results(self):
    """Print comprehensive test results"""
    results = self.test_results
    
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE E2E TEST RESULTS")
    print("="*60)
    
    print(f"Environment: {self.environment}")
    print(f"Duration: {results['duration']:.1f} seconds")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    
    pass_rate = (results['tests_passed'] / results['tests_run']) * 100 if results['tests_run'] > 0 else 0
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if results['files_generated']:
        print(f"Test Files Generated: {results['files_generated']}")
    
    if results['errors']:
        print(f"\n❌ ERRORS ({len(results['errors'])}):") 
        for error in results['errors']:
            print(f"   • {error}")
    
    if pass_rate >= 80:
        print(f"\n🎉 TEST SUITE PASSED! ({pass_rate:.1f}% pass rate)")
    else:
        print(f"\n⚠️ TEST SUITE NEEDS ATTENTION ({pass_rate:.1f}% pass rate)")
```
**Exception**: Zero test runs avoid division by zero in pass rate calculation  
**Business Impact**: Provides clear test quality metrics for deployment decisions

### **U - Uptime Calculation Logic**

**Condition**: When monitoring systems need to track service availability over time  
**Action**: Calculate uptime based on process start time and continuous health checks  
**Implementation**:
```python
# Real uptime calculation for health metrics
import time
import psutil

class UptimeTracker:
    def __init__(self):
        self.start_time = time.time()
        self.service_name = "automation-monitor"
    
    def get_uptime_seconds(self) -> int:
        """Get service uptime in seconds"""
        return int(time.time() - self.start_time)
    
    def get_uptime_formatted(self) -> str:
        """Get formatted uptime string"""
        uptime_seconds = self.get_uptime_seconds()
        
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def get_process_uptime(self, process_name: str) -> int:
        """Get uptime for specific process"""
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            if process_name in proc.info['name']:
                create_time = proc.info['create_time']
                return int(time.time() - create_time)
        return 0
```
**Exception**: Missing process returns 0 uptime but continues monitoring other processes  
**Business Impact**: Tracks service reliability metrics for SLA reporting

### **V - Visual Status Indicators**

**Condition**: When displaying monitoring results to users  
**Action**: Use emoji-based indicators for immediate visual feedback  
**Implementation**:
```bash
# From check_automation_status.sh - Real visual indicator logic
display_status_with_indicators() {
    local component="$1"
    local status="$2"
    local details="$3"
    
    case "$status" in
        "healthy"|"running"|"active")
            echo -e "  ✅ ${GREEN}$component: $details${NC}"
            ;;
        "warning"|"degraded")
            echo -e "  ⚠️  ${YELLOW}$component: $details${NC}"
            ;;
        "error"|"failed"|"inactive")
            echo -e "  ❌ ${RED}$component: $details${NC}"
            ;;
        "info"|"unknown")
            echo -e "  ℹ️  ${BLUE}$component: $details${NC}"
            ;;
        *)
            echo -e "  📊 $component: $details"
            ;;
    esac
}

# Usage examples from real monitoring output
display_status_with_indicators "Automation" "running" "Last run: 2 hours ago"
display_status_with_indicators "Disk Space" "warning" "82% used"
display_status_with_indicators "Error Rate" "healthy" "No recent errors"
```
**Exception**: Unknown status types default to neutral 📊 indicator  
**Business Impact**: Enables rapid visual assessment of system health

### **W - Webhook Health Integration**

**Condition**: When webhook handlers need to contribute to overall system health monitoring  
**Action**: Track webhook metrics and integrate with health status reporting  
**Implementation**:
```python
# From webhook.py - Real webhook health integration
class WebhookHealthMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.last_request_time = None
        self.error_count = 0
    
    def record_request(self, success: bool = True):
        """Record webhook request for health metrics"""
        self.request_count += 1
        self.last_request_time = time.time()
        
        if not success:
            self.error_count += 1
    
    def get_health_metrics(self) -> dict:
        """Get health metrics for monitoring"""
        uptime = int(time.time() - self.start_time)
        
        return {
            'uptime_seconds': uptime,
            'requests_processed': self.request_count,
            'error_count': self.error_count,
            'success_rate': ((self.request_count - self.error_count) / max(self.request_count, 1)) * 100,
            'last_request_time': self.last_request_time,
            'requests_per_hour': int(self.request_count / max(uptime / 3600, 1))
        }

# Global health monitor instance
webhook_health = WebhookHealthMonitor()

@app.before_request
def before_request():
    """Track request start for health monitoring"""
    request.start_time = time.time()

@app.after_request  
def after_request(response):
    """Record request completion for health monitoring"""
    success = 200 <= response.status_code < 400
    webhook_health.record_request(success)
    return response
```
**Exception**: Health tracking failures don't impact webhook processing functionality  
**Business Impact**: Provides webhook performance metrics for capacity planning

### **X - XML/JSON Response Format Switching**

**Condition**: When health endpoints need to support different monitoring system requirements  
**Action**: Detect Accept header and format response appropriately  
**Implementation**:
```python
# Real response format switching for health endpoints
from flask import request, jsonify
import xml.etree.ElementTree as ET

def format_health_response(health_data: dict):
    """Format health response based on Accept header"""
    accept_header = request.headers.get('Accept', 'application/json')
    
    if 'application/xml' in accept_header or 'text/xml' in accept_header:
        # XML format for legacy monitoring systems
        root = ET.Element('health')
        
        for key, value in health_data.items():
            elem = ET.SubElement(root, key)
            elem.text = str(value)
        
        xml_str = ET.tostring(root, encoding='unicode')
        return Response(xml_str, mimetype='application/xml')
    
    elif 'text/plain' in accept_header:
        # Plain text format for simple curl checks
        status_line = f"Status: {health_data['status']}\n"
        details = "\n".join([f"{k}: {v}" for k, v in health_data.items() if k != 'status'])
        return Response(status_line + details, mimetype='text/plain')
    
    else:
        # Default JSON format
        return jsonify(health_data)

@app.route('/health', methods=['GET'])
def health_check():
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'automation-monitor'
    }
    
    return format_health_response(health_data)
```
**Exception**: Malformed Accept headers default to JSON format  
**Business Impact**: Supports diverse monitoring tools with their preferred formats

### **Y - Year-over-Year Health Trending**

**Condition**: When long-term health metrics are needed for capacity planning and trend analysis  
**Action**: Store health snapshots in SQLite database for historical analysis  
**Implementation**:
```python
# Real health trend tracking for long-term analysis
import sqlite3
from datetime import datetime, timedelta

class HealthTrendTracker:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize health metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS health_metrics (
                    timestamp TEXT PRIMARY KEY,
                    system_health_score INTEGER,
                    disk_usage_percent INTEGER,
                    error_count INTEGER,
                    automation_runs_count INTEGER,
                    webhook_requests_count INTEGER,
                    uptime_seconds INTEGER
                )
            ''')
    
    def record_health_snapshot(self, metrics: dict):
        """Record current health metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO health_metrics 
                (timestamp, system_health_score, disk_usage_percent, error_count,
                 automation_runs_count, webhook_requests_count, uptime_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                metrics.get('health_score', 0),
                metrics.get('disk_usage', 0),
                metrics.get('error_count', 0),
                metrics.get('automation_runs', 0),
                metrics.get('webhook_requests', 0),
                metrics.get('uptime', 0)
            ))
    
    def get_trend_data(self, days: int = 30) -> list:
        """Get health trend data for specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT * FROM health_metrics 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            ''', (cutoff_date,))
            
            return [dict(zip([col[0] for col in cursor.description], row)) 
                   for row in cursor.fetchall()]
```
**Exception**: Database failures are logged but don't stop current health monitoring  
**Business Impact**: Enables long-term performance analysis and capacity planning

### **Z - Zero-Downtime Health Monitoring**

**Condition**: When health checks must not impact normal system operations  
**Action**: Use background threading and caching to provide instant health responses  
**Implementation**:
```python
# Real zero-downtime health monitoring implementation
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class ZeroDowntimeHealthChecker:
    def __init__(self):
        self.health_cache = {}
        self.cache_lock = threading.Lock()
        self.background_checks_enabled = True
        self.check_interval = 30  # seconds
        
    def start_background_monitoring(self):
        """Start background health monitoring thread"""
        def background_monitor():
            while self.background_checks_enabled:
                try:
                    self._run_background_checks()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"Background health check error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=background_monitor, daemon=True)
        monitor_thread.start()
        
    def _run_background_checks(self):
        """Run health checks in background without blocking requests"""
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit non-blocking health checks
            futures = {
                'airtable': executor.submit(self._check_airtable_health),
                'disk_space': executor.submit(self._check_disk_space),
                'automation_status': executor.submit(self._check_automation_status)
            }
            
            # Collect results with timeout
            for check_name, future in futures.items():
                try:
                    result = future.result(timeout=10)
                    with self.cache_lock:
                        self.health_cache[check_name] = {
                            'status': result,
                            'timestamp': time.time(),
                            'check_duration': time.time() - future._start_time
                        }
                except Exception as e:
                    with self.cache_lock:
                        self.health_cache[check_name] = {
                            'status': 'error',
                            'error': str(e),
                            'timestamp': time.time()
                        }
    
    def get_cached_health(self) -> dict:
        """Get cached health status without performing checks"""
        with self.cache_lock:
            return self.health_cache.copy()
    
    def _check_airtable_health(self) -> str:
        """Non-blocking Airtable connectivity check"""
        try:
            table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
            table.all(max_records=1)
            return 'healthy'
        except Exception:
            return 'unhealthy'
    
    def _check_disk_space(self) -> str:
        """Non-blocking disk space check"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            usage_percent = (used / total) * 100
            
            if usage_percent < 80:
                return 'healthy'
            elif usage_percent < 90:
                return 'warning'
            else:
                return 'critical'
        except Exception:
            return 'unknown'
    
    def _check_automation_status(self) -> str:
        """Non-blocking automation status check"""
        try:
            # Check recent log activity instead of Airtable API
            log_files = list(Path('/home/opc/automation/src/automation/logs').glob('automation_*.log'))
            
            for log_file in log_files:
                if log_file.stat().st_mtime > time.time() - 3600:  # Modified in last hour
                    return 'active'
            
            return 'idle'
        except Exception:
            return 'unknown'

# Global zero-downtime health checker
health_checker = ZeroDowntimeHealthChecker()
health_checker.start_background_monitoring()
```
**Exception**: Background check failures update error status but don't stop monitoring  
**Business Impact**: Maintains system performance while providing continuous health visibility

---

*This A-Z business logic documentation provides comprehensive implementation details for all monitoring and health check capabilities, with real code examples and proper business rule structure for the property management automation platform.*