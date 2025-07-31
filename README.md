# Property Management Automation System

**Version 2.2.15** - Service Line Description Fix

A comprehensive, enterprise-grade automation system for property management operations with complete development/production environment separation, enhanced security, and robust error handling.

## 🚀 Quick Start

### Development Environment
```bash
# Run development automation (uses dev Airtable base)
python3 src/run_automation_dev.py --dry-run  # Test first
python3 src/run_automation_dev.py            # Run for real

# List available automations
python3 src/run_automation_dev.py --list
```

### Production Environment
```bash
# Run production automation (uses prod Airtable base)
python3 src/run_automation_prod.py --dry-run  # Test first
python3 src/run_automation_prod.py            # Run for real

# List available automations
python3 src/run_automation_prod.py --list
```


## 🏗️ Architecture Overview

### **Complete Environment Separation**
This system provides complete isolation between development and production:

| Aspect | Development | Production |
|--------|-------------|------------|
| **Runner Script** | `run_automation_dev.py` | `run_automation_prod.py` |
| **Airtable Base** | `app67yWFv0hKdl6jM` | `appZzebEIqCU5R9ER` |
| **CSV Directories** | `CSV_*_development/` | `CSV_*_production/` |
| **Log Files** | `automation_dev*.log` | `automation_prod*.log` |
| **API Endpoints** | `/api/dev/*` | `/api/prod/*` |
| **Cron Schedule** | Every 4 hours (:10 past) | Every 4 hours (:00) |

### **Security Features**
- 🔒 **Credential Protection**: Environment-specific .env files with secure permissions
- 🛡️ **Environment Safety**: Cross-environment execution protection
- 🚨 **Enhanced Validation**: Robust configuration validation with detailed error messages
- 🔐 **API Security**: Separate API keys and endpoints for each environment

## 📁 Project Structure

```
automation/                                 # Project root
├── 📄 Core System Files
│   ├── README.md                           # This comprehensive guide
│   ├── VERSION                             # Current version (2.2.13)
│   ├── CHANGELOG.md                        # Version history
│   ├── setup.py                           # Package installation config
│   ├── requirements.txt                   # Python dependencies
│   ├── .env                               # Main environment configuration
│   ├── CRITICAL_FIXES_COMPLETED.md        # Security & reliability fixes
│   └── ENVIRONMENT_SEPARATION_COMPLETE.md # Complete implementation guide
│
├── 🔧 Configuration System (NEW v2.0)
│   └── config/
│       └── environments/
│           ├── dev/.env                    # Development credentials (secure)
│           └── prod/.env                   # Production credentials (secure)
│
├── 🐍 Python Package Structure
│   └── src/
│       ├── run_automation_dev.py           # ⭐ Development automation runner
│       ├── run_automation_prod.py          # ⭐ Production automation runner
│       └── automation/                    # Main package source
│           ├── config_base.py              # ⭐ Base configuration class
│           ├── config_dev.py               # ⭐ Development configuration
│           ├── config_prod.py              # ⭐ Production configuration
│           ├── config_wrapper.py           # ⭐ Auto-environment detection
│           ├── controller.py               # ⭐ Automation orchestration
│           ├── scripts/                    # Individual automation scripts
│           │   ├── CSV_process_development/ # Dev CSV processing
│           │   ├── CSV_process_production/  # Prod CSV processing
│           │   ├── CSV_done_development/    # Dev CSV archive
│           │   ├── CSV_done_production/     # Prod CSV archive
│           │   ├── gmail/                  # Gmail CSV downloader
│           │   ├── evolve/                 # Evolve property scraper
│           │   ├── CSVtoAirtable/          # CSV processing engine
│           │   ├── icsAirtableSync/        # Calendar synchronization
│           │   ├── webhook/                # Webhook handlers
│           │   └── airscripts-api/         # Airtable API server
│           ├── logs/                       # Environment-specific logs
│           └── tests/                      # Comprehensive test suite
│
├── 🛠️ Deployment & Operations
│   ├── cron_setup_dev.sh                  # Setup development cron (30min)
│   ├── cron_setup_prod.sh                 # Setup production cron (4hr)
│   ├── cron_remove.sh                     # Remove old cron jobs
│   └── backups/                           # Backup storage
│
├── 🔧 Development Tools & MCP Servers
│   ├── tools/airtable-mcp-server/          # Airtable MCP integration for Claude
│   ├── tools/hcp-mcp-dev/                 # HousecallPro MCP server (development)
│   ├── tools/hcp-mcp-prod/                # HousecallPro MCP server (production)
│   ├── tools/hcp-mcp-common/              # Shared HCP MCP functionality
│   ├── test_setup.py                      # Setup validation
│   └── docs/                              # Documentation
│
└── 📚 Reference Scripts
    └── src/automation/scripts/airtable-automations/
        ├── README.md                       # Script documentation
        ├── find-next-guest-date.js        # Next guest and same-day detection
        └── update-service-line-description.js # Service line builder with long-term logic
```

## 🚦 Installation & Setup

### 1. **Environment Setup**
```bash
# Clone the repository
git clone <your-repo-url>
cd automation

# Install Python dependencies
pip3 install -r requirements.txt

# Validate setup
python3 test_setup.py
```

### 2. **Cleanup Scripts**
```bash
# Clean up duplicate reservations
python3 src/automation/scripts/cleanup-duplicate-reservations.py --env prod --dry-run  # Test first
python3 src/automation/scripts/cleanup-duplicate-reservations.py --env prod --execute  # Run cleanup
```

### 3. **Configure Environments**
```bash
# Development credentials (secure permissions automatically applied)
nano config/environments/dev/.env

# Production credentials (secure permissions automatically applied)  
nano config/environments/prod/.env
```

### 4. **Set Up Automation Schedules**
```bash
# Development (every 4 hours + 10 minutes after production)
./cron_setup_dev.sh

# Production (every 4 hours for business operations)
./cron_setup_prod.sh

# Remove old cron jobs if needed
./cron_remove.sh
```

## 🔄 Automation Components

### **1. Gmail CSV Downloader**
- Downloads iTrip reservation reports from Gmail
- OAuth2 authentication with automatic token refresh
- Environment-specific download directories

### **2. Evolve Property Scraper**
- Scrapes property data using Selenium WebDriver
- Headless operation with comprehensive error handling
- Environment-aware configuration

### **3. CSV Processing Engine**
- Processes iTrip and Evolve CSV files to Airtable
- Complete change tracking and history preservation
- Environment-specific processing workflows
- **Duplicate Detection Fix** (June 23, 2025):
  - Fixed composite UID vs base UID lookup mismatch
  - Now correctly indexes by both composite and base UIDs
  - Prevents duplicate reservations from being created

### **4. ICS Calendar Sync**
- Synchronizes calendar data from property management systems
- Real-time availability updates
- Conflict detection and resolution
- **Safe Removal System** (v2.2.12):
  - Prevents false removals from temporary feed issues
  - Requires 3 consecutive missing syncs before marking as "Removed"
  - 12-hour grace period for additional safety
  - Protects active HCP jobs, recent check-ins, imminent checkouts
  - Automatic recovery when reservation reappears
  - Tracking fields: `Missing Count`, `Missing Since`, `Last Seen`

### **5. Service Job Management**
- HousecallPro integration for service scheduling
- Automatic job creation and status updates
- Environment-specific API endpoints
- **Service Line Custom Instructions support**
  - Custom instructions appear first in service name: `${customInstructions} - ${baseSvcName}`
  - Automatic truncation to 200 characters for compatibility
  - Full Unicode support (accents, special characters, emojis)
  - Debug logging for troubleshooting service name construction
- **Long-term Guest Detection** (NEW)
  - Automatically detects stays of 14+ days
  - Adds "LONG TERM GUEST DEPARTING" to service name
  - Works with all job creation methods (dev/prod sync, API)
  - Format: `${customInstructions} - LONG TERM GUEST DEPARTING ${baseSvcName}`

### **6. Service Line Updates with Owner Detection** (v2.2.8+)
Enhanced service line update script that automatically detects owner arrivals:

#### **Owner Detection Logic**:
- Detects when a property owner is arriving (Block entry type)
- Checks if block checks in same day or next day after reservation checkout
- Automatically sets "Owner Arriving" field in Airtable
- Adds "OWNER ARRIVING" to service line description

#### **iTrip Next Guest Date Override** (NEW v2.2.10):
- iTrip Next Guest Date field now takes precedence over calculated dates
- When an iTrip reservation has this field populated, it overrides the normal next guest lookup
- Ensures accuracy for iTrip-specific scheduling requirements

#### **Service Line Description Hierarchy**:
1. Custom Instructions (max 200 chars)
2. **OWNER ARRIVING** (if owner is arriving) - NEW v2.2.13: Not marked as same-day turnover
3. LONG TERM GUEST DEPARTING (if 14+ day stay)
4. Base service name (e.g., "Turnover STR Next Guest July 3")

#### **Example Output**:
- Regular: `Turnover STR Next Guest July 3`
- With owner: `OWNER ARRIVING - Turnover STR Next Guest July 3`
- Full: `Custom instructions - OWNER ARRIVING - LONG TERM GUEST DEPARTING - Turnover STR Next Guest July 3`

### **7. HCP MCP Server Integration** (Enhanced v2.2.1)
Claude AI can interact with HousecallPro data through enhanced MCP servers:

#### **New Search Tools**:
- `search_addresses`: Find customer addresses by street, city, customer name, or customer ID
  - Example: `search_addresses(street="26208 N 43rd")`
- `get_jobs_by_address`: Get jobs for specific addresses with filtering
  - Example: `get_jobs_by_address(address_id="adr_123", work_status="completed")`

#### **Advanced Analysis Tools**:
- `analyze_laundry_jobs`: Analyze laundry-related services
- `analyze_service_items`: Search for specific service items (towels, linens)
- `analyze_customer_revenue`: Customer revenue and job statistics
- `analyze_towel_usage`: Towel usage and cost analysis

#### **Enhanced Error Handling**:
- Specific error types with actionable suggestions
- `CustomerHasNoJobs`: Suggests using list_jobs with customer_id filter
- `CustomerNotFound`: Suggests verifying customer ID format
- `InvalidPermissions`: Suggests checking API key permissions

#### **Performance Improvements**:
- Small responses (<500KB) include data directly
- Enhanced cache search with JSONPath-like queries
- Better handling of nested JSON structures

### **8. Airtable Automation Scripts** (NEW)
Reference scripts for Airtable automations located in `src/automation/scripts/airtable-automations/`:

#### **find-next-guest-date.js**
- Finds the next guest reservation for a property
- Detects same-day turnovers using >= date comparison
- Updates `Next Guest Date` and `Same-day Turnover` fields

#### **update-service-line-description.js**
- Builds complete service line descriptions with 3-step construction:
  1. Base service name (with same-day/next guest info)
  2. Long-term guest detection (14+ days)
  3. Final assembly with custom instructions
- Uses pre-calculated `Next Guest Date` when available
- Truncates custom instructions to 200 characters

### **9. Job Reconciliation** (NEW v2.2.5)
Automatically matches existing HCP jobs to Airtable reservations when jobs are created outside normal automation flow:

#### **Standalone Script**
```bash
# Dry run - shows what would be matched
python3 src/automation/scripts/hcp/reconcile-jobs-dev.py

# Execute reconciliation
python3 src/automation/scripts/hcp/reconcile-jobs-dev.py --execute
```

#### **Webhook Integration** (Automatic)
- Triggers when webhooks arrive for unlinked jobs
- Matches based on property, customer, and time (±1 hour)
- Currently dev environment only (configurable)
- Setup: `python3 src/automation/scripts/webhook/integrate_reconciliation.py`

## 🔧 Configuration System

### **Environment-Aware Configuration**
The system uses a sophisticated configuration hierarchy:

1. **Base Configuration** (`config_base.py`) - Shared functionality
2. **Environment-Specific** (`config_dev.py`, `config_prod.py`) - Credentials and settings
3. **Auto-Detection** (`config_wrapper.py`) - Automatic environment selection

### **Environment Variables**
```bash
# Development
DEV_AIRTABLE_API_KEY=pat...
DEV_AIRTABLE_BASE_ID=app...
DEV_HCP_TOKEN=...

# Production  
PROD_AIRTABLE_API_KEY=pat...
PROD_AIRTABLE_BASE_ID=app...
PROD_HCP_TOKEN=...
```

## 🚨 Security Features

### **Credential Protection**
- Environment-specific .env files with `600` permissions
- No world-readable credential files
- Separate API keys for dev/prod environments

### **Environment Safety**
- Automatic hostname-based environment detection
- Warning prompts for cross-environment execution
- `--force` flag for intentional overrides

### **Enhanced Validation**
- API key format validation (must start with 'pat', minimum 20 chars)
- Base ID validation (must start with 'app', exactly 17 chars)
- Empty credential detection with detailed error messages

## 🔗 Webhook Integration

### **HousecallPro Webhook Handler**
- Secure webhook endpoint for real-time HCP events
- Automatic job status synchronization with Airtable
- **NEW**: Webhook forwarding support
  - Accepts forwarded webhooks from Servativ's Java service
  - Shared secret authentication (X-Internal-Auth header)
  - Always returns 200 status to prevent webhook disabling
  - Dual authentication: HCP signature or forwarding secret

### **Webhook Configuration**
```bash
# HCP Status Webhook
https://servativ.themomentcatchers.com/webhooks/hcp

# Service Line Update Webhook (NEW v2.2.13)
https://servativ.themomentcatchers.com/api/prod/automation/update-service-line

# Forwarding authentication header
X-Internal-Auth: [SERVATIV_WEBHOOK_SECRET from environment]
```

### **Service Line Auto-Update** (NEW v2.2.13)
- Real-time synchronization of service line descriptions to HCP
- Webhook-triggered when "Service Line Description" changes in Airtable
- Pipe-separated format preserves manual notes: `"Manual notes | Auto-generated"` 
- Smart logic:
  - Only updates when content changes
  - Preserves existing manual notes before pipe
  - Auto-adds pipe separator if missing
  - Handles 200-char HCP limit
- Currently limited to test property for safety
- See `/docs_v2/service-line-auto-update.md` for full details

## 📊 Operations & Monitoring

### **Logging**
```bash
# Development logs
tail -f src/automation/logs/automation_dev*.log

# Production logs  
tail -f src/automation/logs/automation_prod*.log

# Cron job logs
tail -f src/automation/logs/automation_*_cron.log
```

### **Monitoring Commands**
```bash
# Check automation status
python3 src/run_automation_dev.py --list    # Dev environment
python3 src/run_automation_prod.py --list   # Prod environment

# System information
python3 src/run_anywhere.py --info

# Test system health
python3 src/run_anywhere.py --test
```

### **Cron Job Management**
```bash
# View current cron jobs
crontab -l

# Setup development automation (30 min intervals)
./cron_setup_dev.sh

# Setup production automation (4 hour intervals)  
./cron_setup_prod.sh
```

## 🔧 Development

### **Entry Points**
After installation (`pip install -e .`):
```bash
run-automation-dev      # Development automation
run-automation-prod     # Production automation
run-automation          # Universal runner
evolve-scraper          # Evolve property scraper
csv-processor           # CSV processing tool
ics-sync               # Calendar synchronization
gmail-downloader       # Gmail CSV downloader
```

### **Testing**
```bash
# Run comprehensive tests
python3 -m pytest tests/ -v

# Test with coverage
python3 -m pytest tests/ --cov=automation

# Integration testing
python3 src/run_anywhere.py --test
```

### **Code Quality**
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/
```

## 🚀 Deployment

### **Production Deployment Checklist**
- ✅ Configure production environment variables
- ✅ Set up production cron schedule  
- ✅ Verify file permissions (600 for .env files)
- ✅ Test production automation with `--dry-run`
- ✅ Monitor initial production runs
- ✅ Verify log file separation

### **Environment Verification**
```bash
# Verify development environment
python3 src/run_automation_dev.py --dry-run

# Verify production environment  
python3 src/run_automation_prod.py --dry-run

# Check configuration
python3 -c "
from src.automation.config_dev import DevConfig
from src.automation.config_prod import ProdConfig
print('Dev errors:', DevConfig().validate_config())
print('Prod errors:', ProdConfig().validate_config())
"
```

## 📋 Troubleshooting

### **Common Issues**
1. **Config Validation Errors**: Check environment-specific .env files
2. **Permission Denied**: Ensure .env files have correct permissions (600)
3. **Import Errors**: Verify Python path and package installation
4. **Airtable 403 Errors**: Check API keys and base IDs
5. **Cron Job Failures**: Verify paths and Python executable
6. **Airtable Shows Failures Despite Successful Runs**: 
   - Check for duplicate Airtable native automations running at X:06-X:07
   - These fail and overwrite successful cron results
   - Access Airtable web interface → Automations tab to disable/fix them
   - See CHANGELOG v2.2.12 for details

### **Debug Commands**
```bash
# Check system information
python3 src/run_anywhere.py --info

# Validate configuration
python3 -c "from src.automation.config_wrapper import Config; print(Config.validate_config())"

# Test imports
python3 -c "from src.automation.controller import AutomationController; print('OK')"
```

## 📝 Version History

### **Version 2.2.13** (Current)
- ✅ **Owner Arrival Same-Day Fix** - Owner arrivals no longer marked as same-day turnovers to prevent sync conflicts
- ✅ **Service Time Logic** - Owner arrivals should get 10:00 AM service time (vs 10:15 AM default)
- ✅ **Prevents Modified Records** - Eliminates false "modified" records from same-day field mismatches

### **Version 2.2.12**
- ✅ **Safe ICS Removal System** - 3-sync confirmation before marking feeds as removed
- ✅ **12-Hour Grace Period** - Additional safety for temporary feed issues
- ✅ **Automatic Recovery** - Reservations reappear when feeds come back online

### **Version 2.2.10-2.2.11**
- ✅ **Enhanced Sync Status Reporting** - Detailed breakdowns of new/modified/removed with reservation/block counts
- ✅ **iTrip Next Guest Date Override** - Field now takes precedence over calculated dates
- ✅ **Fixed Double Error Symbols** - Removed duplicate ❌ in sync failure messages
- ✅ **iTrip Same-Day Detection Fix** - Python script correctly detects same-day turnovers with iTrip dates

### **Version 2.2.8-2.2.9**
- ✅ **Enhanced Service Line Updates with Owner Detection**
- ✅ **Hybrid UID Duplicate Detection** - Composite UID support for CSV processing
- ✅ **Long-term Guest Detection** (14+ day stays get "LONG TERM GUEST DEPARTING" prefix)
- ✅ **Service Line Custom Instructions Fix** (proper format: `${customInstructions} - ${baseSvcName}`)
- ✅ **HCP MCP Server Enhancements** (new search tools, analysis capabilities)
- ✅ **Complete environment separation** (dev/prod isolation)
- ✅ **Enterprise security enhancements** (secure credential handling)
- ✅ **Enhanced error handling with actionable suggestions**

### **Version 1.2.0** (Previous)
- Project restructuring and timezone implementation
- Centralized configuration system
- Cross-platform compatibility improvements

## 📚 Operational Documentation

### **Daily Operations Guides**
Complete operational documentation for property management staff:

- **[Operational Scenarios](docs/operations/OPERATIONAL_SCENARIOS.md)** - 30 real-world scenarios with step-by-step resolutions
- **[Scenarios by View](docs/operations/OPERATIONAL_SCENARIOS_BY_VIEW.md)** - Scenarios organized by Airtable views
- **[Quick Reference](docs/operations/SCENARIOS_QUICK_REFERENCE.md)** - Emergency procedures and decision trees
- **[Training Checklist](docs/operations/OPERATIONAL_TRAINING_CHECKLIST.md)** - 3-week training program for new operators
- **[Data Examples](docs/operations/OPERATIONAL_DATA_EXAMPLES.md)** - Real data patterns and edge cases
- **[View Scenarios](docs/operations/AIRTABLE_VIEW_SCENARIOS.md)** - View-specific workflows and filters

### **Technical Documentation**
- **[System Logical Flow](docs/audit/SYSTEM_LOGICAL_FLOW.md)** - Complete system architecture and workflows
- **[Sync Field Logic](docs/operations/SYNC_FIELD_LOGIC_EXPLAINED.md)** - Understanding sync statuses and troubleshooting
- **[API Documentation](docs/api/)** - API endpoints and integration guides

## 🤝 Support

For issues, feature requests, or contributions:

1. **Check Documentation**: Review this README and operational guides
2. **Run Diagnostics**: Use `python3 src/run_anywhere.py --info` and `--test`
3. **Check Logs**: Review environment-specific log files
4. **Validate Config**: Ensure .env files are properly configured

---

**🎉 The system is now enterprise-ready with complete environment separation, enhanced security, production-grade reliability, and comprehensive operational documentation!**