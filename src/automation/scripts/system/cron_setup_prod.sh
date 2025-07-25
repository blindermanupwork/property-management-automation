#!/bin/bash
# Production Cron Setup Script
# This sets up the production automation to run every 1 hour

echo "Setting up PRODUCTION cron jobs..."

# Add production automation cron job
(crontab -l 2>/dev/null; echo "# Production Automation - runs every hour on the hour") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * /usr/bin/python3 /home/opc/automation/src/run_automation_prod.py >> /home/opc/automation/src/automation/logs/automation_prod_cron.log 2>&1") | crontab -

echo "✅ Production cron job added:"
echo "   - Runs at: Every hour on the hour (24 times per day)"
echo "   - Logs to: /home/opc/automation/src/automation/logs/automation_prod_cron.log"
echo ""
echo "Current crontab:"
crontab -l