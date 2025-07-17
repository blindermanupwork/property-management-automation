# Service Line Management - Visual Workflow Diagrams

## Overview
This document contains Mermaid diagrams visualizing the service line management workflows, including custom instruction processing, flag detection, service line assembly, and HousecallPro integration.

## 1. Main Service Line Assembly Flow

```mermaid
graph TD
    A[Reservation Data] --> B[Extract Custom Instructions]
    B --> C{Has Custom Instructions?}
    C -->|Yes| D[Process & Validate UTF-8]
    C -->|No| E[Skip Custom Component]
    D --> F[Check Character Length]
    F --> G{Length > 200 chars?}
    G -->|Yes| H[Smart Truncation]
    G -->|No| I[Keep Full Text]
    H --> J[Add to Components]
    I --> J
    E --> K[Detect Special Flags]
    J --> K
    K --> L[Check Owner Arriving]
    L --> M[Check Long-Term Guest]
    M --> N[Generate Base Service Name]
    N --> O[Assemble Components]
    O --> P[Apply Final Validation]
    P --> Q[Service Line Complete]
```

## 2. Custom Instructions Processing

```mermaid
graph LR
    A[User Input] --> B[Receive UTF-8 Text]
    B --> C[Normalize Whitespace]
    C --> D{Empty After Trim?}
    D -->|Yes| E[Set to Null]
    D -->|No| F[Validate Unicode]
    F --> G{Valid Encoding?}
    G -->|No| H[Convert Problem Chars]
    G -->|Yes| I[Check Length]
    H --> I
    I --> J{Length > 200?}
    J -->|Yes| K[Find Word Boundary]
    J -->|No| L[Keep Full Text]
    K --> M[Truncate at Boundary]
    M --> N[Add Ellipsis]
    N --> O[Store Processed Text]
    L --> O
    E --> P[Skip Component]
```

## 3. Special Flag Detection Workflow

```mermaid
graph TD
    A[Analyze Reservation] --> B[Check Owner Arrival]
    B --> C[Query Future Blocks]
    C --> D{Blocks Found?}
    D -->|No| E[No Owner Flag]
    D -->|Yes| F[Check Block Timing]
    F --> G{Within 0-1 Days?}
    G -->|No| E
    G -->|Yes| H[Set Owner Flag]
    
    A --> I[Check Long-Term Stay]
    I --> J[Calculate Duration]
    J --> K{Duration >= 14 Days?}
    K -->|No| L[No Long-Term Flag]
    K -->|Yes| M{Owner Arriving?}
    M -->|Yes| N[Skip Long-Term]
    M -->|No| O[Set Long-Term Flag]
    
    A --> P[Check Same-Day Turnover]
    P --> Q[Find Next Reservation]
    Q --> R{Same Day Check-in?}
    R -->|No| S[No Same-Day]
    R -->|Yes| T[Set Same-Day Prefix]
```

## 4. Hierarchical Component Assembly

```mermaid
graph TD
    A[Start Assembly] --> B[Initialize Parts Array]
    B --> C{Has Custom Instructions?}
    C -->|Yes| D[Add Custom Text]
    C -->|No| E[Check Flags]
    D --> E
    E --> F{Owner Arriving?}
    F -->|Yes| G[Add OWNER ARRIVING]
    F -->|No| H{Long-Term Guest?}
    G --> H
    H -->|Yes| I[Add LONG TERM GUEST DEPARTING]
    H -->|No| J[Add Base Service Name]
    I --> J
    J --> K[Join with " - " Separator]
    K --> L[Validate Final Length]
    L --> M{Length Acceptable?}
    M -->|Yes| N[Return Service Line]
    M -->|No| O[Apply Emergency Truncation]
    O --> N
```

## 5. Character Limit Enforcement

```mermaid
graph TD
    A[Service Line Input] --> B[Check Primary Limit]
    B --> C{Length > 200?}
    C -->|No| D[Check HCP Limit]
    C -->|Yes| E[Intelligent Truncation]
    
    E --> F[Identify Components]
    F --> G[Calculate Required Space]
    G --> H[Preserve Flags & Base]
    H --> I[Truncate Custom Text]
    I --> J[Reassemble]
    
    D --> K{Length > 255?}
    K -->|No| L[Accept Service Line]
    K -->|Yes| M[Emergency Truncation]
    M --> N[Hard Cut at 252 chars]
    N --> O[Add Ellipsis]
    
    J --> D
    O --> L
    L --> P[Final Service Line]
```

## 6. HousecallPro Integration Process

```mermaid
graph TD
    A[Service Line Ready] --> B[Prepare HCP Job Data]
    B --> C[Set as First Line Item]
    C --> D[Configure Line Item Properties]
    D --> E[Submit to HCP API]
    E --> F{API Success?}
    F -->|No| G[Check Error Type]
    F -->|Yes| H[Store Job ID]
    
    G --> I{Length Error?}
    I -->|Yes| J[Apply Fallback Truncation]
    I -->|No| K{Rate Limited?}
    K -->|Yes| L[Wait and Retry]
    K -->|No| M[Log Error]
    
    J --> N[Retry with Shorter Line]
    L --> E
    N --> E
    
    H --> O[Job Created Successfully]
    M --> P[Manual Intervention Required]
```

## 7. Environment-Specific Processing

```mermaid
graph LR
    A[Service Line Request] --> B{Environment?}
    B -->|Development| C[Dev Airtable Base]
    B -->|Production| D[Prod Airtable Base]
    
    C --> E[Boris HCP Account]
    D --> F[3rd Party HCP Account]
    
    E --> G[Dev Sync Script]
    F --> H[Prod Sync Script]
    
    G --> I[Dev Job Creation]
    H --> J[Prod Job Creation]
    
    I --> K[Dev Monitoring]
    J --> L[Prod Monitoring]
    
    K --> M[Test Data Validation]
    L --> N[Live Data Processing]
```

## 8. Scheduled Update Flow

```mermaid
graph TD
    A[4-Hour Timer Trigger] --> B[Fetch Active Reservations]
    B --> C[Process Each Reservation]
    C --> D[Re-detect Owner Arrival]
    D --> E[Re-check Long-Term Status]
    E --> F{Flags Changed?}
    F -->|No| G[Skip Update]
    F -->|Yes| H[Rebuild Service Line]
    
    H --> I[Update Airtable Fields]
    I --> J{Has HCP Job?}
    J -->|No| K[Job Not Created Yet]
    J -->|Yes| L[Update HCP Line Item]
    
    L --> M{Update Success?}
    M -->|Yes| N[Log Success]
    M -->|No| O[Retry Logic]
    
    O --> P{Retry Limit?}
    P -->|Not Reached| L
    P -->|Exceeded| Q[Flag for Manual Review]
    
    G --> R{More Reservations?}
    N --> R
    K --> R
    Q --> R
    R -->|Yes| C
    R -->|No| S[Batch Complete]
```

## Key Visual Elements Explained

### Flow Direction Patterns
- **Top to Bottom**: Main process flows
- **Left to Right**: Sub-process details
- **Circular**: Retry and validation loops
- **Branching**: Decision points and alternatives

### Component Color Coding (when rendered)
- **Green**: Successful processing
- **Red**: Error conditions
- **Yellow**: Warning states
- **Blue**: Normal operations
- **Purple**: Manual intervention

### Shape Significance
- **Rectangles**: Process steps
- **Diamonds**: Decision points
- **Rounded Rectangles**: Start/end points
- **Hexagons**: Database operations
- **Circles**: State indicators

## Integration Points Highlighted

### 1. Airtable Integration
- **Read Operations**: Custom instructions, reservation data
- **Write Operations**: Flag updates, processed service lines
- **Field Monitoring**: Change detection for real-time updates
- **Validation**: Data quality checks before processing

### 2. HousecallPro Integration
- **Job Creation**: Service line as first line item name
- **API Limitations**: Character limits and update restrictions
- **Error Handling**: Retry logic and fallback procedures
- **Environment Separation**: Dev vs production account isolation

### 3. User Interface Integration
- **Input Collection**: Custom instruction entry in Airtable
- **Feedback Provision**: Truncation warnings and limitations
- **Manual Override**: Direct HCP editing for post-creation changes
- **Status Reporting**: Update success and failure notifications

### 4. Automation Integration
- **Scheduled Processing**: 4-hour batch updates
- **Event Triggers**: Real-time field change responses
- **Flag Detection**: Automatic owner arrival and long-term analysis
- **Cross-System Synchronization**: Consistent data across platforms

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Diagram Count**: 8
**Related**: BusinessLogicAtoZ.md, SYSTEM_LOGICAL_FLOW.md