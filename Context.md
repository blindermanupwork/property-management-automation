# /home/opc/automation/

## Purpose
This is the root directory of a comprehensive property management automation system (v2.2.2) that handles vacation rental operations with complete development/production environment separation. The system processes hundreds of reservations daily from multiple sources and integrates with Airtable and HousecallPro for job management.

## Key Files and What They Do

### **Core System Files**
- `README.md` - Comprehensive system documentation and usage guide
- `VERSION` - Current version number (2.2.2)
- `CHANGELOG.md` - Version history and changes
- `setup.py` - Python package installation configuration
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Modern Python project configuration

### **Environment Management**
- `config/environments/dev/.env` - Development environment credentials (secure)
- `config/environments/prod/.env` - Production environment credentials (secure)

### **Automation Scripts**
- `cron_setup_dev.sh` - Setup development cron jobs (every 4hr at :10)
- `cron_setup_prod.sh` - Setup production cron jobs (every 4hr at :00)
- `cron_remove.sh` - Remove old cron jobs

### **MCP Server Integration**
- `airtable-mcp-wrapper.sh` - Wrapper script for Airtable MCP server
- `tools/` - Contains MCP servers for Claude integration

## How to Use the Code

### **Quick Start Commands**
```bash
# Development Environment
python3 src/run_automation_dev.py --dry-run  # Test first
python3 src/run_automation_dev.py            # Run for real

# Production Environment  
python3 src/run_automation_prod.py --dry-run  # Test first
python3 src/run_automation_prod.py            # Run for real

# Universal Runner (Auto-detects Environment)
python3 src/run_anywhere.py --info           # Show system information
python3 src/run_anywhere.py --test           # Run system tests
python3 src/run_anywhere.py                  # Run automation
```

### **Installation and Setup**
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Validate setup
python3 test_setup.py

# 3. Configure environments
nano config/environments/dev/.env
nano config/environments/prod/.env

# 4. Set up automation schedules
./cron_setup_dev.sh    # Development
./cron_setup_prod.sh   # Production
```

### **Development Commands**
```bash
# Package installation
pip3 install -e .                            # Install in development mode
python3 -m build                             # Build package

# Testing
pytest tests/ -v                             # Run tests with verbose output
pytest tests/ --cov=automation               # Run tests with coverage

# Code quality
black src/ tests/                            # Format code
isort src/ tests/                            # Sort imports  
mypy src/                                    # Type checking
```

## Dependencies and Requirements

### **Python Dependencies**
- Python 3.8+ required
- Key packages: requests, pandas, pyairtable, selenium, google-api-python-client
- Full list in `requirements.txt`

### **System Requirements**
- Linux/Unix environment (tested on Oracle Linux)
- Cron for scheduled execution
- Node.js (for MCP servers and API services)
- Chrome/Chromium (for Selenium web scraping)

### **External Integrations**
- **Airtable**: Central data store (separate dev/prod bases)
- **HousecallPro**: Service job management
- **Gmail**: iTrip CSV report downloads
- **Evolve**: Property data scraping
- **ICS Feeds**: Calendar synchronization

## Common Workflows and Operations

### **Daily Operations Workflow**
1. **Automated Processing** (every 4 hours via cron):
   - Gmail downloads iTrip reservation CSVs
   - Evolve scrapes property data
   - CSV processor syncs data to Airtable
   - ICS sync updates calendar availability
   - Service jobs created in HousecallPro

2. **Manual Operations**:
   - Monitor logs: `tail -f src/automation/logs/automation_*.log`
   - Check system status: `python3 src/run_anywhere.py --info`
   - Test changes: Use `--dry-run` flag before real execution

### **Environment Separation**
- **Development**: Uses `app67yWFv0hKdl6jM` Airtable base, processes to `CSV_*_development/`
- **Production**: Uses `appZzebEIqCU5R9ER` Airtable base, processes to `CSV_*_production/`
- Complete isolation prevents cross-environment data contamination

### **Error Handling and Troubleshooting**
```bash
# Check system health
python3 src/run_anywhere.py --test

# Validate configuration
python3 -c "from src.automation.config_wrapper import Config; print(Config.validate_config())"

# View recent logs
tail -100 src/automation/logs/automation_*.log

# Check cron jobs
crontab -l
```

### **MCP Server Operations**
```bash
# Start Airtable MCP server
./tools/start-airtable-mcp.sh

# Test MCP connectivity
node tools/test-mcp-connection.js

# Build HCP MCP servers
cd tools/hcp-mcp-dev && npm run build
cd tools/hcp-mcp-prod && npm run build
```

## Key Features
- **Complete Environment Separation**: Dev/prod isolation
- **Enterprise Security**: Secure credential handling, environment validation
- **Service Line Custom Instructions**: Unicode support, 200-char truncation
- **Webhook Forwarding**: Dual authentication support
- **Real-time Processing**: Live console output, comprehensive logging
- **Claude Integration**: MCP servers for AI-powered data access and analysis