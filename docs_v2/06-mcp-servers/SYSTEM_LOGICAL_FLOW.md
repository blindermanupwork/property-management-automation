# MCP Servers - Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 11, 2025  
**Purpose:** Natural language flow for Model Context Protocol server operations and AI analysis

---

## 🤖 **MCP SERVER TRIGGERS**

**Claude AI Usage**: Direct invocation by Claude Code for data analysis and operations
**Development Access**: `airtable-dev` and `hcp-mcp-dev` servers
**Production Access**: `airtable-prod` and `hcp-mcp-prod` servers

---

## 📋 **PRIMARY LOGIC FLOW**

### **STEP 1**: Server Selection and Environment Routing
- **Development Operations**:
  - **THEN** use `airtable-dev` MCP server → connects to base `app67yWFv0hKdl6jM`
  - **THEN** use `hcp-mcp-dev` MCP server → connects to Boris's HCP development account
  - **THEN** all analysis and operations target development data

- **Production Operations**:
  - **THEN** use `airtable-prod` MCP server → connects to base `appZzebEIqCU5R9ER`
  - **THEN** use `hcp-mcp-prod` MCP server → connects to production HCP account
  - **THEN** all analysis and operations target live production data

### **STEP 2**: Airtable MCP Server Operations
- **CRUD Operations**:
  - **list_records**: Query records with filtering, sorting, pagination
  - **get_record**: Retrieve specific record by ID
  - **create_record**: Create new records with field validation
  - **update_records**: Batch update up to 10 records
  - **delete_records**: Remove records by ID list

- **Schema Operations**:
  - **list_bases**: Get all accessible Airtable bases
  - **list_tables**: Get tables with configurable detail levels
  - **describe_table**: Detailed table schema with field types
  - **create_table**: Create new tables with field definitions
  - **create_field**: Add new fields to existing tables

- **Search and Query**:
  - **search_records**: Text search across specified fields
  - **Filtering**: Use filterByFormula for complex queries
  - **Views**: Apply view-based filtering and sorting

### **STEP 3**: HousecallPro MCP Server Operations
- **Customer Management**:
  - **list_customers**: Get customers with search and pagination
  - **get_customer**: Retrieve customer details by ID
  - **create_customer**: Create new customer records
  - **update_customer**: Modify existing customer data

- **Job Management**:
  - **list_jobs**: Query jobs with comprehensive filtering
  - **get_job**: Get job details including line items
  - **create_job**: Create jobs with templates and scheduling
  - **update_job**: Modify job details and status
  - **reschedule_job**: Update job scheduling

- **Enhanced Search Tools** (v2.2.1+):
  - **search_addresses**: Find addresses by street, city, customer
  - **get_jobs_by_address**: Get all jobs for specific address
  - **Smart filtering**: Customer ID, date ranges, work status

### **STEP 4**: Bulletproof Analysis Tools (v2.2.2)
- **Native TypeScript Processing**:
  - **THEN** eliminate all bash script dependencies
  - **THEN** process cached JSON data directly in TypeScript
  - **THEN** complete analysis in <10ms with comprehensive metrics

- **Laundry Analysis**:
  - **analyze_laundry_jobs**: Enhanced detection across multiple fields
  - **THEN** return job counts, revenue totals, customer tracking
  - **THEN** include data quality metrics: files processed, records analyzed, errors

- **Service Item Analysis**:
  - **analyze_service_items**: Pattern matching with usage tracking
  - **THEN** search for specific items (towels, linens, supplies)
  - **THEN** return quantity, cost, revenue, job distribution

- **Revenue Analysis**:
  - **analyze_customer_revenue**: Customer financial tracking
  - **THEN** total jobs, revenue, average values per customer
  - **THEN** job status breakdown, top services analysis

- **Statistical Analysis**:
  - **analyze_job_statistics**: Complete business intelligence
  - **THEN** total jobs, revenue, status distributions
  - **THEN** monthly trends, average job values

### **STEP 5**: Cache Management and Data Quality
- **Smart Cache System**:
  - **THEN** store HCP API responses in JSON files with timestamps
  - **THEN** support JSONPath-like queries for complex data access
  - **THEN** include actual data in responses when size < 500KB
  - **THEN** provide file paths for larger datasets

- **Data Quality Tracking**:
  - **THEN** monitor files processed vs failed
  - **THEN** track records analyzed vs skipped
  - **THEN** count parsing errors and missing data
  - **THEN** measure execution time for performance monitoring

- **Cache Operations**:
  - **search_hcp_cache**: Text and field-specific searches
  - **list_hcp_cache**: Available cache files with metadata
  - **cleanup_hcp_cache**: Remove old files based on retention policy

### **STEP 6**: Error Handling and Resilience
- **Enhanced Error Types** (v2.2.1+):
  - **CustomerHasNoJobs**: Suggests using list_jobs with customer_id filter
  - **CustomerNotFound**: Suggests verifying customer ID format
  - **InvalidPermissions**: Suggests checking API key permissions
  - **THEN** all errors include context and actionable suggestions

- **Fallback Strategies**:
  - **THEN** continue processing despite individual file failures
  - **THEN** provide detailed error reporting with file-level context
  - **THEN** implement multiple data extraction approaches
  - **THEN** graceful degradation when API limits reached

### **STEP 7**: Performance Optimization
- **API Efficiency**:
  - **THEN** batch operations where possible (up to 10 records)
  - **THEN** use per_page=100 for pagination to reduce API calls
  - **THEN** filter by customer_id and date ranges before pagination
  - **THEN** cache frequently accessed data (properties, employees)

- **Rate Limit Management**:
  - **THEN** implement exponential backoff for retries
  - **THEN** monitor API usage across all MCP operations
  - **THEN** prioritize critical operations over bulk analysis

### **STEP 8**: Best Practices for MCP Usage
- **Customer Operations**:
  - **THEN** always use exact customer IDs in `cus_xxx` format
  - **THEN** use `list_jobs(customer_id="cus_123")` instead of `get_customer_jobs`
  - **THEN** prefer `search_addresses` over manual customer iteration

- **Data Analysis Workflow**:
  - **THEN** use bulletproof analysis tools for business intelligence
  - **THEN** rely on cached data for complex queries
  - **THEN** combine MCP operations with direct cache analysis for flexibility

- **Error Recovery**:
  - **THEN** check error type and follow suggested resolution
  - **THEN** verify customer/job IDs format before API calls
  - **THEN** use fallback strategies when primary methods fail

---

## 🚨 **ERROR HANDLING**

### **Connection Errors**:
- **MCP server unreachable**: Log connection error, suggest server restart
- **Authentication failures**: Verify API keys and permissions
- **Timeout errors**: Increase timeout thresholds, retry with backoff

### **Data Processing Errors**:
- **Invalid JSON responses**: Log parsing error, attempt data recovery
- **Missing required fields**: Skip problematic records, continue processing
- **Type validation failures**: Log field-specific errors, use defaults

### **API Limit Errors**:
- **Rate limit exceeded**: Implement exponential backoff retry
- **Quota exhaustion**: Alert monitoring, pause non-critical operations
- **Permission denied**: Verify API scopes and user permissions

---

## 🔧 **ENVIRONMENT-SPECIFIC FEATURES**

### **Development MCP Servers**:
- **Safe Testing**: Limited data set prevents accidental production changes
- **Debug Logging**: Enhanced logging for development and troubleshooting
- **Flexible Operations**: Allow experimental queries and operations

### **Production MCP Servers**:
- **Full Data Access**: Complete customer and job database
- **Performance Optimized**: Tuned for high-volume operations
- **Monitoring Integration**: Comprehensive error tracking and alerting

---

*This document captures the complete logical flow for MCP server operations, from environment selection through bulletproof analysis tools, with emphasis on performance and error resilience.*