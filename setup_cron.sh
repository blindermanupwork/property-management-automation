#!/bin/bash
# Setup cron jobs for monitoring and automation

# Create backup of current crontab (if any)
crontab -l > /tmp/current_cron 2>/dev/null || echo "# New crontab" > /tmp/current_cron

# Add our automation jobs
cat >> /tmp/current_cron << 'EOF'

# Property Management Automation
# Run main automation daily at 6 AM
0 6 * * * /home/opc/automation/run_prod.sh >> /home/opc/automation/logs/cron.log 2>&1

# Health monitoring every 30 minutes
*/30 * * * * /home/opc/automation/monitor.sh

# Backup automation weekly on Sundays at 2 AM  
0 2 * * 0 /home/opc/automation/backup.sh >> /home/opc/automation/logs/backup.log 2>&1

# Clean old logs daily at 1 AM
0 1 * * * find /home/opc/automation/logs -name "*.log" -mtime +30 -delete

EOF

# Install the new crontab
crontab /tmp/current_cron

echo "✅ Cron jobs installed successfully"
echo "Current crontab:"
crontab -l