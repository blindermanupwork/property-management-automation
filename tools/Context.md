# /home/opc/automation/tools/

## Purpose
This directory contains Model Context Protocol (MCP) servers and development tools that enable Claude AI integration with the property management system. It provides sophisticated data access, analysis capabilities, and testing utilities for both Airtable and HousecallPro integrations.

## Key Subdirectories and What They Do

### **MCP Servers for Claude Integration**
- `airtable-mcp-server/` - TypeScript MCP server providing Claude access to Airtable data
- `hcp-mcp-dev/` - Development environment HousecallPro MCP server
- `hcp-mcp-prod/` - Production environment HousecallPro MCP server  
- `hcp-mcp-common/` - Shared functionality and utilities for HCP MCP servers

### **Testing and Development Tools**
- `test-mcp-connection.js` - MCP server connectivity testing
- `test-airtable-mcp.js` - Airtable MCP server testing
- `test-analysis.cjs` - Analysis capabilities testing
- `start-airtable-mcp.sh` - Airtable MCP server startup script
- `README-HCP-MCP.md` - HousecallPro MCP documentation

## How to Use the Code

### **Setting Up MCP Servers**

#### **Airtable MCP Server**
```bash
cd tools/airtable-mcp-server/
npm install
npm run build

# Start the server
../start-airtable-mcp.sh

# Test the server
node ../test-airtable-mcp.js
```

#### **HousecallPro MCP Servers**
```bash
# Development server
cd tools/hcp-mcp-dev/
npm install
npm run build

# Production server  
cd tools/hcp-mcp-prod/
npm install
npm run build

# Common utilities
cd tools/hcp-mcp-common/
npm install
npm run build
```

### **Testing MCP Connectivity**
```bash
# Test all MCP connections
node tools/test-mcp-connection.js

# Test specific Airtable functionality
node tools/test-airtable-mcp.js

# Test analysis capabilities
node tools/test-analysis.cjs
```

### **MCP Server Usage in Claude**

#### **Airtable Operations**
```javascript
// List all bases (in Claude interface)
mcp__airtable_dev__list_bases()
mcp__airtable_prod__list_bases()

// Get table structure
mcp__airtable_dev__list_tables(baseId="app67yWFv0hKdl6jM")
mcp__airtable_prod__list_tables(baseId="appZzebEIqCU5R9ER")

// Query records
mcp__airtable_dev__list_records(
  baseId="app67yWFv0hKdl6jM", 
  tableId="tblReservations",
  maxRecords=100
)
```

#### **HousecallPro Operations**
```javascript
// Customer management
mcp__hcp_dev__list_customers(per_page=100)
mcp__hcp_prod__search_addresses(street="26208 N 43rd")

// Job management
mcp__hcp_dev__list_jobs(customer_id="cus_123", per_page=100)
mcp__hcp_prod__get_jobs_by_address(address_id="adr_123", work_status="completed")

// Analysis tools (New in v2.2.1)
mcp__hcp_dev__analyze_laundry_jobs()
mcp__hcp_prod__analyze_service_items(item_pattern="towel")
mcp__hcp_dev__analyze_customer_revenue(customer_id="cus_123")
```

## Dependencies and Requirements

### **Node.js and TypeScript**
- Node.js 18+ required
- TypeScript for all MCP servers
- Model Context Protocol SDK

### **Airtable MCP Server Dependencies**
```json
{
  "@modelcontextprotocol/sdk": "^1.0.3",
  "node-fetch": "^3.3.2", 
  "zod": "^3.24.1",
  "zod-to-json-schema": "^3.24.1"
}
```

### **HCP MCP Server Dependencies**
```json
{
  "@modelcontextprotocol/sdk": "^1.0.3",
  "axios": "^1.6.0",
  "node-fetch": "^3.3.2",
  "zod": "^3.24.1"
}
```

### **Environment Variables Required**
```bash
# For Airtable MCP servers
AIRTABLE_API_KEY=pat_your_api_key
AIRTABLE_BASE_ID=app_your_base_id

# For HCP MCP servers  
HCP_API_KEY=your_hcp_api_key
HCP_BASE_URL=https://api.housecallpro.com
```

## Common Workflows and Operations

### **Development Workflow**
```bash
# 1. Install all dependencies
cd tools/
for dir in airtable-mcp-server hcp-mcp-dev hcp-mcp-prod hcp-mcp-common; do
  cd $dir && npm install && cd ..
done

# 2. Build all servers
for dir in airtable-mcp-server hcp-mcp-dev hcp-mcp-prod hcp-mcp-common; do
  cd $dir && npm run build && cd ..
done

# 3. Test connectivity
node test-mcp-connection.js

# 4. Start servers for Claude integration
./start-airtable-mcp.sh &
# HCP servers auto-start when Claude connects
```

### **Claude Integration Workflow**
1. **Connect to MCP Servers**: Claude connects to running MCP servers
2. **Data Access**: Use MCP tools to query Airtable and HousecallPro
3. **Analysis**: Perform complex data analysis using specialized tools  
4. **Operations**: Create, update, and manage records through MCP interface

### **Testing and Debugging**
```bash
# Test individual MCP server
cd tools/airtable-mcp-server/
npm test

# Debug MCP communication
node ../test-mcp-connection.js --verbose

# Check server logs
tail -f logs/mcp-server.log

# Validate TypeScript
cd tools/hcp-mcp-dev/
npm run lint
```

## Key Features and Capabilities

### **Airtable MCP Server Features**
- **Base Management**: List and access multiple Airtable bases
- **Table Operations**: List tables, fields, and views
- **Record CRUD**: Create, read, update, delete records
- **Search**: Text-based record searching
- **Schema Introspection**: Understand table structures dynamically
- **Filtering**: Advanced record filtering with formulas

### **HousecallPro MCP Server Features (Enhanced v2.2.1)**

#### **Customer Management**
- `list_customers`: Paginated customer listing with search
- `get_customer`: Detailed customer information
- `create_customer`: New customer creation
- `update_customer`: Customer data updates

#### **Advanced Search Tools (New)**
- `search_addresses`: Find addresses by street, city, customer name
- `get_jobs_by_address`: Get jobs for specific addresses with filtering
- **JSONPath Support**: Complex nested data queries

#### **Job Management**
- `list_jobs`: Advanced job filtering and pagination
- `get_job`: Detailed job information
- `create_job`: New job creation with scheduling
- `update_job`: Job updates and status changes
- **Line Item Operations**: Full CRUD for job line items

#### **Analysis Tools (New in v2.2.1)**
- `analyze_laundry_jobs`: Analyze laundry-related services using cached data
- `analyze_service_items`: Search for specific service items (towels, linens, etc.)
- `analyze_customer_revenue`: Customer revenue and job statistics
- `analyze_job_statistics`: Comprehensive job statistics
- `analyze_towel_usage`: Towel usage and costs analysis

#### **Enhanced Error Handling**
- **Specific Error Types**: CustomerNotFound, CustomerHasNoJobs, InvalidPermissions
- **Actionable Suggestions**: Each error includes troubleshooting guidance
- **Context Information**: Detailed error context for debugging

#### **Performance Improvements**
- **Smart Caching**: Automatic caching with intelligent cache management
- **Data Inclusion**: Small responses (<500KB) include data directly
- **Optimized Queries**: Reduced API calls through intelligent batching

### **Common MCP Usage Patterns**

#### **Customer Lookup Pattern**
```javascript
// 1. Search for customer by name
const customers = await mcp__hcp_prod__list_customers({
  q: "John Smith",
  per_page: 10
});

// 2. Get specific customer details
const customer = await mcp__hcp_prod__get_customer({
  customer_id: "cus_123"
});

// 3. Find customer's addresses
const addresses = await mcp__hcp_prod__search_addresses({
  customer_id: "cus_123"
});
```

#### **Job Analysis Pattern**
```javascript
// 1. Get jobs for specific address
const jobs = await mcp__hcp_prod__get_jobs_by_address({
  address_id: "adr_456",
  work_status: "completed",
  scheduled_start_min: "2025-01-01"
});

// 2. Analyze service patterns
const analysis = await mcp__hcp_prod__analyze_service_items({
  item_pattern: "towel"
});

// 3. Get customer revenue analysis
const revenue = await mcp__hcp_prod__analyze_customer_revenue({
  customer_id: "cus_123"
});
```

## Best Practices and Guidelines

### **MCP Server Development**
- **TypeScript First**: All servers developed in TypeScript for type safety
- **Error Handling**: Comprehensive error handling with specific error types
- **Validation**: Input validation using Zod schemas
- **Rate Limiting**: Respect API rate limits with intelligent throttling
- **Caching**: Implement caching for frequently accessed data

### **Environment Separation**
- **Separate Servers**: Different MCP servers for dev/prod environments
- **Isolated Data**: Complete data isolation between environments  
- **Different Credentials**: Separate API keys and configurations
- **Testing**: Comprehensive testing before production deployment

### **Security Considerations**
- **API Key Protection**: Never expose API keys in client code
- **Environment Variables**: Use environment variables for all credentials
- **Input Validation**: Validate all inputs to prevent injection attacks
- **Rate Limiting**: Implement rate limiting to prevent abuse

## Troubleshooting

### **Common MCP Issues**
```bash
# MCP server connection failures
node tools/test-mcp-connection.js

# TypeScript compilation errors
cd tools/[server-name]/ && npm run build

# Missing dependencies
npm install

# Port conflicts
lsof -i :8080  # Check if port is in use
```

### **HCP API Issues**
```bash
# Check API connectivity
curl -H "Authorization: Bearer $HCP_API_KEY" https://api.housecallpro.com/customers

# Validate environment variables
echo $HCP_API_KEY
echo $HCP_BASE_URL
```

### **Debug Commands**
```bash
# Enable debug logging
DEBUG=mcp:* node tools/test-mcp-connection.js

# Check server health
curl http://localhost:8080/health

# View server logs
tail -f logs/mcp-*.log
```