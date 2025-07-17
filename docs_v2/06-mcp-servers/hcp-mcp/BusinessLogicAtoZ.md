# HousecallPro MCP Server - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the HousecallPro MCP (Model Context Protocol) server capabilities, including all API operations, analysis tools, search functions, and business intelligence features.

## Core Business Purpose

The HCP MCP server provides AI assistants with complete access to HousecallPro functionality for property management automation, enabling advanced business analysis, automated job management, and real-time operational insights.

## Business Workflows

### 1. Customer Management Operations

#### **Customer Search and Retrieval**
**MCP Function**: `list_customers`
**Business Logic**: 
```javascript
// Search customers with advanced filtering
list_customers({
    q: "search term",           // Search by name, email, mobile, address
    page: 1,                   // Pagination control
    page_size: 100,            // Results per page (max 200)
    sort_by: "created_at",     // Sort field
    sort_direction: "desc",    // asc or desc
    tags: ["VIP", "Regular"],  // Filter by tags
    created_after: "2025-01-01T00:00:00Z",  // Date filtering
    created_before: "2025-12-31T23:59:59Z"
})
```

**Business Rules**:
1. **Search Scope**: Searches across name, email, mobile number, and address fields
2. **Pagination**: Always use reasonable page sizes (≤100) for performance
3. **Tag Filtering**: Support multiple tag filters for customer segmentation
4. **Date Filtering**: Use ISO 8601 format for temporal queries

#### **Customer Creation Process**
**MCP Function**: `create_customer`
**Business Logic**:
```javascript
create_customer({
    first_name: "John",        // Required
    last_name: "Smith",        // Required
    email: "john@example.com", // Optional but recommended
    mobile_number: "+1234567890", // Optional
    home_number: "+1987654321",   // Optional
    work_number: "+1555666777",   // Optional
    company: "ABC Corp",          // Optional
    addresses: [                  // Customer addresses
        {
            street: "123 Main St",
            city: "Phoenix",
            state: "AZ",
            zip: "85001"
        }
    ],
    tags: ["New Customer"],       // Customer tags
    notes: "VIP customer",        // Internal notes
    lead_source: "Website"        // Lead tracking
})
```

**Validation Rules**:
1. **Required Fields**: First name and last name mandatory
2. **Contact Methods**: At least one contact method recommended
3. **Address Format**: Use complete address for service scheduling
4. **Tag Management**: Use consistent tag naming conventions

### 2. Job Management Operations

#### **Job Creation Workflow**
**MCP Function**: `create_job`
**Business Logic**:
```javascript
create_job({
    customer_id: "cus_123",           // Required - existing customer
    address_id: "addr_456",           // Required - service location
    job_type_id: "jt_789",           // Required - service type
    description: "Property turnover", // Job description
    notes: "Special instructions",    // Internal notes
    work_status: "scheduled",         // Initial status
    schedule: {
        scheduled_start: "2025-07-15T10:00:00Z", // Service start time
        scheduled_end: "2025-07-15T14:00:00Z",   // Service end time
        arrival_window: 30                        // Minutes before/after
    },
    assigned_employee_ids: ["emp_001"], // Employee assignments
    line_items: [                       // Service items
        {
            name: "Turnover STR Next Guest July 20",
            description: "Complete property turnover",
            quantity: 1,
            unit_price: 15000,  // In cents ($150.00)
            kind: "labor",      // "labor", "materials", "discount", "fee"
            taxable: true
        }
    ]
})
```

**Business Rules**:
1. **Customer First**: Customer must exist before job creation
2. **Address Validation**: Address must belong to customer
3. **Job Type Required**: Determines default pricing and line items
4. **Schedule Validation**: Start time must be before end time
5. **Line Item Kinds**: Use correct HCP API values ("labor", "materials", "discount", "fee")

#### **Job Search and Filtering**
**MCP Function**: `list_jobs`
**Preferred Alternative**: Use `list_jobs` with customer filter instead of `get_customer_jobs`

**Business Logic**:
```javascript
// Best practice: Filter by customer
list_jobs({
    customer_id: "cus_123",           // Filter by specific customer
    per_page: 100,                    // Reasonable page size
    work_status: "completed",         // Filter by status
    scheduled_start_min: "2025-01-01T00:00:00Z", // Date range start
    scheduled_start_max: "2025-12-31T23:59:59Z", // Date range end
    job_type_id: "jt_789"            // Filter by job type
})

// Alternative: Get jobs by address
get_jobs_by_address({
    address_id: "addr_456",
    work_status: "completed",
    scheduled_start_min: "2025-01-01T00:00:00Z"
})
```

**Performance Rules**:
1. **Always Filter First**: Use customer_id, date ranges, or status filters
2. **Avoid Broad Pagination**: Don't paginate through all jobs
3. **Date Range Limits**: Use specific time windows for performance
4. **Customer-Specific**: Use list_jobs instead of get_customer_jobs

### 3. Advanced Address Search

#### **Address Search Functionality**
**MCP Function**: `search_addresses`
**Business Logic**:
```javascript
// Search by street address
search_addresses({
    street: "26208 N 43rd"
})

// Search by customer and location
search_addresses({
    customer_id: "cus_123",
    city: "Phoenix",
    state: "AZ"
})

// Search by customer name
search_addresses({
    customer_name: "John Smith",
    zip: "85001"
})
```

**Search Patterns**:
1. **Partial Street Matching**: Supports partial address searches
2. **Customer Filtering**: Combine customer ID with location data
3. **Geographic Search**: City, state, ZIP code filtering
4. **Name-Based**: Search by customer name for address lookup

### 4. BULLETPROOF Analysis Tools (v2.2.2)

#### **Laundry Job Analysis**
**MCP Function**: `analyze_laundry_jobs`
**Business Logic**: Native TypeScript processing for ultra-fast analysis

**Returns**:
```javascript
{
    returnLaundryJobs: [...],       // Jobs with return laundry services
    laundryJobs: [...],             // All laundry-related jobs
    totalRevenue: 252648,           // Total revenue in cents
    averageJobValue: 14036,         // Average job value in cents
    topCustomers: [...],            // Highest value customers
    executionTime: 8,               // Milliseconds
    dataQuality: {
        filesProcessed: 2,
        recordsAnalyzed: 18,
        errorCount: 0
    }
}
```

**Business Applications**:
1. **Revenue Tracking**: Monitor laundry service performance
2. **Customer Analysis**: Identify top laundry customers
3. **Service Optimization**: Analyze return laundry patterns
4. **Performance Monitoring**: <10ms execution time guaranteed

#### **Service Item Analysis**
**MCP Function**: `analyze_service_items`
**Business Logic**: Pattern matching with detailed usage tracking

**Usage Example**:
```javascript
analyze_service_items({
    item_pattern: "towel"  // Search for towel-related services
})

// Returns detailed usage data
{
    itemName: "towel",
    totalQuantity: 45,
    totalCost: 135000,              // Total cost in cents
    totalRevenue: 225000,           // Total revenue in cents
    averagePrice: 5000,             // Average price per unit
    jobCount: 15,                   // Number of jobs
    usage: [                        // Detailed usage breakdown
        {
            jobId: "job_123",
            customer: "John Smith",
            quantity: 3,
            unitPrice: 5000,
            total: 15000
        }
    ],
    executionTime: 6,
    dataQuality: {...}
}
```

#### **Customer Revenue Analysis**
**MCP Function**: `analyze_customer_revenue`
**Business Logic**: Comprehensive customer financial tracking

**Analysis Output**:
```javascript
[
    {
        customerId: "cus_123",
        customerName: "John Smith",
        totalJobs: 8,
        totalRevenue: 120000,        // Total revenue in cents
        averageJobValue: 15000,      // Average per job
        jobStatuses: {
            "completed": 6,
            "scheduled": 2
        },
        topServices: [
            {
                service: "Turnover STR",
                count: 5,
                revenue: 75000
            }
        ]
    }
]
```

#### **Job Statistics Dashboard**
**MCP Function**: `analyze_job_statistics`
**Business Logic**: Complete business intelligence dashboard

**Statistics Overview**:
```javascript
{
    totalJobs: 18,
    totalRevenue: 252648,
    averageJobValue: 14036,
    statusBreakdown: {
        "needs scheduling": 16,
        "scheduled": 2,
        "completed": 0
    },
    revenueByStatus: {
        "needs scheduling": 224216,
        "scheduled": 28432
    },
    monthlyTrends: [
        {
            month: "2025-04",
            jobCount: 4,
            revenue: 84216
        },
        {
            month: "2025-05", 
            jobCount: 14,
            revenue: 168432
        }
    ],
    executionTime: 8,
    dataQuality: {...}
}
```

### 5. Line Item Management

#### **Line Item CRUD Operations**
**Business Rules**: Critical HCP API line item constraints

**Correct Line Item Kinds**:
```javascript
// ✅ CORRECT - Use these exact values
const VALID_KINDS = [
    "labor",      // For services/work
    "materials",  // For sheets, towels, supplies  
    "discount",   // For discounts
    "fee"         // For additional fees
];

// ❌ WRONG - These will cause API errors
// "service", "product" - NOT valid HCP API values
```

**Line Item Creation**:
```javascript
create_job_line_item({
    job_id: "job_123",
    name: "Extra cleaning supplies",
    description: "Additional towels and linens",
    quantity: 2,
    unit_price: 2500,      // In cents ($25.00)
    kind: "materials",     // Use correct API value
    taxable: true,
    service_item_id: "si_456"  // Optional link to service catalog
})
```

**Update Operations**:
```javascript
// Update existing line item
update_job_line_item({
    job_id: "job_123",
    line_item_id: "li_789",
    name: "Updated service name",
    quantity: 3,
    unit_price: 3000,
    kind: "labor"
})

// Bulk update all line items
update_job_line_items({
    job_id: "job_123",
    line_items: [...]  // Complete line item array
})
```

### 6. Employee and Schedule Management

#### **Employee Operations**
**MCP Functions**: `list_employees`, `get_employee`, `create_employee`, `update_employee`

**Employee Search**:
```javascript
list_employees({
    is_active: true,           // Filter by active status
    role: "field_employee",    // Filter by role
    page: 1,
    per_page: 50
})
```

**Employee Schedule Access**:
```javascript
get_employee_schedule({
    employee_id: "emp_123",
    start_date: "2025-07-01",  // ISO 8601 date
    end_date: "2025-07-31"
})
```

### 7. Error Handling and Recovery

#### **Enhanced Error Types**
**Business Logic**: Specific error handling with actionable suggestions

**Error Categories**:
```javascript
// CustomerHasNoJobs Error
{
    type: "CustomerHasNoJobs",
    message: "Customer cus_123 has no jobs",
    suggestion: "Use list_jobs(customer_id='cus_123') instead of get_customer_jobs"
}

// CustomerNotFound Error  
{
    type: "CustomerNotFound",
    message: "Customer not found",
    suggestion: "Verify customer ID format (should be 'cus_xxx')"
}

// InvalidPermissions Error
{
    type: "InvalidPermissions", 
    message: "Insufficient API permissions",
    suggestion: "Check API key permissions for this environment"
}
```

**Recovery Strategies**:
1. **Graceful Degradation**: Continue processing despite individual failures
2. **Alternative Methods**: Suggest list_jobs instead of get_customer_jobs
3. **Validation Guidance**: Help with correct ID formats and API values
4. **Permission Checking**: Environment-specific permission validation

### 8. Cache System and Performance

#### **Smart Cache Operations**
**MCP Functions**: Cache search, list, and management

**Cache Search with JSONPath**:
```javascript
search_hcp_cache({
    file_path: "/tmp/hcp-cache/jobs_*.json",
    search_term: "Phoenix",
    field_path: "addresses.*.city"  // JSONPath-like query
})
```

**Cache Management**:
```javascript
// List cached files
list_hcp_cache({
    operation: "list_jobs"  // Filter by operation type
})

// Get cache summary
get_cache_summary({
    data: job_data,
    operation: "list_jobs"
})

// Clean old cache files
cleanup_hcp_cache()  // Removes files older than retention period
```

**Performance Optimizations**:
1. **Small Response Inclusion**: Responses <500KB include actual data
2. **Reduced Caching**: Only cache large responses (>50,000 chars)
3. **Deep Object Search**: Improved nested JSON traversal
4. **Error Resilience**: Continue processing despite file failures

### 9. Appointment System Integration

#### **Appointment Management**
**MCP Functions**: Complete appointment CRUD operations

**Appointment Creation**:
```javascript
create_appointment({
    job_id: "job_123",
    scheduled_start: "2025-07-15T10:00:00Z",
    scheduled_end: "2025-07-15T14:00:00Z", 
    assigned_employee_ids: ["emp_001", "emp_002"],
    notes: "Bring extra supplies"
})
```

**Appointment Search**:
```javascript
list_appointments({
    job_id: "job_123",                    // Filter by job
    assigned_employee_id: "emp_001",      // Filter by employee
    status: "scheduled",                  // Filter by status
    scheduled_start_min: "2025-07-01T00:00:00Z",
    scheduled_start_max: "2025-07-31T23:59:59Z"
})
```

### 10. Business Intelligence Best Practices

#### **Analysis Tool Usage Patterns**
**Recommended Workflows**:

1. **Daily Operations Review**:
   ```javascript
   // Get today's job statistics
   const stats = await analyze_job_statistics();
   
   // Check towel inventory usage
   const towels = await analyze_towel_usage();
   
   // Review customer revenue trends
   const revenue = await analyze_customer_revenue();
   ```

2. **Service Optimization**:
   ```javascript
   // Analyze specific service items
   const laundry = await analyze_service_items({item_pattern: "laundry"});
   const cleaning = await analyze_service_items({item_pattern: "cleaning"});
   
   // Compare performance metrics
   const comparison = {
       laundry_efficiency: laundry.averagePrice,
       cleaning_efficiency: cleaning.averagePrice
   };
   ```

3. **Customer Insights**:
   ```javascript
   // Identify high-value customers
   const revenue_analysis = await analyze_customer_revenue();
   const top_customers = revenue_analysis
       .sort((a, b) => b.totalRevenue - a.totalRevenue)
       .slice(0, 10);
   ```

## Environment Configuration

### Development Environment (hcp-mcp-dev)
- **Purpose**: Testing and development
- **API Endpoint**: HCP development/sandbox API
- **Cache Location**: `/tmp/hcp-cache-dev/`
- **Rate Limits**: Relaxed for testing
- **Error Tolerance**: More verbose error reporting

### Production Environment (hcp-mcp-prod)  
- **Purpose**: Live operations
- **API Endpoint**: HCP production API
- **Cache Location**: `/tmp/hcp-cache-prod/`
- **Rate Limits**: Standard HCP limits (300 req/min)
- **Error Tolerance**: Optimized error handling

## Critical Business Rules

### API Usage Rules
1. **Customer First**: Always create customers before jobs
2. **Correct Line Item Kinds**: Use "labor", "materials", "discount", "fee" only
3. **Performance Filters**: Always filter by customer_id, date ranges, or status
4. **Rate Limit Respect**: Stay within 300 requests per minute
5. **Error Recovery**: Use suggested alternatives for failed operations

### Analysis Tool Rules
1. **Performance Guaranteed**: All analysis tools complete in <10ms
2. **Data Quality Tracking**: Monitor files processed and error counts
3. **Business Context**: Use analysis for operational decision making
4. **Cache Efficiency**: Leverage cache for repeated analysis

### Integration Rules
1. **Environment Isolation**: Never mix dev/prod data
2. **Security**: API keys are environment-specific
3. **Webhook Compatibility**: Support real-time updates
4. **Audit Trail**: All operations logged with context

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete HCP MCP server business logic
**MCP Servers**: hcp-mcp-dev, hcp-mcp-prod
**Primary Code**: `/tools/hcp-mcp-dev/`, `/tools/hcp-mcp-prod/`