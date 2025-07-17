# Notification System - Mermaid Flow Diagrams

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Visual flow diagrams for notification system operations

---

## 📊 **VISUAL NOTIFICATION FLOWS**

### **1. Multi-Channel Notification Delivery Flow**

```mermaid
graph TD
    A[Event Occurs] --> B{Determine Severity}
    B -->|Critical| C[Select All Channels]
    B -->|Error| D[Console + Log + Airtable]
    B -->|Warning| E[Console + Log]
    B -->|Info| F[Log Only]
    
    C --> G[Console Output]
    C --> H[File Logging]
    C --> I[Airtable Update]
    C --> J[Email Queue]
    
    D --> G
    D --> H
    D --> I
    
    E --> G
    E --> H
    
    F --> H
    
    G --> K{UTF-8 Support?}
    K -->|Yes| L[Rich Emoji Output]
    K -->|No| M[ASCII Fallback]
    
    H --> N{Log Size Check}
    N -->|>10MB| O[Rotate Log File]
    N -->|<10MB| P[Append to Log]
    
    I --> Q{API Available?}
    Q -->|Yes| R[Update Record]
    Q -->|No| S[Queue for Retry]
    
    J --> T[Future Implementation]
    
    L --> U[Display to User]
    M --> U
    O --> P
    P --> V[Persist to Disk]
    R --> W[Confirm Update]
    S --> X[Retry Logic]
```

---

### **2. Automation Status Update Flow**

```mermaid
graph TD
    A[Automation Starts] --> B[Record Start Time]
    B --> C[Print Console Status]
    C --> D[Execute Automation]
    
    D --> E{Success?}
    E -->|Yes| F[Calculate Duration]
    E -->|No| G[Capture Error]
    
    F --> H[Create Success Message]
    G --> I[Create Error Message]
    
    H --> J[Update Airtable]
    I --> J
    
    J --> K{Update Success?}
    K -->|Yes| L[Log Confirmation]
    K -->|No| M[Log Failure]
    
    L --> N[Continue Processing]
    M --> N
    
    subgraph "Airtable Update Details"
        J --> O[Find Record by Name]
        O --> P[Prepare Update Fields]
        P --> Q[PATCH Request]
        Q --> K
    end
    
    subgraph "Message Format"
        H --> R["✅ Success - Duration: Xs"]
        I --> S["❌ Failed: Error Details"]
    end
```

---

### **3. Webhook Notification Processing Flow**

```mermaid
graph TD
    A[Webhook Received] --> B{Authenticate}
    B -->|Valid| C[Parse Payload]
    B -->|Invalid| D[Return 401]
    
    C --> E[Extract Job Info]
    E --> F[Map HCP Status]
    F --> G{Status Changed?}
    
    G -->|Yes| H[Generate Update Message]
    G -->|No| I[Skip Update]
    
    H --> J[Log to Webhook Log]
    H --> K[Print to Console]
    H --> L[Update Airtable]
    
    J --> M[Environment-Specific Log]
    K --> N[Visual Status Indicator]
    L --> O[Service Sync Details Field]
    
    I --> P[Return 200 OK]
    
    M --> P
    N --> P
    O --> P
    
    subgraph "Log Separation"
        M -->|Development| Q[webhook_development.log]
        M -->|Production| R[webhook.log]
    end
    
    subgraph "Status Mapping"
        F --> S["on_my_way → On My Way"]
        F --> T["in_progress → In Progress"]
        F --> U["completed → Completed"]
        F --> V["canceled → Canceled"]
    end
```

---

### **4. Console Progress Notification Flow**

```mermaid
graph TD
    A[Long Operation Starts] --> B[Initialize Progress Tracking]
    B --> C[Display Initial Message]
    
    C --> D[Process Items Loop]
    D --> E{Item Processed}
    E --> F[Increment Counter]
    F --> G{Show Progress?}
    
    G -->|Every 10 items| H[Calculate Percentage]
    G -->|< 10 items| D
    
    H --> I[Format Progress Bar]
    I --> J[Update Console]
    J --> D
    
    E -->|All Done| K[Calculate Total Duration]
    K --> L[Display Summary]
    
    subgraph "Progress Display"
        I --> M["[████████░░] 80% (80/100)"]
        L --> N["✅ Completed 100 items in 45.3s"]
    end
    
    subgraph "Keep-Alive"
        D --> O{30s Since Update?}
        O -->|Yes| P[Show Still Working]
        O -->|No| D
        P --> D
    end
```

---

### **5. Error Notification Escalation Flow**

```mermaid
graph TD
    A[Error Occurs] --> B[Capture Context]
    B --> C{Error Severity}
    
    C -->|Critical| D[Full Escalation]
    C -->|Recoverable| E[Standard Handling]
    C -->|Warning| F[Log Only]
    
    D --> G[Console Alert with ❌]
    D --> H[Detailed Log Entry]
    D --> I[Airtable Status Update]
    D --> J[Email Queue]
    
    E --> K[Console Warning ⚠️]
    E --> L[Log with Context]
    
    F --> M[Simple Log Entry]
    
    G --> N[Stack Trace Display]
    H --> O[Full Error Context]
    I --> P[Mark as Failed]
    J --> Q[Admin Notification]
    
    subgraph "Error Context"
        B --> R[Timestamp]
        B --> S[Component]
        B --> T[Operation]
        B --> U[Input Data]
        B --> V[System State]
    end
    
    subgraph "Recovery Guidance"
        N --> W[Suggest Fix]
        O --> X[Link to Docs]
        P --> Y[Recovery Steps]
    end
```

---

### **6. Batch Notification Aggregation Flow**

```mermaid
graph TD
    A[Event Stream] --> B[Buffer Events]
    B --> C{Buffer Time Elapsed?}
    
    C -->|< 5 seconds| D[Continue Buffering]
    C -->|>= 5 seconds| E[Process Buffer]
    
    D --> F{Critical Event?}
    F -->|Yes| G[Immediate Send]
    F -->|No| B
    
    E --> H[Group by Type]
    H --> I[Generate Summary]
    I --> J[Single Notification]
    
    G --> K[Bypass Buffer]
    K --> L[Direct Delivery]
    
    J --> M[Console Summary]
    J --> N[Log Details]
    
    subgraph "Summary Format"
        I --> O["📊 Summary: 15 success, 3 errors, 2 warnings"]
        I --> P["Details in logs"]
    end
    
    subgraph "Buffer Management"
        B --> Q[Track Event Types]
        B --> R[Count Occurrences]
        B --> S[Store Error Details]
    end
```

---

### **7. Field Update Notification Flow**

```mermaid
graph TD
    A[Field Update Required] --> B{Operation Type}
    
    B -->|Schedule| C[Schedule Sync Details]
    B -->|Service| D[Service Sync Details]
    B -->|Status| E[Service Sync Details]
    
    C --> F[Build Schedule Message]
    D --> G[Build Service Message]
    E --> H[Build Status Message]
    
    F --> I[syncMessageBuilder]
    G --> I
    H --> I
    
    I --> J[Apply Template]
    J --> K[Add Timestamp]
    K --> L[Format for Airtable]
    
    L --> M{Field Length Check}
    M -->|<= 200 chars| N[Direct Update]
    M -->|> 200 chars| O[Truncate Message]
    
    O --> P[Add Ellipsis]
    P --> N
    
    N --> Q[PATCH to Airtable]
    Q --> R{Success?}
    
    R -->|Yes| S[Log Success]
    R -->|No| T[Retry Logic]
    
    subgraph "Message Templates"
        J --> U["✅ Schedules match - Jul 12, 3:45 PM"]
        J --> V["⚠️ Date mismatch - Airtable: Jul 12, HCP: Jul 13"]
        J --> W["🔄 Updated from webhook - Status: In Progress"]
    end
```

---

### **8. Log Rotation Management Flow**

```mermaid
graph TD
    A[Write Log Entry] --> B{Check Log File}
    B -->|Exists| C[Check File Size]
    B -->|Not Exists| D[Create New Log]
    
    C --> E{Size > 10MB?}
    E -->|Yes| F[Rotate Log]
    E -->|No| G[Append Entry]
    
    F --> H[Rename with Timestamp]
    H --> I[Create New Log File]
    I --> G
    
    G --> J[Write with MST Time]
    J --> K[Flush Buffer]
    
    D --> G
    
    subgraph "Rotation Logic"
        H --> L[automation_prod_20250712_1.log]
        H --> M[Check Backup Count]
        M --> N{Count > 5?}
        N -->|Yes| O[Delete Oldest]
        N -->|No| P[Keep All]
    end
    
    subgraph "Environment Logs"
        A --> Q{Which Environment?}
        Q -->|Dev| R[automation_dev_*.log]
        Q -->|Prod| S[automation_prod_*.log]
    end
```

---

### **9. Real-Time Status Dashboard Flow**

```mermaid
graph TD
    A[Status Change] --> B[Immediate Notification]
    B --> C[Multi-Channel Update]
    
    C --> D[Console Display]
    C --> E[Log Entry]
    C --> F[Airtable Dashboard]
    
    D --> G[Emoji Status Icon]
    E --> H[Timestamp Entry]
    F --> I[Field Update]
    
    G --> J[Visual Feedback]
    H --> K[Audit Trail]
    I --> L[Dashboard Refresh]
    
    subgraph "Status Types"
        B --> M["🚀 Starting"]
        B --> N["✅ Success"]
        B --> O["❌ Failed"]
        B --> P["⚠️ Warning"]
        B --> Q["🔄 In Progress"]
        B --> R["⏭️ Skipped"]
    end
    
    subgraph "Dashboard Fields"
        I --> S[Last Run Time]
        I --> T[Status Icon]
        I --> U[Duration]
        I --> V[Details]
    end
```

---

### **10. Summary Report Generation Flow**

```mermaid
graph TD
    A[Operations Complete] --> B[Collect Statistics]
    B --> C[Calculate Metrics]
    C --> D[Format Report]
    
    D --> E[Section Headers]
    D --> F[Component Status]
    D --> G[Timing Details]
    D --> H[Overall Summary]
    
    E --> I[Visual Separators]
    F --> J[Status Icons]
    G --> K[Duration Calc]
    H --> L[Success Rate]
    
    I --> M[Multi-Line Output]
    J --> M
    K --> M
    L --> M
    
    M --> N[Console Display]
    M --> O[Log to File]
    M --> P[Update Airtable]
    
    subgraph "Report Structure"
        M --> Q["═══ Automation Summary ═══"]
        M --> R["✅ CSV: Success (15 files)"]
        M --> S["❌ Evolve: Failed (login)"]
        M --> T["📊 Total: 3/4 success (75%)"]
        M --> U["⏱️ Duration: 5m 32s"]
    end
    
    subgraph "Distribution"
        N --> V[Terminal Output]
        O --> W[Summary Log]
        P --> X[Dashboard Update]
    end
```

---

## 🔧 **NOTIFICATION PATTERNS REFERENCE**

### **Visual Indicators**
- ✅ Success/Complete
- ❌ Error/Failed
- ⚠️ Warning/Caution
- 🔄 In Progress/Sync
- 📝 Update/Modification
- 🔍 Search/Check
- ⏭️ Skip/Bypass
- 🚀 Start/Launch
- 📊 Summary/Stats

### **Channel Matrix**
```
Critical → Console + Log + Airtable + Email
Error    → Console + Log + Airtable
Warning  → Console + Log
Info     → Log
Debug    → Log (verbose only)
```

### **Timing Strategies**
```
Immediate  → Status changes, errors
Buffered   → Similar events (5s window)
Scheduled  → Summary reports
Throttled  → Progress updates (10 items)
```

---

*These visual diagrams provide comprehensive coverage of notification flows throughout the property management automation system.*