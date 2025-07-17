# HousecallPro MCP Server - System Logical Flow

**Version:** 1.0.0  
**Last Updated:** July 12, 2025  
**Purpose:** Text-based description of HCP MCP server operational flows

---

## 🔄 **OVERALL MCP SERVER FLOW**

### **STEP 1**: MCP Connection Initialization
- **AI Assistant Request**: Claude requests connection to HCP MCP server
- **Environment Detection**: Server identifies development vs production context
- **Configuration Loading**: API keys, endpoints, and rate limits loaded from environment
- **API Validation**: Test connection to HousecallPro API to verify credentials
- **Ready State**: MCP server confirms readiness for operations

### **STEP 2**: Operation Request Processing
- **Request Parsing**: AI assistant sends MCP protocol request with parameters
- **Parameter Validation**: Server validates required fields and data types
- **Permission Checking**: Verify operation allowed for current environment
- **Rate Limit Check**: Ensure within 300 requests/minute threshold

### **STEP 3**: HCP API Interaction
- **Request Building**: Construct proper HCP API request with headers and authentication
- **Error Handling**: Implement retry logic for transient failures
- **Response Processing**: Parse API response and handle pagination if needed
- **Data Transformation**: Convert HCP format to MCP response format

### **STEP 4**: Analysis and Intelligence
- **Native Processing**: TypeScript analysis tools execute without bash dependencies
- **Performance Tracking**: Monitor execution time (<10ms target)
- **Data Quality**: Track files processed, records analyzed, error counts
- **Result Packaging**: Format analysis results with metrics and insights

### **STEP 5**: Response Delivery
- **Cache Decision**: Responses >500KB cached, smaller ones included directly
- **Error Context**: Include actionable suggestions for any failures
- **Performance Metrics**: Add execution time and data quality indicators
- **AI Assistant Receipt**: Return formatted response via MCP protocol

---

## 🌐 **CORE OPERATIONAL FLOWS**

### **Customer Management Flow**
1. **Search Operations**:
   - Parse search parameters (name, email, mobile, address)
   - Apply filters (tags, date ranges, pagination)
   - Execute HCP API search request
   - Return paginated results with total count

2. **Customer Creation**:
   - Validate required fields (first_name, last_name)
   - Format phone numbers and addresses
   - Submit to HCP API
   - Return customer ID and full record

3. **Update Operations**:
   - Verify customer exists with provided ID
   - Merge updates with existing data
   - Submit changes to HCP
   - Log update in audit trail

### **Job Management Flow**
1. **Job Creation Process**:
   - Verify customer exists (prerequisite)
   - Validate address belongs to customer
   - Build job payload with schedule and line items
   - Create job in HCP system
   - Return job ID for tracking

2. **Job Search and Filtering**:
   - **Best Practice**: Always use customer_id filter
   - Apply date ranges for performance
   - Filter by work status or job type
   - Use list_jobs instead of get_customer_jobs

3. **Schedule Management**:
   - Validate scheduled_start < scheduled_end
   - Apply arrival window buffer
   - Assign employees to time slots
   - Handle schedule conflicts

### **Advanced Search Operations**
1. **Address Search Flow**:
   - Parse search criteria (street, city, state, zip)
   - Optional customer filtering
   - Execute targeted or global search
   - Return matching addresses with customer info

2. **Jobs by Address**:
   - Validate address ID exists
   - Apply optional date/status filters
   - Retrieve all jobs for location
   - Include job details and schedules

### **BULLETPROOF Analysis Flow**
1. **Data Loading**:
   - Check cache directory for recent data
   - Load JSON files with error handling
   - Continue processing despite file failures

2. **Native TypeScript Processing**:
   - Start performance timer
   - Apply analysis algorithms
   - Extract patterns and metrics
   - Calculate aggregations

3. **Result Generation**:
   - Package findings with context
   - Include data quality metrics
   - Add execution time (<10ms)
   - Return comprehensive insights

### **Error Handling Flow**
1. **Error Detection**:
   - Catch API errors immediately
   - Identify error type and context
   - Log full error details

2. **Recovery Strategy**:
   - **CustomerHasNoJobs**: Suggest list_jobs alternative
   - **CustomerNotFound**: Guide to correct ID format
   - **InvalidPermissions**: Check API key configuration
   - **RateLimit**: Implement exponential backoff
   - **Network Error**: Retry with jitter

3. **User Guidance**:
   - Provide actionable error messages
   - Include example corrections
   - Suggest alternative approaches

---

## 🎯 **KEY OPERATIONAL PATTERNS**

### **Performance Optimization**:
- **Filter First**: Always use customer_id, date ranges, or status filters before pagination
- **Reasonable Pages**: Limit page_size to 100 for optimal performance
- **Cache Intelligence**: Only cache large responses (>500KB)
- **Direct Data**: Include actual data in responses when small enough

### **Line Item Management**:
- **Correct Kinds**: Must use "labor", "materials", "discount", or "fee"
- **Validation**: Check job exists before line item operations
- **Bulk Updates**: Use update_job_line_items for multiple changes
- **Error Prevention**: Validate kind values to prevent API rejections

### **Environment Separation**:
- **Development**: Relaxed rate limits, verbose logging, test data
- **Production**: Standard limits, optimized logging, live data
- **Cache Isolation**: Separate directories for dev/prod caches
- **API Endpoints**: Environment-specific HCP API URLs

### **Business Intelligence**:
- **Laundry Analysis**: Detect patterns across job descriptions and line items
- **Service Tracking**: Monitor specific item usage (towels, linens)
- **Revenue Insights**: Calculate customer lifetime value and trends
- **Performance Metrics**: All analysis completes in <10ms

---

## 📊 **DATA FLOW PATTERNS**

### **Request → API → Response**:
1. AI assistant initiates MCP request
2. Server validates and transforms to HCP format
3. HCP API processes and returns data
4. Server enhances response with caching/metrics
5. AI assistant receives enriched response

### **Cache → Analysis → Insights**:
1. Previous API responses stored in cache
2. Analysis tools load cached data
3. Native TypeScript processing extracts patterns
4. Business intelligence generated
5. Insights returned with performance metrics

### **Error → Recovery → Success**:
1. Operation encounters error condition
2. Error type identified and logged
3. Recovery strategy selected
4. Alternative approach attempted
5. Success achieved or guidance provided

---

## 🔧 **INTEGRATION POINTS**

### **MCP Protocol Integration**:
- Follows Model Context Protocol standards
- Supports all standard MCP operations
- Provides tool discovery and documentation
- Handles streaming responses for large data

### **HousecallPro API Integration**:
- RESTful API communication
- OAuth2 authentication flow
- Webhook support for real-time updates
- Rate limit compliance (300/minute)

### **Cache System Integration**:
- File-based caching for large responses
- Automatic cleanup of old files
- JSONPath query support
- Deep object traversal capabilities

### **Analysis Tool Integration**:
- Seamless access to all cached data
- Cross-reference multiple data sources
- Aggregate metrics calculation
- Trend detection algorithms

---

*This document provides the complete logical flow of the HCP MCP server, describing how all components work together to provide AI assistants with powerful HousecallPro integration capabilities.*