# Property Management Automation - Server Migration Guide

**Generated**: 2025-08-04
**Purpose**: Comprehensive file analysis for server migration

## Executive Summary

This document provides a detailed analysis of every file and folder in the automation system, categorized by:
- **DELETE**: Can be safely deleted (not needed)
- **ARCHIVE**: Keep for reference but not needed for operation
- **KEEP**: Essential for system operation

---

## Directory Structure Analysis

### 🗑️ DELETE - Files/Folders to Remove Before Migration

#### 1. Python Cache Files
```bash
# Remove all Python cache
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
```

#### 2. Node Dependencies (Will be reinstalled)
```bash
rm -rf node_modules/
rm -rf app/node_modules/
rm -rf tools/*/node_modules/
```

#### 3. Build Artifacts
```bash
rm -rf build/
rm -rf dist/
rm -rf .eggs/
rm -rf *.egg-info/
rm -rf app/.expo/
rm -rf app/.tamagui/
```

#### 4. Git Repository (Will be cloned fresh)
```bash
rm -rf .git/
rm -rf .gitignore
```

#### 5. Temporary and Test Data
```bash
# CSV test data that's been processed
rm -rf src/automation/scripts/CSV_done_development/
rm -rf src/automation/scripts/CSV_done_production/
rm -rf src/automation/scripts/CSV_process_development/
rm -rf src/automation/scripts/CSV_process_production/
```

#### 6. Log Files (Start fresh on new server)
```bash
rm -rf src/automation/logs/*
rm -rf logs/
```

#### 7. IDE and Editor Files
```bash
rm -rf .vscode/
rm -rf .idea/
rm -f .DS_Store
```

---

### 📦 ARCHIVE - Files to Keep for Reference Only

#### 1. Archive Folder (Already organized)
```
archive/
├── 2025-07-21-cleanup/    # Previous cleanup efforts
├── old-scripts/            # Deprecated scripts
└── backup-files/           # Old backups
```

#### 2. Testing Data (Keep for reference)
```
testing/
├── test-scenarios/         # Test cases
└── test-runners/          # Test scripts
```

#### 3. Documentation Archives
```
docs/old/                  # Old documentation
docs_github/               # GitHub pages docs
```

#### 4. Old Development Files
```
src/automation/scripts/airtable-agent/  # If replaced by new system
src/automation/scripts/old/             # Any old scripts
```

---

### ✅ KEEP - Essential Files for Operation

#### 1. Core Python Package
```
src/
├── run_automation_dev.py      # Development runner
├── run_automation_prod.py     # Production runner
└── automation/
    ├── __init__.py
    ├── config_base.py         # Configuration system
    ├── config_dev.py
    ├── config_prod.py
    ├── config_wrapper.py
    ├── controller.py          # Main controller
    └── scripts/               # All active scripts
```

#### 2. Configuration Files
```
.env                           # Main environment variables
config/
└── environments/
    ├── dev/.env              # Development credentials
    └── prod/.env             # Production credentials
```

#### 3. Essential Scripts
```
src/automation/scripts/
├── CSVtoAirtable/            # CSV processing
├── icsAirtableSync/          # ICS calendar sync
├── evolve/                   # Evolve scraper
├── hcp/                      # HousecallPro integration
├── webhook/                  # Webhook handlers
├── airscripts-api/           # API server
└── airtable-automations/     # Airtable scripts
```

#### 4. MCP Servers
```
tools/
├── airtable-mcp-server/      # Keep package.json, src/
├── hcp-mcp-dev/              # Keep package.json, src/
├── hcp-mcp-prod/             # Keep package.json, src/
└── hcp-mcp-common/           # Shared MCP code
```

#### 5. Project Files
```
setup.py                      # Package installation
requirements.txt              # Python dependencies
package.json                  # Node dependencies
package-lock.json            # Lock file
README.md                    # Documentation
CHANGELOG.md                 # Version history
VERSION                      # Current version
```

#### 6. Deployment Scripts
```
cron_setup_dev.sh            # Cron setup
cron_setup_prod.sh
cron_remove.sh
```

---

## Pre-Migration Checklist

### 1. Backup Current System
```bash
# Create full backup
tar -czf automation_backup_$(date +%Y%m%d).tar.gz /home/opc/automation/
```

### 2. Export Credentials
```bash
# Save all .env files securely
cp .env ~/env_backup/
cp config/environments/dev/.env ~/env_backup/dev.env
cp config/environments/prod/.env ~/env_backup/prod.env
```

### 3. Document Current Cron Jobs
```bash
crontab -l > ~/cron_backup.txt
```

### 4. Clean Up Before Migration
```bash
# Run cleanup script
./clean_for_migration.sh
```

---

## Migration Steps

### 1. Prepare Source
```bash
# Remove unnecessary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
rm -rf node_modules/
rm -rf .git/
rm -rf logs/
rm -rf src/automation/logs/*
```

### 2. Create Migration Archive
```bash
# Create clean archive
tar -czf automation_clean.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='logs' \
  --exclude='*.log' \
  --exclude='CSV_done_*' \
  --exclude='CSV_process_*' \
  /home/opc/automation/
```

### 3. Transfer to New Server
```bash
# Use rsync for efficient transfer
rsync -avz --progress automation_clean.tar.gz newserver:/home/user/
```

### 4. Setup on New Server
```bash
# Extract
tar -xzf automation_clean.tar.gz

# Install dependencies
cd automation
pip3 install -r requirements.txt
npm install

# Restore credentials
cp ~/env_backup/.env .
cp ~/env_backup/dev.env config/environments/dev/.env
cp ~/env_backup/prod.env config/environments/prod/.env

# Set permissions
chmod 600 config/environments/*/.env

# Setup cron
./cron_setup_prod.sh
```

---

## File Size Analysis

### Large Files to Review
```bash
# Find files larger than 10MB
find . -type f -size +10M -exec ls -lh {} \;
```

### Directories by Size
```bash
# Check directory sizes
du -sh */ | sort -hr | head -20
```

---

## Critical Files Checklist

### Must Have for Operation:
- [ ] All .env files (main, dev, prod)
- [ ] requirements.txt
- [ ] package.json
- [ ] All scripts in src/automation/scripts/
- [ ] MCP server source code
- [ ] Cron setup scripts

### Nice to Have:
- [ ] Recent logs for reference
- [ ] Test scenarios
- [ ] Documentation

### Don't Need:
- [ ] node_modules (will reinstall)
- [ ] Python cache files
- [ ] Old CSV data
- [ ] Git history (will clone fresh)

---

## Post-Migration Verification

### 1. Test Each Component
```bash
# Test runners
python3 src/run_automation_dev.py --dry-run
python3 src/run_automation_prod.py --dry-run

# Test imports
python3 -c "from src.automation.controller import AutomationController; print('OK')"
```

### 2. Verify Services
- [ ] Cron jobs running
- [ ] API endpoints responding
- [ ] MCP servers connecting
- [ ] Webhook endpoints active

### 3. Monitor First Runs
- [ ] Check logs for errors
- [ ] Verify Airtable updates
- [ ] Confirm email downloads
- [ ] Test webhook processing

---

## Space Savings Estimate

Based on typical sizes:
- node_modules: ~500MB-1GB
- Python cache: ~50-100MB
- Logs: ~100-500MB
- Old CSV data: ~200MB-1GB
- Git history: ~100-200MB

**Total savings: 1-3GB**

---

## Specific File Analysis

### 📱 Mobile App (app/)
**Status**: ARCHIVE or DELETE
- React Native mobile app with massive node_modules
- Contains test certificates (.crt, .key files)
- Expo configuration suggests development app
- **Recommendation**: If not actively used, DELETE entire folder to save ~1-2GB

### 📂 Archive Folder Analysis
**Status**: ARCHIVE (move to cold storage)
```
archive/
├── 2025-07-21-cleanup/     # Previous cleanup attempt - 100+ scripts
├── gmail/                  # Old Gmail OAuth implementation
├── logs/                   # Old log files
└── multiple test scripts   # Redundant with testing/
```
**Recommendation**: Compress and store offline, not needed for operation

### 🗃️ CSV Data Files
**Status**: DELETE
- `CSV_done_development/` - Contains 100s of processed CSVs
- `CSV_done_production/` - Contains 1000s of processed CSVs  
- These are historical data, not needed for system operation
- **Space savings**: ~500MB-1GB

### 📝 Log Files
**Status**: DELETE (except recent)
```bash
# Keep only last 7 days of logs
find src/automation/logs -name "*.log*" -mtime +7 -delete
```

### 🔧 MCP Servers
**Keep these active servers**:
- `airtable-mcp-server/` - Used by Claude
- `hcp-mcp-dev/` - Development HCP integration
- `hcp-mcp-prod/` - Production HCP integration
- `trello-mcp-server/` - Trello integration

**Delete build artifacts**:
```bash
rm -rf tools/*/dist/
rm -rf tools/*/node_modules/
```

### 📚 Documentation Consolidation
**Multiple doc locations found**:
- `docs/` - Original docs
- `docs_v2/` - New structured docs (KEEP)
- `docs_github/` - GitHub pages (ARCHIVE)
- `archive/markdown_originals/` - Old docs (DELETE)
- Root level `.md` files - Many duplicates (CLEAN UP)

### 🧪 Testing Consolidation
**Found testing in multiple locations**:
- `testing/` - Main test directory (KEEP)
- `archive/test-files/` - Old tests (DELETE)
- `archive/analysis-scripts/` - One-off scripts (DELETE)
- Root level test files - Move to testing/

### 🗑️ Definite Deletions
1. **All node_modules/** - Will reinstall (saves ~2GB)
2. **All .pyc, __pycache__** - Python cache (saves ~100MB)
3. **archive/ngrok*** - Downloaded binaries (saves ~50MB)
4. **All .log files older than 7 days** - Old logs (saves ~200MB)
5. **app/ folder** - If mobile app not used (saves ~1-2GB)
6. **.eggs/, build/, dist/** - Build artifacts (saves ~100MB)

### 🔐 Security Considerations
**Check these before migration**:
- `archive/gmail/credentials.json` - Contains OAuth credentials
- `app/servitiv-automation.*.crt/key` - SSL certificates
- Any `.env` files in archive folders
- `archive/sensitive-strings.txt` - Listed in archive

---

## Clean Migration Script

Create this script as `prepare_for_migration.sh`:

```bash
#!/bin/bash
# Prepare automation folder for migration

echo "🧹 Starting cleanup for migration..."

# 1. Remove Python cache
echo "Removing Python cache files..."
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# 2. Remove node_modules
echo "Removing node_modules directories..."
find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null

# 3. Remove old logs
echo "Removing logs older than 7 days..."
find ./src/automation/logs -name "*.log*" -mtime +7 -delete 2>/dev/null

# 4. Remove build artifacts
echo "Removing build artifacts..."
rm -rf .eggs/ build/ dist/ 2>/dev/null
find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null

# 5. Archive old CSV data
echo "Archiving old CSV data..."
tar -czf csv_archive_$(date +%Y%m%d).tar.gz \
  src/automation/scripts/CSV_done_* \
  src/automation/scripts/CSV_process_* 2>/dev/null
rm -rf src/automation/scripts/CSV_done_* 2>/dev/null

# 6. Clean git
echo "Removing git repository..."
rm -rf .git/

# 7. Remove app folder if not needed
read -p "Remove mobile app folder? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf app/
fi

# 8. Archive the archive folder
echo "Compressing archive folder..."
tar -czf archive_folder_$(date +%Y%m%d).tar.gz archive/
rm -rf archive/

echo "✅ Cleanup complete!"
echo "Space saved: $(du -sh . | cut -f1)"
```

---

## Final Migration Package

After cleanup, your migration package should contain:

```
automation/
├── src/                    # Core Python package (< 50MB)
├── tools/                  # MCP servers source only (< 10MB)
├── config/                 # Environment configs (< 1MB)
├── docs_v2/                # Current documentation (< 5MB)
├── testing/                # Test framework (< 5MB)
├── *.sh                    # Shell scripts (< 1MB)
├── requirements.txt        # Python deps
├── package.json           # Node deps
├── setup.py               # Python setup
└── README.md              # Documentation

Total size after cleanup: ~75-100MB (vs 3-5GB before)
```

---

## Notes

1. **Mobile App Decision**: The app/ folder contains a full React Native app. Determine if this is still needed before deleting.
2. **Archive Strategy**: The archive/ folder contains valuable historical scripts and analysis. Compress and store offline.
3. **CSV Data**: Consider keeping last 30 days of CSV data for debugging, archive the rest.
4. **Documentation**: Consolidate all docs into docs_v2/ before migration.
5. **Testing**: Move all test files to testing/ directory for better organization.

---

Generated by Claude to assist with server migration.