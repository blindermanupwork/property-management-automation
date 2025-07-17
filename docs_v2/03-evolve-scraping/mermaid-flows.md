# Evolve Portal Scraping - System Logical Flow

## Main Scraping Flow

```mermaid
graph TD
    A[Cron Trigger] --> B{Check Environment}
    B -->|Not Set| C[Exit with Error]
    B -->|Set| D[Initialize Chrome]
    
    D --> E[Configure Options]
    E --> F{Headless Mode?}
    F -->|Yes| G[Add Headless Flags]
    F -->|No| H[GUI Mode]
    
    G --> I[Create Browser]
    H --> I
    
    I --> J[Navigate to Login]
    J --> K[Enter Credentials]
    K --> L{Login Success?}
    
    L -->|No| M[Retry Login]
    L -->|Yes| N[Export Tab1]
    
    M --> O{Max Retries?}
    O -->|No| K
    O -->|Yes| P[Fatal Error]
    
    N --> Q[Wait for Download]
    Q --> R[Move to CSV_process]
    R --> S[Export Tab2]
    
    S --> T[Wait for Download]
    T --> U[Move to CSV_process]
    U --> V[Cleanup & Close]
    
    V --> W[Success Log]
    P --> X[Error Alert]
```

## Browser Initialization Flow

```mermaid
graph LR
    subgraph "Chrome Options"
        A1[Base Options]
        A2[--headless]
        A3[--no-sandbox]
        A4[--disable-gpu]
        A5[--window-size=1920,1080]
    end
    
    subgraph "Download Config"
        B1[Create /tmp/evolve_downloads]
        B2[Set download.default_directory]
        B3[Clear existing files]
        B4[Set permissions]
    end
    
    subgraph "Driver Setup"
        C1[Locate ChromeDriver]
        C2[Check compatibility]
        C3[Initialize WebDriver]
        C4[Set timeouts]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    A4 --> A5
    
    A5 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
```

## Login Authentication Flow

```mermaid
sequenceDiagram
    participant S as Scraper
    participant B as Browser
    participant E as Evolve Portal
    participant L as Logs
    
    S->>B: Navigate to login URL
    B->>E: GET /login
    E-->>B: Login page
    
    S->>B: Find username field
    S->>B: Send keys (username)
    S->>B: Find password field
    S->>B: Send keys (password)
    
    S->>B: Click login button
    B->>E: POST /authenticate
    
    E-->>B: Redirect to dashboard
    S->>S: Wait for dashboard element
    
    alt Success
        S->>L: Log successful login
        S->>S: Continue to exports
    else Failure
        E-->>B: Error message
        S->>L: Log login failure
        S->>S: Retry login
    end
```

## Tab Export Navigation

```mermaid
stateDiagram-v2
    [*] --> Dashboard
    
    Dashboard --> PropertiesMenu: Click Properties
    PropertiesMenu --> CalendarView: Select Calendar
    
    CalendarView --> ExportButton1: Find Export
    ExportButton1 --> DownloadTab1: Click Download
    DownloadTab1 --> WaitDownload1: Poll directory
    
    WaitDownload1 --> FileFound1: File appears
    FileFound1 --> MoveFile1: Move to CSV_process
    
    MoveFile1 --> ReportsMenu: Navigate Reports
    ReportsMenu --> ReservationsView: Select Reservations
    
    ReservationsView --> ExportButton2: Find Export
    ExportButton2 --> DownloadTab2: Click Download
    DownloadTab2 --> WaitDownload2: Poll directory
    
    WaitDownload2 --> FileFound2: File appears
    FileFound2 --> MoveFile2: Move to CSV_process
    
    MoveFile2 --> Logout: Complete
    Logout --> [*]
```

## Element Wait Strategy

```mermaid
graph TD
    A[Find Element] --> B{Element Present?}
    B -->|No| C[Wait 1 second]
    C --> D{Timeout?}
    D -->|No| A
    D -->|Yes| E[Try Alternative Selector]
    
    E --> F{Alternative Found?}
    F -->|Yes| G[Use Element]
    F -->|No| H[Take Screenshot]
    
    B -->|Yes| I{Element Visible?}
    I -->|No| J[Scroll to Element]
    I -->|Yes| K{Element Clickable?}
    
    J --> K
    K -->|No| L[Wait for Clickable]
    K -->|Yes| G
    
    L --> M{Still Not Clickable?}
    M -->|Yes| N[JavaScript Click]
    M -->|No| G
    
    H --> O[Log Error]
    G --> P[Continue Flow]
    N --> P
```

## File Download Management

```mermaid
graph TD
    A[Click Export] --> B[Browser Download Start]
    B --> C[Monitor /tmp/evolve_downloads]
    
    C --> D{New File Detected?}
    D -->|No| E[Wait 1 second]
    E --> F{Timeout?}
    F -->|No| C
    F -->|Yes| G[Download Failed]
    
    D -->|Yes| H{File Still Growing?}
    H -->|Yes| I[Wait for Stable Size]
    H -->|No| J[Validate CSV]
    
    I --> H
    
    J --> K{Valid CSV?}
    K -->|No| G
    K -->|Yes| L[Generate Timestamp]
    
    L --> M[Create Target Filename]
    M --> N{Check Environment}
    
    N -->|Dev| O[Move to CSV_process_development]
    N -->|Prod| P[Move to CSV_process_production]
    
    O --> Q[Delete from /tmp]
    P --> Q
    G --> R[Alert & Retry]
```

## Error Recovery Flow

```mermaid
graph TD
    A[Operation] --> B{Error Occurred?}
    B -->|No| C[Continue]
    B -->|Yes| D{Error Type}
    
    D -->|Timeout| E[Page Refresh]
    D -->|Element Not Found| F[Update Selectors]
    D -->|Download Failed| G[Clear Downloads]
    D -->|Login Failed| H[Clear Cookies]
    
    E --> I{Retry Count}
    F --> I
    G --> I
    H --> I
    
    I -->|< 3| J[Increment Retry]
    I -->|>= 3| K[Fatal Error]
    
    J --> L[Wait 5 seconds]
    L --> M[Retry Operation]
    
    K --> N[Take Screenshot]
    N --> O[Log Full Error]
    O --> P[Close Browser]
    P --> Q[Exit with Code 1]
    
    M --> A
    C --> R[Next Step]
```

## Sequential Processing Mode

```mermaid
graph LR
    subgraph "Parallel Mode Issues"
        A1[Tab1 Export]
        A2[Tab2 Export]
        A3[Chrome Conflict]
        A4[Download Collision]
        
        A1 -.->|Simultaneous| A2
        A1 --> A3
        A2 --> A3
        A3 --> A4
    end
    
    subgraph "Sequential Mode Solution"
        B1[Tab1 Export]
        B2[Wait Complete]
        B3[Tab2 Export]
        B4[Wait Complete]
        B5[Success]
        
        B1 --> B2
        B2 --> B3
        B3 --> B4
        B4 --> B5
    end
    
    A4 -->|Switch to| B1
```

## Example Scenarios

### 1. Happy Path - Successful Export

```mermaid
sequenceDiagram
    participant Cron
    participant Scraper
    participant Chrome
    participant Evolve
    participant FileSystem
    
    Cron->>Scraper: Start (ENVIRONMENT=production)
    Scraper->>Chrome: Launch headless
    Chrome->>Evolve: Navigate to login
    Scraper->>Evolve: Submit credentials
    Evolve-->>Chrome: Dashboard loaded
    
    Scraper->>Evolve: Navigate to Calendar
    Scraper->>Evolve: Click Export
    Evolve-->>FileSystem: Download Tab1.csv
    Scraper->>FileSystem: Move to CSV_process_production
    
    Scraper->>Evolve: Navigate to Reports
    Scraper->>Evolve: Click Export
    Evolve-->>FileSystem: Download Tab2.csv
    Scraper->>FileSystem: Move to CSV_process_production
    
    Scraper->>Chrome: Close browser
    Scraper->>Cron: Exit 0
```

### 2. Error Case - Login Failure

```mermaid
sequenceDiagram
    participant Scraper
    participant Chrome
    participant Evolve
    participant Logs
    
    Scraper->>Chrome: Launch browser
    Chrome->>Evolve: Navigate to login
    Scraper->>Evolve: Submit credentials
    Evolve-->>Chrome: Invalid credentials
    
    Scraper->>Logs: Log attempt 1 failed
    Scraper->>Scraper: Wait 5 seconds
    
    Scraper->>Evolve: Submit credentials
    Evolve-->>Chrome: Account locked
    
    Scraper->>Logs: Log attempt 2 failed
    Scraper->>Chrome: Take screenshot
    Scraper->>Logs: Save error details
    Scraper->>Chrome: Close browser
    Scraper->>Scraper: Exit 1
```

### 3. Recovery Case - Element Not Found

```mermaid
sequenceDiagram
    participant S as Scraper
    participant B as Browser
    participant E as Evolve
    
    S->>B: Find export button (CSS)
    B-->>S: Element not found
    S->>S: Try XPath selector
    S->>B: Find export button (XPath)
    B-->>S: Element found
    S->>B: Click export
    B->>E: Trigger download
    Note over S: Continue normally
```

## Environment-Specific Routing

```mermaid
graph TD
    A[ENVIRONMENT Variable] --> B{Value?}
    
    B -->|"development"| C[Dev Configuration]
    B -->|"production"| D[Prod Configuration]
    B -->|Not Set| E[ERROR: Exit]
    B -->|Invalid| E
    
    C --> F[CSV_process_development/]
    C --> G[automation_dev.log]
    C --> H[Dev Airtable Base]
    
    D --> I[CSV_process_production/]
    D --> J[automation_prod.log]
    D --> K[Prod Airtable Base]
    
    F --> L[Process Files]
    I --> L
    
    L --> M[CSV Processor]
    M --> N[Continue Workflow]
```

---

## Flow Legend

- **Rectangles**: Process steps
- **Diamonds**: Decision points
- **Parallelograms**: Input/Output
- **Circles**: Start/End states
- **Dashed Lines**: Problematic flows
- **Solid Lines**: Recommended flows

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Mermaid Version**: v10.0+