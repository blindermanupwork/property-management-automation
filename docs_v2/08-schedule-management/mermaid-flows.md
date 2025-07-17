# Schedule Management - Visual Workflow Diagrams

## Overview
This document contains Mermaid diagrams visualizing the schedule management workflows, including automatic calculation, special case detection, conflict resolution, and synchronization processes.

## 1. Main Schedule Generation Flow

```mermaid
graph TD
    A[New Reservation Created] --> B{Has Check-out Date?}
    B -->|No| C[Set Error State]
    B -->|Yes| D[Load Default Windows]
    D --> E{Property Override?}
    E -->|Yes| F[Apply Property Settings]
    E -->|No| G[Use Standard Windows]
    F --> H[Calculate Base Time]
    G --> H
    H --> I[Check Special Cases]
    I --> J{Same-Day Turnover?}
    J -->|Yes| K[Adjust for Quick Turn]
    J -->|No| L{Long-Term Guest?}
    K --> M[Generate Final Time]
    L -->|Yes| N[Add Extra Hour]
    L -->|No| O{Owner Arriving?}
    N --> O
    O -->|Yes| P[Upgrade Service Level]
    O -->|No| M
    P --> M
    M --> Q[Save to Airtable]
    Q --> R[Trigger HCP Sync]
```

## 2. Same-Day Turnover Detection

```mermaid
graph LR
    A[Current Checkout] --> B[Query Next Reservations]
    B --> C{Found Same Property?}
    C -->|No| D[No Same-Day]
    C -->|Yes| E{Check-in Same Day?}
    E -->|No| D
    E -->|Yes| F[Get Check-in Time]
    F --> G{Before 2 PM?}
    G -->|Yes| H[Mark Urgent]
    G -->|No| I{Before 4 PM?}
    I -->|Yes| J[Mark Standard]
    I -->|No| K[Mark Relaxed]
    H --> L[2 Hour Window]
    J --> M[3 Hour Window]
    K --> N[3 Hour Window]
    L --> O[Flag Same-Day]
    M --> O
    N --> O
```

## 3. Long-Term Guest Detection

```mermaid
graph TD
    A[Reservation Dates] --> B[Calculate Stay Length]
    B --> C{>= 14 Days?}
    C -->|No| D[Standard Service]
    C -->|Yes| E[Mark Long-Term]
    E --> F{>= 30 Days?}
    F -->|Yes| G[Monthly Category]
    F -->|No| H{>= 21 Days?}
    H -->|Yes| I[Extended Category]
    H -->|No| J[Weekly Category]
    G --> K[Add 1.5x Duration]
    I --> L[Add 1 Hour]
    J --> L
    K --> M[Add Special Instructions]
    L --> M
    M --> N[Set LONG TERM Flag]
```

## 4. Owner Arrival Detection

```mermaid
graph TD
    A[Guest Checkout] --> B[Search Future Blocks]
    B --> C{Blocks Found?}
    C -->|No| D[No Owner Arrival]
    C -->|Yes| E[Check Block Dates]
    E --> F{Within 48 Hours?}
    F -->|No| D
    F -->|Yes| G{Same/Next Day?}
    G -->|No| D
    G -->|Yes| H[Confirm Owner Block]
    H --> I{Intervening Reservations?}
    I -->|Yes| D
    I -->|No| J[Set Owner Flag]
    J --> K[Upgrade Service]
    K --> L[Extend Duration]
    L --> M[Add Premium Tasks]
```

## 5. Custom Time Override Process

```mermaid
graph TD
    A[User Enters Custom Time] --> B[Parse Time Format]
    B --> C{Valid Format?}
    C -->|No| D[Show Error Message]
    C -->|Yes| E[Convert to 24-Hour]
    E --> F{Business Hours?}
    F -->|No| G[Suggest Valid Time]
    F -->|Yes| H[Check Conflicts]
    H --> I{Conflicts Found?}
    I -->|Yes| J[Show Conflicts]
    J --> K{Force Override?}
    K -->|No| L[Cancel Update]
    K -->|Yes| M[Apply Override]
    I -->|No| M
    M --> N[Update Airtable]
    N --> O[Sync to HCP]
    O --> P[Log Override]
```

## 6. Schedule Conflict Resolution

```mermaid
graph TD
    A[Proposed Schedule] --> B[Get Property Schedule]
    B --> C[Check Overlaps]
    C --> D{Conflicts?}
    D -->|No| E[Proceed with Schedule]
    D -->|Yes| F[Analyze Conflict Type]
    F --> G{Full Overlap?}
    G -->|Yes| H[Try Earlier Slot]
    G -->|No| I{Partial Overlap?}
    I -->|Yes| J[Adjust Duration]
    I -->|No| K{Resource Conflict?}
    K -->|Yes| L[Assign Alt Cleaner]
    H --> M{Resolution Found?}
    J --> M
    L --> M
    M -->|Yes| N[Apply Resolution]
    M -->|No| O[Escalate to User]
    N --> E
```

## 7. HousecallPro Synchronization

```mermaid
graph TD
    A[Schedule Change] --> B{Has Job ID?}
    B -->|No| C[Skip Sync]
    B -->|Yes| D[Prepare Schedule Data]
    D --> E{Has Appointment?}
    E -->|No| F[Create Appointment]
    E -->|Yes| G[Update Appointment]
    F --> H[API Call Create]
    G --> I[API Call Update]
    H --> J{Success?}
    I --> J
    J -->|Yes| K[Store Appointment ID]
    J -->|No| L{Rate Limited?}
    L -->|Yes| M[Queue for Retry]
    L -->|No| N[Log Error]
    K --> O[Update Sync Status]
    M --> P[Exponential Backoff]
    P --> H
```

## 8. Complete Schedule State Machine

```mermaid
stateDiagram-v2
    [*] --> NewReservation
    NewReservation --> CalculatingSchedule
    CalculatingSchedule --> CheckingConflicts
    CheckingConflicts --> ResolvingConflicts: Conflicts Found
    CheckingConflicts --> ApplyingFlags: No Conflicts
    ResolvingConflicts --> ApplyingFlags: Resolved
    ResolvingConflicts --> ManualIntervention: Cannot Resolve
    ApplyingFlags --> FinalizedSchedule
    FinalizedSchedule --> SyncingToHCP
    SyncingToHCP --> ScheduleActive: Success
    SyncingToHCP --> SyncError: Failed
    SyncError --> RetrySync: Retryable
    SyncError --> ManualIntervention: Not Retryable
    RetrySync --> SyncingToHCP
    ScheduleActive --> CustomOverride: User Override
    CustomOverride --> ValidatingOverride
    ValidatingOverride --> UpdatingSchedule: Valid
    ValidatingOverride --> ScheduleActive: Invalid
    UpdatingSchedule --> SyncingToHCP
    ScheduleActive --> ServiceCompleted: Job Done
    ManualIntervention --> ScheduleActive: Resolved
    ServiceCompleted --> [*]
```

## Key Visual Elements Explained

### Color Coding (when rendered)
- **Green**: Successful paths
- **Red**: Error states
- **Yellow**: Warning/attention needed
- **Blue**: Normal process flow

### Decision Points
- **Diamond shapes**: Logic branches
- **Rectangles**: Process steps
- **Rounded rectangles**: Start/end points

### Flow Direction
- **Top to bottom**: Main process flow
- **Left to right**: Sub-processes
- **Loops**: Retry mechanisms

## Integration Points Highlighted

1. **Airtable Integration**
   - Read reservation data
   - Save calculated times
   - Update flags and status

2. **HousecallPro Integration**
   - Create appointments
   - Update schedules
   - Handle sync errors

3. **User Interface**
   - Custom time input
   - Conflict resolution
   - Override confirmations

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Diagram Count**: 8
**Related**: BusinessLogicAtoZ.md, SYSTEM_LOGICAL_FLOW.md