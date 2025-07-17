# Airtable Integration - System Logical Flow

## Main Integration Architecture

```mermaid
graph TD
    subgraph "Data Sources"
        A1[CSV Files]
        A2[ICS Feeds]
        A3[Web Scraping]
        A4[Webhooks]
        A5[User Input]
    end
    
    subgraph "Airtable Base"
        B1[(Reservations)]
        B2[(Properties)]
        B3[(Customers)]
        B4[(Settings)]
        B5[(ICS Feeds)]
        B6[(Job Types)]
    end
    
    subgraph "External Systems"
        C1[HousecallPro]
        C2[Email Services]
        C3[Reporting]
        C4[MCP Servers]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B1
    A5 --> B1
    
    B1 --> C1
    B1 --> C2
    B1 --> C3
    B1 --> C4
    
    B2 --> B1
    B3 --> B1
    B4 --> B1
    B5 --> B1
    B6 --> C1
```

## CRUD Operations Flow

```mermaid
sequenceDiagram
    participant App as Application
    participant API as Airtable API
    participant DB as Airtable Base
    participant Cache as Local Cache
    
    App->>API: GET /records
    API->>DB: Query records
    DB-->>API: Return data
    API-->>App: JSON response
    App->>Cache: Store results
    
    App->>API: POST /records
    Note over API: Validate fields
    API->>DB: Create record
    DB-->>API: New record ID
    API-->>App: Success response
    App->>Cache: Update cache
    
    App->>API: PATCH /records/{id}
    API->>DB: Update fields
    DB-->>API: Confirmation
    API-->>App: Updated record
    
    App->>API: DELETE /records/{id}
    API->>DB: Mark deleted
    DB-->>API: Success
    API-->>App: Confirmation
```

## Field Type Validation Flow

```mermaid
graph TD
    A[Input Data] --> B{Validate Type}
    
    B -->|Text| C[String Check]
    B -->|Number| D[Numeric Check]
    B -->|Date| E[ISO Format Check]
    B -->|Select| F[Option Match Check]
    B -->|Link| G[Record ID Check]
    B -->|Checkbox| H[Boolean Check]
    
    C --> I{Valid?}
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    
    I -->|Yes| J[Prepare for API]
    I -->|No| K[Validation Error]
    
    J --> L[Send to Airtable]
    K --> M[Log Error]
    M --> N[User Feedback]
```

## Batch Operation Processing

```mermaid
graph LR
    A[100 Records] --> B[Chunk into 10s]
    
    B --> C[Batch 1: 1-10]
    B --> D[Batch 2: 11-20]
    B --> E[...]
    B --> F[Batch 10: 91-100]
    
    C --> G[API Call 1]
    D --> H[API Call 2]
    E --> I[...]
    F --> J[API Call 10]
    
    G --> K[Wait 200ms]
    H --> K
    I --> K
    J --> K
    
    K --> L[Aggregate Results]
    L --> M[Return Success/Errors]
```

## Rate Limiting Strategy

```mermaid
stateDiagram-v2
    [*] --> Ready
    
    Ready --> Sending: Make Request
    Sending --> Success: 200 OK
    Sending --> RateLimit: 429 Error
    Sending --> Error: Other Error
    
    Success --> Cooldown: Start Timer
    Cooldown --> Ready: 200ms elapsed
    
    RateLimit --> Backoff: Wait 2s
    Backoff --> Retry: Attempt Again
    Retry --> Success: 200 OK
    Retry --> RateLimit: Still Limited
    
    Error --> LogError: Record Issue
    LogError --> Ready: Continue
    
    state RateLimit {
        [*] --> FirstLimit
        FirstLimit --> SecondLimit: Retry
        SecondLimit --> ThirdLimit: Retry
        ThirdLimit --> Abort: Max Retries
    }
```

## Linked Record Management

```mermaid
graph TD
    A[Reservation Record] --> B{Has Property?}
    
    B -->|Yes| C[Extract Property ID]
    B -->|No| D[Find Property]
    
    C --> E[Validate ID Format]
    D --> F[Search by Name]
    
    F --> G{Found?}
    G -->|Yes| H[Get Property ID]
    G -->|No| I[Create Property?]
    
    E --> J{Valid?}
    J -->|Yes| K[Link Records]
    J -->|No| L[Error]
    
    H --> K
    I --> M[Manual Process]
    
    K --> N[Update Reservation]
    N --> O[Save Changes]
```

## Environment-Specific Routing

```mermaid
graph TD
    A[API Request] --> B{Which Environment?}
    
    B -->|Development| C[Dev Config]
    B -->|Production| D[Prod Config]
    
    C --> E[Dev Base ID]
    C --> F[Dev API Key]
    C --> G[Dev Tables]
    
    D --> H[Prod Base ID]
    D --> I[Prod API Key]
    D --> J[Prod Tables]
    
    E --> K[Dev Airtable]
    H --> L[Prod Airtable]
    
    K --> M[Dev Response]
    L --> N[Prod Response]
    
    M --> O[Process Data]
    N --> O
```

## Status Transition Management

```mermaid
stateDiagram-v2
    [*] --> New: Record Created
    
    New --> Active: Processing Start
    Active --> Modified: Data Changed
    Modified --> Active: Revert
    
    Active --> Removed: Deletion
    Modified --> Removed: Deletion
    
    Active --> Old: Archive
    Modified --> Old: Archive
    
    Old --> [*]: Permanent
    Removed --> [*]: Permanent
    
    note right of New: Initial state
    note right of Active: Normal state
    note right of Modified: Changed data
    note right of Old: Historical
    note right of Removed: Soft delete
```

## Pagination Flow

```mermaid
graph TD
    A[Request All Records] --> B[First Page Request]
    B --> C[Receive 100 Records]
    C --> D{Has Offset?}
    
    D -->|Yes| E[Store Offset]
    D -->|No| F[Complete]
    
    E --> G[Request Next Page]
    G --> H[Receive Next 100]
    H --> I[Append to Results]
    I --> D
    
    F --> J[Return All Records]
    
    subgraph "Memory Management"
        K[Process in Chunks]
        L[Clear Processed]
        M[Garbage Collect]
    end
    
    I --> K
    K --> L
    L --> M
```

## Error Recovery Patterns

```mermaid
graph TD
    A[API Operation] --> B{Response}
    
    B -->|Success| C[Process Data]
    B -->|429 Rate Limit| D[Wait & Retry]
    B -->|422 Validation| E[Check Fields]
    B -->|404 Not Found| F[Verify ID]
    B -->|500 Server Error| G[Exponential Backoff]
    B -->|Timeout| H[Single Retry]
    
    D --> I{Retry Count}
    I -->|< 3| J[Wait 2^n seconds]
    I -->|>= 3| K[Abort Operation]
    
    J --> A
    
    E --> L[Log Field Errors]
    F --> M[Check Record Exists]
    G --> N{Retry Count}
    H --> O{First Attempt?}
    
    N -->|< 5| P[Wait Longer]
    N -->|>= 5| Q[Alert Admin]
    
    O -->|Yes| A
    O -->|No| R[Fail Operation]
```

## Example Scenarios

### 1. Creating a Reservation

```mermaid
sequenceDiagram
    participant CSV as CSV Processor
    participant Val as Validator
    participant API as Airtable API
    participant Base as Airtable Base
    
    CSV->>Val: New reservation data
    Val->>Val: Check required fields
    Val->>Val: Validate property exists
    Val->>Val: Format dates
    
    Val->>API: POST /Reservations
    Note over API: {
    Note over API:   "Property": ["recABC123"],
    Note over API:   "Check-in Date": "2025-07-15",
    Note over API:   "Guest Name": "John Smith"
    Note over API: }
    
    API->>Base: Create record
    Base-->>API: Record ID: recXYZ789
    API-->>Val: Success response
    Val-->>CSV: Reservation created
```

### 2. Bulk Update with Rate Limiting

```mermaid
sequenceDiagram
    participant Script as Update Script
    participant Batcher as Batch Manager
    participant API as Airtable API
    participant Monitor as Rate Monitor
    
    Script->>Batcher: 50 records to update
    Batcher->>Batcher: Split into 5 batches
    
    loop Each Batch
        Batcher->>Monitor: Check rate limit
        Monitor-->>Batcher: OK to proceed
        
        Batcher->>API: PATCH 10 records
        API-->>Batcher: Success
        
        Batcher->>Monitor: Record request
        Monitor->>Monitor: Wait 200ms
    end
    
    Batcher-->>Script: All updates complete
```

### 3. Complex Query with Filtering

```mermaid
sequenceDiagram
    participant App as Application
    participant Builder as Query Builder
    participant API as Airtable API
    participant Cache as Result Cache
    
    App->>Builder: Find active beach properties
    Builder->>Builder: Build filterByFormula
    Note over Builder: AND(
    Note over Builder:   {Status} = 'Active',
    Note over Builder:   FIND('Beach', {Property Name})
    Note over Builder: )
    
    Builder->>API: GET /Properties?filterByFormula=...
    API-->>Builder: 15 matching records
    
    Builder->>Cache: Store results
    Builder-->>App: Return properties
    
    Note over Cache: Cache for 5 minutes
```

---

## Flow Legend

- **Rectangles**: Process steps
- **Diamonds**: Decision points
- **Cylinders**: Data storage
- **Parallelograms**: Input/Output
- **Notes**: Important details

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Mermaid Version**: v10.0+