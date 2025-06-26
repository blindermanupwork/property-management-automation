#!/bin/bash
# Production Monitoring Script

# Get paths relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALERT_EMAIL="${ALERT_EMAIL:-admin@localhost}"
LOG_DIR="$SCRIPT_DIR/logs"
HEALTH_LOG="$LOG_DIR/health_check.log"
ALERT_LOG="$LOG_DIR/alerts.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$HEALTH_LOG"
}

# Function to send alert
send_alert() {
    local message="$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $message" | tee -a "$ALERT_LOG"
    
    # Send email alert (requires sendmail setup)
    # echo "Subject: Automation Alert - $message" | sendmail "$ALERT_EMAIL"
    
    # For now, log to file and could integrate with external service
    echo "🚨 ALERT: $message"
}

# Check if automation processes are running
check_processes() {
    log_message "Checking running processes..."
    
    # Check for recent automation runs
    recent_logs=$(find "$LOG_DIR" -name "automation_*.log" -mtime -1 | wc -l)
    if [ "$recent_logs" -eq 0 ]; then
        send_alert "No automation runs in the last 24 hours"
        return 1
    fi
    
    log_message "✅ Recent automation activity detected"
    return 0
}

# Check log files for errors
check_errors() {
    log_message "Checking for errors in recent logs..."
    
    # Get the most recent automation log
    latest_log=$(ls -t "$LOG_DIR"/automation_*.log 2>/dev/null | head -1)
    
    if [ -z "$latest_log" ]; then
        send_alert "No automation logs found"
        return 1
    fi
    
    # Check for actual error patterns (exclude success messages)
    error_count=$(grep -i "error\|failed\|exception" "$latest_log" | grep -v "✅\|🗸\|completed successfully" | wc -l)
    if [ "$error_count" -gt 0 ]; then
        send_alert "Found $error_count errors in latest automation run"
        return 1
    fi
    
    log_message "✅ No errors found in latest automation run"
    return 0
}

# Check disk space
check_disk_space() {
    log_message "Checking disk space..."
    
    disk_usage=$(df /home/opc | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        send_alert "Disk usage is ${disk_usage}% - running low on space"
        return 1
    fi
    
    log_message "✅ Disk usage: ${disk_usage}%"
    return 0
}

# Check CSV processing
check_csv_processing() {
    log_message "Checking CSV processing..."
    
    # Check if there are stuck files in CSV processing directories
    stuck_dev=$(find "$SCRIPT_DIR/CSV_process_development" -name "*.csv" -mtime +1 2>/dev/null | wc -l)
    stuck_prod=$(find "$SCRIPT_DIR/CSV_process_production" -name "*.csv" -mtime +1 2>/dev/null | wc -l)
    total_stuck=$((stuck_dev + stuck_prod))
    
    if [ "$total_stuck" -gt 0 ]; then
        send_alert "$total_stuck CSV files stuck in processing folders for over 24 hours (dev: $stuck_dev, prod: $stuck_prod)"
        return 1
    fi
    
    log_message "✅ No stuck CSV files detected"
    return 0
}

# Main health check
main() {
    log_message "=== Starting health check ==="
    
    local all_good=true
    
    check_processes || all_good=false
    check_errors || all_good=false
    check_disk_space || all_good=false
    check_csv_processing || all_good=false
    
    if [ "$all_good" = true ]; then
        log_message "✅ All systems healthy"
    else
        log_message "❌ Some issues detected - check alerts"
    fi
    
    log_message "=== Health check complete ==="
}

# Run main function
main