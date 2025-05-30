#!/bin/bash
# Setup cron jobs for monitoring and automation

# Get the absolute path of the automation directory
AUTOMATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create backup of current crontab (if any)
crontab -l > /tmp/current_cron 2>/dev/null || echo "# New crontab" > /tmp/current_cron

# Add our automation jobs with absolute paths
cat >> /tmp/current_cron << EOF

# Property Management Automation
# Run main automation daily at 6 AM
0 6 * * * cd $AUTOMATION_DIR && python3 run_anywhere.py >> $AUTOMATION_DIR/logs/cron.log 2>&1

# Health monitoring every 30 minutes
*/30 * * * * $AUTOMATION_DIR/bin/monitor.sh

# Backup automation weekly on Sundays at 2 AM  
0 2 * * 0 $AUTOMATION_DIR/bin/backup.sh >> $AUTOMATION_DIR/logs/backup.log 2>&1

# Clean old logs daily at 1 AM
0 1 * * * find $AUTOMATION_DIR/logs -name "*.log" -mtime +30 -delete

EOF

# Install the new crontab
crontab /tmp/current_cron

echo "✅ Cron jobs installed successfully"
echo "Current crontab:"
crontab -l