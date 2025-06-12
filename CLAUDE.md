# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Current Version: 2.2.3** - Comprehensive Operational Documentation & Training Materials

## 📁 Project Structure (as of June 11, 2025)

```
/home/opc/automation/
├── README.md                    # Project overview
├── CLAUDE.md                    # This file - AI instructions
├── CLAUDE.local.md              # Private AI instructions
├── TASK_TRACKER.md              # Active task tracking
├── VERSION                      # Current version (2.2.2)
├── .env                         # Environment variables
├── package.json                 # Node.js dependencies
│
├── src/                         # Main source code
│   ├── run_automation_dev.py    # Dev automation runner
│   ├── run_automation_prod.py   # Prod automation runner
│   ├── run_anywhere.py          # Universal runner
│   └── automation/
│       ├── config.py            # Base configuration
│       ├── config_dev.py        # Dev configuration
│       ├── config_prod.py       # Prod configuration
│       ├── config_wrapper.py    # Config wrapper
│       ├── controller.py        # Main controller
│       ├── config/
│       │   ├── environments/    # Environment configs
│       │   └── templates/       # Configuration templates
│       │       └── hcp_job_templates.json
│       ├── logs/                # All system logs
│       └── scripts/
│           ├── CSVtoAirtable/   # CSV processing
│           ├── icsAirtableSync/ # ICS processing
│           ├── evolve/          # Evolve scraping
│           ├── webhook/         # Webhook handling
│           ├── hcp/             # HousecallPro sync
│           ├── airscripts-api/  # API server
│           ├── airtable-agent/  # AI agent
│           ├── system/          # System scripts
│           │   ├── cron_setup_dev.sh
│           │   ├── cron_setup_prod.sh
│           │   └── cron_remove.sh
│           └── data-exports/    # Data export scripts
│               ├── airtable-export-dev.mjs
│               ├── export-airtable-data.js
│               ├── export-all-real-data.mjs
│               └── webhook-trigger-export.mjs
│
├── tools/                       # MCP servers and tools
│   ├── airtable-mcp-server/     # Airtable MCP
│   ├── hcp-mcp-dev/             # HCP Dev MCP
│   ├── hcp-mcp-prod/            # HCP Prod MCP
│   └── hcp-mcp-common/          # Shared MCP code
│
├── testing/                     # All testing related
│   ├── test-runners/            # Test execution scripts
│   │   ├── *.py                 # Python tests
│   │   └── *.cjs                # JavaScript tests
│   └── test-scenarios/          # Test data files
│       ├── scenarios/           # Organized test scenarios
│       └── *.csv/*.ics          # Test data files
│
├── docs/                        # Documentation
│   ├── guides/                  # User guides
│   ├── architecture/            # System design
│   ├── api/                     # API documentation
│   ├── testing/                 # Test documentation
│   └── deployment/              # Deployment guides
│
├── app/                         # React Native mobile app
├── config/                      # Configuration files
└── archive/                     # Archived/obsolete files (IGNORED BY GIT)
```

## Project Status & Context

This is a comprehensive property management automation system with complete development/production environment separation. The system processes hundreds of reservations daily from multiple sources (iTrip emails, Evolve portal, ICS feeds) and integrates with Airtable and HousecallPro for job management.

### Current System State (v2.2.2)
- ✅ **Complete environment separation**: Dev/prod isolation fully implemented
- ✅ **ICS processor fixes**: All critical configuration issues resolved  
- ✅ **Optimized cron scheduling**: Both environments run every 4 hours (staggered)
- ✅ **🚀 BULLETPROOF HCP MCP**: Native TypeScript analysis, <10ms execution, zero bash failures
- ✅ **CloudMailin Integration**: Replaced Gmail OAuth with webhook-based email processing
- ✅ **Enhanced search capabilities**: Address search, job filtering, revenue analysis
- ✅ **Service line custom instructions**: Unicode support with 200-char truncation
- ✅ **Webhook forwarding system**: Dual authentication support implemented
- ✅ **Real-time console output**: All automation processes show live progress
- ✅ **Environment-specific webhook logs**: Separate logs for dev (webhook_development.log) and prod (webhook.log)


## HCP Sync Script Locations

### Main HCP Sync Scripts
- **Development**: `/home/opc/automation/src/automation/scripts/hcp/dev-hcp-sync.cjs`
- **Production**: `/home/opc/automation/src/automation/scripts/hcp/prod-hcp-sync.cjs`

These scripts handle the creation and synchronization of HCP jobs from Airtable reservations. They are called by the automation runner through `src/automation/scripts/run_automation.py`.

## Development Commands

### Python Development
```bash
# Environment-specific runners (PREFERRED)
python3 src/run_automation_dev.py --dry-run     # Test development automation
python3 src/run_automation_dev.py              # Run development automation
python3 src/run_automation_prod.py --dry-run   # Test production automation  
python3 src/run_automation_prod.py             # Run production automation

# Universal runner (auto-detects environment)
python3 src/run_anywhere.py --info             # Show system information
python3 src/run_anywhere.py --test             # Run system tests
python3 src/run_anywhere.py --list             # List available automations
python3 src/run_anywhere.py                    # Run automation

# Setup and validation
python3 test_setup.py                          # Validate setup

# Testing
cd testing/test-runners
python3 comprehensive-e2e-test.py              # Run end-to-end tests
python3 critical-business-logic-tests.py       # Run business logic tests

# Code quality
black src/ tests/                              # Format code
isort src/ tests/                              # Sort imports  
mypy src/                                      # Type checking

# Build and install
python3 -m build                               # Build package
pip3 install -e .                              # Install in development mode
```

### TypeScript/Node.js Development
```bash
# Airtable MCP Server
cd tools/airtable-mcp-server
npm install && npm run build                   # Build airtable MCP server
npm test                                       # Run tests
npm run lint                                   # Lint TypeScript

# HousecallPro MCP Servers
cd tools/hcp-mcp-dev
npm install && npm run build                   # Build dev MCP server
cd tools/hcp-mcp-prod  
npm install && npm run build                   # Build prod MCP server

# Test MCP connections
node tools/test-mcp-connection.js              # Test MCP server connectivity
```

### Environment Management
```bash
# Cron setup (Both environments now run every 4 hours, staggered by 10 minutes)
./cron_setup_dev.sh                           # Setup development cron (every 4hr at :10)
./cron_setup_prod.sh                          # Setup production cron (every 4hr at :00)
./cron_remove.sh                              # Remove old cron jobs
# Note: These are symlinks to src/automation/scripts/system/

# View logs
tail -f src/automation/logs/automation_dev*.log     # Development automation logs
tail -f src/automation/logs/automation_prod*.log    # Production automation logs
tail -f src/automation/logs/webhook_development.log  # Development webhook logs
tail -f src/automation/logs/webhook.log             # Production webhook logs

# Check cron status
crontab -l                                     # View current cron jobs
```

### System Features & Data Volumes
```bash
# Daily Operations (Production data as of v2.2.1):
# - iTrip email processing: 50+ reservation CSVs daily
# - ICS feeds processed: 246 feeds (prod), 255 feeds (dev) 
# - Evolve properties: Auto-scraped every 4 hours
# - Service line custom instructions: Unicode support, 200-char limit
# - Webhook forwarding: Dual auth with security headers
```

### Entry Points (after installation)
- `run-automation-dev` - Development automation runner
- `run-automation-prod` - Production automation runner  
- `run-automation` - Universal automation runner
- `evolve-scraper` - Evolve property scraper  
- `csv-processor` - CSV processing tool
- `ics-sync` - Calendar synchronization
- ~~`gmail-downloader`~~ - DEPRECATED (replaced by CloudMailin webhook)

## Architecture Overview

This is a comprehensive property management automation system that orchestrates multiple data flows:

1. **Data Sources**:
   - CloudMailin: Receives iTrip reservation CSVs via email forwarding (Gmail OAuth is DEPRECATED)
   - Evolve: Scrapes property data using Selenium
   - ICS Feeds: Syncs calendar data from property management systems
   - Webhooks: Real-time updates from external services

2. **Core Processing**:
   - **Config System** (`src/automation/config.py`): Centralized configuration managing all paths, timezone handling (PST for logs, Arizona for business data), and environment variables
   - **Controller** (`src/automation/controller.py`): Orchestrates automations based on Airtable settings with error handling and logging
   - **CSV Workflow**: Files move from `CSV_process/` → processing → `CSV_done/` with detailed tracking

3. **Integrations**:
   - **Airtable**: Central data store with two-way sync
   - **HousecallPro**: Service job management via JavaScript integration
   - **AI Agent**: OpenAI-powered interface for data queries (Node.js/Express)

4. **Key Design Patterns**:
   - Universal runner (`run_anywhere.py`) works without installation
   - Cross-platform path handling using `pathlib`
   - Modular script organization by function
   - Dual-timezone strategy for accurate business operations
   - Environment-aware configuration (dev/prod)

## Important Project Conventions

### Environment Separation
- **Complete isolation** between development and production environments
- Use `run_automation_dev.py` for development (Airtable: `app67yWFv0hKdl6jM`)
- Use `run_automation_prod.py` for production (Airtable: `appZzebEIqCU5R9ER`)
- Environment-specific configuration files: `config/environments/dev/.env` and `config/environments/prod/.env`
- CSV directories: `CSV_*_development/` vs `CSV_*_production/`
- Automation logs: `automation_dev*.log` vs `automation_prod*.log`
- Webhook logs: `webhook_development.log` vs `webhook.log`

### File and Path Handling
- Always use `python3` command (not `python`) for execution
- All file paths must use `Config` class methods for cross-platform compatibility
- CSV processing maintains audit trail in environment-specific `CSV_done/` directories
- Logs centralized in `src/automation/logs/` with environment-specific files

### Data and Timezone Management  
- Timezone handling: Use PST for logs, Arizona timezone for business data
- Environment variables loaded from environment-specific `.env` files
- API endpoints separated by environment (`/api/dev/*` vs `/api/prod/*`)

### Technology Stack
- **Python**: Core automation logic, universal runners, data processing
- **JavaScript/TypeScript**: AI agent (OpenAI integration), HousecallPro API, MCP servers
- **MCP (Model Context Protocol)**: Airtable and HousecallPro integrations for Claude
- **Cron**: Automated scheduling (4hr intervals - both dev and prod, staggered by 10 minutes)

### MCP Server Integration (Enhanced v2.2.2 - Bulletproof)
- `airtable-mcp-server`: Provides Claude access to Airtable data
- `hcp-mcp-dev` / `hcp-mcp-prod`: Environment-specific HousecallPro API access with bulletproof capabilities:
  - **✅ BULLETPROOF Analysis Tools**: Native TypeScript processing (no bash scripts)
    - `analyze_laundry_jobs`: Enhanced detection, customer tracking, <10ms execution
    - `analyze_service_items`: Pattern matching with usage tracking  
    - `analyze_customer_revenue`: Revenue analysis with job status breakdown
    - `analyze_job_statistics`: Comprehensive metrics with monthly trends
    - `analyze_towel_usage`: Specialized towel analysis with cost tracking
  - **Enhanced Search Tools**: `search_addresses`, `get_jobs_by_address`
  - **Smart Cache System**: JSONPath support, data inclusion, error resilience
  - **Detailed Error Types**: CustomerHasNoJobs, CustomerNotFound, InvalidPermissions
- Use `airtable-dev` or `airtable-prod` MCP server based on context
- Test MCP connectivity with `node tools/test-mcp-connection.js`

## 🚀 HCP MCP BULLETPROOF Usage Guide (v2.2.2)

### 🎯 Major Bulletproofing Improvements (June 2025)
1. **🛡️ ELIMINATED Bash Script Failures**: Replaced all bash generation with native TypeScript processing
2. **⚡ Ultra-Fast Performance**: All analysis tools complete in <10ms with comprehensive data quality metrics
3. **🔍 Enhanced Business Intelligence**: Revenue tracking, customer analysis, monthly trends, job statistics
4. **🛠️ Robust Error Handling**: Continues processing despite file failures, detailed error reporting
5. **📊 Data Quality Tracking**: Files processed, records analyzed, error counts, execution time monitoring
6. **🔄 Multiple Fallback Strategies**: Revenue extraction, data structure detection, customer name resolution

### Best Practices for Customer Operations
- **get_customer_jobs issue**: Often returns 404 even for valid customers
  - **Solution**: Use `list_jobs` with `customer_id` filter instead
  - **Example**: `list_jobs(customer_id="cus_123", per_page=100)`

### Address Search Patterns (New in v2.2.1)
```javascript
// Use new search_addresses tool instead of manual customer iteration
search_addresses(street="26208 N 43rd")           // Find by street
search_addresses(customer_id="cus_123", city="Phoenix")  // Filter by customer + city
search_addresses(customer_name="Smith", state="AZ")      // Find by customer name + state
```

### Job Management
```javascript
// Use new get_jobs_by_address tool
get_jobs_by_address(address_id="adr_123", work_status="completed")
get_jobs_by_address(address_id="adr_123", scheduled_start_min="2025-01-01", scheduled_start_max="2025-12-31")

// Customer lookups - always use exact customer IDs (cus_xxx format)
get_customer("cus_123")  // Get customer details first
// Then check addresses array or use search_addresses for address lookup
```

### Error Handling Improvements
- **CustomerHasNoJobs**: Suggests using list_jobs instead
- **CustomerNotFound**: Suggests verifying customer ID format
- **InvalidPermissions**: Suggests checking API key permissions
- All errors now include context and actionable suggestions

### Cache Usage Optimization
- Cache search now works properly with improved traversal
- For complex queries, still use Bash with jq for maximum flexibility
- New responses include data directly when small enough
- JSONPath-like queries supported: `search_hcp_cache(field_path="addresses.*.street", search_term="Main")`

### Line Item Operations
```javascript
// CRUD operations for job line items
get_job_line_items(job_id="job_123")
create_job_line_item(job_id="job_123", name="Cleaning Service", unit_price=100, quantity=1, kind="labor")
update_job_line_item(job_id="job_123", line_item_id="li_456", name="Deep Clean", unit_price=150)
delete_job_line_item(job_id="job_123", line_item_id="li_456")

// ⚠️ CRITICAL: Line Item Kind Values
// Use CORRECT HCP API values - these are case-sensitive and must match exactly:
// ✅ "labor" (for services/work)
// ✅ "materials" (for sheets, towels, supplies)
// ✅ "discount"
// ✅ "fee"
// 
// ❌ WRONG: "service", "product" - these will cause API errors
```

### 🚀 BULLETPROOF Analysis Tools (v2.2.2)
```javascript
// 🛡️ ALL TOOLS NOW BULLETPROOF - Native TypeScript, <10ms execution, comprehensive metrics

// Laundry Analysis - Enhanced detection across multiple fields
analyze_laundry_jobs()
// Returns: { returnLaundryJobs, laundryJobs, totalRevenue, averageJobValue, topCustomers, 
//           executionTime, dataQuality: { filesProcessed, recordsAnalyzed, errorCount } }

// Service Item Analysis - Pattern matching with detailed usage tracking  
analyze_service_items(item_pattern="towel")  
// Returns: { itemName, totalQuantity, totalCost, totalRevenue, averagePrice, jobCount,
//           usage: [{ jobId, customer, quantity, unitPrice, total }], executionTime, dataQuality }

// Customer Revenue Analysis - Comprehensive customer financial tracking
analyze_customer_revenue(customer_id="cus_123")  // Optional: specific customer
// Returns: [{ customerId, customerName, totalJobs, totalRevenue, averageJobValue, 
//            jobStatuses: {}, topServices: [] }]

// Job Statistics - Complete business intelligence dashboard
analyze_job_statistics()
// Returns: { totalJobs, totalRevenue, averageJobValue, statusBreakdown: {}, 
//           revenueByStatus: {}, monthlyTrends: [], executionTime, dataQuality }

// Towel Usage Analysis - Specialized towel cost and usage tracking
analyze_towel_usage()  // Calls analyze_service_items("towel")
```

### 📊 Sample Analysis Results
```javascript
// Example: analyze_job_statistics() returns:
{
  "totalJobs": 18,
  "totalRevenue": 252648,        // $2,526.48
  "averageJobValue": 14036,      // $140.36
  "statusBreakdown": {
    "needs scheduling": 16,
    "scheduled": 2
  },
  "monthlyTrends": [
    { "month": "2025-04", "jobCount": 4, "revenue": 84216 },
    { "month": "2025-05", "jobCount": 14, "revenue": 168432 }
  ],
  "executionTime": 8,            // milliseconds
  "dataQuality": {
    "filesProcessed": 2,
    "recordsAnalyzed": 18, 
    "errorCount": 0
  }
}
```


## Key System Features (v2.2.1)

### **Service Line Custom Instructions Support**
- **Feature**: Add custom instructions to HousecallPro job service names
- **Usage**: Set "Service Line Custom Instructions" field in Airtable before creating job
- **Capabilities**: 
  - Automatic truncation to 200 characters for HCP compatibility
  - Full Unicode support (accents, special characters, emojis)
  - Instructions appear in job's first line item name in HCP
- **Limitation**: Cannot update instructions after job creation (must edit in HCP directly)

### **Webhook Forwarding System**
- **Dual Authentication**: Supports both HCP signature and forwarding secret authentication
- **Forwarding Auth**: `X-Internal-Auth: sk_servativ_webhook_7f4d9b2e8a3c1f6d`
- **Behavior**: Always returns 200 status to prevent webhook disabling
- **Integration**: Accepts forwarded webhooks from Servativ's Java service

#### **🚨 CRITICAL: Webhook URL Configuration**
- **Dev HCP Webhooks** (Boris's HCP account): `https://servativ.themomentcatchers.com/webhooks/hcp-dev`
  - Routes to port 5001 (webhook-dev service)
  - Updates Airtable dev base (app67yWFv0hKdl6jM)
  - Service: `sudo systemctl status webhook-dev`
  
- **Prod HCP Webhooks** (3rd party forwarded): `https://servativ.themomentcatchers.com/webhooks/hcp`
  - Routes to port 5000 (webhook service)  
  - Updates Airtable prod base (appZzebEIqCU5R9ER)
  - Service: `sudo systemctl status webhook`

#### **⚠️ Common Webhook Issues & Solutions**
1. **"No matching reservation found" errors**:
   - Check which webhook service is receiving the request (port 5000 vs 5001)
   - Verify the job exists in the correct Airtable base (dev vs prod)
   - Dev jobs MUST use `/webhooks/hcp-dev` endpoint

2. **Port 443 conflicts**:
   - nginx and airscripts-api-https both try to use port 443
   - Solution: Stop airscripts-api-https, start nginx
   ```bash
   sudo systemctl stop airscripts-api-https
   sudo systemctl start nginx
   ```

3. **Testing webhooks**:
   ```bash
   # Test dev webhook
   curl -X POST https://servativ.themomentcatchers.com/webhooks/hcp-dev \
     -H "Content-Type: application/json" -d '{"foo":"bar"}'
   
   # Test prod webhook  
   curl -X POST https://servativ.themomentcatchers.com/webhooks/hcp \
     -H "Content-Type: application/json" -d '{"foo":"bar"}'
   ```

4. **Check webhook logs** (separate logs for each environment):
   ```bash
   # Production webhook activity
   tail -f /home/opc/automation/src/automation/logs/webhook.log
   
   # Development webhook activity  
   tail -f /home/opc/automation/src/automation/logs/webhook_development.log
   
   # Filter for specific job in prod
   grep "job_fdf67b8c04c943e98d75230105a033ab" /home/opc/automation/src/automation/logs/webhook.log
   
   # Filter for specific job in dev
   grep "job_fdf67b8c04c943e98d75230105a033ab" /home/opc/automation/src/automation/logs/webhook_development.log
   ```

### **Enhanced HCP MCP Capabilities (v2.2.1)**

#### **New Search Tools**:
- `search_addresses`: Find customer addresses by street, city, customer name, or customer ID
  - Example: `search_addresses(street="26208 N 43rd")` 
  - Example: `search_addresses(customer_id="cus_123", city="Phoenix")`
- `get_jobs_by_address`: Get jobs for specific address with filtering
  - Example: `get_jobs_by_address(address_id="adr_123", work_status="completed")`

#### **Advanced Analysis Tools**:
- `analyze_laundry_jobs`: Analyze laundry-related jobs using cached data
- `analyze_service_items`: Analyze specific service items (towels, linens, etc.)
- `analyze_customer_revenue`: Customer revenue and job statistics
- `analyze_job_statistics`: Comprehensive job statistics
- `analyze_towel_usage`: Towel usage and costs analysis

#### **Enhanced Error Handling**:
- **HCPDetailedError**: Specific error types with actionable suggestions
- **CustomerHasNoJobs**: Suggests using list_jobs with customer_id filter
- **CustomerNotFound**: Suggests verifying customer ID format
- **InvalidPermissions**: Suggests checking API key permissions
- All errors include context and troubleshooting guidance

#### **Improved Cache System**:
- **Deep Object Search**: Better traversal of nested JSON structures
- **JSONPath Support**: Complex data access with patterns like "addresses.*.street"
- **Smart Data Inclusion**: Small responses (<500KB) include actual data
- **Optimized Thresholds**: Reduced caching of small responses (50,000 chars vs 1,500)

### **Operational Workflow Integration**
- **Daily Workflow**: System supports Veronica's daily cleaning service management
- **Job Creation**: Services imported automatically, user clicks "Create Job & Sync Status"
- **Cleaner Assignment**: Done in HCP, syncs back to Airtable automatically
- **Schedule Updates**: "Custom Service Time" + "Add/Update Schedule" button workflow
- **Time Management**: All scheduling uses MST (Mountain Standard Time)

### **Production Data Volumes**
- **ICS Processing**: 246 feeds (production), 255 feeds (development)
- **Sources**: Airbnb, VRBO, Booking.com, Hospitable, and other property management systems
- **CSV Processing**: Daily iTrip reports and Evolve data automatically processed
- **Environment Isolation**: Complete separation between dev and prod data flows

## HCP MCP Usage Guide

### **Best Practices for HousecallPro MCP Operations**

#### **Customer Operations**:
- Always use exact customer IDs in `cus_xxx` format
- Use `list_customers` with search parameters before pagination
- For customer-specific jobs, use `list_jobs(customer_id="cus_123")` instead of `get_customer_jobs` (often returns 404)

#### **Address Searches**:
- **Preferred**: Use new `search_addresses` tool instead of manual customer iteration
- **Examples**: 
  - Street search: `search_addresses(street="26208 N 43rd")`
  - Customer-specific: `search_addresses(customer_id="cus_123", city="Phoenix")`
  - Multi-field: `search_addresses(street="Main St", city="Phoenix", state="AZ")`

#### **Job Management**:
- Use `list_jobs` with filters rather than broad pagination: `list_jobs(customer_id="cus_123", per_page=100)`
- For address-specific jobs: `get_jobs_by_address(address_id="adr_123", work_status="completed")`
- Filter by date ranges before pagination to improve performance

#### **Error Resolution**:
- **get_customer_jobs** returns 404: Use `list_jobs` with `customer_id` filter instead
- **CustomerNotFound**: Verify customer ID format and existence with `get_customer`
- **InvalidPermissions**: Check API key permissions and environment (dev vs prod)

#### **Cache Usage**:
- New responses include data directly when small enough (<500KB)
- Use `search_hcp_cache` for complex queries with JSONPath patterns
- For maximum flexibility, use Bash with `jq` for complex data analysis

#### **Line Item Operations**:
- Full CRUD support: create, read, update, delete line items
- Use `update_job_line_items` for bulk updates
- Individual operations: `create_job_line_item`, `update_job_line_item`, `delete_job_line_item`

### **Common Patterns**:
```bash
# Find customer addresses
search_addresses(customer_name="John Smith")

# Get customer jobs
list_jobs(customer_id="cus_123", per_page=100, work_status="completed")

# Get jobs for specific address
get_jobs_by_address(address_id="adr_456", scheduled_start_min="2025-01-01")

# Search cache with JSONPath
search_hcp_cache(file_path="/tmp/hcp-cache/jobs_*.json", search_term="Phoenix", field_path="customer.addresses.*.city")
```

