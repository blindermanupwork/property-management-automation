# /home/opc/automation/src/automation/scripts/

## Purpose
This directory contains all the individual automation scripts that perform specific tasks in the property management system. Each script is designed to be environment-aware and can run independently or as part of the orchestrated automation workflow.

## Key Subdirectories and What They Do

### **CSV Processing Workflow**
- `CSV_process_development/` - Staging area for CSV files to be processed in development
- `CSV_process_production/` - Staging area for CSV files to be processed in production
- `CSV_done_development/` - Archive of processed CSV files from development environment
- `CSV_done_production/` - Archive of processed CSV files from production environment
- `CSVtoAirtable/` - Core CSV processing engine that syncs data to Airtable

### **Data Source Scripts**
- `gmail/` - Gmail OAuth integration for downloading iTrip CSV reports
- `evolve/` - Web scraper for Evolve property management platform
- `icsAirtableSync/` - Calendar synchronization from ICS feeds
- `webhook/` - Webhook handlers for real-time updates

### **API and Service Integration**
- `airscripts-api/` - Node.js API server for Airtable/HousecallPro integration
- `airtable-agent/` - AI-powered agent for Airtable data queries
- `hcp/` - HousecallPro service job synchronization scripts

### **Utility Scripts**
- `run_automation.py` - Legacy automation runner (use src/run_automation_*.py instead)
- `update_service_fields.py` - Service field update utilities
- `release.sh` - Release management script
- `version.sh` - Version management utilities

## How to Use the Code

### **Running Individual Scripts**

#### **Gmail CSV Downloader**
```bash
cd src/automation/scripts/gmail/
python3 gmail_downloader.py --days 1 --debug
python3 gmail_downloader.py --list-only  # List emails without downloading
```

#### **CSV Processing**
```bash
cd src/automation/scripts/CSVtoAirtable/
python3 csvProcess.py  # Process all CSV files in staging directory
```

#### **Evolve Scraper**
```bash
cd src/automation/scripts/evolve/
python3 evolveScrape.py  # Scrape property data from Evolve
```

#### **ICS Calendar Sync**
```bash
cd src/automation/scripts/icsAirtableSync/
python3 icsProcess.py  # Sync calendar data from ICS feeds
```

### **API Server Operations**

#### **Airscripts API Server**
```bash
cd src/automation/scripts/airscripts-api/
npm install
npm start  # Start HTTP server on port 3000

# For HTTPS (production)
node server-https.js  # Requires SSL certificates
```

#### **Airtable Agent**
```bash
cd src/automation/scripts/airtable-agent/
npm install
node airtable-agent.js  # Start AI agent on port 8000
```

### **HousecallPro Integration**
```bash
cd src/automation/scripts/hcp/

# Development environment
node dev-hcp-sync.js

# Production environment  
node prod-hcp-sync.js
```

## Dependencies and Requirements

### **Python Scripts Dependencies**
- **Gmail**: `google-auth-oauthlib`, `google-api-python-client`
- **CSV Processing**: `pyairtable`, `pandas`, `python-dateutil`
- **Evolve**: `selenium`, `beautifulsoup4`, `requests`
- **ICS Sync**: `icalendar`, `pytz`, `requests`

### **Node.js Scripts Dependencies**
- **Airscripts API**: `express`, `cors`, `airtable`, `axios`
- **Airtable Agent**: `express`, `openai`, `airtable`
- **HCP Scripts**: `axios`, `node-fetch`

### **System Requirements**
- Chrome/Chromium browser (for Selenium scripts)
- Gmail OAuth credentials (for email downloads)
- Airtable API keys (environment-specific)
- HousecallPro API tokens (environment-specific)

## Common Workflows and Operations

### **Complete Automation Workflow**
1. **Gmail Downloader** fetches iTrip CSV reports
2. **CSV Processor** moves files from `CSV_process_*/` to Airtable
3. **Evolve Scraper** updates property information
4. **ICS Sync** updates calendar availability
5. **HCP Sync** creates/updates service jobs
6. **Processed files** moved to `CSV_done_*/` for audit trail

### **Environment-Specific Processing**
```bash
# Development workflow
# Files flow: CSV_process_development/ → Airtable dev base → CSV_done_development/

# Production workflow  
# Files flow: CSV_process_production/ → Airtable prod base → CSV_done_production/
```

### **CSV Processing Flow**
```
iTrip Email → gmail_downloader.py → CSV_process_*/ → csvProcess.py → Airtable → CSV_done_*/
Evolve Portal → evolveScrape.py → CSV_process_*/ → csvProcess.py → Airtable → CSV_done_*/
```

### **Service Job Management Flow**
```
Airtable Reservations → airscripts-api → HousecallPro Jobs → webhook updates → Airtable Status
```

## Key Features and Capabilities

### **Gmail Integration (`gmail/`)**
- **OAuth2 Authentication**: Secure Gmail access with token refresh
- **Selective Download**: Filter by sender, subject, date range
- **Duplicate Prevention**: Tracks processed emails
- **Environment-Aware**: Downloads to appropriate directory

### **CSV Processing (`CSVtoAirtable/`)**
- **Multi-Source Support**: Handles iTrip and Evolve CSV formats
- **Change Tracking**: Preserves complete history of record changes
- **Deduplication**: Single active record per reservation UID
- **Environment Separation**: Processes to correct Airtable base

### **Web Scraping (`evolve/`)**
- **Headless Operation**: Runs without GUI using Selenium
- **Error Recovery**: Robust error handling and retry logic
- **Data Validation**: Validates scraped property data
- **Rate Limiting**: Respects website rate limits

### **Calendar Sync (`icsAirtableSync/`)**
- **Multi-Feed Support**: Processes multiple ICS calendar feeds
- **Availability Updates**: Real-time calendar synchronization  
- **Conflict Detection**: Identifies and reports booking conflicts
- **Timezone Handling**: Proper timezone conversion

### **API Integration (`airscripts-api/`)**
- **Environment Separation**: Separate `/api/dev/` and `/api/prod/` endpoints
- **Authentication**: Secure API key authentication
- **HTTPS Support**: SSL/TLS encryption for production
- **Service Jobs**: Create/update HousecallPro jobs from Airtable

### **AI Agent (`airtable-agent/`)**
- **Natural Language Queries**: OpenAI-powered data access
- **Web Interface**: Browser-based query interface
- **Airtable Integration**: Direct access to reservation data
- **Response Formatting**: Structured JSON responses

## Error Handling and Monitoring

### **Logging Strategy**
- Each script logs to environment-specific files
- Centralized logs in `src/automation/logs/`
- Real-time console output during execution
- Error details with stack traces

### **Common Issues and Solutions**
```bash
# Permission errors on CSV directories
chmod 755 CSV_process_*/ CSV_done_*/

# Gmail authentication issues  
rm src/automation/scripts/gmail/token.pickle  # Force re-authentication

# Selenium browser issues
sudo apt-get update && sudo apt-get install chromium-browser

# Node.js dependency issues
cd [script_directory] && npm install
```

### **Monitoring Commands**
```bash
# Check recent logs
tail -100 src/automation/logs/automation_*.log

# Monitor real-time processing
tail -f src/automation/logs/csv_sync.log

# Check webhook activity
tail -f src/automation/scripts/webhook/webhook.log
```

## Security Considerations

### **Credential Management**
- All API keys stored in environment-specific `.env` files
- OAuth tokens encrypted and environment-specific
- No hardcoded credentials in source code
- Secure file permissions (600) on credential files

### **Environment Isolation**
- Complete separation between dev/prod data flows
- Different API endpoints and credentials
- Separate CSV processing directories
- Independent logging and monitoring