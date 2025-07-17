# Customer & Property Management - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Customer & Property Management system, including property data models, customer relationships, owner detection algorithms, service assignments, and HousecallPro integration patterns.

## Core Business Purpose

The Customer & Property Management system maintains the complex relationships between physical properties, property owners (who receive services), guests (who stay at properties), and service assignments. It handles multi-source property data integration and sophisticated owner detection logic for automated service scheduling.

## Business Workflows

### 1. Property Data Model and Structure

#### **Core Property Entity Architecture**
**Airtable Properties Table Structure**:
```javascript
const propertySchema = {
    'Property Name': 'String',               // Human-readable property identifier
    'Property ID': 'Auto-generated',         // Unique Airtable property identifier
    'HCP Customer ID': 'Linked Record',      // Link to Customers table record
    'HCP Address ID': 'String',              // Direct HousecallPro address identifier
    'Turnover Job Template ID': 'String',    // HCP template for standard turnovers
    'Return Laundry Job Template ID': 'String', // HCP template for laundry returns
    'Inspection Job Template ID': 'String',  // HCP template for inspections
    'Property Type': 'Single Select',        // STR, LTR, Commercial, etc.
    'Service Specifications': 'Long Text',   // Special cleaning requirements
    'Amenities': 'Multiple Select',          // Pool, hot tub, pets allowed, etc.
    'Access Instructions': 'Long Text',      // Entry codes, key locations
    'Property Status': 'Single Select'       // Active, Inactive, Maintenance
};
```

#### **Property-Customer Relationship Mapping**
**Business Logic for Customer Association**:
```python
# Property to Customer mapping algorithm
def map_property_to_customer(property_record):
    # Properties link to Customers table through linked records
    customer_links = property_record.get('HCP Customer ID', [])
    
    if not customer_links:
        return {
            'status': 'error',
            'message': 'Property missing customer assignment',
            'action_required': 'Assign property to customer in Airtable'
        }
    
    # Get customer record from linked field
    customer_record_id = customer_links[0]
    customer_record = fetch_customer_record(customer_record_id)
    
    # Extract actual HCP Customer ID from customer record
    hcp_customer_id = customer_record.get('HCP Customer ID')
    
    if not hcp_customer_id:
        return {
            'status': 'error', 
            'message': 'Customer record missing HCP Customer ID',
            'action_required': 'Update customer record with HCP ID'
        }
    
    return {
        'status': 'success',
        'hcp_customer_id': hcp_customer_id,
        'customer_name': customer_record.get('Customer Name'),
        'property_address': property_record.get('Property Name')
    }
```

### 2. Customer Relationship Management

#### **Customer vs Guest Distinction**
**Business Roles Definition**:
```javascript
const roleDefinitions = {
    'customer': {
        'description': 'Property owner who receives cleaning services',
        'hcp_role': 'Pays for services, receives invoices',
        'airtable_storage': 'Customers table with HCP Customer ID',
        'job_assignment': 'Services performed at their properties',
        'communication': 'Service notifications and scheduling updates'
    },
    'guest': {
        'description': 'Temporary occupant of property for vacation/business',
        'hcp_role': 'No direct relationship with service provider',
        'airtable_storage': 'Guest Name field in Reservations table',
        'job_assignment': 'No direct service relationship',
        'communication': 'Property access and checkout instructions only'
    }
};
```

#### **HCP Customer ID Resolution Process**
**Multi-Step Validation Logic**:
```javascript
async function resolveHCPCustomerID(propertyRecord) {
    // Step 1: Extract customer link from property
    const customerLinks = propertyRecord.fields['HCP Customer ID'] || [];
    
    if (!customerLinks.length) {
        throw new ValidationError('Property missing customer assignment');
    }
    
    // Step 2: Handle linked record reference  
    const customerRecordId = typeof customerLinks[0] === 'object' 
        ? customerLinks[0].id 
        : customerLinks[0];
    
    // Step 3: Fetch actual customer record
    try {
        const customerRecord = await base('Customers').find(customerRecordId);
        
        // Step 4: Extract HCP Customer ID from customer record
        const hcpCustomerId = customerRecord.fields['HCP Customer ID'];
        
        if (!hcpCustomerId) {
            throw new ValidationError('Customer record missing HCP Customer ID');
        }
        
        return {
            airtableCustomerId: customerRecordId,
            hcpCustomerId: hcpCustomerId,
            customerName: customerRecord.fields['Customer Name'],
            validation: 'success'
        };
        
    } catch (error) {
        throw new ValidationError(`Customer record lookup failed: ${error.message}`);
    }
}
```

### 3. Owner vs Guest Management

#### **Owner Arrival Detection Algorithm**
**Core Business Logic for Identifying Owner Returns**:
```python
def detect_owner_arrival(reservation, all_property_records):
    """
    Detects when property owner is returning after guest checkout.
    Business Rule: Block checking in 0-1 days after guest checkout = Owner Arriving
    """
    checkout_date = reservation.get('Check-out Date')
    property_id = get_property_id(reservation)
    
    if not checkout_date or not property_id:
        return {
            'owner_arriving': False,
            'reason': 'Missing checkout date or property ID'
        }
    
    checkout_datetime = parse_datetime(checkout_date)
    
    # Find all blocks at same property after checkout
    future_blocks = []
    for record in all_property_records:
        # Skip if same record or not a block
        if (record['id'] == reservation['id'] or 
            record.get('Entry Type') != 'Block'):
            continue
            
        # Skip if different property
        if get_property_id(record) != property_id:
            continue
            
        # Skip inactive blocks
        if record.get('Status') in ['Old', 'Removed', 'Cancelled']:
            continue
            
        # Collect future blocks
        block_checkin = record.get('Check-in Date')
        if block_checkin:
            block_datetime = parse_datetime(block_checkin)
            if block_datetime >= checkout_datetime:
                future_blocks.append({
                    'checkin_date': block_datetime,
                    'days_after_checkout': calculate_days_between(
                        checkout_datetime, block_datetime
                    ),
                    'record': record
                })
    
    # Sort by check-in date and find first block
    future_blocks.sort(key=lambda x: x['checkin_date'])
    
    for block in future_blocks:
        # Owner arriving rule: block starts within 1 day of checkout
        if block['days_after_checkout'] <= 1:
            return {
                'owner_arriving': True,
                'arrival_date': block['checkin_date'],
                'days_between': block['days_after_checkout'],
                'block_record_id': block['record']['id']
            }
        else:
            # First block is too far out, owner not arriving immediately
            return {
                'owner_arriving': False,
                'reason': f"Next block is {block['days_after_checkout']} days later"
            }
    
    return {
        'owner_arriving': False,
        'reason': 'No blocks found after checkout'
    }
```

#### **Next Entry Detection and Classification**
**Business Logic for Determining Next Property Occupant**:
```javascript
function findNextEntry(propertyId, checkoutDate, allRecords) {
    // Filter for next reservations AND blocks at same property
    const futureEntries = allRecords.filter(record => {
        // Skip self
        if (record.id === currentRecordId) return false;
        
        // Only reservations and blocks
        const entryType = record.getCellValue("Entry Type")?.name;
        if (!entryType || !["Reservation", "Block"].includes(entryType)) return false;
        
        // Skip inactive entries
        const status = record.getCellValue("Status")?.name;
        if (status === "Old") return false;
        
        // Same property only
        if (!isSameProperty(record, propertyId)) return false;
        
        // Must check in on or after checkout date
        const checkinDate = record.getCellValue("Check-in Date");
        if (!checkinDate || new Date(checkinDate) < new Date(checkoutDate)) return false;
        
        return true;
    });
    
    // Sort by check-in date (earliest first)
    futureEntries.sort((a, b) => {
        const dateA = new Date(a.getCellValue("Check-in Date"));
        const dateB = new Date(b.getCellValue("Check-in Date"));
        return dateA - dateB;
    });
    
    if (futureEntries.length === 0) return null;
    
    const nextEntry = futureEntries[0];
    const nextEntryType = nextEntry.getCellValue("Entry Type")?.name;
    const nextCheckinDate = nextEntry.getCellValue("Check-in Date");
    
    // Calculate timing relationship
    const checkoutDateObj = new Date(checkoutDate);
    const nextCheckinDateObj = new Date(nextCheckinDate);
    const daysBetween = Math.floor(
        (nextCheckinDateObj - checkoutDateObj) / (1000 * 60 * 60 * 24)
    );
    
    return {
        record: nextEntry,
        entryType: nextEntryType,
        checkinDate: nextCheckinDate,
        daysBetween: daysBetween,
        isOwnerArriving: nextEntryType === "Block" && daysBetween <= 1,
        isSameDayTurnover: daysBetween === 0 && nextEntryType === "Reservation"
    };
}
```

### 4. Property-Based Service Logic

#### **Service Type and Template Assignment**
**Business Rules for Service Mapping**:
```javascript
function determineServiceTemplate(serviceType, propertyRecord) {
    // Service type normalization for template selection
    const templateMapping = {
        'Turnover': 'Turnover Job Template ID',
        'Initial Service': 'Turnover Job Template ID',  // Uses turnover template
        'Deep Clean': 'Turnover Job Template ID',       // Uses turnover template
        'Return Laundry': 'Return Laundry Job Template ID',
        'Inspection': 'Inspection Job Template ID'
    };
    
    // Normalize service type for template lookup
    let templateKey;
    if (serviceType === 'Return Laundry') {
        templateKey = 'Return Laundry Job Template ID';
    } else if (serviceType === 'Inspection') {
        templateKey = 'Inspection Job Template ID';
    } else {
        // All other service types use Turnover template
        templateKey = 'Turnover Job Template ID';
    }
    
    const templateId = propertyRecord.fields[templateKey];
    
    if (!templateId) {
        throw new ServiceConfigurationError(
            `Property missing ${templateKey.replace(' ID', '')} configuration`
        );
    }
    
    return {
        templateId: templateId,
        templateType: templateKey.replace(' Job Template ID', ''),
        originalServiceType: serviceType,
        normalizedServiceType: templateKey.includes('Turnover') ? 'Turnover' : 
                             templateKey.includes('Return Laundry') ? 'Return Laundry' : 'Inspection'
    };
}
```

#### **Property-Specific Service Name Generation**
**Business Logic for Service Naming with Property Context**:
```javascript
function generatePropertyServiceName(reservation, propertyContext) {
    const serviceType = reservation.fields['Service Type'];
    const checkoutDate = reservation.fields['Check-out Date'];
    const propertyId = reservation.fields['Property ID'];
    
    // Handle same-day turnover scenarios
    if (propertyContext.isSameDayTurnover) {
        return `SAME DAY ${serviceType} STR`;
    }
    
    // Standard service naming with next entry context
    if (serviceType === 'Turnover' && checkoutDate) {
        const nextEntry = findNextEntry(propertyId, checkoutDate, allRecords);
        
        if (nextEntry) {
            const nextDate = formatServiceDate(nextEntry.checkinDate);
            
            if (nextEntry.isOwnerArriving) {
                return `OWNER ARRIVING ${serviceType} STR ${nextDate}`;
            } else {
                return `${serviceType} STR Next Guest ${nextDate}`;
            }
        } else {
            return `${serviceType} STR Next Guest Unknown`;
        }
    }
    
    // Non-turnover services
    return `${serviceType} STR`;
}

function formatServiceDate(dateString) {
    // Convert to Arizona timezone for consistent service naming
    const date = new Date(dateString + 'T12:00:00-07:00');
    const month = date.toLocaleString('en-US', { 
        month: 'long', 
        timeZone: 'America/Phoenix' 
    });
    const day = parseInt(date.toLocaleDateString('en-US', { 
        day: 'numeric', 
        timeZone: 'America/Phoenix' 
    }));
    
    return `${month} ${day}`;
}
```

### 5. Property Data Validation and Quality

#### **Required Field Validation Rules**
**Comprehensive Property Validation Logic**:
```javascript
function validatePropertyForJobCreation(propertyRecord) {
    const validationResults = {
        valid: true,
        errors: [],
        warnings: [],
        requiredActions: []
    };
    
    // Validate basic property information
    if (!propertyRecord.fields['Property Name']) {
        validationResults.errors.push('Property missing name');
        validationResults.valid = false;
    }
    
    // Validate HCP Customer relationship
    const customerLinks = propertyRecord.fields['HCP Customer ID'];
    if (!customerLinks || customerLinks.length === 0) {
        validationResults.errors.push('Property not assigned to customer');
        validationResults.requiredActions.push('Link property to customer record');
        validationResults.valid = false;
    }
    
    // Validate HCP Address ID
    const addressId = propertyRecord.fields['HCP Address ID'];
    if (!addressId) {
        validationResults.errors.push('Property missing HCP Address ID');
        validationResults.requiredActions.push('Set HCP Address ID in property record');
        validationResults.valid = false;
    }
    
    // Validate service templates
    const requiredTemplates = [
        'Turnover Job Template ID',
        'Return Laundry Job Template ID', 
        'Inspection Job Template ID'
    ];
    
    requiredTemplates.forEach(templateField => {
        if (!propertyRecord.fields[templateField]) {
            validationResults.warnings.push(`Missing ${templateField.replace(' ID', '')}`);
            validationResults.requiredActions.push(`Configure ${templateField.replace(' Job Template ID', '')} template`);
        }
    });
    
    // Validate property status
    const propertyStatus = propertyRecord.fields['Property Status'];
    if (propertyStatus === 'Inactive') {
        validationResults.warnings.push('Property marked as inactive');
    }
    
    return validationResults;
}
```

#### **Property Entry Type and Service Type Detection**
**Automated Classification from Source Data**:
```python
# Entry type detection from CSV imports
ENTRY_TYPE_KEYWORDS = {
    'maintenance': 'Block',
    'owner': 'Block',
    'block': 'Block',
    'blocked': 'Block'
}
DEFAULT_ENTRY_TYPE = "Reservation"

def detect_entry_type(description, guest_name, notes):
    """Detect if entry is reservation or block based on data patterns"""
    combined_text = f"{description} {guest_name} {notes}".lower()
    
    for keyword, entry_type in ENTRY_TYPE_KEYWORDS.items():
        if keyword in combined_text:
            return entry_type
    
    return DEFAULT_ENTRY_TYPE

# Service type detection 
SERVICE_TYPE_KEYWORDS = {
    'owner arrival': 'Owner Arrival',
    'owner stay': 'Owner Arrival', 
    'owner arriving': 'Owner Arrival',
    'inspection': 'Inspection',
    'deep clean': 'Deep Clean',
    'initial': 'Initial Service'
}
DEFAULT_SERVICE_TYPE = "Turnover"

def detect_service_type(description, entry_type):
    """Determine appropriate service type based on entry characteristics"""
    if entry_type == 'Block':
        # Blocks get special service type detection
        description_lower = description.lower()
        for keyword, service_type in SERVICE_TYPE_KEYWORDS.items():
            if keyword in description_lower:
                return service_type
        return "Owner Arrival"  # Default for blocks
    else:
        # Reservations default to Turnover unless specified
        description_lower = description.lower()
        for keyword, service_type in SERVICE_TYPE_KEYWORDS.items():
            if keyword in description_lower:
                return service_type
        return DEFAULT_SERVICE_TYPE
```

### 6. HCP Integration Address Management

#### **Address Validation and Mapping**
**Business Logic for HCP Address Synchronization**:
```javascript
async function validateHCPAddressMapping(propertyRecord, hcpCustomerId) {
    const hcpAddressId = propertyRecord.fields['HCP Address ID'];
    
    if (!hcpAddressId) {
        // Property missing HCP address - needs manual setup
        return {
            valid: false,
            error: 'Property missing HCP Address ID',
            action: 'Create address in HCP and update property record',
            severity: 'critical'
        };
    }
    
    try {
        // Verify address exists in HCP and belongs to customer
        const hcpAddress = await hcpAPI.getAddress(hcpAddressId);
        
        if (hcpAddress.customer_id !== hcpCustomerId) {
            return {
                valid: false,
                error: 'HCP Address belongs to different customer',
                action: 'Verify customer-address relationship in HCP',
                severity: 'critical'
            };
        }
        
        return {
            valid: true,
            hcpAddress: hcpAddress,
            propertyName: propertyRecord.fields['Property Name'],
            addressMatch: addressMatchesProperty(hcpAddress, propertyRecord)
        };
        
    } catch (error) {
        return {
            valid: false,
            error: `HCP Address lookup failed: ${error.message}`,
            action: 'Verify HCP Address ID exists and is accessible',
            severity: 'critical'
        };
    }
}

function addressMatchesProperty(hcpAddress, propertyRecord) {
    // Basic address validation - could be enhanced
    const propertyName = propertyRecord.fields['Property Name'];
    const hcpAddressLine = hcpAddress.street;
    
    // Simple check for address components in property name
    const addressComponents = hcpAddressLine.split(' ');
    const hasMatchingComponent = addressComponents.some(component => 
        propertyName.toLowerCase().includes(component.toLowerCase())
    );
    
    return {
        hasMatch: hasMatchingComponent,
        propertyName: propertyName,
        hcpAddress: hcpAddressLine,
        confidence: hasMatchingComponent ? 'medium' : 'low'
    };
}
```

### 7. Multi-Source Property Data Integration

#### **Data Source Priority and Reconciliation**
**Business Logic for Handling Multiple Property Data Sources**:
```javascript
const dataSourcePriority = {
    'manual': 1,        // Highest priority - admin overrides
    'evolve': 2,        // Automated scraping - current and accurate  
    'csv': 3,           // Email imports - frequent updates
    'ics': 4,           // Calendar feeds - booking focused
    'default': 5        // System defaults - lowest priority
};

function reconcilePropertyData(propertyId, dataSources) {
    const consolidatedData = {};
    
    // Sort sources by priority (lowest number = highest priority)
    const sortedSources = Object.entries(dataSources).sort((a, b) => {
        const priorityA = dataSourcePriority[a[0]] || dataSourcePriority.default;
        const priorityB = dataSourcePriority[b[0]] || dataSourcePriority.default;
        return priorityA - priorityB;
    });
    
    // Apply data from lowest to highest priority (highest overwrites)
    sortedSources.reverse().forEach(([source, data]) => {
        Object.keys(data).forEach(field => {
            if (data[field] !== null && data[field] !== undefined) {
                consolidatedData[field] = {
                    value: data[field],
                    source: source,
                    priority: dataSourcePriority[source],
                    lastUpdated: new Date().toISOString()
                };
            }
        });
    });
    
    return {
        propertyId: propertyId,
        consolidatedFields: consolidatedData,
        sourcesUsed: sortedSources.map(([source]) => source),
        conflictResolution: 'priority-based-overwrite'
    };
}
```

#### **Property Change Detection and Propagation**
**Business Logic for Handling Property Updates**:
```javascript
function detectPropertyChanges(previousState, currentState) {
    const changes = {
        modified: [],
        added: [],
        removed: [],
        criticalChanges: []
    };
    
    // Detect field changes
    Object.keys(currentState).forEach(field => {
        const oldValue = previousState[field];
        const newValue = currentState[field];
        
        if (oldValue !== newValue) {
            const changeRecord = {
                field: field,
                oldValue: oldValue,
                newValue: newValue,
                timestamp: new Date().toISOString()
            };
            
            changes.modified.push(changeRecord);
            
            // Identify critical changes requiring immediate action
            if (isCriticalPropertyField(field)) {
                changes.criticalChanges.push({
                    ...changeRecord,
                    impact: describeCriticalImpact(field, oldValue, newValue),
                    requiredActions: getRequiredActions(field, newValue)
                });
            }
        }
    });
    
    return changes;
}

function isCriticalPropertyField(fieldName) {
    const criticalFields = [
        'HCP Customer ID',
        'HCP Address ID', 
        'Property Status',
        'Turnover Job Template ID',
        'Property Name'
    ];
    
    return criticalFields.includes(fieldName);
}

function describeCriticalImpact(field, oldValue, newValue) {
    switch (field) {
        case 'HCP Customer ID':
            return 'Job creation will use different customer - affects billing';
        case 'HCP Address ID':
            return 'Jobs will be created at different address - affects service location';
        case 'Property Status':
            return newValue === 'Inactive' ? 
                'Property deactivated - no new jobs will be created' :
                'Property reactivated - job creation resumed';
        case 'Turnover Job Template ID':
            return 'New jobs will use different service template - affects service configuration';
        default:
            return 'Property information changed - may affect service delivery';
    }
}
```

## Critical Business Rules

### Property Relationship Rules
1. **Customer Assignment**: Every property must link to exactly one customer record
2. **HCP Integration**: Properties must have valid HCP Address IDs for job creation
3. **Template Configuration**: Properties need service templates for each job type
4. **Status Management**: Inactive properties do not generate jobs

### Owner Detection Rules
1. **Block Timing**: Blocks checking in 0-1 days after checkout = Owner Arriving
2. **Same Property**: Owner detection only applies within same property
3. **Active Blocks**: Only active blocks (not Old/Removed status) considered
4. **First Block**: Only the first future block determines owner arrival

### Service Assignment Rules
1. **Template Mapping**: Service types map to specific HCP job templates
2. **Turnover Default**: Most service types use Turnover template unless specified
3. **Next Guest Logic**: Turnover services include next guest information
4. **Same-Day Priority**: Same-day turnovers get special "SAME DAY" prefix

### Data Quality Rules
1. **Source Priority**: Manual > Evolve > CSV > ICS > Default
2. **Critical Fields**: Customer ID, Address ID, Templates are mandatory
3. **Change Detection**: Critical field changes trigger validation workflows
4. **Error Handling**: Missing data defaults to safe fallbacks

### Validation Requirements
1. **Job Creation**: Full property validation before HCP job creation
2. **Address Verification**: HCP addresses must belong to assigned customer
3. **Template Availability**: Required templates must exist for service types
4. **Status Checking**: Property must be active for job creation

## Error Handling Patterns

### Property Validation Errors
- Missing customer assignment requires manual property linking
- Invalid HCP Address ID needs address creation/correction
- Missing templates require HCP template configuration

### Owner Detection Errors
- Missing checkout dates default to no owner detection
- Property ID issues skip owner analysis
- Invalid date formats use safe parsing with fallbacks

### Data Integration Errors
- Source conflicts resolved by priority system
- Missing data filled from lower priority sources
- Validation failures trigger manual review workflows

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Customer & Property Management business logic
**Primary Code**: Property relationship handlers and validation systems