#!/bin/bash
# SAFE Migration Preparation Script - No deletions, just exclusions
# This script creates a clean archive WITHOUT deleting anything from source

echo "🛡️ SAFE Migration Preparation - Nothing will be deleted!"
echo "=================================================="

# Set variables
BACKUP_DIR="$HOME/migration_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="automation_migration_${TIMESTAMP}.tar.gz"
ENV_BACKUP_DIR="$BACKUP_DIR/env_files"
SERVICE_BACKUP_DIR="$BACKUP_DIR/services"

# Create backup directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$ENV_BACKUP_DIR"
mkdir -p "$SERVICE_BACKUP_DIR"

# Step 0: Pre-flight checks
echo ""
echo "🔍 Pre-flight Checks..."
echo "---------------------------------------------------"

# Check if services are running (just to document state)
echo "Currently running services:"
systemctl is-active webhook && echo "  ✓ webhook (production) - RUNNING"
systemctl is-active webhook-dev && echo "  ✓ webhook-dev (development) - RUNNING"
systemctl is-active airscripts-api && echo "  ✓ airscripts-api - RUNNING"
systemctl is-active airscripts-api-https && echo "  ✓ airscripts-api-https - RUNNING"

# Document current directory
echo ""
echo "Current automation directory: $(pwd)"
echo "Total size: $(du -sh /home/opc/automation | cut -f1)"

# Step 1: Document what we're excluding (but NOT deleting)
echo ""
echo "📊 Analyzing what will be excluded from archive..."
echo "---------------------------------------------------"

# Count files that will be excluded
echo "Python cache files: $(find /home/opc/automation -name "*.pyc" -o -name "__pycache__" 2>/dev/null | wc -l)"
echo "Node modules: $(find /home/opc/automation -type d -name "node_modules" 2>/dev/null | wc -l) directories"
echo "Log files: $(find /home/opc/automation -name "*.log*" 2>/dev/null | wc -l)"
echo "CSV done files: $(find /home/opc/automation -path "*/CSV_done_*" -name "*.csv" 2>/dev/null | wc -l)"
echo "Archive folder size: $(du -sh /home/opc/automation/archive 2>/dev/null | cut -f1)"
echo ".git folder size: $(du -sh /home/opc/automation/.git 2>/dev/null | cut -f1)"
echo ".git-rewrite folder size: $(du -sh /home/opc/automation/.git-rewrite 2>/dev/null | cut -f1)"

# Step 2: Create archive with smart exclusions
echo ""
echo "📦 Creating clean archive (excluding unnecessary files)..."
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
  opc/automation/ 2>/dev/null

# Step 3: Create checksum
cd "$BACKUP_DIR"
sha256sum "$ARCHIVE_NAME" > "${ARCHIVE_NAME}.sha256"

# Step 4: Show results
echo ""
echo "✅ Archive created successfully!"
echo "---------------------------------------------------"
echo "Archive: $BACKUP_DIR/$ARCHIVE_NAME"
echo "Size: $(ls -lh "$ARCHIVE_NAME" | awk '{print $5}')"
echo "Checksum saved to: ${ARCHIVE_NAME}.sha256"

# Step 5: Create verification script for new server
cat << 'VERIFY_EOF' > "$BACKUP_DIR/verify_migration.sh"
#!/bin/bash
# Run this on the NEW server after extracting

echo "🔍 Verifying migration..."

# Check critical files exist
CRITICAL_FILES=(
    "automation/CLAUDE.md"
    "automation/requirements.txt"
    "automation/src/run_automation_prod.py"
    "automation/src/run_automation_dev.py"
    "automation/src/automation/controller.py"
    "automation/tools/airtable-mcp-server/package.json"
    "automation/tools/hcp-mcp-dev/package.json"
    "automation/tools/hcp-mcp-prod/package.json"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "/home/opc/$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
    fi
done

echo ""
echo "📁 Directory structure:"
find /home/opc/automation -maxdepth 2 -type d | sort
VERIFY_EOF

chmod +x "$BACKUP_DIR/verify_migration.sh"

echo ""
echo "📋 Next Steps:"
echo "1. Copy these files to new server:"
echo "   - $BACKUP_DIR/$ARCHIVE_NAME"
echo "   - $BACKUP_DIR/${ARCHIVE_NAME}.sha256"
echo "   - $BACKUP_DIR/verify_migration.sh"
echo "   - All .env files (manually backup)"
echo "   - All systemd service files"
echo ""
echo "2. On new server, extract with:"
echo "   cd /home/opc"
echo "   sudo tar -xzf ~/migration_backup/$ARCHIVE_NAME"
echo "   sudo chown -R opc:opc automation/"
echo ""
echo "3. Run verification:"
echo "   bash ~/migration_backup/verify_migration.sh"
echo ""
echo "⚠️ IMPORTANT: Your source files are UNTOUCHED - nothing was deleted!"
echo "Keep the old server running until migration is confirmed successful."