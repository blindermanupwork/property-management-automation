# Airtable MCP Server - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Airtable MCP server capabilities, including all CRUD operations, schema management, search functionality, and property management integration patterns.

## Core Business Purpose

The Airtable MCP server enables AI assistants to interact with Airtable databases as the central data store for property management automation, providing complete database operations while maintaining data integrity and audit trails.

## Business Workflows

### 1. Database Discovery and Schema Management

#### **List All Accessible Bases**
**MCP Function**: `list_bases`
**Business Logic**:
```javascript
list_bases()

// Returns array of bases:
[
    {
        id: "app67yWFv0hKdl6jM",      // Development base
        name: "Property Management Dev",
        permissionLevel: "create"      // Full access
    },
    {
        id: "appZzebEIqCU5R9ER",      // Production base
        name: "Property Management Prod",
        permissionLevel: "create"
    }
]
```

**Business Rules**:
1. **Permission Levels**: "none", "read", "comment", "edit", "create"
2. **Base Selection**: Use correct base ID for environment
3. **Access Control**: API key determines visible bases
4. **Discovery**: Lists only bases accessible with current credentials

#### **Table Schema Discovery**
**MCP Function**: `list_tables`
**Business Logic**:
```javascript
list_tables({
    baseId: "appZzebEIqCU5R9ER",
    detailLevel: "full"            // Options: "tableIdentifiersOnly", "identifiersOnly", "full"
})

// Returns detailed table information:
[
    {
        id: "tblReservations",
        name: "Reservations",
        description: "Guest bookings and property assignments",
        fields: [
            {
                id: "fldGuestName",
                name: "Guest Name",
                type: "singleLineText",
                description: "Primary guest name"
            },
            {
                id: "fldProperty",
                name: "Property",
                type: "multipleRecordLinks",
                options: {
                    linkedTableId: "tblProperties"
                }
            },
            {
                id: "fldCheckIn",
                name: "Check In",
                type: "date",
                options: {
                    dateFormat: {
                        name: "us",
                        format: "M/D/YYYY"
                    }
                }
            }
        ],
        views: [
            {
                id: "viwActiveReservations",
                name: "Active Reservations",
                type: "grid"
            }
        ]
    }
]
```

**Detail Level Options**:
1. **tableIdentifiersOnly**: Just IDs and names (minimal)
2. **identifiersOnly**: IDs and names for tables, fields, views
3. **full**: Complete schema with field types and options

### 2. Record Operations

#### **List Records with Filtering**
**MCP Function**: `list_records`
**Business Logic**:
```javascript
list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    maxRecords: 100,                    // Limit results
    view: "viwActiveReservations",      // Use view filters
    filterByFormula: "AND({Status} = 'New', {Check In} >= TODAY())",
    sort: [
        {
            field: "Check In",
            direction: "asc"            // or "desc"
        }
    ]
})

// Returns:
{
    records: [
        {
            id: "recABC123",
            createdTime: "2025-07-10T08:00:00.000Z",
            fields: {
                "Guest Name": "John Smith",
                "Property": ["recProp456"],
                "Check In": "2025-07-15",
                "Check Out": "2025-07-20",
                "Status": "New",
                "UID": "evolve_ABC123_2025-07-15"
            }
        }
    ],
    offset: "recXYZ789"  // For pagination
}
```

**Filter Formula Examples**:
```javascript
// Today's checkouts
"AND({Check Out} = TODAY(), {Status} != 'Removed')"

// Upcoming same-day turnovers
"AND({Same Day Turnover} = TRUE(), {Check In} >= TODAY())"

// Long-term guests
"{Stay Length} >= 14"

// Missing HCP Job ID
"AND({HCP Job ID} = BLANK(), {Service Type} != BLANK())"
```

#### **Search Records Across Fields**
**MCP Function**: `search_records`
**Business Logic**:
```javascript
search_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    searchTerm: "Smith",
    fieldIds: ["fldGuestName", "fldNotes"],  // Optional: specific fields
    maxRecords: 50,
    view: "viwActiveReservations"
})

// Searches text content in specified fields
// If fieldIds not provided, searches all text fields
```

**Search Patterns**:
1. **Partial Matching**: Searches contain the term
2. **Case Insensitive**: "smith" matches "Smith"
3. **Field Targeting**: Limit to specific fields for performance
4. **View Filtering**: Combine with view filters

#### **Create New Records**
**MCP Function**: `create_record`
**Business Logic**:
```javascript
create_record({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    fields: {
        "Guest Name": "Jane Doe",
        "Property": ["recProp789"],        // Link to property record
        "Check In": "2025-07-20",
        "Check Out": "2025-07-25",
        "Adults": 2,
        "Children": 0,
        "Source": "Airbnb",
        "Status": "New",
        "UID": "airbnb_RES456_2025-07-20",
        "Service Type": "Turnover STR Next Guest July 20",
        "Created By Automation": true,
        "Import Date": "2025-07-12T10:30:00.000Z"
    }
})

// Returns created record with ID:
{
    id: "recNEW123",
    createdTime: "2025-07-12T10:30:00.000Z",
    fields: { ... }
}
```

**Creation Rules**:
1. **Required Fields**: Vary by table configuration
2. **Field Types**: Must match Airtable schema
3. **Linked Records**: Use array of record IDs
4. **Attachments**: Use array of URL objects
5. **Dates**: Use YYYY-MM-DD format

#### **Update Existing Records**
**MCP Function**: `update_records`
**Business Logic**:
```javascript
update_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    records: [
        {
            id: "recABC123",
            fields: {
                "Status": "Modified",
                "HCP Job ID": "job_789",
                "Job Status": "Scheduled",
                "Service Sync Details": "Job created and synced - Jul 12, 10:45 AM"
            }
        },
        {
            id: "recDEF456",
            fields: {
                "Status": "Old",
                "Notes": "Replaced by modified version"
            }
        }
    ]
})

// Can update up to 10 records in one call
```

**Update Patterns**:
1. **Partial Updates**: Only specified fields change
2. **Batch Operations**: Up to 10 records per call
3. **Linked Records**: Can update relationships
4. **Clearing Fields**: Set to null or empty string

#### **Delete Records**
**MCP Function**: `delete_records`
**Business Logic**:
```javascript
delete_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservationsHistory",
    recordIds: ["recOLD123", "recOLD456", "recOLD789"]
})

// Returns array of deleted record IDs
// Can delete up to 10 records per call
```

**Deletion Rules**:
1. **Permanent**: No undo available
2. **Cascading**: Linked records not auto-deleted
3. **Permissions**: Requires delete permission
4. **Audit Trail**: Log deletions externally

### 3. Table and Field Management

#### **Create New Table**
**MCP Function**: `create_table`
**Business Logic**:
```javascript
create_table({
    baseId: "app67yWFv0hKdl6jM",
    name: "Service Templates",
    description: "Templates for different service types",
    fields: [
        {
            name: "Template Name",
            type: "singleLineText",
            description: "Name of the service template"
        },
        {
            name: "Service Type",
            type: "singleSelect",
            options: {
                choices: [
                    { name: "Turnover STR Next Guest" },
                    { name: "Turnover STR Owner Arriving" },
                    { name: "Midstay Clean" }
                ]
            }
        },
        {
            name: "Base Price",
            type: "currency",
            options: {
                precision: 2,
                symbol: "$"
            }
        },
        {
            name: "Duration Minutes",
            type: "number",
            options: {
                precision: 0
            }
        }
    ]
})
```

**Table Creation Rules**:
1. **Primary Field**: First field must be specific type
2. **Field Types**: Must use valid Airtable types
3. **Field Limits**: Consider plan limitations
4. **Naming**: Unique within base

#### **Add Field to Existing Table**
**MCP Function**: `create_field`
**Business Logic**:
```javascript
create_field({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    name: "Service Line Custom Instructions",
    type: "multilineText",
    description: "Custom instructions to add to HCP job service name (max 200 chars)"
})
```

**Field Type Examples**:
```javascript
// Single Select Field
{
    name: "Priority",
    type: "singleSelect",
    options: {
        choices: [
            { name: "High", color: "red" },
            { name: "Medium", color: "yellow" },
            { name: "Low", color: "green" }
        ]
    }
}

// Formula Field
{
    name: "Stay Length",
    type: "formula",
    options: {
        formula: "DATETIME_DIFF({Check Out}, {Check In}, 'days')"
    }
}

// Linked Record Field
{
    name: "Assigned Cleaner",
    type: "multipleRecordLinks",
    options: {
        linkedTableId: "tblEmployees",
        prefersSingleRecordLink: true
    }
}
```

### 4. Property Management Integration Patterns

#### **Reservation Processing Flow**
**Business Logic**: Complete reservation lifecycle management

```javascript
// 1. Check for existing reservation
const existing = await search_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    searchTerm: "evolve_ABC123_2025-07-15",
    fieldIds: ["fldUID"],
    maxRecords: 1
});

// 2. If exists, mark old and create new
if (existing.records.length > 0) {
    // Mark existing as old
    await update_records({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        records: [{
            id: existing.records[0].id,
            fields: { "Status": "Old" }
        }]
    });
    
    // Create new version
    await create_record({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        fields: {
            ...newReservationData,
            "Status": "Modified",
            "Previous Version": [existing.records[0].id]
        }
    });
}
```

#### **Job Creation Prerequisites**
**Business Logic**: Validate before HCP job creation

```javascript
// Get reservation with property details
const reservation = await get_record({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    recordId: "recABC123"
});

// Validate required fields
const required = [
    "Guest Name",
    "Property",
    "Check In",
    "Check Out",
    "Service Type"
];

const missing = required.filter(field => !reservation.fields[field]);
if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(", ")}`);
}

// Get property HCP IDs
const propertyId = reservation.fields["Property"][0];
const property = await get_record({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblProperties",
    recordId: propertyId
});

if (!property.fields["HCP Customer ID"] || !property.fields["HCP Address ID"]) {
    throw new Error("Property missing HCP integration IDs");
}
```

#### **Webhook Status Updates**
**Business Logic**: Real-time job status synchronization

```javascript
// Webhook receives HCP job update
const webhookData = {
    jobId: "job_789",
    status: "completed",
    assignee: "John Cleaner",
    completedAt: "2025-07-15T14:30:00Z"
};

// Find reservation by HCP Job ID
const reservations = await list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    filterByFormula: `{HCP Job ID} = '${webhookData.jobId}'`,
    maxRecords: 1
});

if (reservations.records.length > 0) {
    // Update job status
    await update_records({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        records: [{
            id: reservations.records[0].id,
            fields: {
                "Job Status": "Completed",
                "Assignee": webhookData.assignee,
                "Service Sync Details": `Job completed - ${new Date().toLocaleString()}`
            }
        }]
    });
}
```

### 5. Advanced Query Patterns

#### **Same-Day Turnover Detection**
```javascript
// Find properties with same-day turnover
const formula = `
AND(
    {Check Out} = TODAY(),
    {Property} != BLANK(),
    {Status} = 'New'
)`;

const checkouts = await list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    filterByFormula: formula
});

// For each checkout, check for same-day checkin
for (const checkout of checkouts.records) {
    const propertyId = checkout.fields["Property"][0];
    const checkInFormula = `
    AND(
        {Check In} = '${checkout.fields["Check Out"]}',
        {Property} = '${propertyId}',
        {Status} = 'New'
    )`;
    
    const checkins = await list_records({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        filterByFormula: checkInFormula,
        maxRecords: 1
    });
    
    if (checkins.records.length > 0) {
        // Update both records with same-day turnover flag
        await update_records({
            baseId: "appZzebEIqCU5R9ER",
            tableId: "tblReservations",
            records: [
                {
                    id: checkout.id,
                    fields: { "Same Day Turnover": true }
                },
                {
                    id: checkins.records[0].id,
                    fields: { "Same Day Turnover": true }
                }
            ]
        });
    }
}
```

#### **Long-Term Guest Detection**
```javascript
// Formula to find long-term stays
const formula = "AND({Stay Length} >= 14, {Status} = 'New')";

const longTermStays = await list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    filterByFormula: formula,
    view: "viwUpcomingCheckouts"
});

// Update service type for long-term guests
for (const stay of longTermStays.records) {
    await update_records({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        records: [{
            id: stay.id,
            fields: {
                "Long Term Guest": true,
                "Service Notes": "LONG TERM GUEST DEPARTING"
            }
        }]
    });
}
```

### 6. Error Handling and Recovery

#### **Rate Limit Management**
**Business Logic**: Handle Airtable API rate limits

```javascript
class AirtableRateLimiter {
    constructor() {
        this.requestCount = 0;
        this.resetTime = Date.now() + 1000;
    }
    
    async executeWithRateLimit(operation) {
        // Airtable limit: 5 requests per second
        if (this.requestCount >= 5) {
            const waitTime = this.resetTime - Date.now();
            if (waitTime > 0) {
                await new Promise(resolve => setTimeout(resolve, waitTime));
            }
            this.requestCount = 0;
            this.resetTime = Date.now() + 1000;
        }
        
        this.requestCount++;
        
        try {
            return await operation();
        } catch (error) {
            if (error.statusCode === 429) {
                // Rate limited - wait and retry
                await new Promise(resolve => setTimeout(resolve, 30000));
                return await operation();
            }
            throw error;
        }
    }
}
```

#### **Field Type Validation**
**Business Logic**: Ensure data matches field types

```javascript
function validateFieldValue(fieldType, value) {
    switch (fieldType) {
        case 'singleLineText':
        case 'multilineText':
        case 'richText':
            return typeof value === 'string';
            
        case 'number':
        case 'percent':
        case 'currency':
        case 'rating':
        case 'duration':
            return typeof value === 'number';
            
        case 'checkbox':
            return typeof value === 'boolean';
            
        case 'date':
            // Must be YYYY-MM-DD format
            return /^\d{4}-\d{2}-\d{2}$/.test(value);
            
        case 'dateTime':
            // Must be ISO 8601 format
            return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value);
            
        case 'multipleRecordLinks':
            return Array.isArray(value) && value.every(id => id.startsWith('rec'));
            
        case 'multipleAttachments':
            return Array.isArray(value) && value.every(att => 
                att.url && typeof att.url === 'string'
            );
            
        case 'singleSelect':
            return typeof value === 'string';
            
        case 'multipleSelects':
            return Array.isArray(value) && value.every(v => typeof v === 'string');
            
        default:
            return true;
    }
}
```

### 7. Resource Management

#### **Schema Resources**
**MCP Resources**: Automatic schema discovery

```javascript
// Resources are exposed as URIs:
// airtable://baseId/tableId/schema

// Example resource:
{
    uri: "airtable://appZzebEIqCU5R9ER/tblReservations/schema",
    mimeType: "application/json",
    name: "Property Management Prod: Reservations schema"
}

// Reading a resource returns:
{
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    name: "Reservations",
    description: "Guest bookings and property assignments",
    primaryFieldId: "fldGuestName",
    fields: [...],  // Complete field definitions
    views: [...]    // Available views
}
```

### 8. Best Practices and Patterns

#### **Efficient Data Retrieval**
```javascript
// DO: Use views to filter data
list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    view: "viwTodaysCheckouts",
    maxRecords: 100
})

// DO: Use filterByFormula for complex queries
list_records({
    baseId: "appZzebEIqCU5R9ER",
    tableId: "tblReservations",
    filterByFormula: "AND({Status} = 'New', {Check In} = TODAY())",
    sort: [{ field: "Property", direction: "asc" }]
})

// DON'T: Retrieve all records then filter in code
// This is inefficient and may hit rate limits
```

#### **Data Integrity Patterns**
```javascript
// Always check for duplicates before creation
async function createReservationSafely(reservationData) {
    // Check if UID already exists
    const existing = await search_records({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        searchTerm: reservationData.UID,
        fieldIds: ["fldUID"],
        maxRecords: 1
    });
    
    if (existing.records.length > 0) {
        // Handle duplicate - update or skip
        console.log(`Reservation ${reservationData.UID} already exists`);
        return existing.records[0];
    }
    
    // Safe to create
    return await create_record({
        baseId: "appZzebEIqCU5R9ER",
        tableId: "tblReservations",
        fields: reservationData
    });
}
```

## Critical Business Rules

### Data Management Rules
1. **UID Uniqueness**: Every reservation must have unique UID
2. **Status Lifecycle**: New → Modified/Old → Removed
3. **Property Links**: Must link to valid property record
4. **Date Validation**: Check-in must be before check-out
5. **History Preservation**: Never delete, mark as old/removed

### Integration Rules
1. **Environment Separation**: Never mix dev/prod data
2. **API Key Security**: Use environment-specific keys
3. **Rate Limiting**: Max 5 requests per second
4. **Batch Limits**: Max 10 records per update/delete
5. **Schema Validation**: Always validate before operations

### Property Management Rules
1. **Service Type Required**: For job creation
2. **HCP IDs Required**: Property must have customer/address IDs
3. **Same-Day Detection**: Flag both checkout and checkin
4. **Long-Term Threshold**: 14+ days is long-term
5. **Owner Detection**: Check for blocks after guest checkout

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Airtable MCP server business logic
**Primary Code**: `/tools/airtable-mcp-server/`
**NPM Package**: `airtable-mcp-server`