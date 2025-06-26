#!/bin/bash
# Setup Production Schedule - Every 4 hours starting at 2:30 PM PST
# Daily backups and monitoring

# Get the absolute path of the automation directory
AUTOMATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

# Create backup of current crontab (if any)
crontab -l > /tmp/current_cron 2>/dev/null || echo "# New crontab" > /tmp/current_cron

# Add our production automation schedule
cat >> /tmp/current_cron << EOF

# ═══════════════════════════════════════════════════════════════════════════
# Property Management Automation - Production Schedule
# ═══════════════════════════════════════════════════════════════════════════

# Run automation every 4 hours starting at 2:30 PM PST (6:30 PM EST)
# 2:30 PM PST, 6:30 PM PST, 10:30 PM PST, 2:30 AM PST
30 14,18,22,2 * * * cd $AUTOMATION_DIR && python3 run_anywhere.py >> $AUTOMATION_DIR/logs/automation_cron.log 2>&1

# Daily backup at 1:00 AM PST (4:00 AM EST)
0 1 * * * $AUTOMATION_DIR/bin/backup.sh >> $AUTOMATION_DIR/logs/backup_cron.log 2>&1

# Health monitoring every 30 minutes
*/30 * * * * $AUTOMATION_DIR/bin/monitor.sh >> $AUTOMATION_DIR/logs/monitor_cron.log 2>&1

# Log cleanup - Remove logs older than 30 days (daily at 3:00 AM PST)
0 3 * * * find $AUTOMATION_DIR/logs -name "*.log" -mtime +30 -delete

# Weekly deep cleanup - Remove old CSV files (Sundays at 4:00 AM PST)
0 4 * * 0 find $AUTOMATION_DIR/CSV_done -name "*.csv" -mtime +7 -exec mv {} $AUTOMATION_DIR/backups/old_csv/ \;

EOF

# Install the new crontab
crontab /tmp/current_cron

echo "✅ Production schedule installed successfully!"
echo ""
echo "📅 Schedule Summary:"
echo "  🚀 Automation runs: Every 4 hours starting at 2:30 PM PST"
echo "     - 2:30 PM PST (22:30 UTC)"
echo "     - 6:30 PM PST (02:30 UTC+1)"  
echo "     - 10:30 PM PST (06:30 UTC+1)"
echo "     - 2:30 AM PST (10:30 UTC+1)"
echo ""
echo "  💾 Daily backup: 1:00 AM PST (09:00 UTC+1)"
echo "  📊 Health monitoring: Every 30 minutes"
echo "  🧹 Log cleanup: Daily at 3:00 AM PST"
echo "  📁 CSV cleanup: Weekly Sundays at 4:00 AM PST"
echo ""
echo "📋 Current crontab:"
crontab -l | grep -E "(automation|backup|monitor)" | tail -6