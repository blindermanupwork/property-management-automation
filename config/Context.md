# /home/opc/automation/config/

## Purpose
This directory contains the environment-specific configuration system that provides complete separation between development and production environments. It houses secure credential files and environment-specific settings that are automatically loaded by the automation system.

## Key Subdirectories and What They Do

### **Environment Separation Structure**
- `environments/dev/` - Development environment configuration and credentials
- `environments/prod/` - Production environment configuration and credentials

### **Environment-Specific Files**
Each environment directory contains:
- `.env` - Environment variables and API credentials (secure, 600 permissions)
- Configuration files specific to that environment's requirements

## How to Use the Code

### **Setting Up Environment Configurations**

#### **Development Environment**
```bash
# Create/edit development configuration
nano config/environments/dev/.env

# Required variables for development:
DEV_AIRTABLE_API_KEY=pat_[your_dev_api_key]
DEV_AIRTABLE_BASE_ID=app67yWFv0hKdl6jM
DEV_HCP_TOKEN=[your_dev_hcp_token]
DEV_GMAIL_CREDENTIALS_PATH=/path/to/dev/credentials.json
```

#### **Production Environment**
```bash
# Create/edit production configuration
nano config/environments/prod/.env

# Required variables for production:
PROD_AIRTABLE_API_KEY=pat_[your_prod_api_key]
PROD_AIRTABLE_BASE_ID=appZzebEIqCU5R9ER
PROD_HCP_TOKEN=[your_prod_hcp_token]
PROD_GMAIL_CREDENTIALS_PATH=/path/to/prod/credentials.json
```

### **Automatic Configuration Loading**
The system automatically loads the appropriate configuration based on:

```python
# The config system auto-detects environment
from src.automation.config_wrapper import Config

# Automatically uses correct environment credentials
api_key = Config.get_airtable_api_key()
base_id = Config.get_airtable_base_id()
```

### **Configuration Validation**
```bash
# Validate all configurations
python3 -c "
from src.automation.config_dev import DevConfig
from src.automation.config_prod import ProdConfig

dev_errors = DevConfig().validate_config()
prod_errors = ProdConfig().validate_config()

print('Development errors:', dev_errors)
print('Production errors:', prod_errors)
"

# Quick validation using wrapper
python3 -c "from src.automation.config_wrapper import Config; print(Config.validate_config())"
```

## Dependencies and Requirements

### **Security Requirements**
- `.env` files must have restrictive permissions (600)
- No world-readable credential files
- Environment-specific API keys and tokens
- Separate authentication for each environment

### **File Permissions Setup**
```bash
# Set secure permissions automatically when files are created
# The system automatically applies these permissions:
chmod 600 config/environments/dev/.env
chmod 600 config/environments/prod/.env
chmod 755 config/environments/dev/
chmod 755 config/environments/prod/
```

### **Required Environment Variables**

#### **Airtable Configuration**
- `DEV_AIRTABLE_API_KEY` / `PROD_AIRTABLE_API_KEY` - API keys (must start with 'pat')
- `DEV_AIRTABLE_BASE_ID` / `PROD_AIRTABLE_BASE_ID` - Base IDs (must start with 'app', 17 chars)

#### **HousecallPro Configuration**
- `DEV_HCP_TOKEN` / `PROD_HCP_TOKEN` - API authentication tokens
- `DEV_HCP_BASE_URL` / `PROD_HCP_BASE_URL` - API endpoints (optional, has defaults)

#### **Gmail Configuration**
- `DEV_GMAIL_CREDENTIALS_PATH` / `PROD_GMAIL_CREDENTIALS_PATH` - OAuth credential file paths

## Common Workflows and Operations

### **Initial Setup Workflow**
```bash
# 1. Create environment directories (if not exist)
mkdir -p config/environments/dev
mkdir -p config/environments/prod

# 2. Create development configuration
cat > config/environments/dev/.env << 'EOF'
DEV_AIRTABLE_API_KEY=pat_your_dev_key_here
DEV_AIRTABLE_BASE_ID=app67yWFv0hKdl6jM
DEV_HCP_TOKEN=your_dev_hcp_token
EOF

# 3. Create production configuration
cat > config/environments/prod/.env << 'EOF'
PROD_AIRTABLE_API_KEY=pat_your_prod_key_here
PROD_AIRTABLE_BASE_ID=appZzebEIqCU5R9ER
PROD_HCP_TOKEN=your_prod_hcp_token
EOF

# 4. Set secure permissions
chmod 600 config/environments/dev/.env
chmod 600 config/environments/prod/.env

# 5. Validate configuration
python3 test_setup.py
```

### **Environment Switching**
The system automatically detects and switches environments based on:

1. **Hostname Detection**: Different hostnames map to different environments
2. **User Confirmation**: Prompts for confirmation when environment is unclear
3. **Force Flags**: `--force` flag to override safety checks

```python
# Example of how the system detects environment
from src.automation.config_wrapper import Config

print(f"Current environment: {Config.environment_name}")
print(f"Airtable base: {Config.get_airtable_base_id()}")
```

### **Configuration Validation Workflow**
```bash
# Check specific environment
python3 -c "
from src.automation.config_dev import DevConfig
config = DevConfig()
errors = config.validate_config()
if errors:
    print('Validation failed:', errors)
else:
    print('Development config valid')
"

# Validate API key format
python3 -c "
from src.automation.config_wrapper import Config
key = Config.get_airtable_api_key()
if key.startswith('pat') and len(key) >= 20:
    print('API key format valid')
else:
    print('Invalid API key format')
"
```

## Key Security Features

### **Credential Protection**
- **Environment Isolation**: Complete separation of dev/prod credentials
- **Secure Storage**: .env files with 600 permissions (owner read/write only)
- **No Code Embedding**: Credentials never hardcoded in source code
- **Format Validation**: API keys and base IDs validated for correct format

### **Environment Safety Mechanisms**
- **Cross-Environment Protection**: Prevents accidental use of prod credentials in dev
- **Warning Prompts**: User confirmation required for potentially dangerous operations
- **Validation First**: Configuration validated before any automation execution
- **Error Context**: Detailed error messages with resolution guidance

### **Access Control**
```bash
# Verify secure permissions
ls -la config/environments/*/. env

# Should show: -rw------- (600 permissions)
# If not, fix with:
chmod 600 config/environments/*/.env
```

## Configuration Schema

### **Required Variables Schema**
```bash
# Development Environment (.env in config/environments/dev/)
DEV_AIRTABLE_API_KEY=pat_[20+ characters]     # Airtable Personal Access Token
DEV_AIRTABLE_BASE_ID=app[exactly 17 chars]    # Development base ID
DEV_HCP_TOKEN=[token]                         # HousecallPro API token

# Production Environment (.env in config/environments/prod/)
PROD_AIRTABLE_API_KEY=pat_[20+ characters]    # Airtable Personal Access Token  
PROD_AIRTABLE_BASE_ID=app[exactly 17 chars]   # Production base ID
PROD_HCP_TOKEN=[token]                        # HousecallPro API token
```

### **Optional Configuration Variables**
```bash
# Gmail OAuth (if using Gmail integration)
DEV_GMAIL_CREDENTIALS_PATH=/path/to/dev/credentials.json
PROD_GMAIL_CREDENTIALS_PATH=/path/to/prod/credentials.json

# Custom API endpoints (optional, has defaults)
DEV_HCP_BASE_URL=https://api.housecallpro.com
PROD_HCP_BASE_URL=https://api.housecallpro.com

# Debug and logging options
DEBUG_MODE=true                               # Enable debug logging
LOG_LEVEL=INFO                               # Set logging level
```

## Troubleshooting

### **Common Configuration Issues**
```bash
# Permission denied errors
sudo chmod 600 config/environments/*/.env

# Missing environment files
ls -la config/environments/dev/.env config/environments/prod/.env

# Invalid API key format
# Keys must start with 'pat' and be at least 20 characters

# Invalid base ID format  
# Base IDs must start with 'app' and be exactly 17 characters
```

### **Validation Commands**
```bash
# Test development config
python3 src/run_automation_dev.py --dry-run

# Test production config
python3 src/run_automation_prod.py --dry-run

# Check environment detection
python3 -c "from src.automation.config_wrapper import Config; print(f'Environment: {Config.environment_name}')"
```