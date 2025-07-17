# HousecallPro MCP Server - Mermaid Flow Diagrams

## 1. MCP Connection and Authentication Flow

```mermaid
sequenceDiagram
    participant AI as AI Assistant (Claude)
    participant MCP as HCP MCP Server
    participant HCP as HousecallPro API
    
    AI->>MCP: Initialize MCP Connection
    MCP->>MCP: Load Environment Config
    MCP->>MCP: Validate API Key
    MCP->>HCP: Test API Connection
    HCP-->>MCP: Connection Confirmed
    MCP-->>AI: MCP Ready
    
    Note over AI,HCP: MCP server now ready for operations
```

## 2. Customer Management Workflow

```mermaid
flowchart TD
    A[AI Request: Customer Operation] --> B{Operation Type}
    
    B -->|Search| C[list_customers with filters]
    B -->|Create| D[create_customer with validation]
    B -->|Update| E[update_customer with ID]
    B -->|Get Details| F[get_customer by ID]
    
    C --> G[Apply Search Filters]
    G --> H[Execute HCP API Call]
    
    D --> I[Validate Required Fields]
    I --> J{Validation Passed?}
    J -->|Yes| H
    J -->|No| K[Return Validation Error]
    
    E --> L[Check Customer Exists]
    L --> H
    
    F --> H
    
    H --> M[Process Response]
    M --> N{API Success?}
    N -->|Yes| O[Return Customer Data]
    N -->|No| P[Return Error with Suggestions]
    
    O --> Q[Cache Response if Large]
    P --> R[Log Error with Context]
```

## 3. Job Creation and Management Flow

```mermaid
flowchart TD
    A[AI Request: Create Job] --> B[Validate Prerequisites]
    B --> C{Customer Exists?}
    C -->|No| D[Create Customer First]
    C -->|Yes| E[Validate Address]
    
    D --> E
    E --> F{Address Valid?}
    F -->|No| G[Return Address Error]
    F -->|Yes| H[Build Job Payload]
    
    H --> I[Validate Line Items]
    I --> J{Line Items Valid?}
    J -->|No| K[Return Line Item Error]
    J -->|Yes| L[Set Schedule]
    
    L --> M[Execute Job Creation]
    M --> N{Creation Success?}
    N -->|Yes| O[Return Job Data]
    N -->|No| P[Check Error Type]
    
    P --> Q{Rate Limited?}
    Q -->|Yes| R[Wait and Retry]
    Q -->|No| S[Return Error]
    
    R --> M
    O --> T[Update Cache]
```

## 4. BULLETPROOF Analysis Tools Flow

```mermaid
flowchart TD
    A[AI Request: Analysis] --> B{Analysis Type}
    
    B -->|Laundry Jobs| C[analyze_laundry_jobs]
    B -->|Service Items| D[analyze_service_items]
    B -->|Customer Revenue| E[analyze_customer_revenue]
    B -->|Job Statistics| F[analyze_job_statistics]
    B -->|Towel Usage| G[analyze_towel_usage]
    
    C --> H[Native TypeScript Processing]
    D --> H
    E --> H
    F --> H
    G --> H
    
    H --> I[Start Performance Timer]
    I --> J[Process Cached Data]
    J --> K[Apply Analysis Logic]
    K --> L[Generate Metrics]
    L --> M[Track Data Quality]
    M --> N[Stop Performance Timer]
    N --> O{Execution < 10ms?}
    
    O -->|Yes| P[Return Results with Metrics]
    O -->|No| Q[Log Performance Warning]
    Q --> P
    
    P --> R[Update Performance Stats]
```

## 5. Advanced Search Operations Flow

```mermaid
flowchart TD
    A[AI Request: Search] --> B{Search Type}
    
    B -->|Address Search| C[search_addresses]
    B -->|Job by Address| D[get_jobs_by_address]
    B -->|List Jobs Filtered| E[list_jobs with filters]
    
    C --> F[Parse Search Parameters]
    F --> G{Has Customer ID?}
    G -->|Yes| H[Customer-Specific Search]
    G -->|No| I[Global Address Search]
    
    H --> J[Execute Targeted Query]
    I --> J
    
    D --> K[Validate Address ID]
    K --> L[Apply Date/Status Filters]
    L --> J
    
    E --> M[Apply Performance Filters]
    M --> N{Customer ID Provided?}
    N -->|Yes| O[Optimized Customer Query]
    N -->|No| P[Warn: Use Customer Filter]
    O --> J
    P --> J
    
    J --> Q[Execute HCP API Call]
    Q --> R[Process Results]
    R --> S[Return Formatted Data]
```

## 6. Error Handling and Recovery Flow

```mermaid
flowchart TD
    A[API Operation] --> B{Operation Success?}
    B -->|Yes| C[Return Success Result]
    B -->|No| D[Analyze Error Type]
    
    D --> E{Error Type}
    E -->|CustomerHasNoJobs| F[Suggest list_jobs Alternative]
    E -->|CustomerNotFound| G[Suggest ID Format Check]
    E -->|InvalidPermissions| H[Suggest API Key Check]
    E -->|RateLimit| I[Implement Backoff]
    E -->|Network Error| J[Retry Logic]
    E -->|Unknown| K[Log Full Context]
    
    F --> L[Return Error with Suggestion]
    G --> L
    H --> L
    
    I --> M[Wait with Exponential Backoff]
    M --> N[Retry Operation]
    N --> B
    
    J --> O{Retry Count < Max?}
    O -->|Yes| M
    O -->|No| L
    
    K --> L
    L --> P[Log Error for Analysis]
```

## 7. Cache System Operations Flow

```mermaid
flowchart TD
    A[Data Request] --> B{Cache Hit?}
    B -->|Yes| C[Check Cache Age]
    C --> D{Cache Fresh?}
    D -->|Yes| E[Return Cached Data]
    D -->|No| F[Fetch Fresh Data]
    
    B -->|No| F
    F --> G[Execute API Call]
    G --> H[Process Response]
    H --> I{Response Size > 500KB?}
    I -->|Yes| J[Cache Response]
    I -->|No| K[Return Without Caching]
    
    J --> L[Update Cache Index]
    L --> E
    K --> E
    
    E --> M[Include Data Quality Metrics]
    M --> N[Return to AI Assistant]
    
    O[Cache Cleanup Process] --> P[Check File Ages]
    P --> Q{Files > Retention?}
    Q -->|Yes| R[Delete Old Files]
    Q -->|No| S[Maintain Files]
    R --> T[Update Cache Stats]
    S --> T
```

## 8. Line Item Management Flow

```mermaid
flowchart TD
    A[AI Request: Line Item Operation] --> B{Operation Type}
    
    B -->|Create| C[create_job_line_item]
    B -->|Update| D[update_job_line_item]
    B -->|Update All| E[update_job_line_items]
    B -->|Delete| F[delete_job_line_item]
    B -->|Get All| G[get_job_line_items]
    
    C --> H[Validate Line Item Data]
    H --> I{Kind Valid?}
    I -->|No| J[Error: Invalid Kind]
    I -->|Yes| K[Check Job Exists]
    
    J --> L[Suggest Correct Kinds]
    L --> M[Return Error with Examples]
    
    K --> N{Job Found?}
    N -->|No| O[Return Job Not Found]
    N -->|Yes| P[Execute Line Item Operation]
    
    D --> K
    E --> K
    F --> K
    G --> K
    
    P --> Q{API Success?}
    Q -->|Yes| R[Return Line Item Data]
    Q -->|No| S[Return API Error]
    
    R --> T[Update Job Cache]
    S --> U[Log Error Details]
```

## 9. Business Intelligence Dashboard Flow

```mermaid
flowchart TD
    A[AI Request: Business Intelligence] --> B[Start Performance Monitoring]
    B --> C[Initialize Data Quality Tracking]
    C --> D[Load Cached Data Files]
    
    D --> E{Files Available?}
    E -->|No| F[Return No Data Error]
    E -->|Yes| G[Parse JSON Data]
    
    G --> H[Apply Analysis Algorithms]
    H --> I[Calculate Revenue Metrics]
    I --> J[Generate Customer Insights]
    J --> K[Create Trend Analysis]
    K --> L[Build Statistical Summary]
    
    L --> M[Validate Results]
    M --> N[Package Response]
    N --> O[Add Performance Metrics]
    O --> P{Execution Time < 10ms?}
    
    P -->|Yes| Q[Mark as BULLETPROOF]
    P -->|No| R[Log Performance Issue]
    
    Q --> S[Return Business Intelligence]
    R --> S
    
    S --> T[Update BI Cache]
    T --> U[Log Analytics Request]
```

## 10. Multi-Environment Operations Flow

```mermaid
flowchart TD
    A[MCP Request] --> B{Environment}
    
    B -->|Development| C[hcp-mcp-dev Server]
    B -->|Production| D[hcp-mcp-prod Server]
    
    C --> E[Dev API Endpoints]
    C --> F[Dev Cache Location]
    C --> G[Relaxed Rate Limits]
    
    D --> H[Prod API Endpoints]
    D --> I[Prod Cache Location]
    D --> J[Standard Rate Limits]
    
    E --> K[Execute Dev Operation]
    F --> K
    G --> K
    
    H --> L[Execute Prod Operation]
    I --> L
    J --> L
    
    K --> M[Dev Response Processing]
    L --> N[Prod Response Processing]
    
    M --> O[Return Dev Results]
    N --> P[Return Prod Results]
    
    O --> Q[Log Dev Activity]
    P --> R[Log Prod Activity]
```

---

**Document Version**: 1.0.0  
**Last Updated**: July 12, 2025  
**Total Diagrams**: 10 comprehensive flow diagrams