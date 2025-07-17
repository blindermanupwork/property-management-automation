# Monitoring & Health Checks - Feature Overview

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Comprehensive system monitoring and health verification for the property management automation platform

---

## 📊 **FEATURE SUMMARY**

The monitoring and health checks feature provides comprehensive system observability, status tracking, and proactive issue detection across all automation components. This includes HTTP health endpoints, script-based monitoring, Airtable status integration, and automated testing frameworks to ensure system reliability.

---

## 🎯 **CORE CAPABILITIES**

### **1. HTTP Health Check Endpoints**
- **API Server Health**: Basic availability check at `/health` endpoint
- **Webhook Server Health**: Advanced health check with Airtable connectivity test and feature status
- **Response Format**: JSON with status, timestamp, version, and feature flags
- **Error Reporting**: Detailed error information when health checks fail

### **2. System Monitoring Scripts**
- **Production Monitor** (`monitor.sh`): Comprehensive system health validation
- **Automation Status Checker** (`check_automation_status.sh`): Cron schedule and status analysis
- **Process Monitoring**: Detection of recent automation runs and stuck processes
- **Error Detection**: Log analysis with smart filtering to exclude success messages
- **Disk Space Monitoring**: Alerts when usage exceeds 85%

### **3. Airtable Status Integration**
- **Real-time Status Tracking**: Controller updates automation status in Airtable
- **Active/Inactive Detection**: Check automation enable/disable states
- **Message History**: Timestamped status messages with success/failure indicators
- **Centralized Dashboard**: Single source of truth for automation states

### **4. Testing Framework Integration**
- **Comprehensive E2E Tests**: Full system workflow validation
- **Business Logic Testing**: Critical automation scenario verification
- **Performance Tracking**: Execution time monitoring
- **Error Collection**: Detailed failure analysis and categorization

---

## 🔄 **OPERATIONAL WORKFLOWS**

### **Health Check Flow**
1. **HTTP Request** → Health endpoint (`/health`)
2. **Basic Checks** → Server availability, timestamp generation
3. **Advanced Checks** → Airtable connectivity, feature status validation
4. **Response Generation** → JSON with status details and error information

### **System Monitoring Flow**
1. **Scheduled Execution** → Monitor script runs via cron
2. **Multi-dimensional Checks** → Processes, errors, disk space, CSV health
3. **Alert Generation** → Email/notification when issues detected
4. **Status Reporting** → Console output with visual indicators

### **Status Tracking Flow**
1. **Automation Start** → Controller checks Airtable for active status
2. **Progress Updates** → Real-time status messages during execution
3. **Completion Logging** → Final success/failure status with timestamp
4. **Historical Tracking** → Maintain status history for trend analysis

---

## 🛠️ **TECHNICAL ARCHITECTURE**

### **Health Endpoints**
- **API Server**: Express.js endpoint returning basic health status
- **Webhook Server**: Flask endpoint with database connectivity verification
- **Response Standards**: Consistent JSON format across all endpoints
- **Error Handling**: Graceful degradation with detailed error messages

### **Monitoring Infrastructure**
- **Bash Scripts**: Production-grade monitoring with alert capabilities
- **Log Analysis**: Smart pattern matching to detect actual errors
- **Cron Integration**: Automated scheduling with next-run prediction
- **Process Detection**: Recent activity validation and stuck process identification

### **Status Management**
- **Airtable Integration**: Direct API calls for status updates
- **Timezone Handling**: Arizona timezone standardization for business data
- **Message Formatting**: Emoji indicators and timestamp standardization
- **Record Management**: Automatic creation/update of automation records

---

## 📋 **MONITORING COVERAGE**

### **Currently Monitored**
✅ **HTTP Endpoint Availability** (API server, webhook server)  
✅ **Automation Execution Status** (via Airtable integration)  
✅ **System Process Health** (recent runs, stuck processes)  
✅ **Error Detection** (log analysis with smart filtering)  
✅ **Disk Space Usage** (85% threshold alerting)  
✅ **CSV Processing Health** (stuck files detection)  
✅ **Cron Schedule Analysis** (next run prediction)  
✅ **End-to-End Testing** (comprehensive workflow validation)  
✅ **Business Logic Verification** (critical scenario testing)  

### **Enhancement Opportunities**
❌ **MCP Server Health Checks** (Airtable, HCP, Trello MCP servers)  
❌ **Performance Monitoring** (response times, execution trends)  
❌ **Uptime Tracking** (persistent availability metrics)  
❌ **Error Rate Analysis** (trend tracking, pattern detection)  
❌ **Webhook Delivery Monitoring** (success rates, retry tracking)  

---

## 🚨 **ALERTING & NOTIFICATIONS**

### **Alert Triggers**
- **No Recent Automation Activity** (24 hour threshold)
- **Error Detection in Logs** (actual errors, excluding success messages)
- **High Disk Usage** (85% threshold)
- **Health Check Failures** (Airtable connectivity issues)
- **Test Suite Failures** (E2E test failures)

### **Alert Mechanisms**
- **Email Notifications** (configured in monitor.sh)
- **Console Output** (visual indicators with emojis)
- **Log File Entries** (structured alert messages)
- **Airtable Status Updates** (failure status recording)

---

## 📈 **BUSINESS VALUE**

### **Operational Benefits**
- **Proactive Issue Detection**: Identify problems before they impact operations
- **System Reliability**: Continuous monitoring maintains high availability
- **Performance Visibility**: Track system health trends over time
- **Automated Recovery**: Status tracking enables quick issue resolution

### **Business Impact**
- **Reduced Downtime**: Early detection prevents service interruptions
- **Data Integrity**: Monitoring validates correct data processing
- **Customer Service**: Reliable automation supports consistent operations
- **Operational Efficiency**: Automated monitoring reduces manual oversight

---

## 🔧 **CONFIGURATION & SETUP**

### **Health Check Access**
```bash
# API Server Health Check
curl http://localhost:3000/health

# Webhook Server Health Check (Development)
curl https://servativ.themomentcatchers.com/webhooks/hcp-dev/health

# Webhook Server Health Check (Production)
curl https://servativ.themomentcatchers.com/webhooks/hcp/health
```

### **Monitor Script Configuration**
```bash
# Run production monitor manually
/home/opc/automation/src/automation/bin/monitor.sh

# Check automation status
/home/opc/automation/src/automation/bin/check_automation_status.sh

# View monitoring logs
tail -f /home/opc/automation/monitoring.log
```

### **Testing Framework Execution**
```bash
# Run comprehensive health tests
cd /home/opc/automation/testing/test-runners
python3 comprehensive-e2e-test.py

# Run business logic tests
python3 critical-business-logic-tests.py
```

---

## 📚 **RELATED DOCUMENTATION**

- **Error Handling & Recovery** → `../15-error-handling-recovery/`
- **Notification System** → `../16-notification-system/`
- **Reporting & Analytics** → `../17-reporting-analytics/`
- **System Architecture** → `../00-system-overview/`

---

*This monitoring and health checks system provides comprehensive visibility into the property management automation platform, enabling proactive issue detection and reliable system operations.*