# HousecallPro Integration - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of HousecallPro integration for service job management, including job creation workflows, status synchronization, webhook processing, and employee scheduling.

## Core Business Purpose

The HousecallPro integration automatically creates and manages cleaning service jobs from Airtable reservations, handles employee scheduling, tracks job status, and maintains real-time synchronization between the property management system and service management platform.

## Business Workflows

### 1. Job Creation Process

#### **"Create Job & Sync Status" Button Action**
**UI Location**: Airtable Reservations table
**Prerequisites**: 
- Record must have complete address and guest information
- Property must have valid HCP Customer ID
- Entry Type must be "Reservation"
- No existing HCP Job ID

**Business Logic**:
1. **Data Validation**:
   ```javascript
   function validateJobCreation(reservation) {
       const errors = [];
       
       if (!reservation['Guest Name']) {
           errors.push('Guest Name required');
       }
       
       if (!reservation['Property'] || !reservation['Property']['HCP Customer ID']) {
           errors.push('Property must have HCP Customer ID');
       }
       
       if (reservation['HCP Job ID']) {
           errors.push('Job already exists');
       }
       
       if (reservation['Entry Type'] !== 'Reservation') {
           errors.push('Only reservations can create jobs');
       }
       
       return errors;
   }
   ```

2. **Customer Management**:
   ```javascript
   async function findOrCreateCustomer(reservation) {
       // Try to find existing customer
       let customer = await findHCPCustomer({
           name: reservation['Guest Name'],
           email: reservation['Email'],
           phone: reservation['Phone']
       });
       
       if (!customer) {
           // Create new customer
           customer = await createHCPCustomer({
               name: reservation['Guest Name'],
               email: reservation['Email'],
               phone: reservation['Phone'],
               address: reservation['Property']['Address']
           });
       }
       
       return customer;
   }
   ```

3. **Job Creation**:
   ```javascript
   const jobData = {
       customer_id: customer.id,
       address_id: property.hcp_customer_id,
       job_type_id: process.env.HCP_JOB_TYPE_ID,
       work_status: 'needs_scheduling',
       scheduled_start: calculateServiceDateTime(reservation),
       scheduled_end: calculateServiceEndTime(reservation),
       description: generateJobDescription(reservation),
       tags: generateJobTags(reservation)
   };
   
   const job = await hcpAPI.createJob(jobData);
   ```

### 2. Service Line Construction

#### **Service Line Name Assembly**
**Field Used**: "Service Line Custom Instructions" in Airtable
**Character Limit**: 200 characters maximum for HCP compatibility

**Construction Logic**:
```javascript
function buildServiceLineName(reservation) {
    let parts = [];
    
    // 1. Custom Instructions (highest priority)
    if (reservation['Service Line Custom Instructions']) {
        let instructions = reservation['Service Line Custom Instructions'];
        if (instructions.length > 200) {
            instructions = instructions.substring(0, 197) + '...';
        }
        parts.push(instructions);
    }
    
    // 2. Special Flags
    if (reservation['Owner Arriving']) {
        parts.push('OWNER ARRIVING');
    }
    
    if (reservation['Long Term Guest']) {
        parts.push('LONG TERM GUEST DEPARTING');
    }
    
    // 3. Base Service Name
    const nextGuestDate = calculateNextGuestDate(reservation);
    const baseService = `Turnover STR Next Guest ${nextGuestDate}`;
    parts.push(baseService);
    
    // Join with ' - ' separator and truncate if needed
    let fullName = parts.join(' - ');
    if (fullName.length > 200) {
        fullName = fullName.substring(0, 197) + '...';
    }
    
    return fullName;
}
```

**Example Service Line Names**:
- `Custom cleaning notes - OWNER ARRIVING - Turnover STR Next Guest July 15`
- `Extra deep clean needed - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 20`
- `Turnover STR Next Guest July 10` (standard case)

### 3. Long-Term Guest Detection

#### **Automatic Flag Setting**
**Business Rule**: Stay duration ≥ 14 days = Long Term Guest

**Detection Logic**:
```javascript
function checkLongTermGuest(reservation) {
    const checkinDate = new Date(reservation['Check-in Date']);
    const checkoutDate = new Date(reservation['Check-out Date']);
    const stayDuration = Math.ceil((checkoutDate - checkinDate) / (1000 * 60 * 60 * 24));
    
    if (stayDuration >= 14) {
        // Auto-set field in Airtable
        return {
            'Long Term Guest': true,
            'Stay Duration': stayDuration
        };
    }
    
    return {};
}
```

**Service Impact**:
- Adds "LONG TERM GUEST DEPARTING" to service line
- May trigger additional cleaning requirements
- Alerts cleaners to expect more intensive work

### 4. Owner Arrival Detection

#### **Detection Algorithm**
**Business Rule**: Block entry checking in same day or next day after reservation checkout

**Detection Logic**:
```python
def detect_owner_arrival(reservation_id, checkout_date, property_id):
    # Look for Block entries at same property
    blocks = airtable.get_all('Reservations', formula=
        f"AND(
            {{Entry Type}} = 'Block',
            {{Property ID}} = '{property_id}',
            {{Check-in Date}} >= '{checkout_date}',
            {{Check-in Date}} <= '{checkout_date + timedelta(days=1)}'
        )"
    )
    
    if blocks:
        # Owner arriving - update reservation
        airtable.update(reservation_id, {
            'Owner Arriving': True,
            'Owner Block ID': blocks[0]['id']
        })
        return True
    
    return False
```

### 5. Schedule Management

#### **"Add/Update Schedule" Button Action**
**UI Location**: Airtable Reservations table
**Prerequisites**: Valid HCP Job ID must exist

**Time Calculation Logic**:
```javascript
function calculateServiceTimes(reservation) {
    // Use Custom Service Time if provided, otherwise Service Time
    const serviceTime = reservation['Custom Service Time'] || reservation['Service Time'] || '10:00 AM';
    const serviceDate = reservation['Service Date'] || reservation['Check-out Date'];
    
    // Convert to MST (Mountain Standard Time)
    const startDateTime = moment.tz(`${serviceDate} ${serviceTime}`, 'America/Phoenix');
    const endDateTime = startDateTime.clone().add(4, 'hours'); // Default 4-hour window
    
    return {
        scheduled_start: startDateTime.toISOString(),
        scheduled_end: endDateTime.toISOString(),
        arrival_window: 120 // 2 hours in minutes
    };
}
```

**Employee Assignment**:
```javascript
function updateEmployeeAssignment(jobId, employeeIds) {
    // Employee assignment done in HCP interface
    // Syncs back to Airtable via webhook
    
    const updateData = {
        assigned_employee_ids: employeeIds || []
    };
    
    return hcpAPI.updateJob(jobId, updateData);
}
```

### 6. Status Synchronization

#### **HCP to Airtable Status Mapping**
**Webhook Endpoint**: `https://servativ.themomentcatchers.com/webhooks/hcp` (prod) or `/webhooks/hcp-dev` (dev)

**Status Translation**:
```javascript
const STATUS_MAPPING = {
    'needs_scheduling': 'New',
    'scheduled': 'Scheduled', 
    'in_progress': 'In Progress',
    'completed': 'Completed',
    'canceled': 'Canceled',
    'on_hold': 'On Hold'
};

function translateStatus(hcpStatus) {
    return STATUS_MAPPING[hcpStatus] || 'Unknown';
}
```

#### **Webhook Processing Logic**
```python
def process_hcp_webhook(request):
    # Verify webhook signature
    if not verify_hcp_signature(request.headers, request.body):
        return 403
    
    payload = request.json
    event_type = payload.get('event')
    
    if event_type == 'job.updated':
        job_data = payload['data']
        
        # Find matching reservation by HCP Job ID
        formula = f"{{HCP Job ID}} = '{job_data['id']}'"
        reservations = airtable.get_all('Reservations', formula=formula)
        
        if reservations:
            reservation = reservations[0]
            
            # Update status if changed
            new_status = translate_status(job_data.get('work_status'))
            if reservation['Status'] != new_status:
                update_data = {
                    'Status': new_status,
                    'Service Sync Details': f"Status updated to {new_status} - {timestamp}"
                }
                
                # Update employee assignment if provided
                if 'assigned_employees' in job_data:
                    employee_names = [emp['name'] for emp in job_data['assigned_employees']]
                    update_data['Assigned Employees'] = ', '.join(employee_names)
                
                airtable.update(reservation['id'], update_data)
    
    # Always return 200 to prevent webhook disabling
    return 200
```

### 7. Next Guest Date Calculation

#### **Business Logic for Service Line Names**
**Purpose**: Include next guest arrival in service line for cleaner context

```javascript
function calculateNextGuestDate(currentReservation) {
    const checkoutDate = new Date(currentReservation['Check-out Date']);
    const propertyId = currentReservation['Property ID'];
    
    // Query future reservations for same property
    const formula = `AND(
        {Property ID} = '${propertyId}',
        {Check-in Date} > '${checkoutDate.toISOString().split('T')[0]}',
        {Entry Type} = 'Reservation',
        {Status} != 'Canceled'
    )`;
    
    const futureReservations = airtable.get_all('Reservations', {
        formula: formula,
        sort: [{field: 'Check-in Date', direction: 'asc'}]
    });
    
    if (futureReservations.length > 0) {
        const nextReservation = futureReservations[0];
        const nextDate = new Date(nextReservation['Check-in Date']);
        
        // Format as "July 15"
        return nextDate.toLocaleDateString('en-US', {
            month: 'long',
            day: 'numeric'
        });
    }
    
    return 'TBD'; // To Be Determined
}
```

### 8. Same-Day Turnover Handling

#### **Detection and Special Processing**
**Business Rule**: When checkout date equals next guest's check-in date at same property

```javascript
function detectSameDayTurnover(reservation) {
    const checkoutDate = reservation['Check-out Date'];
    const propertyId = reservation['Property ID'];
    
    // Check for reservation checking in same day
    const formula = `AND(
        {Property ID} = '${propertyId}',
        {Check-in Date} = '${checkoutDate}',
        {Entry Type} = 'Reservation',
        {UID} != '${reservation['UID']}'
    )`;
    
    const sameDayReservations = airtable.get_all('Reservations', {formula});
    
    if (sameDayReservations.length > 0) {
        return {
            'Same Day Turnover': true,
            'Next Guest Same Day': true,
            'Priority': 'High'
        };
    }
    
    return {};
}
```

**Service Adjustments**:
- Earlier service time (typically 8 AM - 12 PM)
- Priority assignment to experienced cleaners
- Additional buffer time if possible
- Special notes in job description

### 9. Environment-Specific Configuration

#### **Development Environment**
- **HCP Account**: Boris's sandbox account
- **Webhook URL**: `https://servativ.themomentcatchers.com/webhooks/hcp-dev`
- **Airtable Base**: `app67yWFv0hKdl6jM`
- **Job Type ID**: Development-specific ID
- **API Key**: Development HCP API key

#### **Production Environment**
- **HCP Account**: Production service account
- **Webhook URL**: `https://servativ.themomentcatchers.com/webhooks/hcp`
- **Airtable Base**: `appZzebEIqCU5R9ER`
- **Job Type ID**: Production job type ID
- **API Key**: Production HCP API key

### 10. Error Handling and Recovery

#### **API Error Handling**
```javascript
async function createJobWithRetry(jobData, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const job = await hcpAPI.createJob(jobData);
            return {
                success: true,
                job: job,
                message: 'Job created successfully'
            };
        } catch (error) {
            if (attempt === maxRetries) {
                return {
                    success: false,
                    error: error.message,
                    message: `Failed after ${maxRetries} attempts`
                };
            }
            
            // Exponential backoff
            const delay = Math.pow(2, attempt) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}
```

#### **Webhook Failure Recovery**
```python
def handle_webhook_failure(job_id, last_status):
    # If webhook fails, fall back to polling
    try:
        current_job = hcp_api.get_job(job_id)
        current_status = current_job.get('work_status')
        
        if current_status != last_status:
            # Status changed, update Airtable
            update_reservation_status(job_id, current_status)
            
    except Exception as e:
        log.error(f"Polling fallback failed for job {job_id}: {e}")
```

## Field Mapping Reference

### Airtable to HCP Field Mapping
```javascript
const FIELD_MAPPING = {
    // Customer fields
    'Guest Name': 'customer.name',
    'Email': 'customer.email', 
    'Phone': 'customer.mobile_number',
    
    // Job fields
    'Property': 'address_id',
    'Service Date': 'scheduled_start',
    'Service Time': 'scheduled_start', 
    'Custom Service Time': 'scheduled_start',
    'Service Line Custom Instructions': 'line_items[0].name',
    
    // Status fields
    'Status': 'work_status',
    'Assigned Employees': 'assigned_employees',
    
    // Metadata
    'HCP Job ID': 'id',
    'HCP Customer ID': 'customer.id'
};
```

### HCP to Airtable Field Mapping
```javascript
const REVERSE_MAPPING = {
    'work_status': 'Status',
    'scheduled_start': 'Scheduled Start',
    'scheduled_end': 'Scheduled End', 
    'assigned_employees': 'Assigned Employees',
    'completed_at': 'Completion Date',
    'invoice_number': 'Invoice Number'
};
```

## Critical Business Rules

### Job Creation Rules
1. **One Job Per Reservation**: System prevents duplicate job creation
2. **Reservation Type Only**: Blocks never create jobs
3. **Property Required**: Must have valid HCP Customer ID
4. **Future Dates Only**: Cannot create jobs for past dates
5. **Complete Information**: Guest name, property, and service date required

### Status Management Rules
1. **HCP is Source of Truth**: Status changes originate in HCP
2. **Webhook Primary**: Real-time updates via webhooks
3. **Polling Fallback**: Background sync for missed webhooks
4. **Status Preservation**: Never overwrite newer status with older

### Service Line Rules
1. **200 Character Limit**: HCP line item name restriction
2. **Priority Order**: Custom instructions → Special flags → Base name
3. **Unicode Support**: Full character set supported
4. **Immutable After Creation**: Cannot update line items once job created

### Integration Rules
1. **Environment Isolation**: Complete separation of dev/prod
2. **API Rate Limits**: 300 requests per minute maximum
3. **Webhook Security**: HMAC signature verification required
4. **Error Recovery**: Graceful fallback mechanisms

### Job Reconciliation Rules (Optimized)
1. **Automatic Matching**: Links existing HCP jobs with Airtable reservations
2. **Property + Date Matching**: Uses HCP Customer ID, Address ID, and service date
3. **Time Proximity**: Matches jobs within 1-hour window
4. **Performance Optimized**: 5-10x faster with parallel processing and batch operations
5. **Execution Modes**: Dry-run (preview) and execute (update) modes available
6. **Script Location**: `/src/automation/scripts/hcp/reconcile-jobs-optimized.py` (primary)
7. **Backward Compatibility**: Legacy script symlinked to optimized version

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Scope**: Complete HousecallPro integration business logic
**Primary Code**: `/src/automation/scripts/hcp/prod-hcp-sync.cjs`, `/src/automation/scripts/hcp/reconcile-jobs-optimized.py`, `/src/automation/scripts/airscripts-api/handlers/jobs.js`