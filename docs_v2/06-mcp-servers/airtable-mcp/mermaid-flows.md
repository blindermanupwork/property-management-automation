# Airtable MCP Server - Mermaid Flow Diagrams

## 1. MCP Connection and Authentication Flow

```mermaid
sequenceDiagram
    participant AI as AI Assistant (Claude)
    participant MCP as Airtable MCP Server
    participant AT as Airtable API
    
    AI->>MCP: Initialize MCP Connection
    MCP->>MCP: Load AIRTABLE_API_KEY
    MCP->>AT: Test Authentication
    AT-->>MCP: Return User Info
    MCP->>AT: List Bases
    AT-->>MCP: Base List with Permissions
    MCP->>MCP: Cache Base Metadata
    MCP-->>AI: MCP Ready with Tools
    
    Note over AI,AT: Server ready for operations
```

## 2. Schema Discovery Workflow

```mermaid
flowchart TD
    A[AI Request: Schema Info] --> B[MCP Server]
    B --> C{Base Known?}
    
    C -->|No| D[List All Bases]
    C -->|Yes| E[Get Base Schema]
    
    D --> F[Filter by Permissions]
    F --> G[Return Base List]
    
    E --> H[Fetch Table Metadata]
    H --> I[Parse Field Types]
    I --> J[Map Relationships]
    J --> K[Identify Views]
    K --> L[Create Resources]
    
    L --> M[Return Schema]
    G --> M
    
    M --> N[Cache for Future Use]
```

## 3. Record Operations Flow

```mermaid
flowchart TD
    A[AI: Record Operation] --> B{Operation Type}
    
    B -->|List| C[list_records]
    B -->|Search| D[search_records]
    B -->|Create| E[create_record]
    B -->|Update| F[update_records]
    B -->|Delete| G[delete_records]
    
    C --> H[Apply Filters]
    H --> I[Add View Constraints]
    I --> J[Execute Query]
    
    D --> K[Identify Text Fields]
    K --> L[Search Across Fields]
    L --> J
    
    E --> M[Validate Data Types]
    M --> N{Valid?}
    N -->|No| O[Return Validation Error]
    N -->|Yes| P[Create in Airtable]
    
    F --> Q[Batch Updates]
    Q --> R{≤ 10 Records?}
    R -->|No| S[Split into Batches]
    R -->|Yes| T[Execute Update]
    S --> T
    
    G --> U[Validate IDs]
    U --> V[Execute Delete]
    
    J --> W[Process Results]
    P --> W
    T --> W
    V --> W
    
    W --> X[Format Response]
    X --> Y[Return to AI]
```

## 4. Property Management Integration Flow

```mermaid
flowchart TD
    A[Reservation Data] --> B[Check UID Exists]
    B --> C{Found?}
    
    C -->|Yes| D[Mark Old Record]
    C -->|No| E[Skip to Create]
    
    D --> F[Status = 'Old']
    F --> G[Create New Record]
    E --> G
    
    G --> H[Status = 'Modified' or 'New']
    H --> I[Link to Property]
    I --> J[Calculate Service Type]
    J --> K[Check Stay Length]
    
    K --> L{≥ 14 days?}
    L -->|Yes| M[Flag Long-Term Guest]
    L -->|No| N[Standard Service]
    
    M --> O[Add Special Instructions]
    N --> O
    
    O --> P[Check Same-Day Turnover]
    P --> Q{Same Property & Date?}
    Q -->|Yes| R[Flag Both Records]
    Q -->|No| S[Complete Creation]
    
    R --> S
    S --> T[Return New Record]
```

## 5. Search and Filter Operations

```mermaid
sequenceDiagram
    participant AI as AI Assistant
    participant MCP as MCP Server
    participant AT as Airtable API
    
    AI->>MCP: search_records(searchTerm, fieldIds)
    MCP->>MCP: Validate Parameters
    
    alt Field IDs Provided
        MCP->>MCP: Use Specified Fields
    else No Field IDs
        MCP->>AT: Get Table Schema
        AT-->>MCP: Field Definitions
        MCP->>MCP: Filter Text Fields
    end
    
    MCP->>MCP: Build Search Query
    MCP->>AT: Execute Search
    AT-->>MCP: Matching Records
    
    MCP->>MCP: Apply View Filters
    MCP->>MCP: Format Results
    MCP-->>AI: Return Records
```

## 6. Batch Operations and Rate Limiting

```mermaid
flowchart TD
    A[Batch Operation Request] --> B{Record Count}
    
    B -->|≤ 10| C[Single Batch]
    B -->|> 10| D[Split into Chunks]
    
    C --> E[Execute Operation]
    
    D --> F[Create Batches of 10]
    F --> G[For Each Batch]
    
    G --> H[Check Rate Limit]
    H --> I{< 5 req/sec?}
    
    I -->|Yes| J[Execute Batch]
    I -->|No| K[Wait 200ms]
    K --> J
    
    J --> L{More Batches?}
    L -->|Yes| G
    L -->|No| M[Combine Results]
    
    E --> N[Return Result]
    M --> N
    
    N --> O{Any Errors?}
    O -->|Yes| P[Report Partial Success]
    O -->|No| Q[Report Complete Success]
```

## 7. Table and Field Management Flow

```mermaid
flowchart TD
    A[Schema Change Request] --> B{Change Type}
    
    B -->|Create Table| C[Validate Table Name]
    B -->|Add Field| D[Validate Field Config]
    B -->|Update| E[Fetch Current Schema]
    
    C --> F[Check Name Unique]
    F --> G{Unique?}
    G -->|No| H[Return Name Error]
    G -->|Yes| I[Validate Fields Array]
    
    I --> J[Check Primary Field]
    J --> K{Valid Type?}
    K -->|No| L[Return Type Error]
    K -->|Yes| M[Create Table Structure]
    
    D --> N[Check Field Type]
    N --> O[Validate Options]
    O --> P[Add to Table]
    
    E --> Q[Compare Changes]
    Q --> R[Apply Updates]
    
    M --> S[Update Schema Cache]
    P --> S
    R --> S
    
    S --> T[Return Success]
```

## 8. Error Handling and Recovery Flow

```mermaid
stateDiagram-v2
    [*] --> Executing: API Operation
    
    Executing --> Success: 200 OK
    Executing --> RateLimit: 429 Error
    Executing --> Permission: 403 Error
    Executing --> NotFound: 404 Error
    Executing --> Validation: 422 Error
    Executing --> Network: Network Error
    
    RateLimit --> Waiting: Exponential Backoff
    Waiting --> Retry: After Delay
    Retry --> Executing: Retry Operation
    
    Permission --> ErrorReport: Missing Scope
    NotFound --> ErrorReport: Invalid ID
    Validation --> ErrorReport: Bad Data
    Network --> QuickRetry: Immediate Retry
    
    QuickRetry --> Executing: Retry Once
    QuickRetry --> ErrorReport: Still Failing
    
    Success --> [*]: Complete
    ErrorReport --> [*]: Return Error
```

## 9. Webhook Integration Flow

```mermaid
sequenceDiagram
    participant HCP as HousecallPro
    participant WH as Webhook Handler
    participant MCP as Airtable MCP
    participant AT as Airtable
    
    HCP->>WH: Job Status Update
    WH->>WH: Parse Webhook Data
    
    WH->>MCP: Find Reservation by Job ID
    MCP->>AT: filterByFormula = HCP Job ID
    AT-->>MCP: Matching Records
    
    alt Record Found
        MCP-->>WH: Reservation Record
        WH->>MCP: Update Status Fields
        MCP->>AT: Update Record
        AT-->>MCP: Success
        MCP-->>WH: Update Complete
    else No Record
        MCP-->>WH: Not Found
        WH->>WH: Log Missing Record
    end
    
    WH-->>HCP: 200 OK
```

## 10. Complete Reservation Lifecycle

```mermaid
flowchart TD
    A[CSV/ICS Data Arrives] --> B[Generate UID]
    B --> C[Search Existing]
    
    C --> D{Found?}
    D -->|No| E[Create New - Status: New]
    D -->|Yes| F[Create New - Status: Modified]
    F --> G[Mark Old - Status: Old]
    
    E --> H[Link to Property]
    G --> H
    
    H --> I[User Reviews in Airtable]
    I --> J[Click Create Job]
    
    J --> K[Validate Prerequisites]
    K --> L{Valid?}
    L -->|No| M[Show Error]
    L -->|Yes| N[Create HCP Job]
    
    N --> O[Update with Job ID]
    O --> P[Monitor for Updates]
    
    P --> Q[Webhook Updates]
    Q --> R[Sync Status Changes]
    
    R --> S{Job Complete?}
    S -->|No| P
    S -->|Yes| T[Final Status Update]
    
    T --> U[Ready for Next Cycle]
```

---

## Flow Diagram Legend

### Symbols Used
- **Rectangle**: Process or action
- **Diamond**: Decision point
- **Parallelogram**: Input/output
- **Circle**: Start/end point
- **Note**: Additional context

### Status Values
- **New**: First time seeing this reservation
- **Modified**: Updated version of existing
- **Old**: Previous version (kept for history)
- **Removed**: No longer active

### Integration Points
- **MCP Protocol**: AI ↔ Server communication
- **Airtable API**: Server ↔ Database
- **Webhook**: External system updates
- **Schema Resources**: Metadata access

---

**Document Version**: 1.0.0  
**Last Updated**: July 12, 2025  
**Total Diagrams**: 10 comprehensive flow diagrams