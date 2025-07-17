# System Overview - System Logical Flow

## Main System Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        CM[CloudMailin<br/>Email Service]
        ICS[ICS Feeds<br/>246+ Sources]
        EP[Evolve Portal<br/>Web Scraping]
        WH[Webhooks<br/>HCP Updates]
    end
    
    subgraph "Processing Layer"
        AC[Automation Controller<br/>Python]
        CSV[CSV Processor]
        ICSP[ICS Processor]
        ES[Evolve Scraper]
        WP[Webhook Processor<br/>Flask]
    end
    
    subgraph "Data Storage"
        AT[(Airtable<br/>Database)]
        FS[File System<br/>CSV Storage]
    end
    
    subgraph "Service Layer"
        API[API Server<br/>Node.js]
        HCP[HousecallPro<br/>Service Jobs]
        MCP1[Airtable MCP<br/>AI Operations]
        MCP2[HCP MCP<br/>AI Analysis]
    end
    
    CM -->|CSV Files| CSV
    ICS -->|Calendar Data| ICSP
    EP -->|Property Data| ES
    WH -->|Status Updates| WP
    
    CSV --> AT
    ICSP --> AT
    ES --> FS
    WP --> AT
    
    FS --> CSV
    
    AT <--> API
    API <--> HCP
    AT <--> MCP1
    HCP <--> MCP2
    
    AC -->|Orchestrates| CSV
    AC -->|Orchestrates| ICSP
    AC -->|Orchestrates| ES
```

## Data Flow Diagram

```mermaid
graph LR
    subgraph "Reservation Sources"
        E1[iTrip Email]
        E2[Evolve CSV]
        I1[Airbnb ICS]
        I2[VRBO ICS]
        I3[Other ICS]
    end
    
    subgraph "Processing"
        U[UID Generation]
        D[Duplicate Check]
        H[History Preserve]
    end
    
    subgraph "Output"
        R[Reservation Record]
        J[HCP Job]
        N[Notifications]
    end
    
    E1 --> U
    E2 --> U
    I1 --> U
    I2 --> U
    I3 --> U
    
    U --> D
    D -->|New| R
    D -->|Exists| H
    H --> R
    
    R -->|Service Needed| J
    J --> N
```

## Environment Separation Flow

```mermaid
graph TD
    subgraph "Development Environment"
        DEV_CM[Dev CloudMailin]
        DEV_AT[(Dev Airtable<br/>app67yWFv0hKdl6jM)]
        DEV_HCP[Dev HCP<br/>Boris Account]
        DEV_API[/api/dev/*]
        DEV_WH[/webhooks/hcp-dev]
    end
    
    subgraph "Production Environment"
        PROD_CM[Prod CloudMailin]
        PROD_AT[(Prod Airtable<br/>appZzebEIqCU5R9ER)]
        PROD_HCP[Prod HCP<br/>Customer Account]
        PROD_API[/api/prod/*]
        PROD_WH[/webhooks/hcp]
    end
    
    DEV_CM --> DEV_AT
    DEV_AT <--> DEV_API
    DEV_API <--> DEV_HCP
    DEV_HCP --> DEV_WH
    DEV_WH --> DEV_AT
    
    PROD_CM --> PROD_AT
    PROD_AT <--> PROD_API
    PROD_API <--> PROD_HCP
    PROD_HCP --> PROD_WH
    PROD_WH --> PROD_AT
    
    style DEV_AT fill:#e1f5fe
    style PROD_AT fill:#ffebee
```

## Process Orchestration Flow

```mermaid
sequenceDiagram
    participant C as Cron
    participant AC as Automation Controller
    participant AT as Airtable
    participant P as Processors
    
    C->>AC: Trigger (every 4 hours)
    AC->>AT: Get enabled automations
    AT-->>AC: Automation list
    
    loop For each automation
        AC->>AC: Check last run time
        alt Should run
            AC->>P: Execute script
            P->>P: Process data
            P-->>AC: Success/Error
            AC->>AT: Update last run
        else Skip
            AC->>AC: Log skip reason
        end
    end
    
    AC->>AC: Generate summary
    AC-->>C: Complete
```

## Error Handling Flow

```mermaid
stateDiagram-v2
    [*] --> Processing
    Processing --> Success: No errors
    Processing --> Error: Exception
    
    Error --> Retry: Transient error
    Error --> Alert: Critical error
    
    Retry --> Processing: Attempt < 3
    Retry --> Alert: Max attempts
    
    Alert --> Manual: Notification sent
    Manual --> [*]: Resolved
    
    Success --> [*]: Complete
```

## Integration State Machine

```mermaid
stateDiagram-v2
    [*] --> Disconnected
    
    Disconnected --> Connecting: Init
    Connecting --> Connected: Success
    Connecting --> Failed: Error
    
    Connected --> Syncing: Data available
    Connected --> Disconnected: Connection lost
    
    Syncing --> Connected: Complete
    Syncing --> Error: Sync failed
    
    Error --> Retrying: Auto retry
    Retrying --> Connected: Success
    Retrying --> Failed: Max retries
    
    Failed --> Disconnected: Reset
```

## Component Communication

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Airtable UI]
        WEB[Web Interface]
    end
    
    subgraph "API Layer"
        REST[REST API<br/>:3000]
        WH1[Webhook Server<br/>:5000]
        WH2[Webhook Dev<br/>:5001]
    end
    
    subgraph "Processing Layer"
        PY[Python Scripts]
        JS[Node.js Scripts]
    end
    
    subgraph "External Services"
        EXT1[HousecallPro]
        EXT2[CloudMailin]
        EXT3[Evolve]
    end
    
    UI <-->|HTTPS| REST
    WEB <-->|HTTPS| REST
    
    EXT1 -->|Webhook| WH1
    EXT1 -->|Webhook| WH2
    EXT2 -->|Webhook| WH1
    
    REST <--> PY
    REST <--> JS
    WH1 --> PY
    WH2 --> PY
    
    PY <--> EXT1
    PY <--> EXT3
```

## Daily Operation Timeline

```mermaid
gantt
    title Daily Automation Schedule
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Production
    ICS Sync         :00:00, 10m
    CSV Process      :00:10, 5m
    Evolve Scrape    :00:15, 15m
    HCP Sync         :00:30, 10m
    
    section Production
    ICS Sync         :04:00, 10m
    CSV Process      :04:10, 5m
    Evolve Scrape    :04:15, 15m
    HCP Sync         :04:30, 10m
    
    section Development
    ICS Sync         :00:10, 10m
    CSV Process      :00:20, 5m
    Evolve Scrape    :00:25, 15m
    HCP Sync         :00:40, 10m
```

## Example Scenarios

### 1. Happy Path - New Reservation
```mermaid
sequenceDiagram
    participant E as Email
    participant CM as CloudMailin
    participant CSV as CSV Processor
    participant AT as Airtable
    participant API as API Server
    participant HCP as HousecallPro
    
    E->>CM: iTrip CSV
    CM->>CSV: Webhook with file
    CSV->>CSV: Parse & Generate UID
    CSV->>AT: Check existing
    AT-->>CSV: Not found
    CSV->>AT: Create reservation
    Note over AT: User reviews
    AT->>API: Create job request
    API->>HCP: Create job
    HCP-->>API: Job created
    API->>AT: Update with job ID
```

### 2. Error Case - Duplicate Reservation
```mermaid
sequenceDiagram
    participant ICS as ICS Feed
    participant P as ICS Processor
    participant AT as Airtable
    
    ICS->>P: Calendar event
    P->>P: Generate UID
    P->>AT: Check existing
    AT-->>P: Found active record
    P->>P: Compare data
    alt Data changed
        P->>AT: Clone existing
        P->>AT: Mark old as "Old"
        P->>AT: Create "Modified"
    else No change
        P->>P: Skip update
    end
```

### 3. Edge Case - System Recovery
```mermaid
sequenceDiagram
    participant S as System
    participant AC as Controller
    participant P as Processor
    participant L as Logs
    
    S->>AC: Unexpected shutdown
    Note over AC: System restart
    AC->>L: Check last state
    L-->>AC: Incomplete job found
    AC->>P: Resume from checkpoint
    P->>P: Skip processed items
    P->>P: Continue processing
    P-->>AC: Completed
    AC->>L: Log recovery
```

---

## Flow Legend

- **Rectangles**: System components
- **Cylinders**: Databases
- **Diamonds**: Decision points
- **Arrows**: Data flow direction
- **Subgraphs**: Logical groupings

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Diagrams**: Mermaid v10.0+