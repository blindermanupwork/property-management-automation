# ICS Feed Sync - System Logical Flow

## Main ICS Processing Flow

```mermaid
graph TD
    A[Cron Trigger] --> B[Automation Controller]
    B --> C[ICS Processor]
    C --> D[Load Active Feeds]
    
    D --> E{Feed Count}
    E -->|0 feeds| F[Log & Exit]
    E -->|1-10 feeds| G[Process All]
    E -->|>10 feeds| H[Batch Process]
    
    G --> I[Async Fetch]
    H --> J[Chunked Async]
    
    I --> K[Parse ICS]
    J --> K
    
    K --> L{Valid Events?}
    L -->|Yes| M[Generate UIDs]
    L -->|No| N[Log Error]
    
    M --> O[Check Existing]
    O --> P{Duplicates?}
    P -->|New| Q[Create Records]
    P -->|Exists| R[Update Logic]
    
    Q --> S[Sync to Airtable]
    R --> S
    
    S --> T[Removal Detection]
    T --> U[Mark Orphans]
    U --> V[Update Feed Status]
    
    N --> W[Next Feed]
    V --> W
    W --> X{More Feeds?}
    X -->|Yes| I
    X -->|No| Y[Summary Report]
```

## Concurrent Feed Processing

```mermaid
graph TD
    subgraph "Feed Queue"
        A1[Feed 1: Airbnb]
        A2[Feed 2: VRBO]
        A3[Feed 3: Booking]
        A4[Feed 4: Hospitable]
        A5[Feed 5-255...]
    end
    
    subgraph "Async Workers"
        B1[Worker 1]
        B2[Worker 2]
        B3[Worker 3]
        B4[Worker 4]
        B5[Worker 5-10]
    end
    
    subgraph "Processing"
        C1[Fetch ICS]
        C2[Parse Events]
        C3[Generate UIDs]
        C4[Sync Records]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    A5 --> B5
    
    B1 --> C1
    B2 --> C1
    B3 --> C1
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D[Aggregated Results]
```

## Event Parsing Pipeline

```mermaid
graph LR
    A[Raw ICS Data] --> B{Parse Calendar}
    B -->|Success| C[Extract VEVENTs]
    B -->|Failure| D[Log Parse Error]
    
    C --> E{For Each Event}
    E --> F{Has DTSTART?}
    F -->|No| G[Skip Event]
    F -->|Yes| H{Has DTEND?}
    
    H -->|No| G
    H -->|Yes| I{Has UID?}
    
    I -->|No| J[Generate UID]
    I -->|Yes| K{Date in Range?}
    
    J --> K
    K -->|No| G
    K -->|Yes| L{Has SUMMARY?}
    
    L -->|Yes| M[Type: Reservation]
    L -->|No| N[Type: Block]
    
    M --> O[Extract Guest Name]
    N --> P[Set Block Name]
    
    O --> Q[Create Event Object]
    P --> Q
    
    G --> R[Next Event]
    Q --> R
```

## Composite UID Generation

```mermaid
graph TD
    subgraph "Input Data"
        A1[ICS UID: ABC123]
        A2[Property ID: prop_456]
        A3[Platform: Airbnb]
    end
    
    subgraph "Processing"
        B1[Lowercase UID: abc123]
        B2[Format Property: prop_456]
        B3[Clean Special Chars]
    end
    
    subgraph "Output"
        C[Composite UID: UID_prop_456_abc123]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    
    B1 --> C
    B2 --> C
    B3 --> C
```

## Duplicate Detection Flow

```mermaid
stateDiagram-v2
    [*] --> LoadingExisting
    
    LoadingExisting --> BuildingIndex
    BuildingIndex --> ProcessingEvents
    
    ProcessingEvents --> CheckingUID
    
    CheckingUID --> NotFound: No match
    CheckingUID --> Found: UID exists
    
    NotFound --> CreateNew
    Found --> CompareData
    
    CompareData --> NoChange: Identical
    CompareData --> Changed: Different
    
    NoChange --> UpdateTimestamp
    Changed --> UpdateRecord
    
    CreateNew --> SyncToAirtable
    UpdateTimestamp --> SyncToAirtable
    UpdateRecord --> SyncToAirtable
    
    SyncToAirtable --> NextEvent
    NextEvent --> CheckingUID: More events
    NextEvent --> [*]: Done
```

## Removal Detection Algorithm

```mermaid
graph TD
    A[Feed Sync Complete] --> B[Get Current UIDs]
    B --> C[Query Active Records]
    
    C --> D{For Property + Source}
    D --> E[Get DB UIDs]
    
    E --> F[Set Difference]
    F --> G{UIDs in DB but not Feed}
    
    G -->|Found| H[Mark as Removed]
    G -->|None| I[No Orphans]
    
    H --> J[Update Status]
    J --> K[Log Removals]
    
    I --> L[Complete]
    K --> L
```

## Entry Type Determination

```mermaid
graph TD
    A[ICS Event] --> B{Has SUMMARY?}
    
    B -->|Yes| C{Contains Keywords?}
    B -->|No| D[Type: Block]
    
    C -->|'block'| D
    C -->|'owner'| D
    C -->|'maintenance'| D
    C -->|None| E{Parse Guest Name}
    
    E -->|Success| F[Type: Reservation]
    E -->|Failure| G{Check Platform}
    
    G -->|Airbnb| H[Default: Reservation]
    G -->|VRBO| H
    G -->|Other| I[Type: Block]
    
    D --> J[Entry Type = Block]
    F --> K[Entry Type = Reservation]
    H --> K
    I --> J
```

## Error Handling Flow

```mermaid
graph TD
    A[Feed Processing] --> B{Error Type}
    
    B -->|Network| C[Log Timeout]
    B -->|Parse| D[Log Invalid ICS]
    B -->|Validation| E[Log Bad Data]
    B -->|API| F[Log Airtable Error]
    
    C --> G{Retry Logic}
    D --> H[Skip Feed]
    E --> I[Skip Event]
    F --> J{Batch Failed?}
    
    G -->|Under Limit| K[Retry Feed]
    G -->|Over Limit| H
    
    J -->|Partial| L[Retry Failed Items]
    J -->|Total| M[Mark Feed Error]
    
    H --> N[Continue Next]
    I --> N
    K --> N
    L --> N
    M --> N
    
    N --> O{More Feeds?}
    O -->|Yes| A
    O -->|No| P[Error Summary]
```

## Example Scenarios

### 1. Happy Path - New Airbnb Reservation

```mermaid
sequenceDiagram
    participant Cron
    participant ICS as ICS Processor
    participant AB as Airbnb Feed
    participant AT as Airtable
    
    Cron->>ICS: Trigger sync
    ICS->>AT: Load active feeds
    AT-->>ICS: 50 feeds
    ICS->>AB: Fetch ICS data
    AB-->>ICS: Calendar with 10 events
    ICS->>ICS: Parse events
    ICS->>ICS: Generate composite UIDs
    ICS->>AT: Check existing
    AT-->>ICS: 2 exist, 8 new
    ICS->>AT: Create 8 records
    ICS->>AT: Update 2 timestamps
    ICS->>ICS: Check removals
    ICS->>AT: Mark 1 removed
    ICS->>AT: Update feed status
```

### 2. Error Case - Feed Timeout

```mermaid
sequenceDiagram
    participant ICS as ICS Processor
    participant Feed as Problem Feed
    participant Log as Error Log
    participant AT as Airtable
    
    ICS->>Feed: Fetch ICS (30s timeout)
    Note over Feed: No response
    Feed--xICS: Timeout
    ICS->>Log: Log feed timeout
    ICS->>AT: Update feed error count
    ICS->>ICS: Continue next feed
    Note over ICS: Other feeds unaffected
```

### 3. Edge Case - Platform Migration

```mermaid
sequenceDiagram
    participant ICS as ICS Processor
    participant Old as Old Platform
    participant New as New Platform
    participant AT as Airtable
    
    Note over Old: Feed returns empty
    ICS->>Old: Fetch ICS
    Old-->>ICS: 0 events
    ICS->>AT: Find active records
    AT-->>ICS: 5 active reservations
    ICS->>AT: Mark all as removed
    
    Note over New: New feed activated
    ICS->>New: Fetch ICS  
    New-->>ICS: 5 events (same dates)
    ICS->>ICS: Generate new UIDs
    ICS->>AT: Create 5 new records
    Note over AT: History preserved
```

## Performance Optimization

```mermaid
graph TD
    subgraph "Memory Management"
        A1[Stream ICS Data]
        A2[Process Events Individually]
        A3[Batch Airtable Updates]
        A4[Clear Processed Data]
    end
    
    subgraph "Concurrency Control"
        B1[Semaphore: 10 feeds]
        B2[Timeout: 30 seconds]
        B3[Error Isolation]
        B4[Progress Tracking]
    end
    
    subgraph "Database Efficiency"
        C1[Bulk Queries]
        C2[Indexed Lookups]
        C3[Minimal API Calls]
        C4[Cached Property Data]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> A4
    
    B1 --> B2
    B2 --> B3
    B3 --> B4
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
```

---

## Flow Legend

- **Rectangles**: Process steps
- **Diamonds**: Decision points
- **Parallelograms**: Input/Output
- **Subgraphs**: Logical groupings
- **Arrows**: Flow direction
- **Dashed Lines**: Optional paths

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Mermaid Version**: v10.0+