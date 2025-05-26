#!/bin/bash

# Master Property Management Automation Runner
# Runs all components: Gmail → Evolve → CSV → ICS → HCP

cd ~/automation
export PATH="$HOME/.local/bin:$PATH"

# Create log file with timestamp
LOG_FILE="logs/automation_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

echo "=====================================================" | tee -a "$LOG_FILE"
echo "=== PROPERTY MANAGEMENT AUTOMATION STARTED ===" | tee -a "$LOG_FILE"
echo "=====================================================" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"

# Function to log with timestamp
log_with_time() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check script exit status
check_status() {
    if [ $? -eq 0 ]; then
        log_with_time "✅ $1 completed successfully"
        return 0
    else
        log_with_time "❌ $1 failed"
        return 1
    fi
}

# Debug Python environment
log_with_time "DEBUG: Python path: $(which python3.8)"
log_with_time "DEBUG: Python version: $(python3.8 --version)"

# STEP 1: Download iTrip CSV reports from Gmail
log_with_time "STEP 1: Downloading iTrip CSV reports from Gmail..."
python3.8 scripts/gmail/gmail_downloader_linux.py --output-dir CSV_process >> "$LOG_FILE" 2>&1
check_status "Gmail CSV download"

# STEP 2: Scrape Evolve portal data  
log_with_time "STEP 2: Scraping Evolve portal data..."
python3.8 scripts/evolve/evolveScrape.py --headless >> "$LOG_FILE" 2>&1
check_status "Evolve portal scraping"

# STEP 3: Process CSV files (both iTrip and Evolve)
log_with_time "STEP 3: Processing CSV files to Airtable..."
python3.8 scripts/CSVtoAirtable/csvProcess.py >> "$LOG_FILE" 2>&1
check_status "CSV processing"

# STEP 4: Sync ICS calendar feeds
log_with_time "STEP 4: Syncing ICS calendar feeds..."  
python3.8 scripts/icsAirtableSync/icsProcess.py >> "$LOG_FILE" 2>&1
check_status "ICS feed synchronization"

# STEP 5: Create/update HousecallPro jobs
log_with_time "STEP 5: Syncing HousecallPro service jobs..."
node hcp-sync/hcp_sync.js >> "$LOG_FILE" 2>&1
check_status "HousecallPro job sync"

# Summary
echo "=====================================================" | tee -a "$LOG_FILE"
log_with_time "AUTOMATION RUN COMPLETE"
echo "=====================================================" | tee -a "$LOG_FILE"

# Clean up old logs (keep last 30 days)
find logs/ -name "automation_*.log" -mtime +30 -delete 2>/dev/null

# Show quick summary
log_with_time "Summary logged to: $LOG_FILE"
echo ""
echo "🎉 Property Management Automation Cycle Complete!"
echo "Check the log file for detailed results: $LOG_FILE"