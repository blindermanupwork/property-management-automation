# Automation Controller - Visual Flow Diagrams

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Visual representations of automation controller orchestration workflows

---

## 📊 **AUTOMATION CONTROLLER FLOW DIAGRAMS**

### 1. **Main Controller Initialization Flow**

```mermaid
flowchart TD
    A[System Start] --> B{Environment Variable Set?}
    B -->|Yes| C[Load Environment Config]
    B -->|No| D[Detect from Hostname]
    
    D --> E{Hostname Contains 'prod'?}
    E -->|Yes| F[Set Environment: production]
    E -->|No| G[Set Environment: development]
    
    C --> H[Select Config Class]
    F --> H
    G --> H
    
    H --> I{Environment?}
    I -->|development| J[Load DevConfig]
    I -->|production| K[Load ProdConfig]
    
    J --> L[Validate Dev Configuration]
    K --> M[Validate Prod Configuration]
    
    L --> N{Validation Success?}
    M --> N
    
    N -->|Yes| O[Initialize AutomationController]
    N -->|No| P[Exit with Validation Errors]
    
    O --> Q[Setup Environment-Specific Logging]
    Q --> R[Connect to Airtable]
    R --> S[Initialize Automation Mapping]
    S --> T[Controller Ready for Execution]
```

### 2. **Environment Configuration Loading Flow**

```mermaid
flowchart TD
    A[Configuration Loading Start] --> B[Discover Project Root]
    B --> C[Check for setup.py]
    C --> D{setup.py Found?}
    
    D -->|Yes| E[Use setup.py Directory]
    D -->|No| F[Check for VERSION file]
    
    F --> G{VERSION Found?}
    G -->|Yes| H[Use VERSION Directory]
    G -->|No| I[Check for .git]
    
    I --> J{.git Found?}
    J -->|Yes| K[Use .git Directory]
    J -->|No| L[Use Current Directory]
    
    E --> M[Load Main .env File]
    H --> M
    K --> M
    L --> M
    
    M --> N[Load Environment-Specific .env]
    N --> O[Set Up Path Management]
    O --> P[Configure Timezone Handling]
    P --> Q[Initialize Directory Structure]
    Q --> R[Configuration Loading Complete]
```

### 3. **Automation Status Management Flow**

```mermaid
flowchart TD
    A[Automation Execution Request] --> B[Query Airtable Status]
    B --> C{Status Record Exists?}
    
    C -->|Yes| D[Check Active Flag]
    C -->|No| E[Default to Active<br/>(Backward Compatibility)]
    
    D --> F{Is Active?}
    F -->|Yes| G[Update Status to 'Running']
    F -->|No| H[Log Skipped<br/>Return Success]
    
    E --> G
    G --> I[Record Start Timestamp]
    I --> J[Execute Automation Function]
    
    J --> K{Execution Success?}
    K -->|Yes| L[Calculate Execution Time]
    K -->|No| M[Capture Error Details]
    
    L --> N[Extract Statistics from Output]
    M --> O[Format Error Message]
    
    N --> P[Update Status: 'Completed']
    O --> Q[Update Status: 'Failed']
    
    P --> R[Log Success with Statistics]
    Q --> S[Log Failure with Error Details]
    
    H --> T[Return Result]
    R --> T
    S --> T
```

### 4. **Complete Automation Suite Execution Flow**

```mermaid
flowchart TD
    A[Start Automation Suite] --> B[Initialize Execution Tracking]
    B --> C[Begin Sequential Execution]
    
    C --> D[iTrip CSV Gmail]
    D --> E{Success?}
    E -->|Yes| F[Evolve Scraping]
    E -->|No| G[Log Error, Continue]
    
    F --> H{Success?}
    G --> F
    H -->|Yes| I[CSV File Processing]
    H -->|No| J[Log Error, Continue]
    
    I --> K{Success?}
    J --> I
    K -->|Yes| L[ICS Calendar Sync]
    K -->|No| M[Log Error, Continue]
    
    L --> N{Success?}
    M --> L
    N -->|Yes| O[Add Service Jobs]
    N -->|No| P[Log Error, Continue]
    
    O --> Q{Success?}
    P --> O
    Q -->|Yes| R[Sync Service Jobs]
    Q -->|No| S[Log Error, Continue]
    
    R --> T{Success?}
    S --> R
    T -->|Yes| U[Update Service Lines]
    T -->|No| V[Log Error, Continue]
    
    U --> W{Success?}
    V --> U
    W -->|Yes| X[Job Reconciliation]
    W -->|No| Y[Log Error, Continue]
    
    X --> Z[Calculate Total Execution Time]
    Y --> Z
    Z --> AA[Generate Execution Summary]
    AA --> BB[Log Final Results]
```

### 5. **Component Execution Flow**

```mermaid
flowchart TD
    A[Component Execution Start] --> B[Set Environment Variables]
    B --> C[Prepare Subprocess Command]
    C --> D[Start Subprocess with Timeout]
    
    D --> E{Process Completes?}
    E -->|Yes| F[Check Return Code]
    E -->|No| G[Handle Timeout]
    
    F --> H{Return Code = 0?}
    H -->|Yes| I[Parse Standard Output]
    H -->|No| J[Parse Standard Error]
    
    G --> K[Terminate Process]
    K --> L[Log Timeout Error]
    
    I --> M[Extract Statistics]
    J --> N[Extract Error Details]
    L --> O[Return Timeout Error]
    
    M --> P[Format Success Result]
    N --> Q[Format Failure Result]
    
    P --> R[Return Success]
    Q --> S[Return Failure]
    O --> S
```

### 6. **Error Handling and Recovery Flow**

```mermaid
flowchart TD
    A[Error Detected] --> B{Error Level?}
    
    B -->|Configuration| C[Log Configuration Error]
    B -->|Component| D[Log Component Error]
    B -->|System| E[Log System Error]
    
    C --> F[Exit with Error Code]
    D --> G[Continue Suite Execution]
    E --> H[Alert Administrator]
    
    G --> I[Update Component Status: Failed]
    H --> J[Log Critical Error]
    
    I --> K[Check Remaining Components]
    J --> K
    
    K --> L{More Components?}
    L -->|Yes| M[Execute Next Component]
    L -->|No| N[Generate Final Summary]
    
    M --> O[Component Execution]
    O --> K
    
    N --> P[Log Overall Results]
    F --> Q[Process Exit]
    P --> Q
```

### 7. **Environment Safety Validation Flow**

```mermaid
flowchart TD
    A[Runner Execution Start] --> B[Get Current Hostname]
    B --> C{Script Type?}
    
    C -->|Development| D[Check for 'prod' in Hostname]
    C -->|Production| E[Check for 'dev' in Hostname]
    
    D --> F{Contains 'prod'?}
    E --> G{Contains 'dev'?}
    
    F -->|Yes| H[Show Production Warning]
    F -->|No| I[Proceed with Dev Config]
    
    G -->|Yes| J[Show Development Warning]
    G -->|No| K[Proceed with Prod Config]
    
    H --> L{Force Flag Present?}
    J --> M{Force Flag Present?}
    
    L -->|Yes| N[Override Warning, Continue]
    L -->|No| O[Exit with Safety Error]
    
    M -->|Yes| P[Override Warning, Continue]
    M -->|No| Q[Exit with Safety Error]
    
    I --> R[Load Development Configuration]
    K --> S[Load Production Configuration]
    N --> R
    P --> S
    
    R --> T[Validate Configuration]
    S --> U[Validate Configuration]
    
    T --> V{Valid?}
    U --> V
    
    V -->|Yes| W[Initialize Controller]
    V -->|No| X[Exit with Validation Error]
    
    O --> Y[Process Exit]
    Q --> Y
    X --> Y
```

### 8. **Command Line Interface Flow**

```mermaid
flowchart TD
    A[Command Line Execution] --> B[Parse Arguments]
    B --> C{Command Type?}
    
    C -->|--list| D[Display Available Automations]
    C -->|--run <name>| E[Check Specific Automation]
    C -->|--dry-run| F[Show Execution Preview]
    C -->|Default| G[Run Full Suite]
    
    D --> H[Query Automation Status]
    H --> I[Format Status Display]
    I --> J[Exit]
    
    E --> K{Dry Run Flag?}
    K -->|Yes| L[Show What Would Execute]
    K -->|No| M[Execute Specific Automation]
    
    F --> N[List All Automations]
    N --> O[Show Execution Order]
    O --> P[Exit Without Execution]
    
    G --> Q{Dry Run Flag?}
    Q -->|Yes| R[Show Full Suite Preview]
    Q -->|No| S[Execute Full Suite]
    
    L --> T[Exit]
    M --> U[Log Specific Results]
    R --> V[Exit]
    S --> W[Log Suite Results]
    
    U --> T
    W --> T
```

### 9. **Configuration Validation Flow**

```mermaid
flowchart TD
    A[Configuration Validation Start] --> B{Environment Type?}
    
    B -->|Development| C[Validate Dev Settings]
    B -->|Production| D[Validate Prod Settings]
    
    C --> E[Check Airtable API Key Format]
    D --> F[Check Airtable API Key Format]
    
    E --> G[Verify Dev Base ID]
    F --> H[Verify Prod Base ID]
    
    G --> I[Check HCP Token Presence]
    H --> J[Check HCP Token Presence]
    
    I --> K[Validate Webhook Secret]
    J --> L[Enhanced Prod Validation]
    
    K --> M[Compile Validation Results]
    L --> N[Check API Key Length]
    N --> O[Verify Credential Format]
    O --> P[Compile Validation Results]
    
    M --> Q{All Valid?}
    P --> Q
    
    Q -->|Yes| R[Configuration Valid]
    Q -->|No| S[List Validation Errors]
    
    R --> T[Proceed with Execution]
    S --> U[Exit with Error Details]
```

### 10. **Performance Monitoring Flow**

```mermaid
flowchart TD
    A[Execution Start] --> B[Record Start Timestamp]
    B --> C[Initialize Performance Metrics]
    C --> D[Begin Component Execution]
    
    D --> E[Monitor Resource Usage]
    E --> F[Track Component Progress]
    F --> G{Component Complete?}
    
    G -->|Yes| H[Record Component Time]
    G -->|No| I[Check for Timeout]
    
    I --> J{Timeout Exceeded?}
    J -->|Yes| K[Handle Timeout]
    J -->|No| E
    
    H --> L[Calculate Component Metrics]
    K --> M[Record Timeout Event]
    
    L --> N{More Components?}
    M --> N
    
    N -->|Yes| O[Start Next Component]
    N -->|No| P[Calculate Total Metrics]
    
    O --> D
    P --> Q[Generate Performance Report]
    Q --> R[Update Performance Database]
    R --> S[Log Performance Summary]
```

---

*These diagrams provide visual representations of all major automation controller flows, from initialization through execution monitoring, including comprehensive error handling and environment management.*