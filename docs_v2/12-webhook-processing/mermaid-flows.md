# Webhook Processing - Visual Flow Diagrams

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Visual representations of webhook processing workflows

---

## 📊 **WEBHOOK PROCESSING FLOW DIAGRAMS**

### 1. **Main Webhook Processing Flow**

```mermaid
flowchart TD
    A[Webhook Received] --> B{Authentication Valid?}
    B -->|Yes| C[Parse JSON Payload]
    B -->|No| Z[Log Security Warning<br/>Return 200 OK]
    
    C --> D{Event Type?}
    D -->|Appointment| E[Process Appointment Event]
    D -->|Job Status| F[Process Job Status Event]
    D -->|Schedule| G[Process Schedule Event]
    
    E --> H[Find Airtable Record]
    F --> H
    G --> H
    
    H --> I{Record Found?}
    I -->|Yes| J[Update Airtable Fields]
    I -->|No| K[Log Warning<br/>Return 200 OK]
    
    J --> L[Format Sync Message]
    L --> M[Log Success]
    M --> N[Return 200 OK]
    
    K --> N
    Z --> N
```

### 2. **Authentication Flow**

```mermaid
flowchart TD
    A[Webhook Request] --> B[Extract Headers]
    B --> C{HCP Signature Present?}
    
    C -->|Yes| D[Extract Signature & Timestamp]
    C -->|No| E{Servativ Auth Present?}
    
    D --> F[Reconstruct Signed Content]
    F --> G[Calculate HMAC-SHA256]
    G --> H{Signatures Match?}
    
    H -->|Yes| I[Authentication Success<br/>Method: HCP Signature]
    H -->|No| E
    
    E -->|Yes| J[Compare Auth Header]
    E -->|No| K[Authentication Failed]
    
    J --> L{Header Matches Secret?}
    L -->|Yes| M[Authentication Success<br/>Method: Forwarding Auth]
    L -->|No| K
    
    I --> N[Process Webhook]
    M --> N
    K --> O[Log Security Warning<br/>Return 200 OK]
```

### 3. **Environment Routing Flow**

```mermaid
flowchart TD
    A[HTTPS Request<br/>Port 443] --> B[Nginx Load Balancer]
    B --> C{URL Path?}
    
    C -->|/webhooks/hcp-dev| D[Development Service<br/>Port 5001]
    C -->|/webhooks/hcp| E[Production Service<br/>Port 5000]
    
    D --> F[Airtable Dev Base<br/>app67yWFv0hKdl6jM]
    E --> G[Airtable Prod Base<br/>appZzebEIqCU5R9ER]
    
    F --> H[webhook_development.log]
    G --> I[webhook.log]
    
    D --> J[Boris HCP Account<br/>Direct Webhooks]
    E --> K[Production HCP Account<br/>Servativ Forwarded]
```

### 4. **Appointment Event Processing Flow**

```mermaid
flowchart TD
    A[Appointment Event] --> B{Event Type?}
    
    B -->|scheduled| C[Extract Appointment Data]
    B -->|rescheduled| D[Extract Updated Data]
    B -->|discarded| E[Clear Appointment Data]
    B -->|pros_assigned| F[Extract Employee Data]
    B -->|pros_unassigned| G[Remove Employee Data]
    
    C --> H[Update Fields:<br/>- Service Appointment ID<br/>- Assignee<br/>- Scheduled Service Time<br/>- Job Status: Scheduled]
    
    D --> I[Update Fields:<br/>- Service Appointment ID<br/>- Assignee<br/>- Scheduled Service Time<br/>- Sync Message: Rescheduled]
    
    E --> J[Clear Fields:<br/>- Service Appointment ID<br/>- Assignee<br/>- Scheduled Service Time<br/>- Job Status: Unscheduled]
    
    F --> K[Update Fields:<br/>- Assignee<br/>- Sync Message: Pros Assigned]
    
    G --> L[Update Fields:<br/>- Assignee (Remaining)<br/>- Sync Message: Pros Unassigned]
    
    H --> M[Format Sync Message]
    I --> M
    J --> M
    K --> M
    L --> M
    
    M --> N[Update Airtable Record]
```

### 5. **Job Status Processing Flow**

```mermaid
flowchart TD
    A[Job Status Event] --> B[Extract Job Data]
    B --> C[Map HCP Status to Airtable Status]
    
    C --> D{Status Mapping}
    D -->|completed| E[Job Status: Completed]
    D -->|canceled| F[Job Status: Canceled]
    D -->|in_progress| G[Job Status: In Progress]
    D -->|scheduled| H[Job Status: Scheduled]
    D -->|needs_scheduling| I[Job Status: Unscheduled]
    
    E --> J[Extract Work Timestamps]
    F --> J
    G --> J
    H --> J
    I --> J
    
    J --> K[Update Fields:<br/>- On My Way Time<br/>- Job Started Time<br/>- Job Completed Time]
    
    K --> L{Significant Change?}
    L -->|Yes| M[Update Service Sync Details<br/>with Activity Message]
    L -->|No| N[Skip Sync Details Update]
    
    M --> O[Update Airtable Record]
    N --> O
```

### 6. **Record Matching and Reconciliation Flow**

```mermaid
flowchart TD
    A[Webhook with Job ID] --> B[Search Airtable by Job ID]
    B --> C{Record Found?}
    
    C -->|Yes| D[Validate Record Eligibility]
    C -->|No| E[Attempt Job Reconciliation]
    
    D --> F{Eligible for Update?}
    F -->|Yes| G[Process Webhook Update]
    F -->|No| H[Log Skipped Update<br/>Return 200 OK]
    
    E --> I[Search by Customer/Address/Time]
    I --> J{Match Found?}
    
    J -->|Yes| K[Link Job to Reservation]
    J -->|No| L[Log Orphaned Job<br/>Return 200 OK]
    
    K --> M[Update Job ID Field]
    M --> G
    
    G --> N[Update Airtable Fields]
    N --> O[Return 200 OK]
    
    H --> O
    L --> O
```

### 7. **Error Handling Flow**

```mermaid
flowchart TD
    A[Webhook Processing Error] --> B{Error Type?}
    
    B -->|Authentication| C[Log Security Warning<br/>Check Auth Config]
    B -->|Validation| D[Log Payload Error<br/>Check Format]
    B -->|Airtable API| E[Retry with Backoff]
    B -->|System Error| F[Log Full Stack Trace]
    
    C --> G[Always Return 200 OK]
    D --> G
    
    E --> H{Retry Count < 3?}
    H -->|Yes| I[Wait Exponential Backoff]
    H -->|No| J[Log Permanent Failure]
    
    I --> K[Retry Airtable Update]
    K --> L{Success?}
    L -->|Yes| G
    L -->|No| H
    
    J --> G
    F --> M[Send Admin Alert]
    M --> G
    
    G --> N[Maintain Webhook Availability]
```

### 8. **Sync Message Formatting Flow**

```mermaid
flowchart TD
    A[Webhook Event Data] --> B[Determine Message Type]
    B --> C{Event Category?}
    
    C -->|Schedule Sync| D[Build Schedule Message]
    C -->|Status Change| E[Build Status Message]
    C -->|Assignment| F[Build Assignment Message]
    C -->|Error| G[Build Error Message]
    
    D --> H[Format Arizona Timestamp]
    E --> H
    F --> H
    G --> H
    
    H --> I[Apply Message Standards:<br/>- Right-side timestamp<br/>- No bold markdown<br/>- Include IDs<br/>- Length limits]
    
    I --> J{Field Type?}
    J -->|Schedule Sync Details| K[Alert Field<br/>Only when mismatched]
    J -->|Service Sync Details| L[Activity Log<br/>Always updated]
    
    K --> M[Update Airtable Field]
    L --> M
```

### 9. **Performance Monitoring Flow**

```mermaid
flowchart TD
    A[Webhook Processing Start] --> B[Record Start Timestamp]
    B --> C[Process Webhook]
    C --> D[Record End Timestamp]
    
    D --> E[Calculate Processing Time]
    E --> F{Processing Time > Threshold?}
    
    F -->|Yes| G[Log Performance Warning]
    F -->|No| H[Log Normal Processing]
    
    G --> I[Update Performance Metrics]
    H --> I
    
    I --> J[Track Success/Failure Rate]
    J --> K{Error Rate > Threshold?}
    
    K -->|Yes| L[Send Alert to Admins]
    K -->|No| M[Continue Monitoring]
    
    L --> N[Investigate Performance Issues]
    M --> O[Update Dashboard Metrics]
    N --> O
```

### 10. **CloudMailin Email Processing Flow**

```mermaid
flowchart TD
    A[CloudMailin Email Webhook] --> B[Validate Email Source]
    B --> C{From iTrip?}
    
    C -->|Yes| D[Check Subject Line]
    C -->|No| E[Log and Ignore<br/>Return 200 OK]
    
    D --> F{Contains 'Checkouts Report'?}
    F -->|Yes| G[Extract Attachments]
    F -->|No| E
    
    G --> H{CSV Attachments Present?}
    H -->|Yes| I[Process Each Attachment]
    H -->|No| J[Log Warning<br/>No CSV Files]
    
    I --> K[Decode Base64 Content]
    K --> L[Save to Both Environments:<br/>- CSV_process_development/<br/>- CSV_process_production/]
    
    L --> M[Generate Unique Filename<br/>with Timestamp]
    M --> N[Set File Permissions]
    N --> O[Log Successful Processing]
    
    O --> P[Return 200 OK]
    J --> P
    E --> P
```

---

*These diagrams provide visual representations of all major webhook processing flows, from initial request receipt through final data updates, including error handling and performance monitoring.*