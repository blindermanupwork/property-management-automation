# /home/opc/automation/src/automation/

## Purpose
This directory contains the core Python package for the property management automation system. It provides the central configuration system, orchestration controller, and the foundation for all automation scripts with complete environment separation between development and production.

## Key Files and What They Do

### **Configuration System (Environment-Aware)**
- `config_base.py` - Base configuration class with shared logic for all environments
- `config_dev.py` - Development environment configuration (uses `app67yWFv0hKdl6jM` Airtable base)
- `config_prod.py` - Production environment configuration (uses `appZzebEIqCU5R9ER` Airtable base)
- `config_wrapper.py` - Auto-detection wrapper that selects appropriate config based on environment

### **Core Orchestration**
- `controller.py` - Main automation controller that orchestrates all automation scripts
- `__init__.py` - Package initialization file

### **Legacy Files**
- `config.py.backup` - Backup of old monolithic configuration (pre-v2.0)

## How to Use the Code

### **Configuration System Usage**
```python
# Auto-detect environment (recommended)
from src.automation.config_wrapper import Config

# Get environment-specific paths
csv_process_dir = Config.get_csv_process_dir()
logs_dir = Config.get_logs_dir()
airtable_base_id = Config.get_airtable_base_id()

# Validate configuration
errors = Config.validate_config()
if errors:
    print(f"Config errors: {errors}")

# Manual environment selection (advanced)
from src.automation.config_dev import DevConfig
from src.automation.config_prod import ProdConfig

dev_config = DevConfig()
prod_config = ProdConfig()
```

### **Controller Usage**
```python
from src.automation.controller import AutomationController
from src.automation.config_wrapper import Config

# Initialize controller with auto-detected config
controller = AutomationController(Config)

# Check if specific automation is enabled
if controller.get_automation_status("gmail_downloader"):
    # Run the automation
    print("Gmail downloader is enabled")

# Log automation activity
controller.log_automation_run("gmail_downloader", "success", "Downloaded 5 files")
```

### **Environment Detection**
The system automatically detects environment based on:
1. Hostname patterns
2. Environment variables
3. Configuration file presence
4. User confirmation prompts for safety

## Dependencies and Requirements

### **Core Dependencies**
- `pathlib` - Cross-platform path handling
- `pytz` - Timezone handling (PST for logs, Arizona for business data)
- `dotenv` - Environment variable loading
- `requests` - HTTP requests for Airtable API
- `logging` - Comprehensive logging system

### **Configuration Requirements**
Environment-specific `.env` files must contain:
```bash
# Development (.env in config/environments/dev/)
DEV_AIRTABLE_API_KEY=pat_...
DEV_AIRTABLE_BASE_ID=app67yWFv0hKdl6jM
DEV_HCP_TOKEN=...

# Production (.env in config/environments/prod/)
PROD_AIRTABLE_API_KEY=pat_...
PROD_AIRTABLE_BASE_ID=appZzebEIqCU5R9ER
PROD_HCP_TOKEN=...
```

## Common Workflows and Operations

### **Basic Configuration Workflow**
```python
# 1. Import the config system
from src.automation.config_wrapper import Config

# 2. Use config for paths and settings
download_dir = Config.get_itripcsv_downloads_dir()
airtable_key = Config.get_airtable_api_key()

# 3. Validate before proceeding
if Config.validate_config():
    raise Exception("Configuration validation failed")

# 4. Use timezone-aware operations
pst_time = Config.get_pst_time()
arizona_time = Config.get_arizona_time()
```

### **Controller Integration Pattern**
```python
from src.automation.controller import AutomationController
from src.automation.config_wrapper import Config

def run_automation_script(script_name):
    """Standard pattern for automation scripts"""
    controller = AutomationController(Config)
    
    # Check if automation is enabled
    if not controller.get_automation_status(script_name):
        print(f"{script_name} is disabled in Airtable")
        return
    
    try:
        # Run the automation logic
        result = perform_automation()
        
        # Log success
        controller.log_automation_run(
            script_name, 
            "success", 
            f"Processed {result['count']} items"
        )
        
    except Exception as e:
        # Log failure
        controller.log_automation_run(
            script_name, 
            "error", 
            str(e)
        )
        raise
```

### **Environment-Specific Operations**
```python
# Check current environment
env_name = Config.environment_name
print(f"Running in {env_name} environment")

# Environment-specific directory access
if env_name == "development":
    csv_dir = Config.get_csv_process_dir()  # Points to CSV_process_development/
elif env_name == "production":
    csv_dir = Config.get_csv_process_dir()  # Points to CSV_process_production/

# Cross-platform path handling
log_file = Config.get_logs_dir() / f"automation_{env_name}.log"
```

## Key Architecture Patterns

### **Environment Separation**
- **Complete Isolation**: No shared data between dev/prod
- **Config Hierarchy**: Base → Environment-specific → Wrapper
- **Safety Checks**: Prevents accidental cross-environment execution
- **Validation**: Comprehensive config validation with detailed error messages

### **Timezone Strategy**
- **PST for Logs**: All log timestamps in Pacific Standard Time
- **Arizona for Business**: Business logic uses Arizona timezone (no DST)
- **UTC Conversion**: Internal processing in UTC, display in local timezone

### **Path Management**
- **Cross-Platform**: Uses `pathlib.Path` for Windows/Linux/Mac compatibility
- **Dynamic Resolution**: Automatically finds project root
- **Environment-Aware**: Different paths for dev/prod CSV processing

### **Error Handling**
- **Validation First**: Config validation before any operations
- **Detailed Errors**: Specific error messages with resolution suggestions
- **Graceful Degradation**: Fallback paths and error recovery
- **Comprehensive Logging**: All errors logged with full context

### **Security Features**
- **Credential Protection**: Environment-specific .env files with secure permissions
- **API Key Validation**: Format and length validation for API keys
- **Environment Safety**: Warning prompts for cross-environment execution
- **No Hardcoded Secrets**: All sensitive data in environment variables