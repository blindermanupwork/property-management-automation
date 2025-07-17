# Service Line Management - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Service Line Management system, including custom instructions, special flag generation, Unicode support, character limit enforcement, and HousecallPro integration.

## Core Business Purpose

The Service Line Management system creates descriptive, informative service line descriptions that appear as the first line item name in HousecallPro jobs. It combines user-defined custom instructions with automatically-generated flags to provide cleaners with comprehensive service information.

## Business Workflows

### 1. Service Line Construction Hierarchy

#### **Hierarchical Assembly Process**
**Order of Precedence** (first to last in output):
```javascript
// 1. Custom Instructions (user-defined, max 200 chars)
// 2. Special Flags (system-generated)
// 3. Base Service Name (automatically generated)

function buildServiceLine(reservation) {
    const parts = [];
    
    // Add custom instructions if present
    const customInstructions = getCustomInstructions(reservation);
    if (customInstructions && customInstructions.trim()) {
        parts.push(truncateCustomInstructions(customInstructions, 200));
    }
    
    // Add system flags in priority order
    if (reservation.isOwnerArriving) {
        parts.push("OWNER ARRIVING");
    }
    
    if (reservation.isLongTermGuest && !reservation.isNextEntryBlock) {
        parts.push("LONG TERM GUEST DEPARTING");
    }
    
    // Add base service name
    const baseServiceName = generateBaseServiceName(reservation);
    parts.push(baseServiceName);
    
    // Join with separators
    return parts.join(" - ");
}
```

#### **Final Format Examples**:
```
// Simple turnover
"Turnover STR Next Guest July 3"

// With custom instructions
"Extra towels needed - Turnover STR Next Guest July 3"

// With owner arriving
"Check all amenities working - OWNER ARRIVING - Turnover STR Next Guest July 3"

// Complex combination
"Deep clean all surfaces - OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 3"
```

### 2. Custom Instructions Processing

#### **Input Validation and Processing**
**Field**: "Custom Service Line Instructions" in Airtable
**Business Logic**:
```javascript
function processCustomInstructions(rawInstructions) {
    // Handle null/undefined inputs
    if (!rawInstructions) {
        return null;
    }
    
    // Clean whitespace
    const cleaned = rawInstructions.trim();
    if (cleaned === "") {
        return null;
    }
    
    // Apply character limit (200 chars for HCP compatibility)
    const maxLength = 200;
    if (cleaned.length > maxLength) {
        // Smart truncation at word boundary
        const truncated = cleaned.substring(0, maxLength - 3);
        const lastSpace = truncated.lastIndexOf(' ');
        
        if (lastSpace > maxLength * 0.8) {
            // Truncate at last word boundary if reasonable
            return truncated.substring(0, lastSpace) + '...';
        } else {
            // Hard truncation if no good word boundary
            return truncated + '...';
        }
    }
    
    return cleaned;
}
```

#### **Unicode Character Support**
**Full UTF-8 Support** across all components:
```javascript
// Supported character types
const supportedUnicode = {
    'accents': 'café, naïve, piñata, Zürich',
    'emojis': '🧹 ✅ 🏠 💧 (cleaning-related)',
    'symbols': '• → ★ € $ £ ¥',
    'international': 'José, François, Müller, 中文'
};

// Character counting for Unicode
function getUnicodeLength(text) {
    // Use proper Unicode-aware length calculation
    return [...text].length; // Not text.length which counts bytes
}
```

### 3. Special Flag Generation

#### **Owner Arriving Detection**
**Trigger**: Property owner block starts 0-1 days after guest checkout
**Business Logic**:
```javascript
function detectOwnerArrival(reservation, allRecords) {
    const checkoutDate = new Date(reservation.checkoutDate);
    const propertyId = reservation.propertyId;
    
    // Search for blocks within 48 hours after checkout
    const searchStart = checkoutDate;
    const searchEnd = new Date(checkoutDate);
    searchEnd.setDate(searchEnd.getDate() + 2);
    
    const blocks = allRecords.filter(record => {
        return record.propertyId === propertyId &&
               record.entryType === 'Block' &&
               record.checkinDate >= searchStart &&
               record.checkinDate <= searchEnd;
    });
    
    // Check if any block starts 0-1 days after checkout
    const ownerBlock = blocks.find(block => {
        const blockCheckin = new Date(block.checkinDate);
        const daysDiff = (blockCheckin - checkoutDate) / (24 * 60 * 60 * 1000);
        return daysDiff >= 0 && daysDiff <= 1;
    });
    
    return {
        ownerArriving: !!ownerBlock,
        arrivalDate: ownerBlock ? ownerBlock.checkinDate : null,
        blockId: ownerBlock ? ownerBlock.id : null
    };
}
```

#### **Long-Term Guest Detection**
**Trigger**: Stay duration of 14+ consecutive days
**Business Logic**:
```javascript
function detectLongTermGuest(reservation) {
    const checkinDate = new Date(reservation.checkinDate);
    const checkoutDate = new Date(reservation.checkoutDate);
    
    // Calculate stay duration in days
    const millisecondsPerDay = 24 * 60 * 60 * 1000;
    const stayDurationDays = Math.floor(
        (checkoutDate - checkinDate) / millisecondsPerDay
    );
    
    const analysis = {
        duration: stayDurationDays,
        isLongTerm: stayDurationDays >= 14,
        category: categorizeStay(stayDurationDays)
    };
    
    // Special rule: Don't add flag if next entry is owner block
    if (analysis.isLongTerm && !reservation.isNextEntryBlock) {
        analysis.addFlag = true;
    } else {
        analysis.addFlag = false;
        analysis.skipReason = reservation.isNextEntryBlock ? 
            'Owner arriving takes precedence' : 
            'Stay duration below threshold';
    }
    
    return analysis;
}

function categorizeStay(days) {
    if (days >= 30) return 'monthly';
    if (days >= 21) return 'extended';
    if (days >= 14) return 'long-term';
    if (days >= 7) return 'weekly';
    return 'standard';
}
```

#### **Same-Day Turnover Prefix**
**Trigger**: Next guest checks in same day as current checkout
**Business Logic**:
```javascript
function detectSameDayTurnover(reservation, allReservations) {
    const checkoutDate = reservation.checkoutDate;
    const propertyId = reservation.propertyId;
    
    // Find next reservation at same property
    const nextReservations = allReservations.filter(res => {
        return res.propertyId === propertyId &&
               res.checkinDate === checkoutDate &&
               res.entryType === 'Reservation' &&
               res.status !== 'Old' &&
               res.id !== reservation.id;
    });
    
    if (nextReservations.length > 0) {
        const nextGuest = nextReservations[0];
        return {
            isSameDay: true,
            nextGuestId: nextGuest.id,
            nextGuestName: nextGuest.guestName,
            checkinTime: nextGuest.checkinTime || '4:00 PM'
        };
    }
    
    return { isSameDay: false };
}
```

### 4. Base Service Name Generation

#### **Service Type Processing**
**Business Logic**:
```javascript
function generateBaseServiceName(reservation) {
    // Get service type (preserves whatever is set in Airtable)
    const serviceType = reservation.serviceType || 'Turnover';
    
    // Get next guest date for naming
    const nextGuestDate = determineNextGuestDate(reservation);
    
    // Handle same-day scenarios
    if (reservation.isSameDayTurnover) {
        return `SAME DAY ${serviceType} STR`;
    }
    
    // Standard service naming
    if (nextGuestDate && nextGuestDate !== 'Unknown') {
        const formattedDate = formatDateForService(nextGuestDate);
        return `${serviceType} STR Next Guest ${formattedDate}`;
    } else {
        return `${serviceType} STR Next Guest Unknown`;
    }
}
```

#### **Next Guest Date Logic**
**Priority Order**:
```javascript
function determineNextGuestDate(reservation) {
    // 1. Use pre-populated field if available
    if (reservation.nextGuestDate) {
        return reservation.nextGuestDate;
    }
    
    // 2. Search for next reservation at same property
    const nextReservation = findNextReservation(
        reservation.propertyId,
        reservation.checkoutDate
    );
    
    if (nextReservation) {
        return nextReservation.checkinDate;
    }
    
    // 3. Default when no next guest found
    return 'Unknown';
}

function formatDateForService(dateString) {
    const date = new Date(dateString);
    const options = { 
        month: 'short', 
        day: 'numeric',
        timeZone: 'America/Phoenix' // Arizona time
    };
    return date.toLocaleDateString('en-US', options);
}
```

### 5. Character Limit Management

#### **HousecallPro API Limits**
**Primary Limit**: 200 characters (internal system)
**Fallback Limit**: 255 characters (HCP API maximum)

```javascript
function enforceCharacterLimits(serviceLine) {
    const primaryLimit = 200;
    const hcpApiLimit = 255;
    
    // Primary truncation during construction
    if (serviceLine.length > primaryLimit) {
        serviceLine = intelligentTruncation(serviceLine, primaryLimit);
    }
    
    // Fallback truncation for HCP API
    if (serviceLine.length > hcpApiLimit) {
        serviceLine = serviceLine.substring(0, hcpApiLimit - 3) + '...';
    }
    
    return serviceLine;
}
```

#### **Intelligent Truncation Algorithm**
**Priority**: Preserve flags and base service name, truncate custom instructions
```javascript
function intelligentTruncation(fullServiceLine, maxLength) {
    const parts = fullServiceLine.split(' - ');
    
    // Identify component types
    const customInstructions = [];
    const systemFlags = [];
    const baseService = [];
    
    parts.forEach(part => {
        if (isSystemFlag(part)) {
            systemFlags.push(part);
        } else if (isBaseService(part)) {
            baseService.push(part);
        } else {
            customInstructions.push(part);
        }
    });
    
    // Calculate required space for flags and base
    const requiredParts = [...systemFlags, ...baseService];
    const requiredLength = requiredParts.join(' - ').length;
    
    // Truncate custom instructions to fit
    const availableSpace = maxLength - requiredLength - 3; // Space for ' - '
    
    if (availableSpace > 0 && customInstructions.length > 0) {
        const customText = customInstructions.join(' - ');
        if (customText.length <= availableSpace) {
            return [customText, ...requiredParts].join(' - ');
        } else {
            const truncated = truncateAtWordBoundary(customText, availableSpace - 3) + '...';
            return [truncated, ...requiredParts].join(' - ');
        }
    }
    
    // Return just required parts if no space for custom
    return requiredParts.join(' - ');
}
```

### 6. HousecallPro Integration

#### **Job Creation Service Line Assignment**
**Process**: Service line becomes first line item name in HCP job
```javascript
function createHCPJobWithServiceLine(reservation, serviceLine) {
    const jobData = {
        customer_id: reservation.hcpCustomerId,
        address_id: reservation.hcpAddressId,
        job_type_id: getJobTypeId(reservation.serviceType),
        line_items: [
            {
                name: serviceLine, // This is where service line appears
                quantity: 1,
                unit_price: 0, // Price set separately
                kind: "labor"
            }
        ],
        schedule: {
            scheduled_start: reservation.finalServiceTime,
            scheduled_end: calculateEndTime(reservation.finalServiceTime),
            arrival_window: 30
        }
    };
    
    return hcpAPI.createJob(jobData);
}
```

#### **Service Line Updates After Job Creation**
**Limitation**: Cannot update custom instructions after job creation
**Workaround**: Must edit directly in HousecallPro interface
```javascript
function updateServiceLinePostCreation(jobId, newServiceLine) {
    // This is NOT possible via API
    // Custom instructions cannot be updated after job creation
    // User must edit in HCP interface directly
    
    return {
        success: false,
        reason: 'HCP API does not support line item name updates',
        workaround: 'Edit job directly in HousecallPro interface'
    };
}
```

### 7. Environment-Specific Processing

#### **Development vs Production Separation**
**Complete Isolation**:
```javascript
const environmentConfig = {
    development: {
        airtableBase: 'app67yWFv0hKdl6jM',
        hcpAccount: 'boris_dev_account',
        syncScript: 'dev-hcp-sync.cjs'
    },
    production: {
        airtableBase: 'appZzebEIqCU5R9ER', 
        hcpAccount: 'third_party_prod',
        syncScript: 'prod-hcp-sync.cjs'
    }
};

function getEnvironmentConfig(env) {
    return environmentConfig[env] || environmentConfig.development;
}
```

### 8. Update Mechanisms and Triggers

#### **Real-Time Updates**
**Job Creation**: Service lines set during initial job creation
```javascript
// During job creation in handlers/jobs.js
const serviceLine = buildServiceLine(reservation);
const hcpJob = createHCPJob(reservation, serviceLine);
```

#### **Scheduled Updates**
**Every 4 Hours**: Via `update-service-lines-enhanced.py`
```python
def update_service_lines_batch():
    # Enhanced updater with owner detection
    reservations = fetch_active_reservations()
    
    for reservation in reservations:
        owner_detection = detect_owner_arrival(reservation)
        long_term_detection = detect_long_term_guest(reservation)
        
        # Update Airtable fields
        update_airtable_flags(reservation.id, owner_detection, long_term_detection)
        
        # Rebuild service line
        new_service_line = build_service_line(reservation)
        
        # Update HCP if job exists
        if reservation.hcp_job_id:
            update_hcp_service_line(reservation.hcp_job_id, new_service_line)
```

#### **Webhook Updates**
**Limited Scope**: Only for significant status changes
```javascript
// Webhook only updates for major status changes
const significantChanges = ['in_progress', 'completed', 'canceled'];

if (significantChanges.includes(webhook.work_status)) {
    updateServiceLineFromWebhook(webhook);
}
```

## Critical Business Rules

### Service Line Construction Rules
1. **Component Order**: Custom → Flags → Base (never changes)
2. **Flag Priority**: OWNER ARRIVING before LONG TERM GUEST DEPARTING
3. **Separator**: Always use " - " between components
4. **Minimum Content**: Base service name always included

### Character Limit Rules
1. **Primary Limit**: 200 characters for internal processing
2. **API Limit**: 255 characters for HCP compatibility
3. **Truncation Priority**: Preserve flags > base > custom instructions
4. **Smart Truncation**: Cut at word boundaries when possible

### Unicode Support Rules
1. **Full Support**: All UTF-8 characters allowed
2. **Character Counting**: Use Unicode-aware length calculation
3. **Encoding**: UTF-8 throughout the system
4. **No Filtering**: No character restrictions or replacements

### Flag Assignment Rules
1. **Owner Arriving**: Block starts 0-1 days after checkout
2. **Long-Term Guest**: Stay duration ≥ 14 days
3. **Mutual Exclusivity**: Owner arriving takes precedence over long-term
4. **Same-Day**: Prefix when next guest same day as checkout

### Update Mechanism Rules
1. **Creation Time**: Service line set during initial job creation
2. **Post-Creation**: Cannot update custom instructions via API
3. **Scheduled Updates**: Automatic flag detection every 4 hours
4. **Manual Override**: Direct HCP interface editing required

## Error Handling Patterns

### Input Validation Errors
- Empty/null custom instructions handled gracefully
- Invalid Unicode sequences converted to safe alternatives
- Excessive length triggers automatic truncation

### API Integration Errors
- HCP API failures trigger retry with exponential backoff
- Service line rejection fallback to base service name only
- Rate limiting handled with queue management

### Data Consistency Errors
- Flag calculation failures default to no flags
- Missing next guest date defaults to "Unknown"
- Service type missing defaults to "Turnover"

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Service Line Management business logic
**Primary Code**: Job creation handlers and sync scripts