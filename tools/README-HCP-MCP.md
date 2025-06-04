# HousecallPro MCP Servers

This directory contains Model Context Protocol (MCP) servers for HousecallPro API integration, providing Claude and other AI assistants with direct access to HousecallPro data.

## 🏗️ Architecture

### Complete Environment Separation
- **`hcp-mcp-dev/`** - Development server using dev credentials and dev Airtable base
- **`hcp-mcp-prod/`** - Production server using prod credentials and prod Airtable base
- **`hcp-mcp-common/`** - Shared types, constants, and utilities

### Core Features
- **Full CRUD Operations** for Customers, Employees, Jobs, Job Types, and Appointments
- **Rate Limiting** with exponential backoff and retry logic
- **Comprehensive Error Handling** with detailed logging
- **Type Safety** with full TypeScript implementation
- **Environment Isolation** with separate configurations

## 🚀 Quick Start

### Development Environment
```bash
cd tools/hcp-mcp-dev
npm install
npm run build
npm run start
```

### Production Environment
```bash
cd tools/hcp-mcp-prod
npm install
npm run build
npm run start
```

## 🔧 Configuration

### Environment Variables
- **Development**: `/config/environments/dev/.env`
- **Production**: `/config/environments/prod/.env`

Required variables:
```bash
# Development
DEV_HCP_TOKEN=your_dev_token
DEV_HCP_BASE_URL=https://api.housecallpro.com
DEV_HCP_EMPLOYEE_ID=pro_your_employee_id

# Production
PROD_HCP_TOKEN=your_prod_token
PROD_HCP_BASE_URL=https://api.housecallpro.com
PROD_HCP_EMPLOYEE_ID=pro_your_employee_id
```

## 🛠️ Available MCP Tools

### Customer Tools
- `mcp__hcp-{env}__list_customers` - List customers with filtering and pagination
- `mcp__hcp-{env}__get_customer` - Get detailed customer information
- `mcp__hcp-{env}__create_customer` - Create new customer
- `mcp__hcp-{env}__update_customer` - Update existing customer
- `mcp__hcp-{env}__delete_customer` - Delete customer
- `mcp__hcp-{env}__get_customer_jobs` - Get all jobs for a customer

### Employee Tools
- `mcp__hcp-{env}__list_employees` - List employees with filtering
- `mcp__hcp-{env}__get_employee` - Get employee details
- `mcp__hcp-{env}__create_employee` - Create new employee
- `mcp__hcp-{env}__update_employee` - Update employee information
- `mcp__hcp-{env}__get_employee_schedule` - Get employee schedule

### Job Tools
- `mcp__hcp-{env}__list_jobs` - List jobs with comprehensive filtering
- `mcp__hcp-{env}__get_job` - Get detailed job information
- `mcp__hcp-{env}__create_job` - Create new job with schedule
- `mcp__hcp-{env}__update_job` - Update existing job
- `mcp__hcp-{env}__delete_job` - Delete job
- `mcp__hcp-{env}__reschedule_job` - Reschedule existing job
- `mcp__hcp-{env}__get_job_line_items` - Get job line items
- `mcp__hcp-{env}__update_job_line_items` - Update job line items

### Job Type Tools
- `mcp__hcp-{env}__list_job_types` - List job types
- `mcp__hcp-{env}__get_job_type` - Get job type details
- `mcp__hcp-{env}__create_job_type` - Create new job type
- `mcp__hcp-{env}__update_job_type` - Update job type

### Appointment Tools
- `mcp__hcp-{env}__list_appointments` - List appointments with filtering
- `mcp__hcp-{env}__get_appointment` - Get appointment details
- `mcp__hcp-{env}__create_appointment` - Create new appointment
- `mcp__hcp-{env}__update_appointment` - Update appointment
- `mcp__hcp-{env}__delete_appointment` - Delete appointment

## 🧪 Testing

### Development Testing
```bash
cd tools/hcp-mcp-dev
npm run build
node dist/hcp-mcp-dev/src/test.js
```

**Note**: Production testing is disabled by design to prevent accidental data modification.

## 📱 Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "hcp-dev": {
      "command": "node",
      "args": ["/path/to/tools/hcp-mcp-dev/dist/hcp-mcp-dev/src/index.js"],
      "env": {
        "NODE_ENV": "development"
      }
    },
    "hcp-prod": {
      "command": "node", 
      "args": ["/path/to/tools/hcp-mcp-prod/dist/hcp-mcp-prod/src/index.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

## 💡 Usage Examples

### List Recent Jobs
```
Use the mcp__hcp-dev__list_jobs tool to show me all scheduled jobs for today
```

### Create a New Customer
```
Use mcp__hcp-prod__create_customer to add John Smith with email john@example.com and phone 555-0123
```

### Reschedule a Job
```
Use mcp__hcp-dev__reschedule_job to move job job_abc123 to tomorrow at 2:00 PM
```

## 🔐 Security Features

- **Environment Isolation**: Complete separation between dev and prod
- **Credential Protection**: Environment-specific .env files with secure permissions
- **API Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: Prevents API abuse with intelligent retry logic
- **Error Handling**: Detailed error reporting without exposing sensitive data

## 📊 Monitoring

### Status Checking
The servers provide detailed status information including:
- Environment configuration
- Rate limiter status
- API connectivity
- Recent request metrics

### Logging
All operations are logged with appropriate detail levels:
- Development: Debug level logging
- Production: Info level logging

## 🚨 Important Notes

1. **Environment Separation**: Always use the correct environment server
2. **Rate Limits**: The HCP API has rate limits - the servers handle this automatically
3. **Data Validation**: All input is validated before sending to the HCP API
4. **Error Handling**: Failed requests are retried with exponential backoff
5. **Credentials**: Never share tokens between environments

## 🔄 Development Workflow

1. **Make changes** in `hcp-mcp-dev/`
2. **Test thoroughly** using the dev environment
3. **Once stable**, replicate changes to `hcp-mcp-prod/`
4. **Deploy** to production only after dev validation

## 📚 API Reference

For detailed HousecallPro API documentation, see:
- [HousecallPro API Docs](https://docs.housecallpro.com/)

## 🐛 Troubleshooting

### Common Issues
1. **404 Errors**: Some HCP API endpoints may not be available with current permissions
2. **Rate Limiting**: Automatically handled with backoff and retry
3. **Token Issues**: Verify tokens are correct and have proper permissions
4. **Environment Mix-up**: Always verify you're using the correct environment

### Debug Commands
```bash
# Check configuration
node dist/hcp-mcp-{env}/src/index.js --help

# Test API connectivity
node dist/hcp-mcp-dev/src/test.js
```

---

**Created**: 2025-06-03  
**Author**: Claude AI Assistant  
**Status**: Production Ready