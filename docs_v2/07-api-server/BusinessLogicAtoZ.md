# API Server - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the API Server's capabilities, including all endpoints, job creation logic, schedule management, webhook processing, and environment-specific routing.

## Core Business Purpose

The API Server acts as the secure bridge between Airtable's interface and HousecallPro's service management system, replacing embedded Airtable scripts with robust backend APIs that handle authentication, rate limiting, and environment separation.

## Business Workflows

### 1. Job Creation Operations

#### **Create Job from Reservation**
**API Endpoint**: `POST /api/{env}/jobs/create/{recordId}`
**Business Logic**:
```javascript
// Headers required
{
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

// Process flow:
1. Load reservation from Airtable
2. Validate required fields
3. Check property HCP IDs
4. Generate service line description
5. Create job in HCP
6. Update Airtable with job ID
```

**Field Validation**:
```javascript
// Required reservation fields
const requiredFields = [
    'Guest Name',
    'Property ID',        // Linked to Properties table
    'Check-in Date',
    'Check-out Date',
    'Service Type'       // Determines job template
];

// Property must have
const propertyRequirements = [
    'HCP Customer ID',   // Customer in HousecallPro
    'HCP Address ID'     // Service address
];
```

**Service Line Generation**:
```javascript
// Order of components (max 200 chars total)
function generateServiceLine(reservation, property) {
    let components = [];
    
    // 1. Custom instructions (if any)
    if (reservation['Service Line Custom Instructions']) {
        components.push(reservation['Service Line Custom Instructions']);
    }
    
    // 2. Owner arriving flag
    if (reservation['Owner Arriving']) {
        components.push('OWNER ARRIVING');
    }
    
    // 3. Long-term guest flag (14+ days)
    const stayLength = calculateStayLength(
        reservation['Check-in Date'],
        reservation['Check-out Date']
    );
    if (stayLength >= 14) {
        components.push('LONG TERM GUEST DEPARTING');
    }
    
    // 4. Base service name
    components.push(reservation['Service Type']);
    
    // Join with " - " and truncate
    return components.join(' - ').substring(0, 200);
}
```

**Next Guest Detection**:
```javascript
// Find next reservation at same property
async function findNextReservation(base, propertyId, checkOutDate) {
    const reservations = await base('Reservations').select({
        sorts: [{ field: 'Check-in Date', direction: 'asc' }]
    }).all();
    
    const nextReservation = reservations.find(record => {
        // Must be same property
        const propLinks = record.get('Property ID');
        if (!propLinks || propLinks[0] !== propertyId) return false;
        
        // Must be a reservation (not block)
        if (record.get('Entry Type')?.name !== 'Reservation') return false;
        
        // Must not be old status
        if (record.get('Status')?.name === 'Old') return false;
        
        // Must check in after checkout
        const checkIn = record.get('Check-in Date');
        return checkIn && new Date(checkIn) > new Date(checkOutDate);
    });
    
    return nextReservation;
}
```

**Job Template Application**:
```javascript
// Get template based on service type
async function getJobTemplate(base, serviceType) {
    // Job type IDs from environment
    const jobTypeIds = {
        development: {
            'Turnover STR Next Guest': process.env.JOB_TYPE_TURNOVER_DEV,
            'Turnover STR Owner Arriving': process.env.JOB_TYPE_OWNER_DEV,
            'Midstay Clean': process.env.JOB_TYPE_MIDSTAY_DEV
        },
        production: {
            'Turnover STR Next Guest': process.env.JOB_TYPE_TURNOVER_PROD,
            'Turnover STR Owner Arriving': process.env.JOB_TYPE_OWNER_PROD,
            'Midstay Clean': process.env.JOB_TYPE_MIDSTAY_PROD
        }
    };
    
    // Get appropriate job type ID
    const jobTypeId = jobTypeIds[environment][serviceType];
    
    // Fetch template line items
    const templates = await base('Job Templates').select({
        filterByFormula: `{Service Type} = '${serviceType}'`
    }).firstPage();
    
    return {
        jobTypeId,
        lineItems: templates.map(t => ({
            name: t.get('Line Item Name'),
            description: t.get('Description'),
            quantity: t.get('Quantity') || 1,
            unit_price: Math.round(t.get('Unit Price') * 100), // Convert to cents
            unit_cost: Math.round(t.get('Unit Cost') * 100),
            taxable: t.get('Taxable') || false,
            kind: 'labor'  // HCP API requires specific values
        }))
    };
}
```

**HCP Job Creation**:
```javascript
// Create job in HousecallPro
const jobPayload = {
    customer_id: property['HCP Customer ID'],
    address_id: property['HCP Address ID'],
    job_value: calculateJobValue(lineItems),
    job_type_id: jobTypeId,
    employee_ids: [hcpConfig.employeeId],
    scheduled_start: scheduledStart.toISOString(),
    scheduled_end: scheduledEnd.toISOString(),
    arrival_window: 30,  // minutes
    description: `Reservation: ${guestName}`,
    tags: ['api-created', environment],
    line_items: [
        {
            name: serviceLine,  // Generated service line
            description: `Service for ${guestName}`,
            unit_price: lineItems[0].unit_price,
            unit_cost: lineItems[0].unit_cost,
            quantity: 1,
            taxable: false,
            kind: 'labor'
        },
        ...additionalLineItems  // From template
    ]
};

const response = await hcpFetch(
    hcpConfig,
    '/v1/jobs',
    'POST',
    jobPayload
);
```

#### **Cancel Job**
**API Endpoint**: `POST /api/{env}/jobs/cancel/{recordId}`
**Business Logic**:
```javascript
// Update job status to canceled
async function cancelJob(recordId) {
    // Get HCP Job ID from Airtable
    const reservation = await getReservation(recordId);
    const jobId = reservation['HCP Job ID'];
    
    if (!jobId) {
        throw new Error('No HCP Job ID found');
    }
    
    // Cancel in HCP
    await hcpFetch(
        hcpConfig,
        `/v1/jobs/${jobId}`,
        'PUT',
        { job_status: 'canceled' }
    );
    
    // Update Airtable
    await updateReservation(recordId, {
        'Job Status': 'Canceled',
        'Service Sync Details': buildSyncMessage(
            'Job canceled',
            'canceled'
        )
    });
}
```

### 2. Schedule Management Operations

#### **Add or Update Schedule**
**API Endpoint**: `POST /api/{env}/schedules/add/{recordId}`
**Business Logic**:
```javascript
// Parse custom service time
function parseServiceTime(timeString) {
    // Expected format: "HH:MM AM/PM" in MST
    const match = timeString.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if (!match) {
        throw new Error('Invalid time format. Use HH:MM AM/PM');
    }
    
    let hours = parseInt(match[1]);
    const minutes = parseInt(match[2]);
    const period = match[3].toUpperCase();
    
    // Convert to 24-hour format
    if (period === 'PM' && hours !== 12) hours += 12;
    if (period === 'AM' && hours === 12) hours = 0;
    
    return { hours, minutes };
}

// Create appointment schedule
async function createSchedule(reservation, customTime) {
    const checkInDate = new Date(reservation['Check-in Date']);
    const { hours, minutes } = parseServiceTime(customTime);
    
    // Set time in MST
    const scheduledStart = new Date(checkInDate);
    scheduledStart.setHours(hours, minutes, 0, 0);
    
    // Default 4-hour service window
    const scheduledEnd = new Date(scheduledStart);
    scheduledEnd.setHours(scheduledStart.getHours() + 4);
    
    // Create appointment in HCP
    const appointment = {
        job_id: reservation['HCP Job ID'],
        scheduled_start: scheduledStart.toISOString(),
        scheduled_end: scheduledEnd.toISOString(),
        arrival_window_in_minutes: 30,
        employee_ids: [hcpConfig.employeeId]
    };
    
    return await hcpFetch(
        hcpConfig,
        '/v1/appointments',
        'POST',
        appointment
    );
}
```

#### **Update Existing Schedule**
**API Endpoint**: `PUT /api/{env}/schedules/update/{recordId}`
**Business Logic**:
```javascript
// Compare and update schedule
async function updateSchedule(reservation, newTime) {
    const appointmentId = reservation['HCP Appointment ID'];
    
    if (!appointmentId) {
        // No existing appointment, create new
        return await createSchedule(reservation, newTime);
    }
    
    // Get current appointment
    const current = await hcpFetch(
        hcpConfig,
        `/v1/appointments/${appointmentId}`,
        'GET'
    );
    
    // Parse new time
    const newSchedule = parseNewSchedule(reservation, newTime);
    
    // Update if different
    if (current.scheduled_start !== newSchedule.start) {
        await hcpFetch(
            hcpConfig,
            `/v1/appointments/${appointmentId}`,
            'PUT',
            {
                scheduled_start: newSchedule.start,
                scheduled_end: newSchedule.end
            }
        );
        
        // Update sync fields
        await updateReservation(reservation.id, {
            'Schedule Sync Details': buildSyncMessage(
                'Schedule updated',
                'rescheduled',
                { 
                    from: formatTime(current.scheduled_start),
                    to: formatTime(newSchedule.start)
                }
            )
        });
    }
}
```

### 3. Status Synchronization

#### **Sync Job Status**
**API Endpoint**: `POST /api/{env}/jobs/sync/{recordId}`
**Business Logic**:
```javascript
async function syncJobStatus(recordId) {
    const reservation = await getReservation(recordId);
    const jobId = reservation['HCP Job ID'];
    
    if (!jobId) {
        throw new Error('No job to sync');
    }
    
    // Get latest from HCP
    const job = await hcpFetch(
        hcpConfig,
        `/v1/jobs/${jobId}`,
        'GET'
    );
    
    // Map HCP status to Airtable
    const statusMap = {
        'needs scheduling': 'Needs Scheduling',
        'scheduled': 'Scheduled',
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'canceled': 'Canceled'
    };
    
    // Get employee name
    const assignee = job.employee_ids?.length > 0
        ? await getEmployeeName(job.employee_ids[0])
        : 'Unassigned';
    
    // Update Airtable
    await updateReservation(recordId, {
        'Job Status': statusMap[job.work_status] || job.work_status,
        'Assignee': assignee,
        'Service Sync Details': buildSyncMessage(
            'Status synced from HCP',
            job.work_status
        )
    });
}
```

### 4. Webhook Processing

#### **Receive HCP Updates**
**API Endpoint**: `POST /api/{env}/webhooks/hcp`
**Business Logic**:
```javascript
// Process incoming webhook
async function processWebhook(payload) {
    const { event_type, object_id, object } = payload;
    
    switch (event_type) {
        case 'job.updated':
            await processJobUpdate(object_id, object);
            break;
            
        case 'job.completed':
            await processJobCompletion(object_id, object);
            break;
            
        case 'appointment.updated':
            await processAppointmentUpdate(object_id, object);
            break;
            
        default:
            console.log(`Unhandled event type: ${event_type}`);
    }
}

// Update reservation from job webhook
async function processJobUpdate(jobId, jobData) {
    // Find reservation by HCP Job ID
    const reservations = await base('Reservations').select({
        filterByFormula: `{HCP Job ID} = '${jobId}'`,
        maxRecords: 1
    }).firstPage();
    
    if (reservations.length === 0) {
        console.error(`No reservation found for job ${jobId}`);
        return;
    }
    
    const reservation = reservations[0];
    const updates = {};
    
    // Update status
    if (jobData.work_status) {
        updates['Job Status'] = mapHCPStatus(jobData.work_status);
    }
    
    // Update assignee
    if (jobData.employee_ids?.length > 0) {
        updates['Assignee'] = await getEmployeeName(jobData.employee_ids[0]);
    }
    
    // Add sync details
    updates['Service Sync Details'] = buildSyncMessage(
        'Updated via webhook',
        jobData.work_status
    );
    
    await base('Reservations').update(reservation.id, updates);
}
```

### 5. Environment Management

#### **Environment-Specific Routing**
**Business Logic**:
```javascript
// Determine environment from request path
function getEnvironment(req) {
    // Force environment for testing
    if (req.forceEnvironment) {
        return req.forceEnvironment;
    }
    
    // Check path
    if (req.path.includes('/dev/')) {
        return 'development';
    } else if (req.path.includes('/prod/')) {
        return 'production';
    }
    
    // Default to production
    return 'production';
}

// Load environment-specific configuration
function getConfig(environment) {
    return {
        airtable: {
            apiKey: environment === 'development'
                ? process.env.AIRTABLE_API_KEY_DEV
                : process.env.AIRTABLE_API_KEY_PROD,
            baseId: environment === 'development'
                ? process.env.AIRTABLE_BASE_ID_DEV
                : process.env.AIRTABLE_BASE_ID_PROD
        },
        hcp: {
            token: environment === 'development'
                ? process.env.HCP_API_KEY_DEV
                : process.env.HCP_API_KEY_PROD,
            employeeId: environment === 'development'
                ? process.env.HCP_EMPLOYEE_ID_DEV
                : process.env.HCP_EMPLOYEE_ID_PROD
        }
    };
}
```

### 6. Error Handling and Validation

#### **Request Validation**
**Business Logic**:
```javascript
// API key validation middleware
function validateApiKey(req, res, next) {
    const apiKey = req.headers['x-api-key'];
    
    if (!apiKey) {
        return res.status(401).json({
            error: 'Missing API key',
            details: 'Include X-API-Key header'
        });
    }
    
    const validKeys = [
        process.env.API_KEY_DEV,
        process.env.API_KEY_PROD
    ];
    
    if (!validKeys.includes(apiKey)) {
        return res.status(401).json({
            error: 'Invalid API key'
        });
    }
    
    next();
}

// Field validation
function validateReservation(reservation) {
    const errors = [];
    
    // Check required fields
    if (!reservation['Guest Name']) {
        errors.push('Guest Name is required');
    }
    
    if (!reservation['Property ID']) {
        errors.push('Property must be selected');
    }
    
    if (!reservation['Service Type']) {
        errors.push('Service Type is required');
    }
    
    if (!reservation['Check-in Date']) {
        errors.push('Check-in Date is required');
    }
    
    if (errors.length > 0) {
        throw new ValidationError(errors.join(', '));
    }
}
```

#### **Error Response Format**
**Business Logic**:
```javascript
// Standardized error responses
class APIError extends Error {
    constructor(message, statusCode = 400, details = null) {
        super(message);
        this.statusCode = statusCode;
        this.details = details;
    }
}

// Error handler middleware
function errorHandler(err, req, res, next) {
    console.error('API Error:', err);
    
    // Default error response
    let response = {
        error: 'Internal server error',
        timestamp: new Date().toISOString()
    };
    
    // Handle specific errors
    if (err instanceof APIError) {
        response.error = err.message;
        response.details = err.details;
        return res.status(err.statusCode).json(response);
    }
    
    // Validation errors
    if (err.name === 'ValidationError') {
        response.error = 'Validation failed';
        response.details = err.message;
        return res.status(400).json(response);
    }
    
    // HCP API errors
    if (err.message.includes('HCP API Error')) {
        response.error = 'HousecallPro API error';
        response.details = err.message;
        return res.status(502).json(response);
    }
    
    // Default
    res.status(500).json(response);
}
```

### 7. Performance Optimization

#### **Rate Limiting**
**Business Logic**:
```javascript
const rateLimit = require('express-rate-limit');

// Create limiter
const apiLimiter = rateLimit({
    windowMs: 60 * 1000,        // 1 minute
    max: 100,                   // 100 requests per minute
    message: {
        error: 'Too many requests',
        retryAfter: '60 seconds'
    },
    standardHeaders: true,      // Return rate limit info in headers
    legacyHeaders: false
});

// Apply to API routes
app.use('/api/', apiLimiter);
```

#### **Connection Pooling**
**Business Logic**:
```javascript
// Airtable connection management
const airtableConnections = new Map();

function getAirtableBase(environment) {
    const key = `${environment}_base`;
    
    if (!airtableConnections.has(key)) {
        const config = getAirtableConfig(environment);
        const base = new Airtable({
            apiKey: config.apiKey
        }).base(config.baseId);
        
        airtableConnections.set(key, base);
    }
    
    return airtableConnections.get(key);
}
```

### 8. Security Implementation

#### **CORS Configuration**
**Business Logic**:
```javascript
const corsOptions = {
    origin: function (origin, callback) {
        const allowedOrigins = [
            'https://airtable.com',
            'https://block--xxxxxxxxx.airtableblocks.com',  // Airtable apps
            'http://localhost:3000'  // Development
        ];
        
        // Allow requests with no origin (like mobile apps)
        if (!origin) return callback(null, true);
        
        // Check if origin is allowed
        const isAllowed = allowedOrigins.some(allowed => 
            origin.startsWith(allowed)
        );
        
        if (isAllowed) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'X-API-Key']
};

app.use(cors(corsOptions));
```

#### **Input Sanitization**
**Business Logic**:
```javascript
// Sanitize user input
function sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    
    // Remove potential script tags
    input = input.replace(/<script[^>]*>.*?<\/script>/gi, '');
    
    // Escape HTML entities
    input = input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;');
    
    return input;
}
```

## Critical Business Rules

### Job Creation Rules
1. **Property Requirements**: Must have HCP Customer ID and Address ID
2. **Service Line Limit**: Maximum 200 characters
3. **Long-Term Threshold**: 14+ days triggers special handling
4. **Owner Detection**: Checks for blocks after checkout
5. **Template Application**: Service type determines line items

### Schedule Management Rules
1. **Time Format**: Must be "HH:MM AM/PM" in MST
2. **Default Duration**: 4 hours for service window
3. **Arrival Window**: 30 minutes before/after
4. **Update Logic**: Only update if time changed
5. **Sync Recording**: All changes logged

### Environment Rules
1. **Path-Based Routing**: /dev/ vs /prod/ determines environment
2. **Configuration Isolation**: Separate API keys and base IDs
3. **Error Handling**: Environment included in error logs
4. **Webhook Separation**: Different endpoints per environment
5. **Testing Support**: forceEnvironment parameter

### Security Rules
1. **API Key Required**: All endpoints need X-API-Key header
2. **CORS Restriction**: Only Airtable domains allowed
3. **Rate Limiting**: 100 requests per minute per IP
4. **Input Validation**: All inputs sanitized
5. **Error Masking**: Sensitive details hidden in responses

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete API Server business logic
**Primary Code**: `/src/automation/scripts/airscripts-api/`
**Port**: 3000 (HTTP), 3001 (HTTPS)