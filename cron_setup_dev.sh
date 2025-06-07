#!/bin/bash
# Development Cron Setup Script
# This sets up the development automation to run every 4 hours, 10 minutes after production

echo "Setting up DEVELOPMENT cron jobs..."

# Add development automation cron job
(crontab -l 2>/dev/null; echo "# Development Automation - runs every 4 hours, 10 minutes after production") | crontab -
(crontab -l 2>/dev/null; echo "10 0,4,8,12,16,20 * * * /usr/bin/python3 /home/opc/automation/src/run_automation_dev.py >> /home/opc/automation/src/automation/logs/automation_dev_cron.log 2>&1") | crontab -

echo "✅ Development cron job added:"
echo "   - Runs at: 12:10am, 4:10am, 8:10am, 12:10pm, 4:10pm, 8:10pm"
echo "   - Logs to: /home/opc/automation/src/automation/logs/automation_dev_cron.log"
echo ""
echo "Current crontab:"
crontab -l