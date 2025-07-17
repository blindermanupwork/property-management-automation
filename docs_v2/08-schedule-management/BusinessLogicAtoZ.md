# Schedule Management - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Schedule Management system, including automatic schedule generation, same-day turnover detection, long-term guest handling, owner arrival coordination, and custom time overrides.

## Core Business Purpose

The Schedule Management system ensures cleaning services are scheduled at optimal times based on reservation patterns, property requirements, and special circumstances. It automatically detects various scenarios and adjusts service windows accordingly.

## Business Workflows

### 1. Automatic Schedule Generation

#### **Calculate Final Service Time**
**Trigger**: New reservation created or checkout time modified
**Business Logic**:
```javascript
// Standard checkout-based scheduling
function calculateFinalServiceTime(reservation) {
    const checkoutTime = reservation['Check-out Time'] || '11:00 AM';
    const checkoutDate = reservation['Check-out Date'];
    
    // Map checkout times to service windows
    const serviceWindows = {
        '10:00 AM': { start: '11:00 AM', duration: 4 },
        '11:00 AM': { start: '12:00 PM', duration: 4 },
        '12:00 PM': { start: '1:00 PM', duration: 4 },
        '2:00 PM': { start: '3:00 PM', duration: 4 },
        '3:00 PM': { start: '4:00 PM', duration: 3 },
        '4:00 PM': { start: '5:00 PM', duration: 3 }
    };
    
    // Get window or use default
    const window = serviceWindows[checkoutTime] || 
                  serviceWindows['11:00 AM'];
    
    // Combine date and time in MST
    const serviceDateTime = new Date(
        `${checkoutDate}T${convertTo24Hour(window.start)}-07:00`
    );
    
    return serviceDateTime.toISOString();
}
```

#### **Apply Property-Specific Defaults**
**Business Rules**:
- Each property can have custom default service times
- Property defaults override standard windows
- Vacation rentals typically need 3-4 hour windows
- Residential properties may need 2-3 hour windows

**Implementation**:
```javascript
// Check for property overrides
const propertyDefaults = property['Default Service Window'];
if (propertyDefaults) {
    return applyPropertyDefaults(checkoutDate, propertyDefaults);
}
```

### 2. Same-Day Turnover Detection

#### **Identify Back-to-Back Reservations**
**Detection Logic**:
```javascript
function detectSameDayTurnover(currentReservation, allReservations) {
    const checkoutDate = currentReservation['Check-out Date'];
    const propertyId = currentReservation['Property ID'][0];
    
    // Find next reservation at same property
    const nextReservation = allReservations.find(res => {
        return res['Property ID'][0] === propertyId &&
               res['Check-in Date'] === checkoutDate &&
               res['Entry Type'] === 'Reservation' &&
               res['Status'] !== 'Old';
    });
    
    if (nextReservation) {
        // Calculate urgency based on check-in time
        const checkInTime = nextReservation['Check-in Time'] || '4:00 PM';
        const urgencyLevel = calculateUrgency(checkInTime);
        
        return {
            isSameDay: true,
            nextGuestTime: checkInTime,
            urgencyLevel: urgencyLevel
        };
    }
    
    return { isSameDay: false };
}
```

#### **Adjust Service Windows**
**Business Rules**:
```javascript
// Same-day service adjustments
if (sameDayTurnover.isSameDay) {
    const adjustedWindow = {
        'urgent': { start: '10:00 AM', duration: 2 },    // Check-in before 2 PM
        'standard': { start: '11:00 AM', duration: 3 },  // Check-in 2-4 PM
        'relaxed': { start: '12:00 PM', duration: 3 }    // Check-in after 4 PM
    };
    
    const window = adjustedWindow[sameDayTurnover.urgencyLevel];
    
    // Update service name to reflect urgency
    serviceName = `SAME DAY ${baseServiceType} STR`;
}
```

### 3. Long-Term Guest Management

#### **Detect Extended Stays**
**Business Logic**:
```javascript
function calculateStayDuration(checkIn, checkOut) {
    const checkInDate = new Date(checkIn);
    const checkOutDate = new Date(checkOut);
    const millisecondsPerDay = 24 * 60 * 60 * 1000;
    
    const daysDifference = Math.floor(
        (checkOutDate - checkInDate) / millisecondsPerDay
    );
    
    return {
        days: daysDifference,
        isLongTerm: daysDifference >= 14,
        category: daysDifference >= 30 ? 'monthly' : 
                  daysDifference >= 14 ? 'extended' : 
                  daysDifference >= 7 ? 'weekly' : 'standard'
    };
}
```

#### **Apply Long-Term Adjustments**
**Service Modifications**:
```javascript
if (stayDuration.isLongTerm) {
    // Add extra time for deep cleaning
    serviceDuration += 1; // Extra hour
    
    // Add special flag to service name
    serviceFlags.push('LONG TERM GUEST DEPARTING');
    
    // Update service instructions
    serviceInstructions += '\n- Deep clean required after extended stay';
    serviceInstructions += '\n- Check for excessive wear/damage';
    serviceInstructions += '\n- Replace all linens';
    
    // Adjust pricing if applicable
    if (stayDuration.category === 'monthly') {
        serviceMultiplier = 1.5; // 50% surcharge for monthly stays
    }
}
```

### 4. Owner Arrival Detection

#### **Identify Owner Blocks**
**Detection Algorithm**:
```javascript
async function detectOwnerArrival(reservation) {
    const checkoutDate = new Date(reservation['Check-out Date']);
    const propertyId = reservation['Property ID'][0];
    
    // Look for blocks within 48 hours after checkout
    const searchStart = checkoutDate;
    const searchEnd = new Date(checkoutDate);
    searchEnd.setDate(searchEnd.getDate() + 2);
    
    const blocks = await findBlocks({
        propertyId: propertyId,
        checkInStart: searchStart,
        checkInEnd: searchEnd,
        entryType: 'Block'
    });
    
    // Check if any block starts same day or next day
    const ownerBlock = blocks.find(block => {
        const blockCheckIn = new Date(block['Check-in Date']);
        const daysDiff = (blockCheckIn - checkoutDate) / (24*60*60*1000);
        return daysDiff >= 0 && daysDiff <= 1;
    });
    
    return {
        ownerArriving: !!ownerBlock,
        arrivalDate: ownerBlock ? ownerBlock['Check-in Date'] : null,
        arrivalTime: ownerBlock ? ownerBlock['Check-in Time'] : null
    };
}
```

#### **Apply Owner Arrival Settings**
**Enhanced Service Requirements**:
```javascript
if (ownerDetection.ownerArriving) {
    // Upgrade service level
    serviceLevel = 'premium';
    
    // Add owner flag to service name
    serviceFlags.unshift('OWNER ARRIVING'); // Add at beginning
    
    // Extend service window for thorough cleaning
    serviceDuration = Math.max(serviceDuration, 4); // Minimum 4 hours
    
    // Add specific instructions
    ownerInstructions = [
        'Premium clean - owner arriving',
        'Check all appliances functioning',
        'Ensure all personal items removed',
        'Fresh flowers if available',
        'Written status report required'
    ];
    
    // Update Airtable field
    updates['Owner Arriving'] = true;
    updates['Owner Arrival Date'] = ownerDetection.arrivalDate;
}
```

### 5. Custom Time Override Management

#### **Parse Custom Service Time**
**Input Validation**:
```javascript
function parseCustomServiceTime(customTime, serviceDate) {
    // Expected format: "HH:MM AM/PM"
    const timeRegex = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i;
    const match = customTime.trim().match(timeRegex);
    
    if (!match) {
        throw new Error('Invalid time format. Use HH:MM AM/PM');
    }
    
    let hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    const period = match[3].toUpperCase();
    
    // Validate ranges
    if (hours < 1 || hours > 12) {
        throw new Error('Hours must be between 1 and 12');
    }
    if (minutes < 0 || minutes > 59) {
        throw new Error('Minutes must be between 0 and 59');
    }
    
    // Convert to 24-hour format
    if (period === 'PM' && hours !== 12) hours += 12;
    if (period === 'AM' && hours === 12) hours = 0;
    
    // Create datetime in MST
    const customDateTime = new Date(serviceDate);
    customDateTime.setHours(hours, minutes, 0, 0);
    
    return customDateTime;
}
```

#### **Apply Override with Validation**
**Business Logic**:
```javascript
function applyCustomTime(reservation, customTime) {
    const baseDate = reservation['Check-out Date'];
    
    try {
        const customDateTime = parseCustomServiceTime(customTime, baseDate);
        
        // Validate business hours (7 AM - 8 PM)
        const hours = customDateTime.getHours();
        if (hours < 7 || hours >= 20) {
            return {
                success: false,
                error: 'Service must be scheduled between 7 AM and 8 PM'
            };
        }
        
        // Check for conflicts
        const conflicts = checkScheduleConflicts(
            reservation['Property ID'][0],
            customDateTime,
            4 // Default duration
        );
        
        if (conflicts.length > 0) {
            return {
                success: false,
                error: 'Schedule conflict detected',
                conflicts: conflicts
            };
        }
        
        // Apply the override
        return {
            success: true,
            finalServiceTime: customDateTime.toISOString(),
            source: 'custom_override',
            overriddenBy: getCurrentUser(),
            overriddenAt: new Date().toISOString()
        };
        
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}
```

### 6. Schedule Conflict Resolution

#### **Detect Overlapping Services**
**Conflict Detection**:
```javascript
function checkScheduleConflicts(propertyId, proposedStart, duration) {
    const proposedEnd = new Date(proposedStart);
    proposedEnd.setHours(proposedEnd.getHours() + duration);
    
    // Get all scheduled services for the property
    const existingServices = getPropertySchedule(propertyId, 
        proposedStart.toDateString()
    );
    
    const conflicts = existingServices.filter(service => {
        const serviceStart = new Date(service['Scheduled Service Time']);
        const serviceEnd = new Date(serviceStart);
        serviceEnd.setHours(serviceEnd.getHours() + service['Duration']);
        
        // Check for overlap
        return (proposedStart < serviceEnd && proposedEnd > serviceStart);
    });
    
    return conflicts.map(conflict => ({
        reservationId: conflict['Reservation ID'],
        guestName: conflict['Guest Name'],
        scheduledTime: conflict['Scheduled Service Time'],
        overlapMinutes: calculateOverlap(
            proposedStart, proposedEnd,
            conflict.start, conflict.end
        )
    }));
}
```

#### **Automatic Conflict Resolution**
**Resolution Strategies**:
```javascript
function resolveScheduleConflict(conflicts, proposedSchedule) {
    // Strategy 1: Shift earlier if possible
    const earliestStart = new Date(proposedSchedule.date);
    earliestStart.setHours(7, 0, 0, 0); // 7 AM
    
    // Strategy 2: Shift later if needed
    const latestStart = new Date(proposedSchedule.date);
    latestStart.setHours(16, 0, 0, 0); // 4 PM
    
    // Strategy 3: Reduce duration for same-day
    if (proposedSchedule.isSameDay) {
        proposedSchedule.duration = Math.min(proposedSchedule.duration, 3);
    }
    
    // Strategy 4: Assign different cleaner
    if (conflicts.every(c => c.assignedEmployee === proposedSchedule.employee)) {
        proposedSchedule.employee = getAlternateEmployee();
    }
    
    // Strategy 5: Split service across days
    if (proposedSchedule.duration > 4 && !proposedSchedule.isSameDay) {
        return splitServiceAcrossDays(proposedSchedule);
    }
}
```

### 7. Timezone Management

#### **MST/Arizona Time Handling**
**Conversion Logic**:
```javascript
function convertToServiceTimezone(dateTime, fromTimezone = 'UTC') {
    // Arizona doesn't observe DST
    const arizonaOffset = -7; // Always UTC-7
    
    if (fromTimezone === 'UTC') {
        const utcDate = new Date(dateTime);
        const arizonaDate = new Date(
            utcDate.getTime() + (arizonaOffset * 60 * 60 * 1000)
        );
        return arizonaDate;
    }
    
    // Handle other timezone conversions
    return convertTimezone(dateTime, fromTimezone, 'America/Phoenix');
}

// Display formatting
function formatServiceTime(isoDateTime) {
    const serviceTime = convertToServiceTimezone(isoDateTime);
    
    return serviceTime.toLocaleString('en-US', {
        timeZone: 'America/Phoenix',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}
```

### 8. Schedule Synchronization

#### **Push to HousecallPro**
**Sync Process**:
```javascript
async function syncScheduleToHCP(reservation) {
    const jobId = reservation['Service Job ID'];
    const appointmentId = reservation['Service Appointment ID'];
    const finalServiceTime = reservation['Final Service Time'];
    
    if (!jobId) {
        return { error: 'No job created yet' };
    }
    
    const scheduleData = {
        scheduled_start: finalServiceTime,
        scheduled_end: calculateEndTime(finalServiceTime, 4),
        arrival_window: 30, // minutes
        notes: buildScheduleNotes(reservation)
    };
    
    try {
        if (appointmentId) {
            // Update existing appointment
            await updateHCPAppointment(appointmentId, scheduleData);
        } else {
            // Create new appointment
            const newAppointment = await createHCPAppointment(
                jobId, 
                scheduleData
            );
            
            // Store appointment ID
            await updateReservation(reservation.id, {
                'Service Appointment ID': newAppointment.id
            });
        }
        
        return { success: true };
        
    } catch (error) {
        return { 
            error: error.message,
            retry: error.code === 'RATE_LIMIT'
        };
    }
}
```

## Critical Business Rules

### Schedule Generation Rules
1. **Default Window**: 12 PM - 4 PM for 11 AM checkouts
2. **Business Hours**: Services between 7 AM - 8 PM only
3. **Minimum Duration**: 2 hours for any service
4. **Maximum Duration**: 6 hours for deep cleans
5. **Buffer Time**: 30 minutes between services

### Same-Day Turnover Rules
1. **Detection**: Check-in date equals checkout date
2. **Priority**: Highest priority assignment
3. **Duration**: Reduced to enable quick turnover
4. **Assignment**: Best available cleaner
5. **Notification**: Alert sent to operations

### Long-Term Guest Rules
1. **Threshold**: 14+ consecutive days
2. **Service Time**: +1 hour minimum added
3. **Deep Clean**: Required protocols activated
4. **Inspection**: Damage assessment included
5. **Pricing**: May include surcharge

### Owner Arrival Rules
1. **Detection Window**: 0-1 days after checkout
2. **Service Level**: Upgraded to premium
3. **Duration**: Minimum 4 hours
4. **Quality Check**: Manager inspection required
5. **Communication**: Owner notified of status

### Override Rules
1. **Authority**: Managers can override any schedule
2. **Format**: Must use "HH:MM AM/PM" format
3. **Validation**: Must be within business hours
4. **Logging**: All overrides tracked
5. **Sync**: Immediately pushed to HCP

## Schedule State Machine

```
NEW_RESERVATION
    ↓
CALCULATE_SCHEDULE
    ↓
CHECK_CONFLICTS → RESOLVE_CONFLICTS
    ↓
APPLY_SPECIAL_FLAGS (same-day, long-term, owner)
    ↓
FINALIZE_SCHEDULE
    ↓
SYNC_TO_HCP
    ↓
SCHEDULE_ACTIVE
    ↓
[Custom Override?] → VALIDATE_OVERRIDE → UPDATE_SCHEDULE
    ↓
SERVICE_COMPLETED
```

## Error Handling

### Common Errors
1. **Invalid Time Format**: Reject and show example
2. **Outside Business Hours**: Suggest nearest valid time
3. **Schedule Conflict**: Show conflicts and alternatives
4. **Missing Check-out Date**: Cannot calculate without date
5. **Sync Failure**: Retry with exponential backoff

### Error Recovery
1. Log all errors with context
2. Preserve original schedule on failure
3. Queue failed syncs for retry
4. Alert operations on critical failures
5. Provide manual override options

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Schedule Management business logic
**Primary Code**: Multiple integration points across system