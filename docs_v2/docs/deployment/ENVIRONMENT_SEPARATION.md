# Environment Separation Implementation - COMPLETE

## Overview
Successfully implemented complete separation between development and production environments for the Property Management Automation System.

## Key Changes Made

### 1. **New Configuration Architecture**
```
src/automation/
├── config_base.py      # Base configuration class
├── config_dev.py       # Development-specific config
├── config_prod.py      # Production-specific config
└── config_wrapper.py   # Auto-selects config based on ENVIRONMENT var
```

### 2. **Separate Automation Runners**
```
src/
├── run_automation_dev.py   # Development automation runner
└── run_automation_prod.py  # Production automation runner
```

### 3. **Environment-Specific Directories**
```
src/automation/scripts/
├── CSV_process_development/    # Dev CSV processing
├── CSV_done_development/       # Dev CSV archive
├── CSV_process_production/     # Prod CSV processing
└── CSV_done_production/        # Prod CSV archive
```

### 4. **Updated API Server**
- **Removed** legacy endpoints (`/api/jobs`, `/api/schedules`)
- **Kept** environment-specific endpoints:
  - `/api/dev/jobs` and `/api/dev/schedules` (Development)
  - `/api/prod/jobs` and `/api/prod/schedules` (Production)

### 5. **Cron Job Scripts**
```
/home/opc/automation/
├── cron_setup_dev.sh    # Setup dev cron (every 30 min)
├── cron_setup_prod.sh   # Setup prod cron (every 4 hours)
└── cron_remove.sh       # Remove old single cron job
```

## Environment Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| **Airtable Base** | `app67yWFv0hKdl6jM` | `appZzebEIqCU5R9ER` |
| **API Key** | `DEV_AIRTABLE_API_KEY` | `PROD_AIRTABLE_API_KEY` |
| **CSV Directories** | `CSV_*_development/` | `CSV_*_production/` |
| **Log Files** | `automation_dev*.log` | `automation_prod*.log` |
| **Cron Schedule** | Every 30 minutes | Every 4 hours |
| **API Endpoints** | `/api/dev/*` | `/api/prod/*` |

## Usage Instructions

### Running Manually

**Development:**
```bash
cd /home/opc/automation
python3 src/run_automation_dev.py                 # Run all active automations
python3 src/run_automation_dev.py --dry-run       # Show what would run
python3 src/run_automation_dev.py --list          # List automations
python3 src/run_automation_dev.py --run "CSV Files"  # Run specific automation
```

**Production:**
```bash
cd /home/opc/automation
python3 src/run_automation_prod.py                # Run all active automations
python3 src/run_automation_prod.py --dry-run      # Show what would run
python3 src/run_automation_prod.py --list         # List automations
python3 src/run_automation_prod.py --run "Evolve" # Run specific automation
```

### Setting Up Cron Jobs

**Development (every 30 minutes):**
```bash
cd /home/opc/automation
./cron_setup_dev.sh
```

**Production (every 4 hours at 12am, 4am, 8am, 12pm, 4pm, 8pm):**
```bash
cd /home/opc/automation
./cron_setup_prod.sh
```

**Remove old cron jobs:**
```bash
cd /home/opc/automation
./cron_remove.sh
```

### API Usage

**Development API calls:**
```javascript
// In Airtable scripts - use dev endpoints
const API_URL = 'https://servativ.themomentcatchers.com/api/dev/schedules';
```

**Production API calls:**
```javascript
// In Airtable scripts - use prod endpoints  
const API_URL = 'https://servativ.themomentcatchers.com/api/prod/schedules';
```

## Benefits Achieved

✅ **Complete Isolation**: Dev and prod never interfere with each other
✅ **Separate Schedules**: Dev can run frequently for testing, prod runs on business schedule
✅ **Separate Data**: Different Airtable bases, different CSV directories
✅ **Clear Distinction**: No more confusion about which environment is running
✅ **Testing Safety**: Can test dev automation without affecting production
✅ **Parallel Operation**: Both environments can run simultaneously

## Files Modified/Created

### Created:
- `src/automation/config_base.py`
- `src/automation/config_dev.py` 
- `src/automation/config_prod.py`
- `src/automation/config_wrapper.py`
- `src/run_automation_dev.py`
- `src/run_automation_prod.py`
- `cron_setup_dev.sh`
- `cron_setup_prod.sh`
- `cron_remove.sh`

### Modified:
- `src/automation/controller.py` - Now accepts config instance
- `src/automation/scripts/run_automation.py` - Refactored to individual functions
- `src/automation/scripts/__init__.py` - Updated exports
- All Python scripts in `scripts/` - Now use `config_wrapper`
- `src/automation/scripts/airscripts-api/server.js` - Removed legacy endpoints
- `src/automation/scripts/airscripts-api/.env` - Removed ENVIRONMENT variable

## Testing Results

Both development and production runners tested successfully:
- ✅ Development runner uses dev Airtable base (`app67yWFv0hKdl6jM`)
- ✅ Production runner uses prod Airtable base (`appZzebEIqCU5R9ER`)
- ✅ Separate CSV directories created and used
- ✅ API server updated with environment-specific endpoints only
- ✅ Configuration validation working correctly
- ✅ Logging to separate files per environment

## Next Steps

1. **Set up cron jobs** using the provided scripts based on your testing needs
2. **Update Airtable scripts** to use environment-specific API endpoints
3. **Configure proper Airtable API keys** if the test keys need updating
4. **Monitor logs** in the separate log files for each environment

The environment separation is now complete and ready for production use!