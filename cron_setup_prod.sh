#!/bin/bash
# Production Cron Setup Script
# This sets up the production automation to run every 4 hours

echo "Setting up PRODUCTION cron jobs..."

# Add production automation cron job
(crontab -l 2>/dev/null; echo "# Production Automation - runs every 4 hours at midnight, 4am, 8am, noon, 4pm, 8pm") | crontab -
(crontab -l 2>/dev/null; echo "0 0,4,8,12,16,20 * * * /usr/bin/python3 /home/opc/automation/src/run_automation_prod.py >> /home/opc/automation/src/automation/logs/automation_prod_cron.log 2>&1") | crontab -

echo "✅ Production cron job added:"
echo "   - Runs at: 12am, 4am, 8am, 12pm, 4pm, 8pm"
echo "   - Logs to: /home/opc/automation/src/automation/logs/automation_prod_cron.log"
echo ""
echo "Current crontab:"
crontab -l