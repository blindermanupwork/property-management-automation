# API Server - Mermaid Flow Diagrams

## Overview
Visual representations of the API Server's core workflows, including job creation, schedule management, webhook processing, and environment routing.

## 1. Main API Request Flow

```mermaid
graph TD
    A[Incoming Request] --> B{Environment Route?}
    B -->|/api/dev/*| C[Development Config]
    B -->|/api/prod/*| D[Production Config]
    
    C --> E[Authentication Check]
    D --> E
    
    E -->|Valid API Key| F[Route Handler]
    E -->|Invalid/Missing| G[401 Unauthorized]
    
    F --> H{Endpoint Type?}
    H -->|Jobs| I[Job Handler]
    H -->|Schedules| J[Schedule Handler]
    H -->|Webhooks| K[Webhook Handler]
    H -->|Health| L[Health Check]
    
    I --> M[Process Request]
    J --> M
    K --> M
    
    M -->|Success| N[200 Response]
    M -->|Error| O[Error Response]
    
    style C fill:#e1f5fe
    style D fill:#fff3e0
    style G fill:#ffcdd2
    style N fill:#c8e6c9
    style O fill:#ffcdd2
```

## 2. Job Creation Workflow

```mermaid
graph TD
    A[Create Job Request] --> B[Load Reservation]
    B --> C{Required Fields?}
    
    C -->|Missing| D[400 Bad Request]
    C -->|Valid| E[Load Property]
    
    E --> F{HCP IDs Present?}
    F -->|No| G[422 Unprocessable]
    F -->|Yes| H[Generate Service Line]
    
    H --> I[Check Stay Length]
    I -->|>=14 days| J[Add Long Term Flag]
    I -->|<14 days| K[Check Next Entry]
    
    J --> K
    K -->|Block Found| L[Add Owner Arriving]
    K -->|Reservation/None| M[Standard Service]
    
    L --> N[Create HCP Job]
    M --> N
    
    N --> O[Apply Line Items]
    O --> P[Update Airtable]
    P --> Q[Return Success]
    
    style D fill:#ffcdd2
    style G fill:#ffcdd2
    style J fill:#fff9c4
    style L fill:#fff9c4
    style Q fill:#c8e6c9
```

## 3. Schedule Management Flow

```mermaid
graph TD
    A[Schedule Update Request] --> B[Parse Service Time]
    B --> C{Valid Format?}
    
    C -->|Invalid| D[400 Bad Request]
    C -->|Valid HH:MM AM/PM| E[Load Job Details]
    
    E --> F{Appointment Exists?}
    F -->|No| G[Create Appointment]
    F -->|Yes| H[Compare Times]
    
    H --> I{Times Match?}
    I -->|Yes| J[No Update Needed]
    I -->|No| K[Update Appointment]
    
    G --> L[Set Schedule]
    K --> L
    
    L --> M[Update Sync Fields]
    M --> N[Return Status]
    
    style D fill:#ffcdd2
    style J fill:#fff9c4
    style N fill:#c8e6c9
```

## 4. Webhook Processing Flow

```mermaid
graph TD
    A[Webhook Receipt] --> B{Signature Valid?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D[Parse Event]
    
    D --> E{Event Type?}
    E -->|job.updated| F[Job Update Handler]
    E -->|job.completed| G[Completion Handler]
    E -->|appointment.updated| H[Schedule Handler]
    E -->|unknown| I[Log & Ignore]
    
    F --> J[Find Reservation]
    G --> J
    H --> J
    
    J --> K{Found?}
    K -->|No| L[Log Error]
    K -->|Yes| M[Update Fields]
    
    M --> N[Map Status]
    N --> O[Update Assignee]
    O --> P[Log in Sync Details]
    P --> Q[200 OK]
    
    style C fill:#ffcdd2
    style L fill:#fff3e0
    style Q fill:#c8e6c9
```

## 5. Service Line Generation Logic

```mermaid
graph TD
    A[Start Generation] --> B{Custom Instructions?}
    B -->|Yes| C[Add Instructions]
    B -->|No| D{Owner Arriving?}
    
    C --> E[Truncate to 200]
    E --> D
    
    D -->|Yes| F[Add OWNER ARRIVING]
    D -->|No| G{Long Term Guest?}
    
    F --> G
    G -->|Yes >=14 days| H[Add LONG TERM FLAG]
    G -->|No| I[Base Service Name]
    
    H --> I
    I --> J{Next Guest Known?}
    
    J -->|Yes| K[Add Next Guest Date]
    J -->|No| L[Add Unknown]
    
    K --> M[Combine All Parts]
    L --> M
    
    M --> N[Final Truncation]
    N --> O[Return Service Line]
    
    style C fill:#e3f2fd
    style F fill:#fff9c4
    style H fill:#fff9c4
    style O fill:#c8e6c9
```

## 6. Environment Configuration Flow

```mermaid
graph TD
    A[Request Path] --> B{Extract Environment}
    B -->|/api/dev/*| C[Dev Environment]
    B -->|/api/prod/*| D[Prod Environment]
    
    C --> E[Load Dev Config]
    D --> F[Load Prod Config]
    
    E --> G[Dev Airtable Base]
    E --> H[Dev HCP Account]
    E --> I[Dev Job Types]
    
    F --> J[Prod Airtable Base]
    F --> K[Prod HCP Account]
    F --> L[Prod Job Types]
    
    G --> M[Process Request]
    H --> M
    I --> M
    
    J --> M
    K --> M
    L --> M
    
    style C fill:#e1f5fe
    style D fill:#fff3e0
    style M fill:#f5f5f5
```

## 7. Error Handling Cascade

```mermaid
graph TD
    A[Error Occurs] --> B{Error Type?}
    
    B -->|Validation| C[400 Bad Request]
    B -->|Auth| D[401 Unauthorized]
    B -->|Not Found| E[404 Not Found]
    B -->|Business Logic| F[422 Unprocessable]
    B -->|External API| G[502 Bad Gateway]
    B -->|Unexpected| H[500 Internal Error]
    
    C --> I[Clear Message]
    D --> I
    E --> I
    F --> I
    
    G --> J[Retry Logic]
    J -->|Success| K[Continue]
    J -->|Fail| L[Return Error]
    
    H --> M[Log Full Stack]
    M --> N[Generic Message]
    
    I --> O[Log Error]
    L --> O
    N --> O
    
    O --> P[Return Response]
    
    style C fill:#ffcdd2
    style D fill:#ffcdd2
    style E fill:#ffcdd2
    style F fill:#ffcdd2
    style G fill:#ffcdd2
    style H fill:#ffcdd2
```

## 8. Status Synchronization Flow

```mermaid
graph TD
    A[Sync Request] --> B[Fetch HCP Job]
    B --> C[Fetch Airtable Record]
    
    C --> D{Compare Status}
    D -->|Different| E[Map HCP to Airtable]
    D -->|Same| F{Compare Schedule}
    
    E --> G[Update Status Field]
    
    F -->|Different Date| H[Flag Wrong Date]
    F -->|Different Time| I[Flag Wrong Time]
    F -->|Match| J[Mark Synced]
    
    H --> K[Update Sync Fields]
    I --> K
    J --> K
    G --> K
    
    K --> L[Log Sync Details]
    L --> M[Update Timestamp]
    M --> N[Return Result]
    
    style H fill:#fff3e0
    style I fill:#fff3e0
    style J fill:#c8e6c9
    style N fill:#c8e6c9
```

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Related**: BusinessLogicAtoZ.md, SYSTEM_LOGICAL_FLOW.md, README.md