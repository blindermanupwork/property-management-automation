# Environment Management - Visual Flow Diagrams

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Visual representations of environment management workflows and system interactions

---

## 📊 **ENVIRONMENT MANAGEMENT FLOW DIAGRAMS**

### 1. **Environment Detection and Configuration Loading Flow**

```mermaid
flowchart TD
    A[System Startup] --> B{ENVIRONMENT Variable Set?}
    B -->|Yes| C[Use Explicit Environment]
    B -->|No| D[Analyze Hostname]
    
    D --> E{Hostname Contains 'prod'?}
    E -->|Yes| F[Set Environment: production]
    E -->|No| G[Set Environment: development]
    
    C --> H{Environment Type?}
    F --> H
    G --> H
    
    H -->|development| I[Instantiate DevConfig]
    H -->|production| J[Instantiate ProdConfig]
    
    I --> K[Load Base Configuration]
    J --> L[Load Base Configuration]
    
    K --> M[Load Main .env File]
    L --> M
    
    M --> N[Load Environment-Specific .env]
    N --> O[Validate Configuration]
    
    O --> P{Validation Success?}
    P -->|Yes| Q[Configuration Ready]
    P -->|No| R[Display Errors & Exit]
    
    Q --> S[Initialize Directory Structure]
    S --> T[Setup Environment-Specific Logging]
    T --> U[Environment Management Ready]
```

### 2. **Project Root Discovery Flow**

```mermaid
flowchart TD
    A[Start Project Root Discovery] --> B[Get Current Working Directory]
    B --> C[Check for setup.py in Current Dir]
    
    C --> D{setup.py Found?}
    D -->|Yes| E[Use Current Directory as Root]
    D -->|No| F[Check Parent Directories]
    
    F --> G[Check Parent for setup.py]
    G --> H{setup.py Found in Parent?}
    H -->|Yes| I[Use Parent as Root]
    H -->|No| J[Continue to Next Parent]
    
    J --> K{More Parents to Check?}
    K -->|Yes| G
    K -->|No| L[Method 1 Failed - Try VERSION File]
    
    L --> M[Check for VERSION File]
    M --> N{VERSION Found?}
    N -->|Yes| O[Use VERSION Directory as Root]
    N -->|No| P[Method 2 Failed - Try .git]
    
    P --> Q[Check for .git Directory]
    Q --> R{.git Found?}
    R -->|Yes| S[Use .git Directory as Root]
    R -->|No| T[Use Current Directory as Root]
    
    E --> U[Project Root Established]
    I --> U
    O --> U
    S --> U
    T --> U
    
    U --> V[Initialize Path Management]
    V --> W[Root Discovery Complete]
```

### 3. **Configuration Validation Flow**

```mermaid
flowchart TD
    A[Configuration Validation Start] --> B{Environment Type?}
    
    B -->|Development| C[Run Development Validation]
    B -->|Production| D[Run Production Validation]
    
    C --> E[Check DEV_AIRTABLE_API_KEY]
    E --> F{API Key Present?}
    F -->|Yes| G[Validate API Key Format]
    F -->|No| H[Add Missing API Key Error]
    
    G --> I{Starts with 'pat'?}
    I -->|Yes| J[Check DEV_AIRTABLE_BASE_ID]
    I -->|No| K[Add Invalid Format Error]
    
    J --> L{Base ID Present?}
    L -->|Yes| M[Validate Base ID Length]
    L -->|No| N[Add Missing Base ID Error]
    
    M --> O{Length = 17 chars?}
    O -->|Yes| P[Development Validation Complete]
    O -->|No| Q[Add Invalid Length Error]
    
    D --> R[Check PROD_AIRTABLE_API_KEY]
    R --> S{API Key Present?}
    S -->|Yes| T[Enhanced Production Validation]
    S -->|No| U[Add Missing API Key Error]
    
    T --> V{Key Length > 50 chars?}
    V -->|Yes| W[Check PROD_HCP_TOKEN]
    V -->|No| X[Add Insufficient Length Error]
    
    W --> Y{HCP Token Present?}
    Y -->|Yes| Z[Production Validation Complete]
    Y -->|No| AA[Add Missing HCP Token Error]
    
    H --> BB[Compile Validation Results]
    K --> BB
    N --> BB
    Q --> BB
    P --> BB
    U --> BB
    X --> BB
    AA --> BB
    Z --> BB
    
    BB --> CC{Any Errors?}
    CC -->|Yes| DD[Return Error List]
    CC -->|No| EE[Return Validation Success]
```

### 4. **Safety Check and Runner Validation Flow**

```mermaid
flowchart TD
    A[Runner Script Execution] --> B[Parse Command Line Arguments]
    B --> C{Script Type?}
    
    C -->|Development Runner| D[Get Current Hostname]
    C -->|Production Runner| E[Get Current Hostname]
    
    D --> F{Force Flag Present?}
    E --> G{Force Flag Present?}
    
    F -->|Yes| H[Skip Safety Checks]
    F -->|No| I[Check Hostname for 'prod']
    
    G -->|Yes| J[Skip Safety Checks]
    G -->|No| K[Check Hostname for 'dev']
    
    I --> L{Contains 'prod' or 'production'?}
    L -->|Yes| M[Display Production Warning]
    L -->|No| N[Proceed with Development Config]
    
    K --> O{Contains 'dev' or 'development'?}
    O -->|Yes| P[Display Development Warning]
    O -->|No| Q[Proceed with Production Config]
    
    M --> R[Exit with Safety Error]
    P --> S[Exit with Safety Error]
    
    H --> T[Load Configuration with Override]
    J --> U[Load Configuration with Override]
    N --> V[Load Development Configuration]
    Q --> W[Load Production Configuration]
    
    T --> X[Validate Configuration]
    U --> X
    V --> X
    W --> X
    
    X --> Y{Configuration Valid?}
    Y -->|Yes| Z[Initialize Controller]
    Y -->|No| AA[Exit with Configuration Error]
    
    R --> BB[Process Exit]
    S --> BB
    AA --> BB
```

### 5. **Directory Structure Initialization Flow**

```mermaid
flowchart TD
    A[Directory Initialization Start] --> B[Get Environment Type]
    B --> C[Calculate Environment-Specific Paths]
    
    C --> D[Generate CSV Process Directory Path]
    D --> E[Generate CSV Done Directory Path]
    E --> F[Generate Logs Directory Path]
    F --> G[Generate Scripts Directory Path]
    
    G --> H[Check CSV Process Directory Exists]
    H --> I{Directory Exists?}
    I -->|Yes| J[Directory Already Present]
    I -->|No| K[Create CSV Process Directory]
    
    K --> L[Set Directory Permissions]
    L --> M[Check CSV Done Directory Exists]
    J --> M
    
    M --> N{Directory Exists?}
    N -->|Yes| O[Directory Already Present]
    N -->|No| P[Create CSV Done Directory]
    
    P --> Q[Set Directory Permissions]
    Q --> R[Check Logs Directory Exists]
    O --> R
    
    R --> S{Directory Exists?}
    S -->|Yes| T[Directory Already Present]
    S -->|No| U[Create Logs Directory]
    
    U --> V[Set Directory Permissions]
    V --> W[Validate All Directories Created]
    T --> W
    
    W --> X{All Directories Valid?}
    X -->|Yes| Y[Directory Initialization Complete]
    X -->|No| Z[Exit with Directory Error]
```

### 6. **Environment-Specific Logging Setup Flow**

```mermaid
flowchart TD
    A[Logging Setup Start] --> B{Environment Type?}
    
    B -->|Development| C[Setup Development Logging]
    B -->|Production| D[Setup Production Logging]
    
    C --> E[Set Log Level: DEBUG]
    E --> F[Create File Handler]
    F --> G[Create Console Handler]
    G --> H[Setup Development Log Format]
    H --> I[Add Timestamp and Module Info]
    I --> J[Configure File: automation_dev_YYYYMMDD.log]
    J --> K[Enable Console Output]
    K --> L[Development Logging Ready]
    
    D --> M[Set Log Level: INFO]
    M --> N[Create File Handler Only]
    N --> O[Setup Production Log Format]
    O --> P[Add Timestamp and Level Info]
    P --> Q[Configure File: automation_prod_YYYYMMDD.log]
    Q --> R[Disable Console Output]
    R --> S[Production Logging Ready]
    
    L --> T[Test Log Configuration]
    S --> T
    
    T --> U[Write Test Log Entry]
    U --> V{Log Entry Successful?}
    V -->|Yes| W[Logging Configuration Complete]
    V -->|No| X[Fix Logging Configuration]
    
    X --> Y[Retry Logging Setup]
    Y --> T
```

### 7. **Webhook Environment Routing Flow**

```mermaid
flowchart TD
    A[Webhook Request Received] --> B[Determine Request Endpoint]
    B --> C{Endpoint Type?}
    
    C -->|/webhooks/hcp-dev| D[Route to Development Handler]
    C -->|/webhooks/hcp| E[Route to Production Handler]
    
    D --> F[Load Development Environment]
    E --> G[Load Production Environment]
    
    F --> H[Set ENVIRONMENT=development]
    G --> I[Set ENVIRONMENT=production]
    
    H --> J[Use Dev Airtable Base]
    I --> K[Use Prod Airtable Base]
    
    J --> L[Create Dev Log Entry]
    K --> M[Create Prod Log Entry]
    
    L --> N[Process with Dev Configuration]
    M --> O[Process with Prod Configuration]
    
    N --> P[Update Dev Database]
    O --> Q[Update Prod Database]
    
    P --> R[Log to webhook_development.log]
    Q --> S[Log to webhook.log]
    
    R --> T[Return Response to Dev Webhook]
    S --> U[Return Response to Prod Webhook]
```

### 8. **Cron Schedule Environment Separation Flow**

```mermaid
flowchart TD
    A[Cron Schedule Setup] --> B{Environment Type?}
    
    B -->|Development| C[Setup Development Schedule]
    B -->|Production| D[Setup Production Schedule]
    
    C --> E[Schedule: Every 4 hours at :10]
    D --> F[Schedule: Every 4 hours at :00]
    
    E --> G[Command: run_automation_dev.py]
    F --> H[Command: run_automation_prod.py]
    
    G --> I[Environment: ENVIRONMENT=development]
    H --> J[Environment: ENVIRONMENT=production]
    
    I --> K[Working Directory: /home/opc/automation]
    J --> L[Working Directory: /home/opc/automation]
    
    K --> M[Dev Cron Entry Created]
    L --> N[Prod Cron Entry Created]
    
    M --> O[Install Development Cron]
    N --> P[Install Production Cron]
    
    O --> Q[Verify Cron Installation]
    P --> Q
    
    Q --> R{Installation Successful?}
    R -->|Yes| S[Cron Scheduling Complete]
    R -->|No| T[Fix Cron Installation]
    
    T --> U[Retry Cron Setup]
    U --> Q
```

### 9. **Configuration Override and Emergency Access Flow**

```mermaid
flowchart TD
    A[Emergency Configuration Need] --> B{Override Type?}
    
    B -->|Force Flag| C[Process Force Override]
    B -->|Environment Variable| D[Process Environment Override]
    B -->|Configuration File| E[Process File Override]
    
    C --> F[Bypass Safety Checks]
    F --> G[Display Override Warning]
    G --> H[Continue with Forced Configuration]
    
    D --> I[Set ENVIRONMENT Variable]
    I --> J[Reload Configuration Singleton]
    J --> K[Validate New Configuration]
    
    E --> L[Load Emergency .env File]
    L --> M[Override Existing Variables]
    M --> N[Validate Emergency Configuration]
    
    H --> O[Execute with Override]
    K --> P{Configuration Valid?}
    N --> P
    
    P -->|Yes| Q[Proceed with Emergency Access]
    P -->|No| R[Display Configuration Errors]
    
    O --> S[Log Override Usage]
    Q --> S
    
    S --> T[Continue Normal Operations]
    R --> U[Fix Configuration Issues]
    
    U --> V[Retry Configuration Loading]
    V --> P
```

### 10. **Cross-Environment Data Isolation Verification Flow**

```mermaid
flowchart TD
    A[Data Isolation Verification Start] --> B[Check Current Environment]
    B --> C{Environment Type?}
    
    C -->|Development| D[Verify Dev Data Paths]
    C -->|Production| E[Verify Prod Data Paths]
    
    D --> F[Check CSV_process_development/]
    F --> G[Check CSV_done_development/]
    G --> H[Check automation_dev_*.log]
    H --> I[Check DEV_AIRTABLE_BASE_ID Usage]
    
    E --> J[Check CSV_process_production/]
    J --> K[Check CSV_done_production/]
    K --> L[Check automation_prod_*.log]
    L --> M[Check PROD_AIRTABLE_BASE_ID Usage]
    
    I --> N[Verify No Production Data Access]
    M --> O[Verify No Development Data Access]
    
    N --> P{Cross-Environment Access Detected?}
    O --> P
    
    P -->|Yes| Q[Log Isolation Violation]
    P -->|No| R[Isolation Verification Passed]
    
    Q --> S[Alert Administrator]
    S --> T[Block Violating Operation]
    T --> U[Fix Isolation Issue]
    
    R --> V[Continue Normal Operations]
    U --> W[Retry Isolation Verification]
    W --> P
```

---

*These diagrams provide comprehensive visual representations of all environment management flows, from basic configuration loading through complex cross-environment isolation verification, ensuring complete understanding of the system's environment separation architecture.*