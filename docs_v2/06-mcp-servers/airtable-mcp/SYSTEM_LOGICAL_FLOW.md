# Airtable MCP Server - System Logical Flow

**Version:** 1.0.0  
**Last Updated:** July 12, 2025  
**Purpose:** Text-based description of Airtable MCP server operational flows

---

## 🔄 **OVERALL MCP SERVER FLOW**

### **STEP 1**: MCP Connection Initialization
- **AI Assistant Request**: Claude requests connection to Airtable MCP server
- **Environment Detection**: Server loads AIRTABLE_API_KEY from environment
- **Permission Validation**: API key scopes verified for required operations
- **Base Discovery**: Initial scan of accessible Airtable bases
- **Ready State**: MCP server confirms readiness with available tools

### **STEP 2**: Schema Discovery Process
- **Base Listing**: Enumerate all bases accessible with API key
- **Table Discovery**: For each base, retrieve table metadata
- **Field Mapping**: Parse field types, options, and relationships
- **View Identification**: Catalog available views for filtering
- **Resource Registration**: Create MCP resources for schema access

### **STEP 3**: Operation Request Processing
- **Request Receipt**: AI assistant sends operation via MCP protocol
- **Parameter Validation**: Check required fields and data types
- **Permission Verification**: Ensure operation allowed with current key
- **Data Transformation**: Convert MCP format to Airtable API format

### **STEP 4**: Airtable API Interaction
- **Request Construction**: Build proper Airtable REST API request
- **Authentication**: Add Bearer token from API key
- **Rate Limit Check**: Ensure within 5 requests/second limit
- **API Execution**: Send request to Airtable servers
- **Response Handling**: Parse and validate API response

### **STEP 5**: Result Processing and Delivery
- **Data Formatting**: Convert Airtable response to MCP format
- **Error Handling**: Transform API errors to meaningful messages
- **Pagination Support**: Include offset for large result sets
- **Response Delivery**: Return formatted data to AI assistant

---

## 🌐 **CORE OPERATIONAL FLOWS**

### **Database Discovery Flow**
1. **Initial Connection**:
   - Load API key from environment
   - Test authentication with Airtable
   - Retrieve user permissions
   
2. **Base Enumeration**:
   - Call Airtable Meta API for base list
   - Filter by permission level
   - Cache base metadata
   
3. **Schema Loading**:
   - For each discovered base
   - Retrieve complete table schemas
   - Parse field configurations
   - Map relationships between tables

### **Record Operations Flow**
1. **List Records Process**:
   - Validate base and table IDs exist
   - Apply optional view filtering
   - Construct filterByFormula if provided
   - Add sort parameters
   - Execute paginated query
   - Return records with offset

2. **Search Records Process**:
   - Identify searchable fields (text types)
   - Or use specified field IDs
   - Apply search term across fields
   - Combine with view filters
   - Return matching records

3. **Create Record Process**:
   - Validate field data types
   - Check required fields
   - Format dates and numbers
   - Handle linked records
   - Submit to Airtable
   - Return created record with ID

4. **Update Records Process**:
   - Validate record IDs exist
   - Merge field updates
   - Maintain unchanged fields
   - Batch up to 10 updates
   - Execute atomic update
   - Return success confirmation

5. **Delete Records Process**:
   - Validate record IDs
   - Check delete permissions
   - Batch up to 10 deletions
   - Execute permanent deletion
   - Return deleted IDs

### **Table Management Flow**
1. **Table Creation**:
   - Validate table name uniqueness
   - Check field type validity
   - Ensure primary field compatibility
   - Submit table structure
   - Configure initial permissions
   - Return table ID

2. **Field Addition**:
   - Check table structure
   - Validate field type
   - Ensure name uniqueness
   - Configure field options
   - Update table schema
   - Refresh cached metadata

3. **Table/Field Updates**:
   - Retrieve current configuration
   - Apply name/description changes
   - Validate changes don't break schema
   - Submit updates
   - Refresh schema cache

### **Property Management Integration Flow**
1. **Reservation Processing**:
   - Search for existing UID
   - If found, mark as "Old"
   - Create new record with "Modified" status
   - Link to property record
   - Calculate service type
   - Set appropriate flags

2. **Job Creation Prerequisites**:
   - Load reservation record
   - Validate required fields present
   - Retrieve linked property
   - Check HCP integration IDs
   - Verify service configuration
   - Return validation status

3. **Status Synchronization**:
   - Receive webhook data
   - Search by HCP Job ID
   - Update job status fields
   - Add sync timestamp
   - Log status change
   - Trigger dependent updates

### **Advanced Query Flow**
1. **Formula Construction**:
   - Parse query requirements
   - Build Airtable formula syntax
   - Handle date comparisons
   - Add logical operators
   - Escape special characters

2. **Batch Operations**:
   - Group related operations
   - Check batch size limits
   - Maintain operation order
   - Execute atomically
   - Handle partial failures

3. **Relationship Navigation**:
   - Identify linked records
   - Fetch related data
   - Resolve circular references
   - Build complete object graph

---

## 🎯 **KEY OPERATIONAL PATTERNS**

### **Performance Optimization**:
- **View Usage**: Leverage pre-filtered views for common queries
- **Formula Efficiency**: Use server-side filtering via filterByFormula
- **Batch Operations**: Group updates/deletes up to limit of 10
- **Field Selection**: Request only needed fields when possible

### **Data Integrity**:
- **UID Validation**: Always check uniqueness before creation
- **Status Management**: Follow New → Modified/Old → Removed lifecycle
- **Relationship Integrity**: Validate linked records exist
- **Type Safety**: Ensure data matches field types

### **Error Handling**:
- **Rate Limiting**: Implement exponential backoff on 429 errors
- **Permission Errors**: Provide clear missing scope messages
- **Validation Failures**: Return specific field error details
- **Network Resilience**: Retry transient failures

### **Schema Management**:
- **Discovery First**: Always check schema before operations
- **Type Validation**: Match data to field type requirements
- **Relationship Mapping**: Understand table connections
- **View Utilization**: Use views for complex filtering

---

## 📊 **DATA FLOW PATTERNS**

### **Request → Validation → API → Response**:
1. AI assistant initiates MCP request
2. Server validates all parameters
3. Transform to Airtable API format
4. Execute API call with auth
5. Process and format response
6. Return enriched result

### **Schema → Cache → Operations**:
1. Discover bases on connection
2. Load and cache table schemas
3. Use cache for validation
4. Execute operations with confidence
5. Update cache on schema changes

### **Search → Filter → Sort → Paginate**:
1. Apply search terms to fields
2. Add formula-based filters
3. Apply sort parameters
4. Limit results with maxRecords
5. Provide offset for pagination

---

## 🔧 **INTEGRATION POINTS**

### **MCP Protocol Integration**:
- Standard tool discovery
- Parameter validation
- Resource exposure
- Error standardization

### **Airtable API Integration**:
- REST API communication
- Bearer token authentication
- Rate limit compliance
- Pagination handling

### **Property Management System**:
- Reservation table operations
- Property linking
- Status synchronization
- Job creation validation

### **Audit and Logging**:
- Operation tracking
- Error logging
- Performance monitoring
- Usage analytics

---

## 🚦 **OPERATIONAL STATES**

### **Connection States**:
1. **Initializing**: Loading configuration
2. **Authenticating**: Validating API key
3. **Discovering**: Loading schemas
4. **Ready**: Available for operations
5. **Error**: Connection failed

### **Operation States**:
1. **Received**: Request arrived
2. **Validating**: Checking parameters
3. **Executing**: API call in progress
4. **Processing**: Handling response
5. **Complete**: Result returned

### **Error States**:
1. **ValidationError**: Bad parameters
2. **PermissionError**: Insufficient scope
3. **RateLimitError**: Too many requests
4. **NetworkError**: Connection issue
5. **DataError**: Type mismatch

---

## 🔄 **COMMON WORKFLOWS**

### **Daily Reservation Import**:
1. Search for today's new reservations
2. Check each against existing UIDs
3. Create new or update existing
4. Link to property records
5. Calculate service requirements
6. Flag special conditions

### **Job Status Updates**:
1. Receive webhook with job changes
2. Find reservation by HCP Job ID
3. Update status and assignee
4. Add timestamp to sync field
5. Check for dependent updates

### **Property Data Validation**:
1. List all property records
2. Check for required HCP IDs
3. Validate address completeness
4. Flag missing integrations
5. Report validation results

---

*This document provides the complete logical flow of the Airtable MCP server, describing how all components work together to provide AI assistants with comprehensive database access.*