#!/bin/bash
# Automated Backup System

# Get paths relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
AUTOMATION_DIR="$SCRIPT_DIR"
DATE=$(date +%Y%m%d-%H%M%S)

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log_message "Starting automated backup..."

# Create full system backup
backup_name="automation-full-$DATE.tar.gz"
tar -czf "$BACKUP_DIR/$backup_name" \
    --exclude="node_modules" \
    --exclude="logs/*.log" \
    --exclude="CSV_done" \
    --exclude="backups" \
    "$AUTOMATION_DIR"

log_message "✅ Full backup created: $backup_name"

# Create data-only backup (CSV files, configs)
data_backup="automation-data-$DATE.tar.gz"
tar -czf "$BACKUP_DIR/$data_backup" \
    "$AUTOMATION_DIR/CSV_process_development" \
    "$AUTOMATION_DIR/CSV_process_production" \
    "$AUTOMATION_DIR/CSV_done_development" \
    "$AUTOMATION_DIR/CSV_done_production" \
    "$AUTOMATION_DIR/config/environments" \
    "$AUTOMATION_DIR/.env" \
    "$AUTOMATION_DIR/scripts/gmail/credentials.json" \
    "$AUTOMATION_DIR/scripts/gmail/token.pickle" 2>/dev/null || \
    tar -czf "$BACKUP_DIR/$data_backup" \
    "$AUTOMATION_DIR/CSV_process_development" \
    "$AUTOMATION_DIR/CSV_process_production" \
    "$AUTOMATION_DIR/CSV_done_development" \
    "$AUTOMATION_DIR/CSV_done_production" \
    "$AUTOMATION_DIR/config/environments" \
    "$AUTOMATION_DIR/.env"

log_message "✅ Data backup created: $data_backup"

# Keep last 14 full backups, 30 data backups
cd "$BACKUP_DIR"
ls -t automation-full-*.tar.gz | tail -n +15 | xargs rm -f 2>/dev/null || true
ls -t automation-data-*.tar.gz | tail -n +31 | xargs rm -f 2>/dev/null || true

# Check backup integrity
if tar -tzf "$backup_name" >/dev/null 2>&1; then
    log_message "✅ Backup integrity verified"
else
    log_message "❌ Backup integrity check failed!"
    exit 1
fi

# Report backup size and count
backup_size=$(du -h "$backup_name" | cut -f1)
backup_count=$(ls -1 automation-*.tar.gz | wc -l)

log_message "Backup complete: $backup_size, Total backups: $backup_count"