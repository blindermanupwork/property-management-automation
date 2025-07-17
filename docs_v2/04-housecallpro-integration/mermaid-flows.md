# HousecallPro Integration - System Logical Flow

## Main Integration Flow

```mermaid
graph TD
    A[Airtable Reservation] --> B{Ready for Job?}
    B -->|No| C[Wait]
    B -->|Yes| D{Has HCP Job?}
    
    D -->|Yes| E[Update Schedule Only]
    D -->|No| F[Create Job Flow]
    
    F --> G[Validate Prerequisites]
    G --> H{Valid?}
    H -->|No| I[Show Error]
    H -->|Yes| J[Find/Create Customer]
    
    J --> K[Build Job Payload]
    K --> L[Add Service Lines]
    L --> M[Set Schedule]
    M --> N[Call HCP API]
    
    N --> O{Success?}
    O -->|No| P[Log Error]
    O -->|Yes| Q[Store Job ID]
    
    Q --> R[Update Airtable]
    R --> S[Wait for Webhook]
    
    S --> T[Status Updates]
    T --> U[Schedule Changes]
    U --> V[Completion]
```

## Job Creation Detailed Flow

```mermaid
sequenceDiagram
    participant U as User
    participant AT as Airtable
    participant API as API Server
    participant HCP as HousecallPro
    participant WH as Webhook
    
    U->>AT: Click "Create Job"
    AT->>API: POST /create-job
    API->>API: Validate request
    
    API->>HCP: GET /customers?email=
    alt Customer Found
        HCP-->>API: Customer data
    else Customer Not Found
        API->>HCP: POST /customers
        HCP-->>API: New customer ID
    end
    
    API->>API: Build job payload
    Note over API: Add line items, schedule
    
    API->>HCP: POST /jobs
    HCP-->>API: Job created
    
    API->>AT: Update record
    AT-->>U: Success message
    
    Note over WH: Async webhook
    HCP->>WH: Job status update
    WH->>AT: Update status
```

## Service Line Name Construction

```mermaid
graph TD
    subgraph "Input Data"
        A1[Base Service: Turnover STR Next Guest]
        A2[Next Date: July 15]
        A3[Custom: Please check pool]
        A4[Long-term: 21 nights]
        A5[Owner Next: Yes]
    end
    
    subgraph "Processing Logic"
        B1[Add Next Guest Date]
        B2[Check Custom Instructions]
        B3[Check Long-term Status]
        B4[Check Owner Arrival]
        B5[Truncate to 200 chars]
    end
    
    subgraph "Final Output"
        C[Please check pool - OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 15]
    end
    
    A1 --> B1
    A2 --> B1
    A3 --> B2
    A4 --> B3
    A5 --> B4
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> B5
    B5 --> C
```

## Status Synchronization Flow

```mermaid
stateDiagram-v2
    [*] --> NeedsScheduling: Job Created
    
    NeedsScheduling --> Scheduled: Assign Employee
    Scheduled --> Dispatched: Day of Service
    Dispatched --> InProgress: Employee Arrives
    InProgress --> Completed: Job Finished
    
    NeedsScheduling --> Canceled: Cancel Job
    Scheduled --> Canceled: Cancel Job
    Dispatched --> Canceled: Cancel Job
    
    state Airtable {
        New
        Scheduled2: Scheduled
        InProgress2: In Progress
        Completed2: Completed
        Canceled2: Canceled
    }
    
    NeedsScheduling --> New: Sync
    Scheduled --> Scheduled2: Sync
    InProgress --> InProgress2: Sync
    Completed --> Completed2: Sync
    Canceled --> Canceled2: Sync
```

## Webhook Processing Flow

```mermaid
graph TD
    A[HCP Event] --> B[Webhook Endpoint]
    B --> C{Verify Signature}
    
    C -->|Invalid| D[Return 401]
    C -->|Valid| E{Parse Event}
    
    E --> F{Event Type}
    
    F -->|job.created| G[Log Only]
    F -->|job.updated| H[Check Changes]
    F -->|schedule.updated| I[Update Schedule]
    F -->|job.completed| J[Mark Complete]
    
    H --> K{Status Changed?}
    K -->|No| L[Skip Update]
    K -->|Yes| M[Update Airtable]
    
    I --> N[Update Times]
    J --> O[Set Completed]
    
    G --> P[Return 200]
    L --> P
    M --> P
    N --> P
    O --> P
    
    D --> Q[Log Security Error]
```

## Customer Matching Algorithm

```mermaid
graph TD
    A[Airtable Record] --> B{Has HCP ID?}
    
    B -->|Yes| C[Use Existing]
    B -->|No| D{Has Email?}
    
    D -->|Yes| E[Search by Email]
    D -->|No| F{Has Phone?}
    
    E --> G{Found?}
    G -->|Yes| C
    G -->|No| F
    
    F -->|Yes| H[Search by Phone]
    F -->|No| I[Search by Name]
    
    H --> J{Found?}
    J -->|Yes| C
    J -->|No| I
    
    I --> K{Found?}
    K -->|Yes| C
    K -->|No| L[Create New Customer]
    
    L --> M[Store HCP ID]
    C --> N[Continue Job Creation]
    M --> N
```

## Schedule Update Flow

```mermaid
sequenceDiagram
    participant User
    participant AT as Airtable
    participant API as API Server
    participant HCP as HousecallPro
    
    User->>AT: Set Custom Service Time
    User->>AT: Click "Update Schedule"
    
    AT->>API: POST /update-schedule
    Note over API: Include job ID, new times
    
    API->>API: Validate times
    API->>API: Calculate duration
    
    API->>HCP: PATCH /jobs/{id}
    Note over HCP: Update scheduled_start_at
    Note over HCP: Update scheduled_end_at
    
    HCP-->>API: Success
    API->>AT: Update confirmation
    
    AT-->>User: Schedule updated
    
    Note over HCP: Triggers webhook
    HCP->>AT: Webhook update
```

## Error Handling Flow

```mermaid
graph TD
    A[API Call] --> B{Error Type}
    
    B -->|400| C[Validation Error]
    B -->|401| D[Auth Error]
    B -->|404| E[Not Found]
    B -->|429| F[Rate Limit]
    B -->|500| G[Server Error]
    
    C --> H[Show User Message]
    D --> I[Check API Key]
    E --> J[Check Resource]
    F --> K[Backoff & Retry]
    G --> L[Log & Alert]
    
    H --> M[Log Details]
    I --> M
    J --> M
    K --> N{Retry Success?}
    L --> M
    
    N -->|Yes| O[Continue]
    N -->|No| M
    
    M --> P[Update UI]
    O --> P
```

## Long-term Guest Detection

```mermaid
graph LR
    A[Check-in Date] --> B[Check-out Date]
    B --> C{Calculate Nights}
    
    C --> D[Nights Stayed]
    D --> E{>= 14?}
    
    E -->|Yes| F[Set Flag: longTermGuest = true]
    E -->|No| G[Set Flag: longTermGuest = false]
    
    F --> H[Add to Service Line]
    G --> I[Standard Service Line]
    
    H --> J["LONG TERM GUEST DEPARTING"]
    I --> K[No Special Flag]
```

## Owner Arrival Detection

```mermaid
graph TD
    A[Reservation Checkout] --> B[Query Future Entries]
    B --> C{Same Property?}
    
    C -->|No| D[No Owner]
    C -->|Yes| E{Next Entry Type?}
    
    E -->|Reservation| F[No Owner]
    E -->|Block| G{Check-in Date}
    
    G --> H{Same/Next Day?}
    H -->|No| I[No Owner]
    H -->|Yes| J{Guest Name Match?}
    
    J -->|Owner| K[Set ownerArriving = true]
    J -->|Other| L[Check Keywords]
    
    L --> M{Contains 'owner'?}
    M -->|Yes| K
    M -->|No| I
    
    K --> N[Add "OWNER ARRIVING"]
    I --> O[Standard Service]
    F --> O
    D --> O
```

## Example Scenarios

### 1. Happy Path - New Job Creation

```mermaid
sequenceDiagram
    participant User
    participant Airtable
    participant API
    participant HCP
    
    User->>Airtable: Mark "Ready for Job"
    User->>Airtable: Click "Create Job"
    Airtable->>API: Reservation data
    
    API->>HCP: Find customer
    HCP-->>API: Customer found
    
    API->>API: Build job:
    Note over API: - Turnover STR Next Guest
    Note over API: - July 15-17, 2025
    Note over API: - 10 AM - 2 PM
    Note over API: - LONG TERM (15 nights)
    
    API->>HCP: Create job
    HCP-->>API: Job ID: job_123
    
    API->>Airtable: Update HCP Job ID
    Airtable-->>User: Success!
```

### 2. Error Case - Missing Customer

```mermaid
sequenceDiagram
    participant API
    participant HCP
    participant Logs
    
    API->>HCP: Find customer by email
    HCP-->>API: Not found
    
    API->>HCP: Find by phone
    HCP-->>API: Not found
    
    API->>HCP: Create customer
    Note over API: Name: John Smith
    Note over API: Email: john@email.com
    Note over API: Phone: 555-1234
    
    HCP-->>API: Customer created
    API->>Logs: New customer: cus_456
    
    API->>API: Continue job creation
```

### 3. Webhook Case - Status Update

```mermaid
sequenceDiagram
    participant Tech as HCP Technician
    participant HCP
    participant Webhook
    participant Airtable
    
    Tech->>HCP: Start job
    HCP->>HCP: Status = in_progress
    
    HCP->>Webhook: POST /webhooks/hcp
    Note over Webhook: Event: job.updated
    Note over Webhook: Status: in_progress
    
    Webhook->>Webhook: Verify signature
    Webhook->>Airtable: Find by Job ID
    Webhook->>Airtable: Update Status
    
    Webhook-->>HCP: 200 OK
    
    Note over Airtable: Status = "In Progress"
```

---

## Flow Legend

- **Rectangles**: Process steps
- **Diamonds**: Decision points
- **Parallelograms**: Input/Output
- **Cylinders**: Data stores
- **Notes**: Important details
- **Alt blocks**: Conditional logic

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Mermaid Version**: v10.0+