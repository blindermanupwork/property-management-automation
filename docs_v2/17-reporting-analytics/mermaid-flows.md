# Reporting & Analytics - Mermaid Flow Diagrams

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Visual flow diagrams for reporting and analytics operations

---

## 📊 **VISUAL REPORTING FLOWS**

### **1. HCP Bulletproof Analysis Flow**

```mermaid
graph TD
    A[Analysis Request] --> B{Cache Available?}
    B -->|No| C[Error: Run list_jobs first]
    B -->|Yes| D[Find Valid Cache Files]
    
    D --> E[Initialize Counters]
    E --> F[Process Each File]
    
    F --> G{Parse JSON}
    G -->|Success| H[Extract Jobs Array]
    G -->|Error| I[Log Error & Continue]
    
    H --> J[Process Each Job]
    J --> K[Extract Revenue]
    J --> L[Categorize Status]
    J --> M[Track Customer]
    
    K --> N{Revenue Found?}
    N -->|Direct Field| O[Use Field Value]
    N -->|String Field| P[Parse to Number]
    N -->|No Fields| Q[Sum Line Items]
    N -->|Nothing| R[Default to 0]
    
    L --> S[Status Breakdown]
    M --> T[Customer Stats]
    
    I --> U{More Files?}
    O --> U
    P --> U
    Q --> U
    R --> U
    
    U -->|Yes| F
    U -->|No| V[Generate Results]
    
    V --> W[Calculate Averages]
    V --> X[Rank Customers]
    V --> Y[Add Quality Metrics]
    V --> Z[Return Analysis]
    
    subgraph "Quality Metrics"
        Y --> AA[Files Processed]
        Y --> AB[Records Analyzed]
        Y --> AC[Error Count]
        Y --> AD[Execution Time]
    end
```

---

### **2. Service Item Analysis Flow**

```mermaid
graph TD
    A[Item Pattern Input] --> B[Compile Regex]
    B --> C[Load Cache Files]
    
    C --> D{Files Found?}
    D -->|No| E[Return Empty Results]
    D -->|Yes| F[Initialize Totals]
    
    F --> G[Process Each File]
    G --> H[Parse Job Data]
    
    H --> I{Has Line Items?}
    I -->|No| J[Skip Job]
    I -->|Yes| K[Check Each Item]
    
    K --> L{Matches Pattern?}
    L -->|No| M[Next Item]
    L -->|Yes| N[Extract Quantities]
    
    N --> O[Parse Numbers]
    O --> P[Calculate Costs]
    O --> Q[Calculate Revenue]
    O --> R[Track Usage]
    
    P --> S[Total Cost += Item Cost]
    Q --> T[Total Revenue += Item Revenue]
    R --> U[Usage Array Push]
    
    M --> V{More Items?}
    J --> W{More Jobs?}
    V -->|Yes| K
    V -->|No| W
    W -->|Yes| H
    W -->|No| X{More Files?}
    
    X -->|Yes| G
    X -->|No| Y[Generate Summary]
    
    Y --> Z[Calculate Averages]
    Y --> AA[Sort Usage Data]
    Y --> AB[Package Results]
    
    subgraph "Usage Details"
        U --> AC[Job ID]
        U --> AD[Customer Name]
        U --> AE[Quantity]
        U --> AF[Unit Price]
        U --> AG[Total Value]
    end
```

---

### **3. CSV Processing Report Flow**

```mermaid
graph TD
    A[CSV Processing Complete] --> B[Collect Results]
    B --> C[Group by Property]
    
    C --> D[Initialize Counters]
    D --> E[Process Each Property]
    
    E --> F[Get Property Name]
    F --> G{Name Found?}
    G -->|Yes| H[Use Property Name]
    G -->|No| I[Use "Unknown Property"]
    
    H --> J[Count Outcomes]
    I --> J
    
    J --> K[New Records]
    J --> L[Modified Records]
    J --> M[Unchanged Records]
    
    K --> N[Property Report Section]
    L --> N
    M --> N
    
    N --> O{More Properties?}
    O -->|Yes| E
    O -->|No| P[Calculate Totals]
    
    P --> Q[Sum All New]
    P --> R[Sum All Modified]
    P --> S[Sum All Unchanged]
    
    Q --> T[Generate Summary]
    R --> T
    S --> T
    
    T --> U[Format Report]
    U --> V[Add Headers]
    U --> W[Add Property Details]
    U --> X[Add Summary Section]
    U --> Y[Add Footers]
    
    subgraph "Report Structure"
        V --> Z["------------ Run digest ------------"]
        W --> AA["CSV -> Source for Property Name"]
        X --> AB["------------ Summary ------------"]
        Y --> AC["------------ End Summary ------------"]
    end
```

---

### **4. Monthly Trend Analysis Flow**

```mermaid
graph TD
    A[Job Data Stream] --> B[Extract Date]
    
    B --> C{Valid Date?}
    C -->|No| D[Month = "unknown"]
    C -->|Yes| E[Parse Date Object]
    
    E --> F[Extract Year]
    E --> G[Extract Month]
    
    F --> H[Format YYYY-MM]
    G --> H
    
    H --> I{Month Exists?}
    I -->|No| J[Initialize Month]
    I -->|Yes| K[Get Month Data]
    
    J --> L[Set Job Count = 0]
    J --> M[Set Revenue = 0]
    
    K --> N[Increment Job Count]
    K --> O[Add to Revenue]
    L --> N
    M --> O
    
    N --> P{More Jobs?}
    O --> P
    P -->|Yes| A
    P -->|No| Q[Convert to Array]
    
    Q --> R[Map Entries]
    R --> S[Sort by Month]
    S --> T[Calculate Trends]
    
    T --> U[Month-over-Month]
    T --> V[Seasonal Patterns]
    T --> W[Growth Rate]
    
    subgraph "Trend Metrics"
        U --> X[% Change]
        V --> Y[Peak Months]
        W --> Z[Annual Growth]
    end
```

---

### **5. Customer Revenue Ranking Flow**

```mermaid
graph TD
    A[Start Analysis] --> B[Initialize Customer Map]
    B --> C[Process Jobs]
    
    C --> D[Extract Customer ID]
    D --> E{Customer Exists?}
    
    E -->|No| F[Skip Job]
    E -->|Yes| G[Get Customer Name]
    
    G --> H{In Map?}
    H -->|No| I[Create Entry]
    H -->|Yes| J[Get Entry]
    
    I --> K[Initialize Stats]
    K --> L[Job Count = 0]
    K --> M[Revenue = 0]
    K --> N[Status Map = {}]
    
    J --> O[Update Stats]
    L --> O
    M --> O
    N --> O
    
    O --> P[Increment Jobs]
    O --> Q[Add Revenue]
    O --> R[Track Status]
    
    P --> S{More Jobs?}
    Q --> S
    R --> S
    
    S -->|Yes| C
    S -->|No| T[Convert to Array]
    
    T --> U[Calculate Averages]
    U --> V[Sort by Revenue]
    V --> W[Take Top 10]
    
    W --> X[Format Results]
    
    subgraph "Customer Metrics"
        X --> Y[Total Jobs]
        X --> Z[Total Revenue]
        X --> AA[Average Value]
        X --> AB[Status Breakdown]
    end
```

---

### **6. Data Quality Assurance Flow**

```mermaid
graph TD
    A[Analysis Start] --> B[Init Quality Trackers]
    
    B --> C[Files Processed = 0]
    B --> D[Records Analyzed = 0]
    B --> E[Error Count = 0]
    B --> F[Start Timer]
    
    C --> G[Begin Processing]
    D --> G
    E --> G
    F --> G
    
    G --> H[Open File]
    H --> I{File Valid?}
    
    I -->|Yes| J[Increment Files]
    I -->|No| K[Increment Errors]
    
    J --> L[Count Records]
    L --> M[Add to Total]
    
    K --> N[Log Error]
    N --> O{Continue?}
    
    O -->|Yes| P{More Files?}
    O -->|No| Q[Abort Analysis]
    
    M --> P
    P -->|Yes| H
    P -->|No| R[Calculate Metrics]
    
    R --> S[Stop Timer]
    S --> T[Error Rate %]
    S --> U[Completion %]
    S --> V[Reliability Score]
    
    T --> W[Package Metrics]
    U --> W
    V --> W
    
    subgraph "Quality Report"
        W --> X[Files: Success/Total]
        W --> Y[Records: Processed]
        W --> Z[Errors: Count & Rate]
        W --> AA[Time: Milliseconds]
    end
```

---

### **7. Revenue Extraction Strategy Flow**

```mermaid
graph TD
    A[Job Object] --> B[Try Direct Fields]
    
    B --> C{job.total exists?}
    C -->|Yes| D[Check Type]
    C -->|No| E[Try total_amount]
    
    D --> F{Is Number?}
    F -->|Yes| G[Return Value]
    F -->|No| H[Parse String]
    
    H --> I{Valid Number?}
    I -->|Yes| G
    I -->|No| E
    
    E --> J{More Fields?}
    J -->|Yes| K[Try Next Field]
    J -->|No| L[Check Line Items]
    
    K --> D
    
    L --> M{Has Line Items?}
    M -->|No| N[Return 0]
    M -->|Yes| O[Sum Items]
    
    O --> P[For Each Item]
    P --> Q[Get Quantity]
    P --> R[Get Unit Price]
    
    Q --> S[Multiply Q × P]
    R --> S
    S --> T[Add to Sum]
    
    T --> U{More Items?}
    U -->|Yes| P
    U -->|No| V[Return Sum]
    
    subgraph "Field Priority"
        B --> W[1. total]
        B --> X[2. total_amount]
        B --> Y[3. invoice_total]
        B --> Z[4. amount/price/subtotal]
    end
```

---

### **8. Automation Performance Summary Flow**

```mermaid
graph TD
    A[Suite Complete] --> B[Collect Results]
    B --> C[Count Successes]
    B --> D[Count Failures]
    B --> E[Calculate Duration]
    
    C --> F[Success Rate %]
    D --> F
    
    E --> G[Total Time]
    E --> H[Per-Component Time]
    
    F --> I[Generate Summary]
    G --> I
    H --> I
    
    I --> J[Format Header]
    I --> K[List Components]
    I --> L[Show Metrics]
    I --> M[Add Footer]
    
    K --> N[Component Loop]
    N --> O{Success?}
    
    O -->|Yes| P[✅ Component Name]
    O -->|No| Q[❌ Component Name]
    
    P --> R[Show Duration]
    Q --> R
    
    R --> S{More Components?}
    S -->|Yes| N
    S -->|No| T[Display Totals]
    
    subgraph "Summary Format"
        J --> U["═══ Automation Summary ═══"]
        T --> V["📊 Results: X/Y successful"]
        T --> W["⏱️ Duration: XXs"]
        M --> X["═══ Complete ═══"]
    end
```

---

### **9. Report Distribution Flow**

```mermaid
graph TD
    A[Report Request] --> B{Scheduled?}
    B -->|Yes| C[Check Schedule]
    B -->|No| D[On-Demand]
    
    C --> E{Time to Run?}
    E -->|No| F[Wait]
    E -->|Yes| G[Select Report Type]
    D --> G
    
    G --> H[Daily Summary]
    G --> I[Weekly Analytics]
    G --> J[Monthly Trends]
    G --> K[Custom Query]
    
    H --> L[Gather Data]
    I --> L
    J --> L
    K --> L
    
    L --> M[Run Analyses]
    M --> N[Format Output]
    
    N --> O{Distribution List}
    O --> P[Console Output]
    O --> Q[Log File]
    O --> R[Airtable Update]
    O --> S[Export File]
    
    P --> T[Display Report]
    Q --> U[Write to Log]
    R --> V[Update Dashboard]
    S --> W[Generate CSV]
    
    T --> X[Track Delivery]
    U --> X
    V --> X
    W --> X
    
    subgraph "Delivery Confirmation"
        X --> Y[Log Success]
        X --> Z[Update Last Sent]
        X --> AA[Notify Complete]
    end
```

---

### **10. Real-Time Dashboard Update Flow**

```mermaid
graph TD
    A[Data Change Event] --> B[Trigger Analysis]
    B --> C[Quick Metrics Calc]
    
    C --> D[Active Jobs Count]
    C --> E[Today's Revenue]
    C --> F[Success Rate]
    C --> G[Error Count]
    
    D --> H[Dashboard API]
    E --> H
    F --> H
    G --> H
    
    H --> I{Airtable Ready?}
    I -->|No| J[Queue Update]
    I -->|Yes| K[Push Updates]
    
    J --> L[Retry Queue]
    L --> M{Retry Limit?}
    M -->|No| N[Wait & Retry]
    M -->|Yes| O[Log Failure]
    
    N --> I
    
    K --> P[Update Fields]
    P --> Q[Refresh Views]
    Q --> R[Trigger Formulas]
    
    R --> S[Update Complete]
    
    subgraph "Dashboard Metrics"
        D --> T[Running/Scheduled/Complete]
        E --> U[Sum of Today's Jobs]
        F --> V[Success/Total × 100]
        G --> W[Errors Last 24h]
    end
```

---

## 🔧 **ANALYTICS PATTERNS REFERENCE**

### **Data Sources**
- HCP cached job files
- CSV processing results
- ICS sync statistics
- Automation run logs

### **Analysis Types**
```
Revenue    → Customer ranking, monthly trends
Inventory  → Service item usage, costs
Operations → Success rates, timing
Quality    → Error rates, completeness
```

### **Output Destinations**
```
Console    → Human-readable summaries
Logs       → Structured reports
Airtable   → Dashboard updates
Exports    → CSV/JSON files
```

---

*These visual diagrams provide comprehensive coverage of reporting and analytics flows throughout the property management automation system.*