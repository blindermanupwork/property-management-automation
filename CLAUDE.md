# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Current Version: 2.2.17** - Fix Unnecessary Last Updated Changes & ICS Sync Format

**📚 IMPORTANT: Always read `/home/opc/automation/README.md` for comprehensive system documentation, features, and operational guides.**


## 📁 Project Structure (as of July 21, 2025)

```
/home/opc/automation/
├── README.md                    # Project overview - Contains v2.2.10 features, quick start, architecture, and troubleshooting
├── CLAUDE.md                    # This file - AI instructions
├── CLAUDE.local.md              # Private AI instructions
├── TASK_TRACKER.md              # Active task tracking
├── VERSION                      # Current version (2.2.10)
├── .env                         # Environment variables
├── package.json                 # Node.js dependencies
│
├── src/                         # Main source code
│   ├── run_automation_dev.py    # Dev automation runner
│   ├── run_automation_prod.py   # Prod automation runner
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
│           │   ├── csvProcess.py         # Main stable CSV processor
│           │   ├── csvProcess_enhanced.py # Wrapper for main processor
│           │   └── csvProcess_best.py    # Backup of best working version
│           ├── icsAirtableSync/ # ICS processing (with hybrid detection)
│           ├── evolve/          # Evolve scraping
│           ├── webhook/         # Webhook handling
│           ├── hcp/             # HousecallPro sync
│           ├── airscripts-api/  # API server
│           ├── airtable-agent/  # AI agent
│           ├── airtable-automations/ # Airtable automation scripts
│           │   ├── find-next-guest-date.js
│           │   ├── update-service-line-description.js
│           │   └── README.md
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
├── docs_v2/                     # Enhanced documentation (v2.2.8+)
│   └── logging-architecture.md  # Environment-specific logging design
│
├── app/                         # React Native mobile app
├── config/                      # Configuration files
└── archive/                     # Archived/obsolete files (IGNORED BY GIT)
```

## Project Status & Context

This is a comprehensive property management automation system with complete development/production environment separation. The system processes hundreds of reservations daily from multiple sources (iTrip emails, Evolve portal, ICS feeds) and integrates with Airtable and HousecallPro for job management.

### Current System State (v2.2.17)
- ✅ **Complete environment separation**: Dev/prod isolation fully implemented
- ✅ **ICS processor fixes**: All critical configuration issues resolved  
- ✅ **Optimized cron scheduling**: Production runs hourly, development every 4 hours
- ✅ **🚀 BULLETPROOF HCP MCP**: Native TypeScript analysis, <10ms execution, zero bash failures
- ✅ **CloudMailin Integration**: Replaced Gmail OAuth with webhook-based email processing
- ✅ **Enhanced search capabilities**: Address search, job filtering, revenue analysis
- ✅ **Service line custom instructions**: Unicode support with 200-char truncation
- ✅ **Long-term guest detection**: Auto-adds "LONG TERM GUEST DEPARTING" for 14+ day stays
- ✅ **Owner arrival detection**: Auto-detects blocks and adds "OWNER ARRIVING" to service lines
- ✅ **Webhook forwarding system**: Dual authentication support implemented
- ✅ **Real-time console output**: All automation processes show live progress
- ✅ **Environment-specific logging system**: Complete log separation for all components (v2.2.8)
  - CSV processing: `csv_sync_Development.log` / `csv_sync_Production.log`
  - ICS processing: `ics_sync_dev.log` / `ics_sync_prod.log` 
  - Webhook processing: `webhook_development.log` / `webhook.log`
  - Automation runners: `automation_dev*.log` / `automation_prod*.log`
- ✅ **CSV Duplicate Detection Fix**: Fixed composite UID vs base UID lookup mismatch (June 23, 2025)
- ✅ **Duplicate Cleanup Script**: Script to mark old duplicates as "Old" status
- ✅ **HCP Job Reconciliation (Optimized)**: High-performance automatic matching of unlinked HCP jobs to Airtable reservations with parallel processing
- ✅ **Reservation Duplicate Detection**: Scripts to find and fix duplicate active UIDs and property/date conflicts (June 30, 2025)
- ✅ **Property Name Logging**: CSV sync logs now display property names (e.g., "2065 W 1st Pl, Mesa, AZ") instead of cryptic record IDs for better searchability (July 12, 2025)
- ✅ **Enhanced Sync Reporting**: Detailed breakdowns showing new/modified/removed counts for both reservations and blocks (v2.2.10)
- ✅ **iTrip Next Guest Date Support**: Service lines now use iTrip-provided next guest dates when available (v2.2.10)
- ✅ **Single Error Symbol Display**: Fixed double ❌ issue in error messages (v2.2.10)
- ✅ **iTrip Same-Day Detection Fix**: Python script now correctly detects and updates same-day turnovers when using iTrip Next Guest Date (v2.2.11)
- ✅ **Owner Arrival Same-Day Fix**: Owner arrivals NOT marked as same-day to prevent sync conflicts, should get 10:00 AM service time (v2.2.13)
- ✅ **Error Handling Improvements**: Fixed double ❌❌ status icons, improved error messages with specific context instead of generic "Unknown error" (v2.2.14)
- ✅ **Service Line Description Fix**: All flags now independent - OWNER ARRIVING, LONG TERM GUEST DEPARTING, and SAME DAY work correctly in all combinations (v2.2.15)
- ✅ **iTrip Automation Fix**: find-next-guest-date.js now completely skips iTrip reservations - all iTrip fields handled exclusively by CSV processor (v2.2.16)
- ✅ **Fix Unnecessary Last Updated Changes**: ICS processor no longer updates "Last Seen" field for records that were never missing, preventing unnecessary "Last Updated" field changes in Airtable (v2.2.17)


## HCP Sync Script Locations

### Main HCP Sync Scripts
- **Development**: `/home/opc/automation/src/automation/scripts/hcp/dev-hcp-sync.cjs`
- **Production**: `/home/opc/automation/src/automation/scripts/hcp/prod-hcp-sync.cjs`

These scripts handle the creation and synchronization of HCP jobs from Airtable reservations. They are called by the automation runner through `src/automation/scripts/run_automation.py`.

## Development Commands

### Python Development
```bash
# Environment-specific runners
python3 src/run_automation_dev.py --dry-run     # Test development automation
python3 src/run_automation_dev.py              # Run development automation
python3 src/run_automation_prod.py --dry-run   # Test production automation  
python3 src/run_automation_prod.py             # Run production automation

# Setup and validation
python3 test_setup.py                          # Validate setup

# Testing
cd testing/test-runners
python3 comprehensive-e2e-test.py              # Run end-to-end tests
python3 critical-business-logic-tests.py       # Run business logic tests

# Hybrid Processing Tests (v2.2.9)
python3 test_ics_hybrid.py                     # Test ICS hybrid duplicate detection
python3 test_csv_hybrid.py                     # Test CSV hybrid duplicate detection
python3 test_hybrid_live.py                    # Test live Airtable integration
./run_hybrid_tests.sh                          # Run all hybrid tests automatically

# Cleanup scripts
python3 src/automation/scripts/cleanup-duplicate-reservations.py --env prod --dry-run  # Test cleanup
python3 src/automation/scripts/cleanup-duplicate-reservations.py --env prod --execute  # Run cleanup

# HCP Job Reconciliation (OPTIMIZED VERSION)
python3 src/automation/scripts/hcp/reconcile-jobs-optimized.py --env dev --dry-run    # Test dev reconciliation
python3 src/automation/scripts/hcp/reconcile-jobs-optimized.py --env dev --execute   # Run dev reconciliation
python3 src/automation/scripts/hcp/reconcile-jobs-optimized.py --env prod --dry-run  # Test prod reconciliation
python3 src/automation/scripts/hcp/reconcile-jobs-optimized.py --env prod --execute  # Run prod reconciliation

# Duplicate detection and fixing scripts
python3 src/automation/scripts/find-duplicate-active-uids.py            # Find UIDs with multiple active records
python3 src/automation/scripts/fix-uid-duplicates.py --execute         # Fix duplicate active UIDs
python3 src/automation/scripts/find-property-date-duplicates-active.py  # Find property/date duplicates with multiple active UIDs
python3 src/automation/scripts/find-property-date-duplicates-active.py --fix  # Fix property/date duplicates

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
# Cron setup
./cron_setup_dev.sh                           # Setup development cron (every 4hr at :10)
./cron_setup_prod.sh                          # Setup production cron (every 1hr at :00)
./cron_remove.sh                              # Remove old cron jobs
# Note: These are symlinks to src/automation/scripts/system/

# View logs - Environment-Specific Logging (v2.2.8)
tail -f src/automation/logs/automation_dev*.log     # Development automation logs
tail -f src/automation/logs/automation_prod*.log    # Production automation logs
tail -f src/automation/logs/csv_sync_Development.log # Development CSV processing logs
tail -f src/automation/logs/csv_sync_Production.log  # Production CSV processing logs
tail -f src/automation/logs/ics_sync_dev.log        # Development ICS processing logs
tail -f src/automation/logs/ics_sync_prod.log       # Production ICS processing logs
tail -f src/automation/logs/webhook_development.log  # Development webhook logs
tail -f src/automation/logs/webhook.log             # Production webhook logs

# Check cron status
crontab -l                                     # View current cron jobs
```

### 🚨 CRITICAL: Running Evolve Scraper Manually
```bash
# ⚠️ IMPORTANT: Environment variable MUST be set BEFORE Python starts!

# ✅ CORRECT - Run Evolve scraper for PRODUCTION:
ENVIRONMENT=production python3 src/automation/scripts/evolve/evolveScrape.py --headless --sequential

# ✅ CORRECT - Run Evolve scraper for DEVELOPMENT:
ENVIRONMENT=development python3 src/automation/scripts/evolve/evolveScrape.py --headless --sequential

# ❌ WRONG - This will NOT work:
export ENVIRONMENT=production
python3 src/automation/scripts/evolve/evolveScrape.py  # Environment already set to dev!

# Why? The Config singleton is created when Python imports the module, BEFORE your export runs.

# Other important flags:
# --headless     : Run without GUI (required on server)
# --sequential   : Run tab exports one after another (avoids Chrome conflicts)
```

### System Features & Data Volumes
```bash
# Daily Operations (Production data as of v2.2.1):
# - iTrip email processing: 50+ reservation CSVs daily
# - ICS feeds processed: 246 feeds (prod), 255 feeds (dev) 
# - Evolve properties: Auto-scraped hourly (prod), every 4 hours (dev)
# - Service line custom instructions: Unicode support, 200-char limit
# - Webhook forwarding: Dual auth with security headers
```

### Entry Points (after installation)
- `run-automation-dev` - Development automation runner
- `run-automation-prod` - Production automation runner
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
   - Environment-specific runners (`run_automation_dev.py`, `run_automation_prod.py`) for direct control
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
- **Cron**: Automated scheduling (prod: hourly, dev: 4hr intervals)

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
- `trello-mcp-server`: Provides Claude access to Trello boards and cards
  - **Board Management**: List boards, set active board, manage workspaces
  - **Card Operations**: Create, update, move, and archive cards with markdown descriptions
  - **List Management**: Create and archive lists
  - **Attachments**: Attach images to cards from URLs
  - **Activity Tracking**: Get recent board activity
  - **Rate Limiting**: Automatic handling of Trello API limits (300 req/10s)
  - **Active Board**: Servativ (ID: 684c85bde6851c221fffb25f)
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


## Key System Features (v2.2.9)

### **Property Name Logging Enhancement**
- **Feature**: Human-readable property names in all CSV sync logs
- **Format**: `Property "2065 W 1st Pl, Mesa, AZ" (recsKzsYIlFCXXmg5)` instead of just `Property recsKzsYIlFCXXmg5`
- **Benefits**: 
  - Easy log searching without needing to look up property record IDs
  - Better debugging and monitoring of specific properties
  - Consistent property identification across all log entries
- **Implementation**: Comprehensive property mapping loaded at initialization using Property Name and Address fields
- **Coverage**: All property references in logging statements

### **Airtable Automation Scripts (v2.2.16)**
- **Location**: `/home/opc/automation/src/automation/scripts/airtable-automations/`
- **find-next-guest-date.js**:
  - **iTrip Handling**: Completely skips iTrip reservations (Entry Source = "iTrip")
  - **Why**: iTrip fields (Next Guest Date, Same-day Turnover) are set exclusively by CSV processor
  - **Other Sources**: Searches database for next guest/owner arrivals (Airbnb, VRBO, etc.)
- **update-service-line-description.js**:
  - **Priority**: Uses iTrip Next Guest Date first, falls back to calculated Next Guest Date
  - **Works for ALL**: Processes both iTrip and non-iTrip reservations correctly
  - **Reads fields**: Same-day Turnover, Owner Arriving, Long Term Guest flags

### **Enhanced Service Line Updates with Owner Detection**
- **Feature**: Automatically detect when property owners are arriving
- **Detection Logic**: Identifies Block entries checking in same/next day after reservation checkout
- **Implementation**: Python-based detection in `update-service-lines-enhanced.py`
- **Updates**:
  - Sets "Owner Arriving" field in Airtable automatically
  - Adds "OWNER ARRIVING" to service line descriptions
- **Service Line Hierarchy**:
  1. Custom Instructions (max 200 chars)
  2. OWNER ARRIVING (if owner is arriving)
  3. LONG TERM GUEST DEPARTING (if 14+ day stay)
  4. Base service name (e.g., "Turnover STR Next Guest July 3")
- **Example**: `Custom text - OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 3`

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
- **Forwarding Auth**: `X-Internal-Auth: [SERVATIV_WEBHOOK_SECRET from env]`
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

### **Sync Field Business Rules & Message Formatting (v2.2.8)**

#### **Comprehensive Sync Field Management**
- **Complete Business Rules**: See `docs/sync-field-business-rules.md` for detailed field usage guidelines
- **Message Formatting Standards**: All sync messages use right-side timestamps (`[content] - Jul 10, 3:45 PM`)
- **Airtable Compatibility**: Fixed problematic `**bold**` markdown that displayed as literal asterisks
- **Cross-System Consistency**: Standardized formatting across 6 components:
  - syncMessageBuilder.js (development)
  - jobs.js & schedules.js (API handlers)
  - webhook.py (webhook processing)
  - dev-hcp-sync.cjs & prod-hcp-sync.cjs (sync scripts)

#### **Field Separation Strategy**
- **Schedule Sync Details**: Alert field - only populated when schedules are mismatched
- **Service Sync Details**: Activity log - continuously updated with all operations
- **Reduced Noise**: Webhook updates only for significant status changes (In Progress, Completed, Canceled)

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

### **Important Code Structure Notes**
- **API Handlers**: Job creation logic is in `handlers/jobs.js` (NOT `handlers/createJob.js` which was removed)
- **Long-term Guest Logic**: Implemented in dev-hcp-sync.cjs, prod-hcp-sync.cjs, and handlers/jobs.js
- **Job Type IDs**: Stored in environment variables (never hardcoded)

### **Production Data Volumes**
- **ICS Processing**: 246 feeds (production), 255 feeds (development)
- **Sources**: Airbnb, VRBO, Booking.com, Hospitable, and other property management systems
- **CSV Processing**: Daily iTrip reports and Evolve data automatically processed
- **Environment Isolation**: Complete separation between dev and prod data flows

## Duplicate Detection Test Framework (v2.2.8)

### Automated Testing
The system now includes automated duplicate detection testing that runs after every ICS and CSV processing:

#### Test Scenarios
1. **New reservation** - New UID and dates should be created
2. **Same UID modifications** - Same UID with changes should update existing
3. **UID removed (future)** - Missing UID with future checkout marks as removed
4. **Different UID same dates** - Lodgify case - new UID but same dates ignores duplicate
5. **Same UID different dates** - Date change for same UID updates existing
6. **Block vs Reservation** - Different entry types are separate

#### Integration
- **ICS Processing**: Tests run automatically after successful processing
- **CSV Processing**: Tests run automatically after successful processing
- **Results Storage**: Test results are saved to Airtable "Automation" table
- **Record Name**: "Duplicate Detection Tests"
- **Fields Updated**:
  - `Last Ran Time`: Timestamp of test execution
  - `Sync Details`: Detailed test results with pass/fail for each scenario
  - `Active`: Checkbox indicating if all tests passed

#### Manual Testing
```bash
# Run tests standalone
python3 src/automation/scripts/test_duplicate_detection_framework.py

# View test results in logs
tail -f src/automation/logs/ics_sync_*.log | grep "duplicate detection"
tail -f src/automation/logs/csv_sync_*.log | grep "duplicate detection"
```

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

