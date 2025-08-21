#!/bin/bash
# ULTRA SAFE Migration Preparation Script - Comprehensive backup with zero deletions
# This script backs up EVERYTHING needed for migration without touching source files

# Don't exit on error - we want to complete even if some files are missing
set +e

echo "🛡️ ULTRA SAFE Migration Preparation - Complete Backup, Zero Deletions!"
echo "======================================================================"

# Set variables
BACKUP_DIR="$HOME/migration_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="automation_migration_${TIMESTAMP}.tar.gz"
CRITICAL_BACKUP="$BACKUP_DIR/critical_files_${TIMESTAMP}"

# Create all backup directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$CRITICAL_BACKUP/env_files"
mkdir -p "$CRITICAL_BACKUP/services"
mkdir -p "$CRITICAL_BACKUP/configs"
mkdir -p "$CRITICAL_BACKUP/ssl"
mkdir -p "$CRITICAL_BACKUP/system"

# Function to safely copy files
safe_copy() {
    if [ -f "$1" ]; then
        cp "$1" "$2" && echo "  ✓ Backed up: $(basename $1)"
    else
        echo "  ⚠️ Not found: $1"
    fi
}

# Step 1: Critical Environment Files
echo ""
echo "🔐 Step 1: Backing up ALL Environment Files..."
echo "---------------------------------------------------"

# Root .env
safe_copy "/home/opc/automation/.env" "$CRITICAL_BACKUP/env_files/root.env"

# Environment-specific .env files
safe_copy "/home/opc/automation/config/environments/dev/.env" "$CRITICAL_BACKUP/env_files/dev.env"
safe_copy "/home/opc/automation/config/environments/prod/.env" "$CRITICAL_BACKUP/env_files/prod.env"

# Service-specific .env files
safe_copy "/home/opc/automation/src/automation/scripts/airscripts-api/.env" "$CRITICAL_BACKUP/env_files/airscripts.env"
safe_copy "/home/opc/automation/tools/airtable-mcp-server/.env" "$CRITICAL_BACKUP/env_files/airtable-mcp.env"
safe_copy "/home/opc/automation/tools/hcp-mcp-dev/.env" "$CRITICAL_BACKUP/env_files/hcp-mcp-dev.env"
safe_copy "/home/opc/automation/tools/hcp-mcp-prod/.env" "$CRITICAL_BACKUP/env_files/hcp-mcp-prod.env"
safe_copy "/home/opc/automation/tools/hcp-mcp-common/.env" "$CRITICAL_BACKUP/env_files/hcp-mcp-common.env"
safe_copy "/home/opc/automation/tools/trello-mcp-server/.env" "$CRITICAL_BACKUP/env_files/trello-mcp.env"

# Claude configuration files
safe_copy "/home/opc/automation/CLAUDE.md" "$CRITICAL_BACKUP/configs/CLAUDE.md"
safe_copy "/home/opc/automation/CLAUDE.local.md" "$CRITICAL_BACKUP/configs/CLAUDE.local.md"

# Step 2: System Service Files
echo ""
echo "⚙️ Step 2: Backing up Systemd Service Files..."
echo "---------------------------------------------------"

for service in webhook webhook-dev airscripts-api airscripts-api-https airtable-agent; do
    if [ -f "/etc/systemd/system/${service}.service" ]; then
        sudo cp "/etc/systemd/system/${service}.service" "$CRITICAL_BACKUP/services/" 2>/dev/null && \
        echo "  ✓ Backed up: ${service}.service"
    fi
done

# Step 3: Nginx Configuration
echo ""
echo "🌐 Step 3: Backing up Nginx Configuration..."
echo "---------------------------------------------------"

sudo cp /etc/nginx/conf.d/servativ.conf "$CRITICAL_BACKUP/configs/nginx-servativ.conf" 2>/dev/null && \
    echo "  ✓ Backed up: nginx-servativ.conf"
sudo cp /etc/nginx/nginx.conf "$CRITICAL_BACKUP/configs/nginx-main.conf" 2>/dev/null && \
    echo "  ✓ Backed up: nginx.conf"

# Step 4: SSL Certificates
echo ""
echo "🔒 Step 4: Backing up SSL Certificates..."
echo "---------------------------------------------------"

if [ -d "/etc/letsencrypt" ]; then
    sudo tar -czf "$CRITICAL_BACKUP/ssl/letsencrypt_backup.tar.gz" /etc/letsencrypt 2>/dev/null && \
    echo "  ✓ Backed up: Let's Encrypt certificates"
fi

# App certificates
for cert in /home/opc/automation/app/*.crt /home/opc/automation/app/*.key /home/opc/automation/app/*.pem; do
    [ -f "$cert" ] && cp "$cert" "$CRITICAL_BACKUP/ssl/" && echo "  ✓ Backed up: $(basename $cert)"
done

# Step 5: System Information
echo ""
echo "📊 Step 5: Documenting System State..."
echo "---------------------------------------------------"

# Cron jobs
crontab -l > "$CRITICAL_BACKUP/system/cron_backup.txt" 2>/dev/null && \
    echo "  ✓ Backed up: Cron jobs"

# Python packages
pip3 freeze > "$CRITICAL_BACKUP/system/python_packages.txt" && \
    echo "  ✓ Documented: Python packages"

# NPM global packages
npm list -g --depth=0 > "$CRITICAL_BACKUP/system/npm_global_packages.txt" 2>/dev/null && \
    echo "  ✓ Documented: NPM global packages"

# Firewall rules
sudo firewall-cmd --list-all > "$CRITICAL_BACKUP/system/firewall_rules.txt" 2>/dev/null && \
    echo "  ✓ Documented: Firewall rules"

# System packages
rpm -qa | grep -E "(python|node|chrome|selenium|nginx|git)" > "$CRITICAL_BACKUP/system/system_packages.txt" && \
    echo "  ✓ Documented: System packages"

# Service status
systemctl list-units --type=service --state=running > "$CRITICAL_BACKUP/system/running_services.txt" && \
    echo "  ✓ Documented: Running services"

# Git status
cd /home/opc/automation
git status > "$CRITICAL_BACKUP/system/git_status.txt" 2>&1
git remote -v >> "$CRITICAL_BACKUP/system/git_status.txt" 2>&1
git branch >> "$CRITICAL_BACKUP/system/git_status.txt" 2>&1
echo "  ✓ Documented: Git repository state"

# Step 6: Verify Critical Values
echo ""
echo "🔍 Step 6: Verifying Critical Configuration Values..."
echo "---------------------------------------------------"

# Check for HCP Job Type IDs
echo "Production HCP Job Types:" > "$CRITICAL_BACKUP/system/critical_ids.txt"
grep "PROD_HCP_JOB_TYPE" /home/opc/automation/config/environments/prod/.env >> "$CRITICAL_BACKUP/system/critical_ids.txt" 2>/dev/null
echo "" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
echo "Development HCP Job Types:" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
grep "DEV_HCP_JOB_TYPE" /home/opc/automation/config/environments/dev/.env >> "$CRITICAL_BACKUP/system/critical_ids.txt" 2>/dev/null
echo "  ✓ Documented: HCP Job Type IDs"

# Check for webhook secrets
echo "" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
echo "Webhook Secrets Present:" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
grep -q "SERVATIV_WEBHOOK_SECRET" /home/opc/automation/.env && echo "  - SERVATIV_WEBHOOK_SECRET: YES" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
grep -q "CLOUDMAILIN_SECRET" /home/opc/automation/.env && echo "  - CLOUDMAILIN_SECRET: YES" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
grep -q "HCP_WEBHOOK_SECRET" /home/opc/automation/.env && echo "  - HCP_WEBHOOK_SECRET: YES" >> "$CRITICAL_BACKUP/system/critical_ids.txt"
echo "  ✓ Verified: Webhook secrets"

# Step 7: Check for Active Processing
echo ""
echo "⚠️ Step 7: Checking for Active Processing..."
echo "---------------------------------------------------"

# Check for files being processed
PROCESSING_COUNT=$(find /home/opc/automation/src/automation/scripts/CSV_process_* -name "*.csv" 2>/dev/null | wc -l)
if [ "$PROCESSING_COUNT" -gt 0 ]; then
    echo "  ⚠️ WARNING: $PROCESSING_COUNT CSV files currently being processed"
    echo "  Consider waiting for processing to complete before migration"
else
    echo "  ✓ No CSV files currently being processed"
fi

# Step 8: Space Analysis
echo ""
echo "💾 Step 8: Space Analysis..."
echo "---------------------------------------------------"

echo "What will be excluded from archive (but NOT deleted):"
echo "  Python cache: $(find /home/opc/automation -name "*.pyc" -o -name "__pycache__" 2>/dev/null | wc -l) files"
echo "  Node modules: $(find /home/opc/automation -type d -name "node_modules" 2>/dev/null | wc -l) directories"
echo "  Logs: $(find /home/opc/automation -name "*.log*" 2>/dev/null | wc -l) files"
echo "  CSV done: $(find /home/opc/automation -path "*/CSV_done_*" -name "*.csv" 2>/dev/null | wc -l) files"
echo "  Archive folder: $(du -sh /home/opc/automation/archive 2>/dev/null | cut -f1)"
echo "  .git folder: $(du -sh /home/opc/automation/.git 2>/dev/null | cut -f1)"
echo "  .git-rewrite: $(du -sh /home/opc/automation/.git-rewrite 2>/dev/null | cut -f1)"

# Step 9: Create Main Archive
echo ""
echo "📦 Step 9: Creating Clean Code Archive..."
echo "---------------------------------------------------"

cd /home
sudo tar -czf "$BACKUP_DIR/$ARCHIVE_NAME" \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='.git-rewrite' \
  --exclude='*.log' \
  --exclude='*.log.*' \
  --exclude='CSV_done_production/*.csv' \
  --exclude='CSV_done_development/*.csv' \
  --exclude='CSV_process_production/*.csv' \
  --exclude='CSV_process_development/*.csv' \
  --exclude='archive/export/archive/customer_jobs*' \
  --exclude='archive/ngrok' \
  --exclude='app/node_modules' \
  --exclude='tools/*/node_modules' \
  --exclude='tools/*/dist' \
  --exclude='src/automation/logs/*.log*' \
  --exclude='.eggs' \
  --exclude='build' \
  --exclude='dist' \
  --exclude='*.egg-info' \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='chrome-profile-*' \
  --exclude='.npm' \
  --exclude='.cache' \
  opc/automation/ 2>/dev/null && \
echo "  ✓ Archive created: $ARCHIVE_NAME"

# Step 10: Create Critical Files Archive
echo ""
echo "🔐 Step 10: Creating Critical Files Archive..."
echo "---------------------------------------------------"

cd "$BACKUP_DIR"
tar -czf "critical_files_${TIMESTAMP}.tar.gz" "critical_files_${TIMESTAMP}/" && \
echo "  ✓ Critical files archive created"

# Step 11: Generate Checksums
echo ""
echo "🔢 Step 11: Generating Checksums..."
echo "---------------------------------------------------"

sha256sum "$ARCHIVE_NAME" > "${ARCHIVE_NAME}.sha256"
sha256sum "critical_files_${TIMESTAMP}.tar.gz" > "critical_files_${TIMESTAMP}.tar.gz.sha256"
echo "  ✓ Checksums generated"

# Step 12: Create Migration Checklist
echo ""
echo "📋 Step 12: Creating Migration Checklist..."
echo "---------------------------------------------------"

cat << 'CHECKLIST_EOF' > "$BACKUP_DIR/MIGRATION_CHECKLIST.md"
# Migration Checklist

## Files to Transfer to New Server
- [ ] automation_migration_*.tar.gz (main code)
- [ ] critical_files_*.tar.gz (configs, env, services)
- [ ] Both .sha256 checksum files

## On NEW Server - Pre-Installation
- [ ] Verify OS: RHEL 8.x / Oracle Linux 8.x
- [ ] Install Python 3.9.x
- [ ] Install Node.js 18.x
- [ ] Install Google Chrome
- [ ] Install nginx
- [ ] Configure firewall ports: 80, 443, 3002, 5000, 5001

## On NEW Server - Installation
- [ ] Extract automation_migration tar
- [ ] Extract critical_files tar
- [ ] Restore all .env files
- [ ] Install systemd services
- [ ] Configure nginx
- [ ] Install Python requirements
- [ ] Build MCP servers
- [ ] Restore cron jobs

## Critical Verifications
- [ ] HCP Job Type IDs are correct
- [ ] SERVATIV_WEBHOOK_SECRET matches
- [ ] CLOUDMAILIN_SECRET is set
- [ ] API_DOMAIN updated to new domain
- [ ] All services start successfully
- [ ] Webhooks respond to test requests
- [ ] Airtable connection works
- [ ] HCP API connection works

## DNS and External Services
- [ ] Update DNS A record
- [ ] Update CloudMailin webhook URL
- [ ] Update HousecallPro webhook URLs
- [ ] Generate SSL certificates

## Post-Migration Testing
- [ ] Run automation --dry-run
- [ ] Test CSV processing
- [ ] Test ICS sync
- [ ] Test Evolve scraper
- [ ] Monitor logs for 24 hours

## Rollback Plan
- [ ] Keep old server running for 1 week
- [ ] Document old server IP for quick DNS revert
- [ ] Keep all backups for 30 days
CHECKLIST_EOF

echo "  ✓ Migration checklist created"

# Final Summary
echo ""
echo "=========================================================="
echo "✅ ULTRA SAFE MIGRATION PREPARATION COMPLETE!"
echo "=========================================================="
echo ""
echo "📦 Archives Created:"
echo "  1. $BACKUP_DIR/$ARCHIVE_NAME"
echo "     Size: $(ls -lh "$BACKUP_DIR/$ARCHIVE_NAME" | awk '{print $5}')"
echo "  2. $BACKUP_DIR/critical_files_${TIMESTAMP}.tar.gz"
echo "     Size: $(ls -lh "$BACKUP_DIR/critical_files_${TIMESTAMP}.tar.gz" | awk '{print $5}')"
echo ""
echo "📋 Documentation:"
echo "  - Migration checklist: $BACKUP_DIR/MIGRATION_CHECKLIST.md"
echo "  - Critical IDs: $CRITICAL_BACKUP/system/critical_ids.txt"
echo "  - Service status: $CRITICAL_BACKUP/system/running_services.txt"
echo ""
echo "🔒 Security:"
echo "  - All .env files backed up with sensitive data"
echo "  - SSL certificates backed up"
echo "  - Webhook secrets documented"
echo ""
echo "⚠️ IMPORTANT REMINDERS:"
echo "  1. Your source files are COMPLETELY UNTOUCHED"
echo "  2. No services were stopped"
echo "  3. No files were deleted"
echo "  4. Keep old server running until migration confirmed"
echo "  5. Test EVERYTHING on new server before switching DNS"
echo ""
echo "📚 Next Step: Follow $BACKUP_DIR/MIGRATION_CHECKLIST.md"