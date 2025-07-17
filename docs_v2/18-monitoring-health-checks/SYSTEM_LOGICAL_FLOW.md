# System Logical Flow - Monitoring & Health Checks

**Feature:** 18-monitoring-health-checks  
**Version:** 2.2.8  
**Last Updated:** July 13, 2025

---

## **FLOW 1: HTTP Health Check Endpoint Processing**

```
1. HTTP Request Received
   ├─ Validate request method (GET only)
   ├─ Check Accept header for response format preference
   └─ Route to appropriate health check handler

2. Basic Health Assessment
   ├─ Generate current timestamp in UTC format
   ├─ Check service uptime since startup
   ├─ Validate environment configuration variables
   └─ Initialize health response object with basic metadata

3. Advanced Connectivity Testing
   ├─ Test Airtable API connectivity
   │  ├─ Attempt to connect to reservations table
   │  ├─ Execute minimal query (max_records=1)
   │  ├─ Record connection success/failure
   │  └─ Measure connection response time
   ├─ Test webhook processing capabilities
   │  ├─ Verify webhook secret configuration
   │  ├─ Check queue availability
   │  └─ Validate request processing threads
   └─ Aggregate connectivity results

4. Response Generation
   ├─ Compile health status (healthy/degraded/unhealthy)
   ├─ Include feature availability flags
   ├─ Add performance metrics if available
   ├─ Format response based on Accept header
   │  ├─ JSON format (default)
   │  ├─ XML format for legacy systems
   │  └─ Plain text format for simple curl checks
   └─ Set appropriate HTTP status code (200/503)

5. Response Delivery
   ├─ Send formatted response to client
   ├─ Log health check request details
   └─ Update internal health metrics
```

---

## **FLOW 2: System Monitoring Script Execution**

```
1. Monitor Script Initialization
   ├─ Set working directory to automation root
   ├─ Load color codes for visual output
   ├─ Initialize timezone to PST for display
   └─ Define monitoring thresholds and limits

2. Scheduled Job Verification
   ├─ Query current user's crontab
   ├─ Search for automation-related scheduled jobs
   ├─ Parse cron expressions for run frequency
   ├─ Validate automation scripts exist and are executable
   └─ Display schedule status with visual indicators

3. Automation Activity Analysis
   ├─ Check for recent automation process activity
   │  ├─ Scan process list for running automation scripts
   │  ├─ Check log file modification timestamps
   │  ├─ Analyze last 24 hours of automation runs
   │  └─ Detect stuck or zombie processes
   ├─ Parse automation logs for success/failure patterns
   │  ├─ Filter out success messages to find actual errors
   │  ├─ Count error occurrences by severity level
   │  ├─ Extract recent error messages for display
   │  └─ Calculate error rate trends
   └─ Generate automation health summary

4. System Resource Monitoring
   ├─ Check disk space usage on primary filesystem
   │  ├─ Calculate percentage used vs available
   │  ├─ Apply color coding based on thresholds
   │  │  ├─ Green: < 80% used
   │  │  ├─ Yellow: 80-89% used
   │  │  └─ Red: >= 90% used
   │  └─ Alert if approaching capacity limits
   ├─ Monitor CPU and memory usage patterns
   ├─ Check file system health for CSV processing directories
   └─ Validate log file rotation and cleanup

5. Next Run Prediction Calculation
   ├─ Parse active cron schedule expressions
   ├─ Calculate next execution time based on current time
   ├─ Handle complex cron formats
   │  ├─ Every N hours (*/4)
   │  ├─ Specific times (14,18,22,2)
   │  ├─ Daily schedules
   │  └─ Weekly patterns
   ├─ Convert 24-hour time to 12-hour format
   ├─ Account for timezone differences (PST display)
   └─ Display next scheduled run with confidence level

6. Alert Generation and Notification
   ├─ Evaluate all monitoring results against thresholds
   ├─ Generate alert messages for detected issues
   ├─ Send email notifications if configured
   ├─ Update monitoring log with detailed results
   └─ Exit with appropriate status code for upstream monitoring
```

---

## **FLOW 3: Airtable Status Integration Workflow**

```
1. Automation Controller Startup
   ├─ Initialize automation controller with environment config
   ├─ Validate Airtable API credentials
   ├─ Connect to automation status table
   └─ Check if automation is enabled before proceeding

2. Status Record Management
   ├─ Search for existing automation status record
   │  ├─ Query automation table by ID field
   │  ├─ Create new record if none exists
   │  └─ Validate record structure and required fields
   ├─ Update record with startup information
   │  ├─ Set status to "Starting"
   │  ├─ Add timestamp in Arizona timezone
   │  ├─ Include environment identifier (dev/prod)
   │  └─ Clear any previous error messages

3. Real-time Progress Tracking
   ├─ Update status during each automation phase
   │  ├─ CSV Processing: "Processing email attachments"
   │  ├─ ICS Sync: "Syncing calendar feeds"
   │  ├─ Evolve Scraping: "Updating property data"
   │  ├─ Job Creation: "Creating service jobs"
   │  └─ Cleanup: "Finalizing automation run"
   ├─ Include progress indicators and counts
   │  ├─ Files processed: X of Y
   │  ├─ Records created/updated: count
   │  ├─ Jobs scheduled: count
   │  └─ Errors encountered: count
   └─ Timestamp each status update

4. Error Handling and Recovery Status
   ├─ Capture detailed error information
   │  ├─ Error type and severity level
   │  ├─ Component where error occurred
   │  ├─ Stack trace for debugging
   │  └─ Recovery actions attempted
   ├─ Update status record with error details
   │  ├─ Set status to "Error" or "Warning"
   │  ├─ Include human-readable error message
   │  ├─ Add timestamp of error occurrence
   │  └─ Flag for manual intervention if needed
   └─ Continue processing if recoverable

5. Completion Status Recording
   ├─ Calculate automation run statistics
   │  ├─ Total execution time
   │  ├─ Files processed successfully
   │  ├─ Records created/updated
   │  ├─ Jobs created in HCP
   │  └─ Error count by category
   ├─ Update final status record
   │  ├─ Set status to "Completed" or "Completed with Warnings"
   │  ├─ Include comprehensive summary message
   │  ├─ Add completion timestamp
   │  └─ Set next expected run time
   └─ Archive old status messages if configured
```

---

## **FLOW 4: Comprehensive E2E Testing Framework**

```
1. Test Suite Initialization
   ├─ Parse command line arguments for test configuration
   ├─ Initialize test environment (development/production)
   ├─ Set up logging and result tracking structures
   ├─ Validate required test dependencies and paths
   └─ Initialize Arizona timezone for consistent timestamps

2. Test Data Generation Phase
   ├─ Generate realistic test CSV files
   │  ├─ Create various reservation scenarios
   │  ├─ Include edge cases and error conditions
   │  ├─ Generate files with different date ranges
   │  └─ Place files in appropriate CSV processing directory
   ├─ Generate test ICS feed data
   ├─ Create test property configurations
   └─ Track generated files for cleanup

3. CSV Processing Workflow Testing
   ├─ Execute automation runner in dry-run mode
   ├─ Monitor CSV file processing stages
   │  ├─ File detection and validation
   │  ├─ Data parsing and transformation
   │  ├─ Airtable record creation/updates
   │  └─ File archival to CSV_done directory
   ├─ Validate CSV processing success metrics
   ├─ Check for proper error handling
   └─ Record processing time and throughput

4. Job Creation Workflow Validation
   ├─ Test job creation handler code validation
   │  ├─ Verify custom service line instructions support
   │  ├─ Check long-term guest detection logic
   │  ├─ Validate job type configuration
   │  └─ Test service name generation
   ├─ Test HCP sync script validation
   │  ├─ Verify service line custom instructions handling
   │  ├─ Check 14-day long-term guest threshold
   │  ├─ Test stay duration calculation
   │  └─ Validate job creation API calls
   └─ Test schedule management functionality

5. Business Logic Scenario Testing
   ├─ Long-term Guest Detection Testing
   │  ├─ Test 7-day stay (should be normal)
   │  ├─ Test 14-day stay (should be long-term)
   │  ├─ Test 21-day stay (should be long-term)
   │  └─ Test 30-day stay (should be long-term)
   ├─ Custom Instructions Truncation Testing
   │  ├─ Test 250-character input
   │  ├─ Verify truncation to 200 characters
   │  ├─ Check ellipsis addition
   │  └─ Validate final length compliance
   ├─ Same-day Turnover Logic Testing
   ├─ Service Name Generation Testing
   └─ Error Handling Edge Case Testing

6. Test Result Compilation and Reporting
   ├─ Calculate pass/fail rates for each test category
   ├─ Aggregate execution times and performance metrics
   ├─ Compile error messages and failure details
   ├─ Generate comprehensive test report
   │  ├─ Test summary with visual indicators
   │  ├─ Detailed failure analysis
   │  ├─ Performance metrics
   │  └─ Recommendations for improvements
   └─ Clean up test data and temporary files
```

---

## **FLOW 5: Webhook Health Monitoring Integration**

```
1. Webhook Request Reception
   ├─ Receive incoming webhook request
   ├─ Record request timestamp and basic metrics
   ├─ Validate request format and authentication
   └─ Queue request for processing

2. Health Metrics Collection During Processing
   ├─ Track request processing time
   ├─ Monitor queue depth and throughput
   ├─ Record success/failure rates
   ├─ Update webhook-specific health counters
   └─ Log any processing errors or warnings

3. Background Health Status Updates
   ├─ Run health status update in separate thread
   ├─ Avoid blocking webhook request processing
   ├─ Update global health metrics periodically
   ├─ Check for stuck webhook processes
   └─ Monitor webhook server resource usage

4. Health Status Response Generation
   ├─ Aggregate webhook processing metrics
   │  ├─ Requests processed per hour
   │  ├─ Success rate percentage
   │  ├─ Average processing time
   │  └─ Current queue status
   ├─ Include Airtable connectivity status
   ├─ Add webhook server uptime information
   └─ Format response for monitoring systems

5. Error Recovery and Alerting
   ├─ Detect webhook processing failures
   ├─ Attempt automatic recovery procedures
   ├─ Update health status to reflect issues
   ├─ Generate alerts for persistent problems
   └─ Continue processing other requests if possible
```

---

## **FLOW 6: Cron Schedule Analysis and Prediction**

```
1. Cron Configuration Parsing
   ├─ Extract current user's crontab configuration
   ├─ Filter for automation-related scheduled jobs
   ├─ Parse cron expression fields (minute, hour, day, month, dayofweek)
   └─ Validate cron syntax and identify format patterns

2. Current Time Context Establishment
   ├─ Get current time in PST timezone
   ├─ Convert to minutes since midnight for calculations
   ├─ Extract current day and month for scheduling context
   └─ Account for daylight saving time transitions

3. Schedule Pattern Recognition
   ├─ Identify interval-based schedules (*/4 = every 4 hours)
   ├─ Recognize comma-separated hour lists (14,18,22,2)
   ├─ Handle wildcard patterns (* = every occurrence)
   ├─ Process specific time designations
   └─ Support complex cron expressions

4. Next Run Time Calculation
   ├─ For interval schedules:
   │  ├─ Find next valid hour based on interval
   │  ├─ Calculate minutes until next occurrence
   │  ├─ Handle day boundary crossings
   │  └─ Account for tomorrow's first run if needed
   ├─ For specific time schedules:
   │  ├─ Compare each scheduled time to current time
   │  ├─ Find earliest future occurrence today
   │  ├─ Fall back to first occurrence tomorrow
   │  └─ Handle multiple time slots per day
   └─ Convert calculated time to human-readable format

5. Time Format Conversion and Display
   ├─ Convert 24-hour format to 12-hour format
   ├─ Add AM/PM designation
   ├─ Include timezone information (PST)
   ├─ Add "tomorrow" designation when applicable
   └─ Handle special cases (midnight, noon)

6. Schedule Validation and Confidence Assessment
   ├─ Verify calculated time makes logical sense
   ├─ Check for impossible time combinations
   ├─ Validate against known cron behavior
   ├─ Provide confidence level in prediction
   └─ Fall back to generic message if calculation fails
```

---

## **FLOW 7: Error Detection and Smart Filtering**

```
1. Log File Identification and Access
   ├─ Scan automation logs directory
   ├─ Identify relevant log files by naming pattern
   ├─ Check file accessibility and permissions
   ├─ Sort files by modification time for recent-first processing
   └─ Handle locked or rotating log files gracefully

2. Time-based Filtering
   ├─ Calculate time threshold for "recent" errors
   ├─ Filter log entries to specified time window
   ├─ Handle timezone differences in log timestamps
   ├─ Account for log file rotation timing
   └─ Process only files modified within threshold

3. Smart Pattern Recognition
   ├─ Exclude success patterns from error detection
   │  ├─ Skip lines containing "✅" or "SUCCESS"
   │  ├─ Ignore "completed successfully" messages
   │  ├─ Filter out "All systems healthy" entries
   │  └─ Skip automation completion confirmations
   ├─ Identify actual error patterns
   │  ├─ Search for "ERROR", "FAILED", "EXCEPTION"
   │  ├─ Look for "CRITICAL" and "FATAL" messages
   │  ├─ Detect stack traces and error codes
   │  └─ Identify timeout and connection failures
   └─ Categorize errors by severity level

4. Error Context Extraction
   ├─ Extract timestamp information from error lines
   ├─ Capture surrounding context lines for debugging
   ├─ Identify which component generated the error
   ├─ Extract error codes and specific failure messages
   └─ Group related errors to avoid duplicate counting

5. Error Rate Calculation and Trending
   ├─ Count total errors by category and time period
   ├─ Calculate error rate per hour/day
   ├─ Compare current rates to historical baselines
   ├─ Identify error spikes or unusual patterns
   └─ Generate trend indicators (increasing/decreasing/stable)

6. Alert Generation and Reporting
   ├─ Determine if error count exceeds thresholds
   ├─ Generate human-readable error summaries
   ├─ Include specific file paths and line numbers
   ├─ Provide suggested investigation commands
   └─ Format alerts with appropriate urgency levels
```

---

## **FLOW 8: Performance Metrics Collection**

```
1. Metrics Initialization and Setup
   ├─ Initialize performance tracking variables
   ├─ Set up timing measurement capabilities
   ├─ Create metrics storage structures
   ├─ Define measurement intervals and windows
   └─ Establish baseline performance expectations

2. Request-level Performance Tracking
   ├─ Record request start time on entry
   ├─ Track processing duration for each component
   ├─ Monitor memory usage during processing
   ├─ Measure database query execution times
   └─ Record request completion time and status

3. System-level Resource Monitoring
   ├─ Track CPU usage patterns over time
   ├─ Monitor memory consumption trends
   ├─ Measure disk I/O performance
   ├─ Track network request latencies
   └─ Monitor file system performance

4. Business Process Performance Measurement
   ├─ Measure CSV processing throughput (files/hour)
   ├─ Track Airtable API response times
   ├─ Monitor HCP job creation success rates
   ├─ Measure webhook processing latency
   └─ Track end-to-end automation execution time

5. Performance Trend Analysis
   ├─ Calculate moving averages for key metrics
   ├─ Identify performance degradation trends
   ├─ Compare current performance to historical baselines
   ├─ Detect performance anomalies and spikes
   └─ Generate performance alerts when thresholds exceeded

6. Performance Reporting and Optimization
   ├─ Generate performance summary reports
   ├─ Identify bottlenecks and optimization opportunities
   ├─ Provide performance improvement recommendations
   ├─ Track impact of optimization changes
   └─ Update performance baselines periodically
```

---

## **FLOW 9: Uptime and Availability Tracking**

```
1. Service Startup and Registration
   ├─ Record service startup timestamp
   ├─ Register service instance with monitoring system
   ├─ Initialize availability tracking counters
   ├─ Set up periodic availability check schedule
   └─ Create service identification metadata

2. Availability Check Execution
   ├─ Execute periodic service availability checks
   ├─ Test critical service functionality
   ├─ Verify external dependency connectivity
   ├─ Record check results with timestamps
   └─ Calculate availability percentage over time

3. Downtime Detection and Recording
   ├─ Detect service unavailability events
   ├─ Record downtime start time and cause
   ├─ Monitor for service recovery
   ├─ Calculate downtime duration
   └─ Categorize downtime by root cause

4. Uptime Calculation and Reporting
   ├─ Calculate total uptime percentage
   ├─ Generate uptime reports by time period
   ├─ Track service level agreement compliance
   ├─ Compare uptime across different components
   └─ Identify patterns in availability issues

5. High Availability Monitoring
   ├─ Monitor multiple service instances
   ├─ Track failover events and recovery times
   ├─ Measure load balancing effectiveness
   ├─ Monitor redundancy and backup systems
   └─ Generate availability trend reports
```

---

## **FLOW 10: Comprehensive Health Status Aggregation**

```
1. Multi-dimensional Health Assessment
   ├─ Collect health data from all monitored components
   │  ├─ HTTP endpoint availability
   │  ├─ Database connectivity status
   │  ├─ Automation execution status
   │  ├─ System resource utilization
   │  └─ Error rates and trends
   ├─ Weight each component by business criticality
   ├─ Apply scoring algorithms to normalize metrics
   └─ Calculate overall system health score

2. Health Status Categorization
   ├─ Healthy: All systems operating within normal parameters
   ├─ Warning: Some systems showing degraded performance
   ├─ Critical: Major systems failing or severely degraded
   ├─ Unknown: Unable to determine status due to monitoring issues
   └─ Maintenance: Planned downtime or maintenance mode

3. Health History and Trend Analysis
   ├─ Maintain historical health status records
   ├─ Identify patterns in health degradation
   ├─ Predict potential issues based on trends
   ├─ Generate health improvement recommendations
   └─ Track effectiveness of remediation actions

4. Cross-system Dependency Mapping
   ├─ Identify dependencies between system components
   ├─ Track cascade effects of component failures
   ├─ Prioritize remediation efforts based on impact
   ├─ Generate dependency health reports
   └─ Monitor for single points of failure

5. Executive Health Dashboard Generation
   ├─ Create high-level health status summaries
   ├─ Generate visual health indicators
   ├─ Provide drill-down capabilities for detailed analysis
   ├─ Include business impact assessments
   └─ Format reports for different stakeholder audiences
```

---

*These system logical flows provide comprehensive operational guidance for implementing, maintaining, and troubleshooting the monitoring and health check capabilities of the property management automation platform.*