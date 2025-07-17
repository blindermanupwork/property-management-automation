# Notification System - System Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Text-based operational flow documentation for notification system

---

## 🔄 **OPERATIONAL NOTIFICATION FLOWS**

### **1. Automation Status Update Flow**

**Trigger**: Any automation component starts, completes, or fails

**Process Flow**:
1. **Automation Initiation**
   - Controller checks automation status in Airtable
   - Prints console notification with emoji indicator
   - Records start timestamp in Arizona timezone

2. **Status Update Execution**
   - Attempts to find automation record by name
   - Prepares update fields with timestamp and status icon
   - Updates Airtable record with PATCH request
   - Logs update success/failure to console

3. **Failure Handling**
   - If Airtable update fails, logs error
   - Continues automation execution without blocking
   - Preserves error details for troubleshooting

**Output**: Updated Airtable record with latest status and console feedback

---

### **2. Multi-Channel Notification Delivery Flow**

**Trigger**: Critical events requiring guaranteed notification delivery

**Process Flow**:
1. **Event Classification**
   - Determine event severity level
   - Map severity to notification channels
   - Prepare message with appropriate formatting

2. **Channel Selection**
   - Critical: console + log + Airtable + email
   - Error: console + log + Airtable
   - Warning: console + log
   - Info/Debug: log only

3. **Parallel Delivery**
   - Send to all selected channels simultaneously
   - Track delivery success per channel
   - Aggregate delivery results

4. **Delivery Verification**
   - Check each channel for successful delivery
   - Log any channel failures
   - Ensure at least one channel succeeds

**Output**: Notifications delivered across multiple channels with delivery tracking

---

### **3. Console Output Notification Flow**

**Trigger**: Any operation requiring real-time user feedback

**Process Flow**:
1. **Message Preparation**
   - Select appropriate emoji indicator
   - Format message with operation context
   - Include relevant data (counts, names, IDs)

2. **UTF-8 Configuration**
   - Wrap stdout with UTF-8 encoding
   - Set error handling to 'replace'
   - Enable line buffering for immediate display

3. **Visual Formatting**
   - Apply emoji prefix for quick recognition
   - Structure multi-line output with indentation
   - Add color coding if terminal supports it

4. **Progress Tracking**
   - Display initial operation message
   - Update with progress indicators
   - Show final completion status

**Output**: Rich console output with visual indicators and real-time progress

---

### **4. Log File Management Flow**

**Trigger**: Any logging event from system components

**Process Flow**:
1. **Environment Detection**
   - Check ENVIRONMENT variable
   - Select appropriate log filename
   - Create environment-specific log path

2. **Log Rotation Check**
   - Check current log file size
   - If exceeds 10MB, rotate with timestamp
   - Maintain up to 5 backup files

3. **Message Formatting**
   - Apply MST timezone formatting
   - Add severity level prefix
   - Include source component identifier

4. **Write Operation**
   - Open file in append mode
   - Write formatted message
   - Flush buffer for immediate persistence

**Output**: Organized log files with rotation and environment separation

---

### **5. Webhook Notification Processing Flow**

**Trigger**: Incoming webhook from HousecallPro or forwarded source

**Process Flow**:
1. **Authentication Verification**
   - Check for HCP signature or forwarding auth header
   - Validate timestamp within tolerance window
   - Verify payload integrity

2. **Payload Processing**
   - Parse JSON webhook data
   - Extract job ID and status information
   - Map HCP status to internal status

3. **Notification Generation**
   - Create status change message
   - Format with Arizona timezone
   - Include transition details (old → new)

4. **Multi-Channel Update**
   - Log to webhook-specific log file
   - Print to console for visibility
   - Update Airtable reservation record
   - Track processing duration

**Output**: Processed webhook with notifications across all channels

---

### **6. Batch Notification Aggregation Flow**

**Trigger**: Multiple similar events within short timeframe

**Process Flow**:
1. **Event Collection**
   - Buffer similar events for aggregation
   - Track event counts by type
   - Monitor time window (default 5 seconds)

2. **Aggregation Decision**
   - Check if events exceed threshold
   - Verify events are similar type
   - Ensure no critical events in batch

3. **Summary Generation**
   - Create consolidated message
   - Include total counts per category
   - Highlight any errors or warnings

4. **Delivery Optimization**
   - Send single aggregated notification
   - Preserve individual error details in logs
   - Update UI with summary statistics

**Output**: Reduced notification volume while maintaining visibility

---

### **7. Field Update Notification Flow**

**Trigger**: Airtable field updates required

**Process Flow**:
1. **Field Mapping**
   - Identify operation type (schedule/service/status)
   - Map to appropriate Airtable field
   - Prepare update payload

2. **Message Construction**
   - Use syncMessageBuilder for consistency
   - Apply standardized format templates
   - Append Arizona timezone timestamp

3. **Update Execution**
   - Send PATCH request to Airtable API
   - Handle rate limiting with retry
   - Verify update success

4. **Confirmation Feedback**
   - Log successful update
   - Display console confirmation
   - Record in audit trail

**Output**: Updated Airtable fields with standardized messages

---

### **8. Progress Indicator Notification Flow**

**Trigger**: Long-running operations that may appear frozen

**Process Flow**:
1. **Operation Monitoring**
   - Track operation start time
   - Monitor progress milestones
   - Calculate completion percentage

2. **Update Frequency**
   - Display update every 10 items processed
   - Show update every 30 seconds minimum
   - Include estimated time remaining

3. **Visual Progress**
   - Show progress bar for known totals
   - Display item counter for unknown totals
   - Include percentage when calculable

4. **Keep-Alive Signal**
   - Prevent timeout assumptions
   - Maintain user confidence
   - Show system is actively working

**Output**: Regular progress updates preventing perceived system freeze

---

### **9. Error Notification Escalation Flow**

**Trigger**: Critical errors requiring immediate attention

**Process Flow**:
1. **Error Classification**
   - Determine error severity
   - Check if error is recoverable
   - Identify affected components

2. **Escalation Path**
   - Log full error details with stack trace
   - Send console alert with red indicators
   - Update Airtable status as failed
   - Queue email notification (if configured)

3. **Context Preservation**
   - Capture system state at error time
   - Include recent operation history
   - Save diagnostic information

4. **Recovery Guidance**
   - Suggest corrective actions
   - Link to relevant documentation
   - Provide contact information

**Output**: Comprehensive error notification with recovery guidance

---

### **10. Summary Report Notification Flow**

**Trigger**: Completion of automation suite or major operation

**Process Flow**:
1. **Statistics Collection**
   - Gather success/failure counts
   - Calculate total duration
   - Compile per-component metrics

2. **Report Generation**
   - Create formatted summary header
   - List each component with status
   - Include timing information
   - Add visual separators

3. **Multi-Line Formatting**
   - Structure with clear sections
   - Use indentation for readability
   - Apply emoji indicators throughout

4. **Distribution**
   - Display in console
   - Write to summary log
   - Update Airtable dashboard
   - Store for historical analysis

**Output**: Comprehensive summary report with operational metrics

---

## 🔧 **NOTIFICATION CONFIGURATION PATTERNS**

### **Channel Priority Matrix**
- **Critical**: All channels (console, log, Airtable, email)
- **Error**: Console + Log + Airtable
- **Warning**: Console + Log
- **Info**: Log only
- **Debug**: Log only (verbose mode)

### **Timing Strategies**
- **Immediate**: Status changes, errors, user actions
- **Buffered**: Similar events, bulk operations
- **Scheduled**: Summary reports, digest notifications
- **Throttled**: High-frequency updates, progress indicators

### **Format Standards**
- **Timestamps**: Arizona timezone, human-readable
- **Icons**: Consistent emoji usage for status
- **Structure**: Operation → Details → Result → Time
- **Length**: Console (1 line), Logs (detailed), Airtable (200 char)

---

*This operational flow documentation provides comprehensive coverage of how notifications flow through the property management automation system, ensuring reliable communication and operational visibility.*