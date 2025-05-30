# Property Management Automation System

**Version 1.2.0** - Complete Project Restructuring & Timezone Implementation

A comprehensive, cross-platform automation system for property management operations including CSV processing, calendar synchronization, web scraping, and service integrations.

## 🚀 Quick Start

### Option 1: Universal Runner (No Installation)
```bash
git clone <your-repo-url>
cd automation
python src/run_anywhere.py    # Auto-detects environment and runs
```

### Option 2: Package Installation
```bash
pip install -e .           # Install in development mode
run-automation             # Run from anywhere
```

### Option 3: Test First
```bash
python test_setup.py       # Validate setup
python src/run_anywhere.py --test  # Run system tests
```

## 📁 Complete File Structure

```
automation/                          # Project root
├── 📄 Core System Files
│   ├── README.md                    # This comprehensive guide
│   ├── VERSION                      # Current version number (1.2.0)
│   ├── CHANGELOG.md                 # Version history
│   ├── setup.py                    # Package installation config
│   ├── pyproject.toml              # Modern Python packaging
│   ├── requirements.txt            # Python dependencies
│   ├── package.json                # Node.js dependencies
│   ├── package-lock.json           # Locked Node.js versions
│   ├── test_setup.py               # Setup validation script
│   └── .env                        # Environment configuration (create from template)
│
├── 🐍 Python Package Structure (REORGANIZED)
│   └── src/
│       ├── run_anywhere.py         # ⭐ Universal runner (works from anywhere)
│       └── automation/             # Main package source
│           ├── __init__.py         # Package initialization
│           ├── config.py           # ⭐ Centralized configuration system
│           ├── controller.py       # ⭐ Automation orchestration
│           ├── bin/                # Shell scripts directory  
│           │   ├── backup.sh       # Data backup system
│           │   ├── deploy.sh       # Production deployment
│           │   ├── deploy_to_prod.sh # Git-based deployment workflow
│           │   ├── monitor.sh      # Production health monitoring
│           │   └── setup_cron.sh   # Automated scheduling setup
│           ├── logs/               # ⭐ Centralized application logs
│           │   ├── alerts.log      # Alert notifications
│           │   ├── automation_cron.log # Scheduled execution logs
│           │   ├── csv_sync.log    # CSV processing logs
│           │   ├── ics_sync.log    # Calendar sync logs
│           │   └── webhook.log     # Webhook handling logs
│           ├── scripts/            # ⭐ All automation scripts organized
│           │   ├── __init__.py     # Scripts package init
│           │   ├── run_automation.py # Main automation runner
│           │   ├── CSV_done/       # ⭐ Processed CSV files
│           │   ├── CSV_process/    # ⭐ Incoming CSV files  
│           │   ├── CSVtoAirtable/  # CSV processing system
│           │   │   ├── config.py   # CSV processor config
│           │   │   └── csvProcess.py # Main CSV processing logic
│           │   ├── gmail/          # Email integration
│           │   │   ├── credentials.json # Google OAuth credentials
│           │   │   ├── gmail_downloader.py # iTrip CSV downloader
│           │   │   ├── processed_emails.txt # Tracking file
│           │   │   └── token.pickle # OAuth token cache
│           │   ├── evolve/         # Web scraping
│           │   │   └── evolveScrape.py # Evolve property data scraper
│           │   ├── icsAirtableSync/ # Calendar integration
│           │   │   └── icsProcess.py # ICS calendar processor
│           │   ├── webhook/        # Webhook handlers
│           │   │   ├── webhook.py  # Flask webhook server
│           │   │   └── notes.txt   # Webhook documentation
│           │   ├── airtable-agent/ # AI-powered agent
│           │   │   ├── airtable-agent.js # Node.js AI agent
│           │   │   ├── systemPrompt.js # AI system prompts
│           │   │   ├── package.json # Agent dependencies
│           │   │   └── public/     # Web interface assets
│           │   ├── hcp/            # HousecallPro integration
│           │   │   ├── hcp_sync.js # HCP synchronization service
│           │   │   └── agent.log   # HCP service logs
│           │   ├── release.sh      # Version release automation
│           │   └── version.sh      # Version display utility
│           ├── tests/              # ⭐ Comprehensive test suite
│           │   ├── __init__.py     # Test package init
│           │   ├── test_config.py  # Configuration system tests
│           │   ├── test_controller.py # Controller functionality tests
│           │   └── test_portability.py # Cross-platform compatibility tests
│           └── utils/              # Utility modules
│
├── 📚 Documentation
│   └── docs/                       # Additional documentation
│       └── INSTALLATION.md         # Detailed installation guide
│
├── ⚙️ Configuration
│   └── config/                     # Configuration management
│       └── environments/           # Environment-specific configs
│           ├── dev/                # Development environment
│           └── prod/               # Production environment
│
└── 📊 Data Directories
    └── backups/                    # System backups (auto-created)
```

## 🎯 Core Features

### **Automation Components**
- **📧 iTrip CSV Download**: Automated Gmail integration for CSV retrieval with Arizona timezone timestamps
- **🏠 Evolve Scraping**: Web scraping for property data collection with PST browser time and Arizona data timestamps
- **📊 CSV Processing**: Intelligent CSV-to-Airtable synchronization with conflict prevention and timezone-aware data
- **📅 ICS Calendar Sync**: Multi-source calendar data integration with timezone normalization
- **🔧 HousecallPro Integration**: Service job management and synchronization with Arizona timezone consistency
- **🤖 AI Agent**: OpenAI-powered Airtable data agent
- **🕐 Webhook Server**: Flask-based webhook handler with PST logging and Arizona data timestamps

### **System Features**
- **🌍 Cross-Platform**: Works on Windows, macOS, and Linux with pathlib compatibility
- **📦 Portable**: Run from any directory without installation via `run_anywhere.py`
- **⚙️ Environment-Aware**: Automatic dev/prod environment detection with Airtable base switching
- **🔍 Self-Testing**: Built-in validation and health checks with comprehensive test suite
- **📝 Comprehensive Logging**: Centralized logging with PST timestamps for system operations
- **🕐 Timezone Management**: Dual-timezone strategy (PST for logs, Arizona for business data)
- **🔄 Automatic Backup**: Scheduled data protection with configurable retention
- **📈 Production Monitoring**: Health checks and alerting with Airtable-based control
- **🏗️ Professional Structure**: Organized `/src/automation/` package structure following Python best practices

## 🚀 Usage Guide

### **Development & Testing**
```bash
# Validate setup
python test_setup.py

# Test all components
python src/run_anywhere.py --test

# List available automations
python src/run_anywhere.py --list

# Show system information
python src/run_anywhere.py --info

# Install missing dependencies automatically
python src/run_anywhere.py --auto-install
```

### **Running Automations**
```bash
# Run all automations (respects Airtable control settings)
python src/run_anywhere.py

# Package installation method
pip install -e .
run-automation

# Direct module execution
python -m automation.scripts.run_automation
```

### **Production Operations**
```bash
# Deploy to production
./bin/deploy_to_prod.sh

# Manual deployment
./bin/deploy.sh

# System health check
./bin/monitor.sh

# Create system backup
./bin/backup.sh

# Setup automated scheduling
./bin/setup_cron.sh

# Check version
./scripts/version.sh

# Create new release
./scripts/release.sh patch "Bug fixes and improvements"
```

### **Individual Script Execution**
```bash
# Gmail CSV download
python src/automation/scripts/gmail/gmail_downloader.py

# Evolve data scraping  
python src/automation/scripts/evolve/evolveScrape.py --headless

# CSV processing
python src/automation/scripts/CSVtoAirtable/csvProcess.py

# ICS calendar sync
python src/automation/scripts/icsAirtableSync/icsProcess.py

# Webhook server
python src/automation/scripts/webhook/webhook.py

# AI agent (Node.js)
cd src/automation/scripts/airtable-agent && node airtable-agent.js

# HousecallPro sync (Node.js)  
cd src/automation/scripts/hcp && node hcp_sync.js
```

## 🕐 Timezone Management

### **Dual-Timezone Strategy**
The system implements a sophisticated dual-timezone approach for optimal usability and business consistency:

#### **PST (Pacific Standard Time) - System Operations**
- **All log timestamps**: System logs, error messages, debug output
- **Health check responses**: `/health` endpoint timestamps
- **Browser automation**: Evolve scraper forces browser to use PST
- **User-facing timestamps**: System information and status displays

```python
# PST timezone implementation across all scripts
pst = pytz.timezone('US/Pacific')
class PSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=pst)
        return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S %Z")
```

#### **Arizona Time (America/Phoenix) - Business Data**
- **All Airtable data**: Timestamps written to business records
- **CSV file processing**: Business event timestamps
- **Email download timestamps**: File naming and processing
- **HousecallPro integration**: Service job scheduling
- **Webhook data processing**: Business event timestamps

```python
# Arizona timezone for business data consistency
arizona_tz = pytz.timezone('America/Phoenix')
run_time = datetime.now(arizona_tz).isoformat()
```

#### **Benefits of This Approach**
- **System Operations**: PST timestamps make log analysis intuitive for Pacific coast operations
- **Business Consistency**: Arizona time ensures data consistency (no daylight saving complications)
- **Cross-Platform**: Works identically across different server timezones
- **Audit Trail**: Clear separation between system events and business events

## ⚙️ Configuration

### **Environment Setup**
Create `.env` file in project root:
```bash
# Required Configuration
AIRTABLE_API_KEY=your_api_key_here
PROD_AIRTABLE_BASE_ID=your_base_id_here
AUTOMATION_TABLE_NAME=Automation

# Optional Field Names (defaults provided)
AUTOMATION_NAME_FIELD=Name
AUTOMATION_ACTIVE_FIELD=Active
AUTOMATION_LAST_RAN_FIELD=Last Ran
AUTOMATION_SYNC_DETAILS_FIELD=Sync Details

# Gmail Integration
GMAIL_CREDENTIALS_PATH=scripts/gmail/credentials.json

# Evolve Configuration
EVOLVE_USER=your_username
EVOLVE_PASS=your_password

# HousecallPro Integration
HCP_API_KEY=your_hcp_key
HCP_COMPANY_ID=your_company_id

# AI Agent
OPENAI_API_KEY=your_openai_key

# System Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
BACKUP_RETENTION_DAYS=90
```

### **Airtable Control System**
The system uses an Airtable "Automation" table to control which automations run:

| Field Name | Type | Description |
|------------|------|-------------|
| Name | Single line text | Automation identifier |
| Active | Checkbox | Enable/disable automation |
| Last Ran | Date & time | Last execution timestamp |
| Sync Details | Long text | Execution results and logs |

### **Environment-Specific Configuration**
```bash
# Development environment
config/environments/dev/.env

# Production environment  
config/environments/prod/.env

# Copy from templates
cp config/environments/dev/.env.example config/environments/dev/.env
cp config/environments/prod/.env.example config/environments/prod/.env
```

## 🔧 Installation & Dependencies

### **Python Dependencies** (requirements.txt)
- `selenium` - Web scraping automation
- `webdriver-manager` - Browser driver management
- `python-dotenv` - Environment variable management
- `pandas` - Data processing
- `aiohttp` - Async HTTP client
- `icalendar` - ICS calendar parsing
- `pyairtable` - Airtable API client
- `python-dateutil` - Date parsing utilities
- `requests` - HTTP client
- `airtable-python-wrapper` - Alternative Airtable client
- `flask` - Web framework for webhooks

### **Node.js Dependencies** (package.json)
- AI agent and web interface components
- Airtable integration utilities

### **System Requirements**
- **Python**: 3.8 or higher
- **Node.js**: 16 or higher (for AI agent)
- **Chrome/Chromium**: For web scraping
- **Git**: For version control and deployment

## 🧪 Testing

### **Test Suite**
```bash
# Quick validation
python test_setup.py

# Full test suite  
pytest tests/ -v

# CI/CD testing
python run_anywhere.py --test
```

### **Test Coverage**
- ✅ Configuration system validation
- ✅ Controller functionality
- ✅ Cross-platform portability
- ✅ Import and dependency checks
- ✅ Error handling and edge cases
- ✅ Environment detection
- ✅ Path resolution across platforms

## 🚀 Deployment

### **Development Workflow**
```bash
# Work on dev branch
git checkout dev
# Make changes...
git add . && git commit -m "Feature update"
git push origin dev

# Deploy to production
./deploy_to_prod.sh
```

### **Production Deployment**
```bash
# Automated deployment with testing
./bin/deploy.sh

# Manual production setup
pip install -e .
cp .env.example .env
# Edit .env with production values
./bin/setup_cron.sh
```

### **Docker Deployment**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["run-automation"]
```

## 📊 Monitoring & Maintenance

### **Health Monitoring**
- **System Health**: `./bin/monitor.sh` - Checks processes, errors, disk space
- **Log Analysis**: Automatic error detection and alerting
- **Performance**: Execution time tracking and optimization
- **Resource Usage**: Disk space and memory monitoring

### **Backup System**
- **Automated Backups**: `./bin/backup.sh` - Full system and data backups
- **Retention Policy**: Configurable backup retention
- **Integrity Checks**: Automatic backup validation
- **Disaster Recovery**: Complete system restoration procedures

### **Logging System**
- **Centralized Logs**: All logs in `logs/` directory
- **Log Rotation**: Automatic cleanup based on retention policy
- **Error Tracking**: Detailed error logging and alerting
- **Audit Trail**: Complete operation history

## 🔒 Security

### **Data Protection**
- All credentials stored in `.env` files (never committed)
- Separate development and production environments
- Automatic backup encryption (when configured)
- Comprehensive audit logging

### **Access Control**
- Environment-based access control
- API key rotation support
- Webhook signature validation
- Secure credential storage

## 🐛 Troubleshooting

### **Common Issues**
```bash
# Import errors
python run_anywhere.py --info

# Missing dependencies
python run_anywhere.py --auto-install

# Permission issues
sudo chown -R $USER:$USER automation/

# Path problems
python test_setup.py

# Environment issues
python -c "from automation.config import Config; print(Config.validate_required_env(['AIRTABLE_API_KEY']))"
```

### **Debug Mode**
```bash
export AUTOMATION_DEBUG=1
python run_anywhere.py
```

### **Log Analysis**
```bash
# View recent logs
tail -f logs/automation.log

# Check for errors
grep -i error logs/*.log

# Monitor health
./bin/monitor.sh
```

## 🤝 Contributing

### **Development Setup**
```bash
git clone <repo-url>
cd automation
pip install -e ".[dev]"
pytest tests/
```

### **Code Quality**
```bash
# Formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Testing
pytest tests/ --cov=automation
```

## 📋 File-by-File Reference

### **🔴 Core System Files (DO NOT MODIFY)**
- `setup.py` - Package installation configuration
- `pyproject.toml` - Modern Python packaging standards
- `src/automation/` - Main package source code
- `requirements.txt` - Python dependencies

### **🟡 Configuration Files (MODIFY AS NEEDED)**
- `.env` - Main environment configuration
- `config/environments/dev/.env` - Development settings
- `config/environments/prod/.env` - Production settings

### **🟢 Operational Scripts (SAFE TO MODIFY)**
- `bin/` - All operational shell scripts
- `bin/backup.sh` - Customize backup strategy
- `bin/monitor.sh` - Add custom health checks  
- `bin/deploy.sh` - Modify deployment process
- `bin/setup_cron.sh` - Adjust scheduling

### **🔵 Automation Scripts (EXTEND AS NEEDED)**
- `scripts/*/` - All individual automation components
- Add new scripts here following existing patterns

### **⚪ Generated/Cache Files (SAFE TO DELETE)**
- `logs/*.log` - Will be regenerated
- `CSV_done/*.csv` - Processed files (backup first)
- `__pycache__/` - Python cache (auto-regenerated)

## 📞 Support

- **Documentation**: [Installation Guide](docs/INSTALLATION.md)
- **Issues**: GitHub Issues
- **Testing**: `python test_setup.py`
- **Health Check**: `./bin/monitor.sh`

---

**🎉 Your automation system is now fully portable, documented, and ready for production deployment!**

*Generated with [Claude Code](https://claude.ai/code)*