# CSV Processing - System Logical Flow

## Main CSV Processing Flow

```mermaid
graph TD
    A[Email with CSV] --> B[CloudMailin]
    B --> C{Webhook}
    C --> D[Save to Process Folder]
    D --> E[Automation Controller]
    E --> F[CSV Processor]
    
    F --> G{Detect Supplier}
    G -->|iTrip| H[Parse iTrip Format]
    G -->|Evolve| I[Parse Evolve Format]
    G -->|Unknown| J[Generic Parser]
    
    H --> K[Generate UIDs]
    I --> K
    J --> K
    
    K --> L{Check Duplicates}
    L -->|New| M[Create Records]
    L -->|Exists| N[Update Logic]
    
    N --> O{Data Changed?}
    O -->|Yes| P[Clone & Update]
    O -->|No| Q[Skip]
    
    M --> R[Sync to Airtable]
    P --> R
    Q --> S[Log Skip]
    
    R --> T[Move to Done]
    S --> T
```

## CloudMailin Webhook Flow

```mermaid
sequenceDiagram
    participant E as Email Server
    participant CM as CloudMailin
    participant W as Webhook Server
    participant FS as File System
    participant Q as Process Queue
    
    E->>CM: Email with attachment
    CM->>CM: Parse email
    CM->>W: POST /webhooks/csv-email
    Note over W: Verify signature
    W->>W: Extract attachments
    W->>FS: Save CSV files
    W->>Q: Queue for processing
    W-->>CM: 200 OK
    Q->>Q: Wait for automation
```

## Supplier Detection Logic

```mermaid
graph TD
    A[CSV File] --> B{Filename Check}
    B -->|Contains 'itrip'| C[iTrip Supplier]
    B -->|Contains 'evolve'| D[Evolve Supplier]
    B -->|Neither| E{Header Check}
    
    E --> F{Has 'Company Use'?}
    F -->|Yes| C
    F -->|No| G{Has 'address'?}
    G -->|Yes| D
    G -->|No| H[Unknown Supplier]
    
    C --> I[Use iTrip Parser]
    D --> J[Use Evolve Parser]
    H --> K[Use Generic Parser]
```

## UID Generation Flow

```mermaid
graph LR
    subgraph "Input Data"
        A1[Source: itrip]
        A2[Property: Beach House]
        A3[Check-in: 2025-07-15]
        A4[Check-out: 2025-07-20]
        A5[Guest: John Smith]
    end
    
    subgraph "Processing"
        B1[Extract Last Name: Smith]
        B2[Normalize Property: beach_house]
        B3[Format Dates: 2025-07-15]
        B4[Lowercase All: smith]
    end
    
    subgraph "Output"
        C[UID: itrip_beach_house_2025-07-15_2025-07-20_smith]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B3
    A5 --> B4
    
    B1 --> C
    B2 --> C
    B3 --> C
    B4 --> C
```

## Duplicate Detection State Machine

```mermaid
stateDiagram-v2
    [*] --> CheckingUID
    
    CheckingUID --> NotFound: No match
    CheckingUID --> Found: UID exists
    
    NotFound --> CreateNew
    CreateNew --> [*]
    
    Found --> CompareData
    CompareData --> NoChange: Data identical
    CompareData --> Changed: Data different
    
    NoChange --> Skip
    Skip --> [*]
    
    Changed --> CloneExisting
    CloneExisting --> MarkOld
    MarkOld --> CreateModified
    CreateModified --> [*]
```

## Property Matching Flow

```mermaid
graph TD
    A[Property Name from CSV] --> B{Exact Match?}
    B -->|Yes| C[Link Property ID]
    B -->|No| D{Owner Override?}
    
    D -->|Yes| E[Use Override Property]
    D -->|No| F{Close Match?}
    
    E --> C
    
    F -->|Yes| G[Log Suggestion]
    F -->|No| H[Log Error]
    
    G --> I[Skip Record]
    H --> I
    
    C --> J[Continue Processing]
```

## Error Handling Flow

```mermaid
graph TD
    A[Process CSV] --> B{Error Type}
    
    B -->|File Error| C[Log File Error]
    B -->|Parse Error| D[Log Parse Error]
    B -->|Validation Error| E[Log Validation Error]
    B -->|API Error| F[Log API Error]
    
    C --> G{Critical?}
    D --> G
    E --> G
    F --> G
    
    G -->|Yes| H[Alert Admin]
    G -->|No| I[Continue Next]
    
    H --> J[Move to Error Folder]
    I --> K[Process Next File]
    
    J --> L[Manual Review]
    K --> M[Complete Run]
```

## Date Processing Pipeline

```mermaid
graph LR
    A[Raw Date String] --> B{Format Detection}
    
    B -->|MM/DD/YYYY| C[Parse US Format]
    B -->|YYYY-MM-DD| D[Parse ISO Format]
    B -->|DD/MM/YYYY| E[Parse EU Format]
    B -->|Unknown| F[Try All Formats]
    
    C --> G[Validate Date]
    D --> G
    E --> G
    F --> G
    
    G --> H{Valid?}
    H -->|Yes| I[Normalize to YYYY-MM-DD]
    H -->|No| J[Reject Record]
    
    I --> K{In Range?}
    K -->|Yes| L[Accept Date]
    K -->|No| M[Skip Record]
```

## Example Scenarios

### 1. Happy Path - New iTrip Reservation
```mermaid
sequenceDiagram
    participant CM as CloudMailin
    participant W as Webhook
    participant CSV as CSV Processor
    participant AT as Airtable
    
    CM->>W: iTrip CSV email
    W->>W: Save tkCCJWPg.csv
    Note over CSV: Automation runs
    CSV->>CSV: Detect iTrip format
    CSV->>CSV: Parse 5 reservations
    CSV->>CSV: Generate 5 UIDs
    CSV->>AT: Check existing
    AT-->>CSV: 0 matches
    CSV->>AT: Create 5 records
    CSV->>CSV: Move to done folder
```

### 2. Error Case - Missing Property
```mermaid
sequenceDiagram
    participant CSV as CSV Processor
    participant AT as Airtable
    participant L as Logs
    
    CSV->>CSV: Parse reservation
    CSV->>AT: Lookup "Beech House"
    AT-->>CSV: Not found
    CSV->>L: Log missing property
    CSV->>L: Suggest "Beach House"
    CSV->>CSV: Skip this record
    CSV->>CSV: Continue next record
```

### 3. Edge Case - Duplicate with Changes
```mermaid
sequenceDiagram
    participant CSV as CSV Processor
    participant AT as Airtable
    
    CSV->>CSV: Generate UID
    CSV->>AT: Check existing
    AT-->>CSV: Found active record
    CSV->>CSV: Compare all fields
    Note over CSV: Guest name changed
    CSV->>AT: Clone existing record
    CSV->>AT: Mark old as "Old"
    CSV->>AT: Create "Modified" record
    CSV->>CSV: Log update
```

---

## Flow Legend

- **Rectangles**: Process steps
- **Diamonds**: Decision points
- **Parallelograms**: Input/Output
- **Cylinders**: Data stores
- **Swim lanes**: Different systems

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Mermaid Version**: v10.0+