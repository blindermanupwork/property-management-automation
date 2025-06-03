#!/bin/bash
# Development Cron Setup Script
# This sets up the development automation to run every 30 minutes for testing

echo "Setting up DEVELOPMENT cron jobs..."

# Add development automation cron job
(crontab -l 2>/dev/null; echo "# Development Automation - runs every 30 minutes") | crontab -
(crontab -l 2>/dev/null; echo "*/30 * * * * /usr/bin/python3 /home/opc/automation/src/run_automation_dev.py >> /home/opc/automation/src/automation/logs/automation_dev_cron.log 2>&1") | crontab -

echo "✅ Development cron job added:"
echo "   - Runs every 30 minutes"
echo "   - Logs to: /home/opc/automation/src/automation/logs/automation_dev_cron.log"
echo ""
echo "Current crontab:"
crontab -l