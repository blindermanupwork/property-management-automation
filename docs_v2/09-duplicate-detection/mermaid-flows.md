# Duplicate Detection - Visual Workflow Diagrams

## Overview
This document contains Mermaid diagrams visualizing the duplicate detection workflows, including UID generation, duplicate identification, status resolution, and cleanup processes.

## 1. Main Duplicate Detection Flow

```mermaid
graph TD
    A[New Record Import] --> B[Extract UID]
    B --> C{UID Found?}
    C -->|No| D[Generate Placeholder]
    C -->|Yes| E[Query Existing Records]
    D --> E
    E --> F{Exact UID Match?}
    F -->|No| G[Check Property-Date]
    F -->|Yes| H[Analyze Conflict]
    G --> I{Property-Date Match?}
    I -->|No| J[Create New Record]
    I -->|Yes| K[Mark as Duplicate]
    H --> L{Keep Existing?}
    L -->|Yes| M[Mark New as Old]
    L -->|No| N[Mark Existing as Old]
    K --> O[Skip Creation]
    M --> P[Log Resolution]
    N --> Q[Create New Record]
    J --> R[Success]
    O --> R
    P --> R
    Q --> R
```

## 2. UID Generation Process

```mermaid
graph LR
    A[Data Source] --> B{Source Type?}
    B -->|CSV| C[Scan Column Headers]
    B -->|ICS| D[Extract VEVENT UID]
    
    C --> E[Find UID Column]
    E --> F{UID Column Found?}
    F -->|Yes| G[Extract Raw Value]
    F -->|No| H[Generate Placeholder]
    
    D --> I{Multi-Property Feed?}
    I -->|Yes| J[Create Composite UID]
    I -->|No| K[Use Original UID]
    
    G --> L[Clean and Validate]
    H --> L
    J --> M[Format: UID_PropertyID]
    K --> N[Store Original]
    L --> O[Store in Airtable]
    M --> P[Store Both UIDs]
    N --> O
    P --> O
```

## 3. Status-Based Conflict Resolution

```mermaid
graph TD
    A[Duplicate Detected] --> B[Compare Records]
    B --> C[Data Completeness Check]
    C --> D[Recency Check]
    D --> E[Source Authority Check]
    E --> F{Clear Winner?}
    F -->|Yes| G[Apply Resolution]
    F -->|No| H[Manual Review Queue]
    
    G --> I{Keep Which?}
    I -->|Existing| J[Mark New as Old]
    I -->|New| K[Mark Existing as Old]
    
    J --> L[Update Status: Old]
    K --> L
    L --> M[Record Reason]
    M --> N[Log Change]
    N --> O[Success]
    
    H --> P[Flag for Human Review]
    P --> Q[Escalation Process]
```

## 4. Session Tracking Workflow

```mermaid
graph TD
    A[Start Processing Session] --> B[Initialize Tracker]
    B --> C[Process Next Record]
    C --> D{In Session Already?}
    D -->|Yes| E[Mark as Duplicate]
    D -->|No| F[Check Property-Date]
    F --> G{Property-Date Exists?}
    G -->|Yes| H[Mark as Duplicate]
    G -->|No| I[Add to Tracker]
    I --> J[Process Record]
    E --> K[Skip Record]
    H --> K
    J --> L{More Records?}
    K --> L
    L -->|Yes| C
    L -->|No| M[End Session]
    M --> N[Clear Tracker]
```

## 5. Cleanup Script Operations

```mermaid
graph TD
    A[Start Cleanup] --> B[Scan All Records]
    B --> C[Group by UID]
    C --> D[Find Violations]
    D --> E{Violations Found?}
    E -->|No| F[No Action Needed]
    E -->|Yes| G[Analyze Each Violation]
    
    G --> H[Sort by Newest ID]
    H --> I[Keep First Record]
    I --> J[Mark Others as Old]
    J --> K{Dry Run Mode?}
    K -->|Yes| L[Show What Would Change]
    K -->|No| M[Execute Changes]
    
    L --> N[Present Results]
    M --> O[Update Database]
    O --> P[Log Actions]
    P --> Q[Generate Report]
    F --> Q
    N --> Q
```

## 6. ICS Removal Detection

```mermaid
graph TD
    A[Process ICS Feed] --> B[Build Existing Map]
    B --> C[Build Current Map]
    C --> D[Find Missing Keys]
    D --> E{Missing Events Found?}
    E -->|No| F[No Removals]
    E -->|Yes| G[Check Each Missing]
    
    G --> H{Checkout Date Past?}
    H -->|Yes| I[Skip - Historical]
    H -->|No| J{Duplicate Detected?}
    J -->|Yes| K[Skip - Protected]
    J -->|No| L[Mark as Removed]
    
    I --> M{More Missing?}
    K --> M
    L --> N[Update Status]
    N --> M
    M -->|Yes| G
    M -->|No| O[Process Complete]
    F --> O
```

## 7. Orphaned Record Detection

```mermaid
graph LR
    A[Start Orphan Scan] --> B[Get Active Feeds]
    B --> C[Get All ICS Records]
    C --> D[Check Each Record]
    D --> E{Feed Still Active?}
    E -->|Yes| F[Record OK]
    E -->|No| G{Grace Period Expired?}
    G -->|No| H[Still Protected]
    G -->|Yes| I[Mark as Orphaned]
    
    F --> J{More Records?}
    H --> J
    I --> K[Queue for Cleanup]
    K --> J
    J -->|Yes| D
    J -->|No| L[Generate Orphan Report]
```

## 8. Complete State Machine

```mermaid
stateDiagram-v2
    [*] --> NewRecord
    NewRecord --> UIDExtraction
    UIDExtraction --> DuplicateCheck
    DuplicateCheck --> NoDuplicate: Not Found
    DuplicateCheck --> ExactDuplicate: UID Match
    DuplicateCheck --> PropertyDateDuplicate: Property+Date Match
    
    NoDuplicate --> RecordCreated
    
    ExactDuplicate --> ConflictAnalysis
    ConflictAnalysis --> KeepExisting: Existing Better
    ConflictAnalysis --> KeepNew: New Better
    ConflictAnalysis --> ManualReview: Unclear
    
    PropertyDateDuplicate --> DuplicateSkipped
    
    KeepExisting --> MarkNewOld
    KeepNew --> MarkExistingOld
    
    MarkNewOld --> RecordCreated
    MarkExistingOld --> RecordCreated
    
    DuplicateSkipped --> ProcessComplete
    ManualReview --> ProcessComplete
    RecordCreated --> ProcessComplete
    
    ProcessComplete --> [*]
    
    note right of ConflictAnalysis
        Factors:
        - Data completeness
        - Recency
        - Source authority
        - Quality score
    end note
```

## Key Visual Elements Explained

### Decision Flow Colors (when rendered)
- **Green**: Successful processing paths
- **Red**: Error or conflict states  
- **Yellow**: Warning/attention needed
- **Blue**: Normal process flow
- **Purple**: Manual intervention required

### Shape Meanings
- **Diamond**: Decision points requiring logic evaluation
- **Rectangle**: Process steps or actions
- **Rounded Rectangle**: Start/end points
- **Hexagon**: Database operations
- **Circle**: State transitions

### Flow Patterns
- **Parallel Flows**: Concurrent processing paths
- **Loop Backs**: Retry or batch processing
- **Branch Points**: Multiple possible outcomes
- **Merge Points**: Convergence of different paths

## Integration Points Highlighted

### 1. Database Integration
- Read existing records for comparison
- Write new records with proper status
- Update status changes with audit trails
- Query for cleanup and analysis operations

### 2. Source System Integration
- CSV file parsing and UID extraction
- ICS feed processing and composite UID creation
- Multi-system duplicate detection
- Source authority hierarchy enforcement

### 3. User Interface Integration
- Manual review queue for complex conflicts
- Cleanup script execution with dry-run options
- Status change reporting and audit trails
- Error notification and escalation procedures

### 4. Monitoring Integration
- Duplicate detection rate tracking
- Cleanup operation success metrics
- Performance monitoring for large batches
- Alert generation for unusual patterns

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Diagram Count**: 8
**Related**: BusinessLogicAtoZ.md, SYSTEM_LOGICAL_FLOW.md