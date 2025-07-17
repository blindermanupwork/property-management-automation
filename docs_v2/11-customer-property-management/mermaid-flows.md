# Customer & Property Management - Visual Workflow Diagrams

## Overview
This document contains Mermaid diagrams visualizing the customer and property management workflows, including property data consolidation, customer relationship management, owner detection algorithms, service assignments, and HousecallPro integration processes.

## 1. Property Data Consolidation Flow

```mermaid
graph TD
    A[Multiple Data Sources] --> B[Manual Admin Updates]
    A --> C[Evolve Property Scraping]
    A --> D[CSV Email Processing]
    A --> E[ICS Calendar Feeds]
    A --> F[System Defaults]
    
    B --> G[Priority 1 - Highest]
    C --> H[Priority 2 - Automated]
    D --> I[Priority 3 - Frequent]
    E --> J[Priority 4 - Calendar]
    F --> K[Priority 5 - Fallback]
    
    G --> L[Consolidation Engine]
    H --> L
    I --> L
    J --> L
    K --> L
    
    L --> M[Field-by-Field Analysis]
    M --> N[Apply Highest Priority]
    N --> O[Track Data Source]
    O --> P[Record Timestamp]
    P --> Q[Consolidated Property Record]
```

## 2. Customer Relationship Management Process

```mermaid
graph TD
    A[Property Record] --> B[Check Customer Link]
    B --> C{Customer Linked?}
    C -->|No| D[Manual Assignment Required]
    C -->|Yes| E[Extract Customer Record ID]
    
    E --> F[Fetch Customer Record]
    F --> G{Record Found?}
    G -->|No| H[Customer Link Error]
    G -->|Yes| I[Extract HCP Customer ID]
    
    I --> J{HCP ID Present?}
    J -->|No| K[Customer Configuration Error]
    J -->|Yes| L[Validate Customer Name]
    
    L --> M[Collect Contact Info]
    M --> N[Verify Account Status]
    N --> O{Valid Customer?}
    O -->|No| P[Customer Validation Failed]
    O -->|Yes| Q[Customer Relationship Established]
    
    D --> R[Admin Workflow]
    H --> R
    K --> R
    P --> R
```

## 3. Owner Arrival Detection Algorithm

```mermaid
graph TD
    A[Guest Checkout Completed] --> B[Extract Property & Date]
    B --> C[Query Future Property Entries]
    C --> D[Filter Active Blocks Only]
    D --> E{Blocks Found?}
    E -->|No| F[No Owner Arrival]
    E -->|Yes| G[Sort by Check-in Date]
    
    G --> H[Analyze First Block]
    H --> I[Calculate Days Between]
    I --> J{Days <= 1?}
    J -->|No| K[Block Too Far Out]
    J -->|Yes| L[Owner Arriving Detected]
    
    L --> M[Set Owner Arrival Flag]
    M --> N[Update Service Line Flags]
    N --> O[Trigger Special Service]
    
    F --> P[Standard Service Process]
    K --> P
    
    O --> Q[Owner Preparation Service]
    P --> R[Standard Turnover Service]
```

## 4. Property-Based Service Assignment

```mermaid
graph LR
    A[Reservation Created] --> B[Analyze Entry Type]
    B --> C{Entry Type?}
    C -->|Reservation| D[Standard Guest Service]
    C -->|Block| E[Owner/Maintenance Service]
    
    D --> F[Determine Service Type]
    E --> G[Detect Block Purpose]
    
    F --> H{Service Type?}
    H -->|Turnover| I[Use Turnover Template]
    H -->|Return Laundry| J[Use Laundry Template] 
    H -->|Inspection| K[Use Inspection Template]
    H -->|Other| L[Default to Turnover]
    
    G --> M{Block Type?}
    M -->|Owner Arrival| N[Owner Arrival Service]
    M -->|Maintenance| O[Maintenance Service]
    M -->|Other| P[Standard Block Service]
    
    I --> Q[Generate Service Name]
    J --> Q
    K --> Q
    L --> Q
    N --> Q
    O --> Q
    P --> Q
```

## 5. HCP Address Validation Process

```mermaid
graph TD
    A[Property Record] --> B[Extract HCP Address ID]
    B --> C{Address ID Present?}
    C -->|No| D[Address Configuration Error]
    C -->|Yes| E[Query HCP API]
    
    E --> F{API Success?}
    F -->|No| G[Address Lookup Failed]
    F -->|Yes| H[Validate Address Customer]
    
    H --> I{Customer Match?}
    I -->|No| J[Customer Mismatch Error]
    I -->|Yes| K[Check Address Details]
    
    K --> L[Compare Property Name]
    L --> M{Reasonable Match?}
    M -->|Low Confidence| N[Flag for Review]
    M -->|Good Match| O[Address Validated]
    
    D --> P[Property Setup Required]
    G --> P
    J --> P
    N --> Q[Manual Verification]
    O --> R[Proceed with Job Creation]
```

## 6. Service Template Configuration Management

```mermaid
graph TD
    A[Service Type Determined] --> B{Service Type?}
    B -->|Turnover| C[Check Turnover Template]
    B -->|Return Laundry| D[Check Laundry Template]
    B -->|Inspection| E[Check Inspection Template]
    B -->|Deep Clean| F[Use Turnover Template]
    B -->|Initial Service| G[Use Turnover Template]
    
    C --> H{Template Found?}
    D --> I{Template Found?}
    E --> J{Template Found?}
    F --> H
    G --> H
    
    H -->|No| K[Turnover Template Missing]
    H -->|Yes| L[Template Validated]
    I -->|No| M[Laundry Template Missing]
    I -->|Yes| L
    J -->|No| N[Inspection Template Missing]
    J -->|Yes| L
    
    K --> O[Configuration Error]
    M --> O
    N --> O
    L --> P[Template Ready for Job]
    O --> Q[Admin Setup Required]
```

## 7. Data Quality and Validation Workflow

```mermaid
graph TD
    A[Property Change Detected] --> B[Identify Changed Fields]
    B --> C{Critical Field?}
    C -->|No| D[Standard Update Process]
    C -->|Yes| E[Critical Change Analysis]
    
    E --> F{Field Type?}
    F -->|Customer ID| G[Customer Relationship Impact]
    F -->|Address ID| H[Service Location Impact]
    F -->|Template ID| I[Service Configuration Impact]
    F -->|Status| J[Service Eligibility Impact]
    
    G --> K[Validate New Customer]
    H --> L[Validate New Address]
    I --> M[Validate New Template]
    J --> N[Update Service Eligibility]
    
    K --> O{Validation Success?}
    L --> P{Validation Success?}
    M --> Q{Validation Success?}
    N --> R{Status Valid?}
    
    O -->|No| S[Block Job Creation]
    O -->|Yes| T[Update Successful]
    P -->|No| S
    P -->|Yes| T
    Q -->|No| S
    Q -->|Yes| T
    R -->|No| S
    R -->|Yes| T
    
    D --> T
    S --> U[Error Resolution Required]
    T --> V[Change Applied Successfully]
```

## 8. Error Recovery and Resolution Process

```mermaid
graph TD
    A[Error Detected] --> B{Error Type?}
    B -->|Missing Customer| C[Customer Assignment Workflow]
    B -->|Invalid Address| D[Address Configuration Workflow]
    B -->|Missing Template| E[Template Setup Workflow]
    B -->|Owner Detection| F[Owner Analysis Workflow]
    B -->|Data Conflict| G[Conflict Resolution Workflow]
    
    C --> H[Identify Available Customers]
    D --> I[Verify HCP Address Access]
    E --> J[Configure Required Templates]
    F --> K[Manual Owner Review]
    G --> L[Priority-Based Resolution]
    
    H --> M[Admin Customer Selection]
    I --> N[HCP Admin Address Setup]
    J --> O[HCP Template Configuration]
    K --> P[Override Detection Result]
    L --> Q[Apply Highest Priority Data]
    
    M --> R{Assignment Valid?}
    N --> S{Address Valid?}
    O --> T{Template Valid?}
    P --> U{Override Accepted?}
    Q --> V{Conflict Resolved?}
    
    R -->|No| W[Escalate to Manager]
    R -->|Yes| X[Error Resolved]
    S -->|No| W
    S -->|Yes| X
    T -->|No| W
    T -->|Yes| X
    U -->|No| W
    U -->|Yes| X
    V -->|No| W
    V -->|Yes| X
    
    W --> Y[Manual Intervention Required]
    X --> Z[Resume Normal Processing]
```

## Key Visual Elements Explained

### Flow Direction Patterns
- **Top to Bottom**: Main process flows and decision trees
- **Left to Right**: Sequential processing steps
- **Circular**: Validation and retry loops
- **Branching**: Multiple outcome scenarios and error paths

### Component Color Coding (when rendered)
- **Green**: Successful processing and validation
- **Red**: Error conditions and failures
- **Yellow**: Warning states and manual review required
- **Blue**: Normal operational processing
- **Purple**: Administrative intervention needed

### Shape Significance
- **Rectangles**: Process steps and operations
- **Diamonds**: Decision points and validations
- **Rounded Rectangles**: Start/end points and states
- **Hexagons**: Database operations and API calls
- **Circles**: State indicators and status markers

## Integration Points Highlighted

### 1. Airtable Integration
- **Property Records**: Central property registry with comprehensive metadata
- **Customer Records**: Customer information and HCP relationship mapping
- **Reservation Records**: Booking data with property and customer associations
- **Status Tracking**: Property and customer relationship status management

### 2. HousecallPro Integration
- **Customer Validation**: Verify customer existence and accessibility
- **Address Management**: Validate service locations and customer associations
- **Template Configuration**: Manage job templates and service configurations
- **Job Creation**: Property-based service assignment and scheduling

### 3. Multi-Source Data Integration
- **Evolve Platform**: Automated property listing and characteristic updates
- **CSV Processing**: Bulk reservation and property data imports
- **ICS Feeds**: Calendar and booking information integration
- **Manual Administration**: Override and correction capabilities

### 4. Error Handling Integration
- **Validation Workflows**: Systematic property and customer validation
- **Recovery Procedures**: Automated error detection and resolution guidance
- **Escalation Paths**: Administrative intervention for complex issues
- **Audit Trails**: Complete change tracking and resolution documentation

## Business Logic Flow Patterns

### Property Lifecycle Management
1. **Data Ingestion**: Multi-source property information collection
2. **Consolidation**: Priority-based data resolution and storage
3. **Validation**: Customer relationship and HCP integration verification
4. **Activation**: Service template configuration and readiness checking
5. **Operation**: Active service assignment and owner detection
6. **Maintenance**: Ongoing validation and relationship management

### Customer Relationship Lifecycle
1. **Discovery**: Property-customer relationship identification
2. **Validation**: Customer record and HCP integration verification
3. **Association**: Property-customer link establishment and validation
4. **Monitoring**: Ongoing relationship status and configuration checking
5. **Maintenance**: Relationship updates and conflict resolution
6. **Resolution**: Error handling and administrative intervention

### Service Assignment Lifecycle
1. **Context Analysis**: Reservation type and property characteristic evaluation
2. **Template Selection**: Service type to HCP template mapping
3. **Name Generation**: Descriptive service name creation with context
4. **Validation**: Template availability and configuration verification
5. **Assignment**: Service type and template assignment to reservation
6. **Delivery**: Job creation and service execution preparation

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Diagram Count**: 8
**Related**: BusinessLogicAtoZ.md, SYSTEM_LOGICAL_FLOW.md