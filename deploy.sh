#!/bin/bash
# Safe Production Deployment Script

set -e  # Exit on any error

BACKUP_DIR="/home/opc/automation/backups"
AUTOMATION_DIR="/home/opc/automation"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup before deployment
create_backup() {
    log_message "Creating backup before deployment..."
    mkdir -p "$BACKUP_DIR"
    
    backup_name="automation-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$BACKUP_DIR/$backup_name" \
        --exclude="node_modules" \
        --exclude="*.log" \
        --exclude="CSV_done" \
        "$AUTOMATION_DIR"
    
    log_message "✅ Backup created: $backup_name"
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t automation-backup-*.tar.gz | tail -n +11 | xargs rm -f 2>/dev/null || true
}

# Run tests in development environment first
run_tests() {
    log_message "Running tests in development environment..."
    
    # Set to dev environment
    export ENVIRONMENT=development
    source "$AUTOMATION_DIR/environments/dev/.env"
    
    # Run a quick test of the automation (just CSV processing)
    cd "$AUTOMATION_DIR"
    timeout 300 python3.8 scripts/CSVtoAirtable/csvProcess.py --dry-run 2>/dev/null || {
        log_message "❌ Development tests failed"
        return 1
    }
    
    log_message "✅ Development tests passed"
}

# Deploy to production
deploy_to_production() {
    log_message "Deploying to production..."
    
    # Set to production environment
    export ENVIRONMENT=production
    source "$AUTOMATION_DIR/environments/prod/.env"
    
    # Update dependencies
    cd "$AUTOMATION_DIR"
    pip install -r requirements.txt --quiet
    npm install --silent
    
    log_message "✅ Production deployment complete"
}

# Verify deployment
verify_deployment() {
    log_message "Verifying deployment..."
    
    # Run health check
    "$AUTOMATION_DIR/monitor.sh"
    
    log_message "✅ Deployment verification complete"
}

# Main deployment process
main() {
    log_message "=== Starting deployment process ==="
    
    create_backup
    run_tests
    deploy_to_production
    verify_deployment
    
    log_message "🚀 Deployment successful!"
    log_message "=== Deployment complete ==="
}

# Run main function
main