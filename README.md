# Property Management Automation System

**Version 2.2.0** - Environment Separation, ICS Processor Fixes & Automation Improvements

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

### Universal Runner (Auto-detects Environment)
```bash
# Works from anywhere, auto-detects environment
python3 src/run_anywhere.py --info           # Show system information
python3 src/run_anywhere.py --test           # Run system tests
python3 src/run_anywhere.py                  # Run automation
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
│   ├── VERSION                             # Current version (2.2.0)
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
│       ├── run_anywhere.py                # ⭐ Universal runner
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
└── 🔧 Development Tools
    ├── tools/airtable-mcp-server/          # Airtable MCP integration
    ├── test_setup.py                      # Setup validation
    └── docs/                              # Documentation
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

### 2. **Configure Environments**
```bash
# Development credentials (secure permissions automatically applied)
nano config/environments/dev/.env

# Production credentials (secure permissions automatically applied)  
nano config/environments/prod/.env
```

### 3. **Set Up Automation Schedules**
```bash
# Development (every 30 minutes for testing)
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

### **4. ICS Calendar Sync**
- Synchronizes calendar data from property management systems
- Real-time availability updates
- Conflict detection and resolution

### **5. Service Job Management**
- HousecallPro integration for service scheduling
- Automatic job creation and status updates
- Environment-specific API endpoints
- **NEW**: Service Line Custom Instructions support
  - Appends custom instructions to job service names
  - Automatic truncation to 200 characters for compatibility
  - Full Unicode support (accents, special characters, emojis)

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
# Webhook endpoint
https://servativ.themomentcatchers.com/webhooks/hcp

# Forwarding authentication header
X-Internal-Auth: sk_servativ_webhook_7f4d9b2e8a3c1f6d
```

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

### **Version 2.0.0** (Current)
- ✅ **Complete environment separation** (dev/prod isolation)
- ✅ **Enterprise security enhancements** (secure credential handling)
- ✅ **Robust error handling** (enhanced validation & safety checks)
- ✅ **Production-ready deployment** (cron jobs, logging, monitoring)

### **Version 1.2.0** (Previous)
- Project restructuring and timezone implementation
- Centralized configuration system
- Cross-platform compatibility improvements

## 🤝 Support

For issues, feature requests, or contributions:

1. **Check Documentation**: Review this README and configuration guides
2. **Run Diagnostics**: Use `python3 src/run_anywhere.py --info` and `--test`
3. **Check Logs**: Review environment-specific log files
4. **Validate Config**: Ensure .env files are properly configured

---

**🎉 The system is now enterprise-ready with complete environment separation, enhanced security, and production-grade reliability!**