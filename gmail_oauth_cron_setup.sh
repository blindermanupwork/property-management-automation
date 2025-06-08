#!/bin/bash
# Gmail OAuth Monitoring Cron Setup
# This script adds OAuth token health monitoring to the existing cron jobs

echo "Setting up Gmail OAuth token monitoring..."

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "oauth_cron_monitor.sh"; then
    echo "OAuth monitoring cron job already exists"
    echo "Current OAuth-related cron jobs:"
    crontab -l 2>/dev/null | grep oauth
else
    echo "Adding OAuth monitoring cron job..."
    
    # Add OAuth monitoring - check every 6 hours, offset from main automation
    (crontab -l 2>/dev/null; echo "# Gmail OAuth Token Health Monitor - runs every 6 hours at 30 minutes past the hour") | crontab -
    (crontab -l 2>/dev/null; echo "30 0,6,12,18 * * * /home/opc/automation/src/automation/scripts/gmail/oauth_cron_monitor.sh >> /home/opc/automation/src/automation/logs/gmail_oauth_cron.log 2>&1") | crontab -
    
    echo "✅ OAuth monitoring cron job added:"
    echo "   - Runs at: 12:30am, 6:30am, 12:30pm, 6:30pm"
    echo "   - Logs to: /home/opc/automation/src/automation/logs/gmail_oauth_cron.log"
fi

echo ""
echo "Current crontab:"
crontab -l

echo ""
echo "OAuth monitoring commands:"
echo "  Check token health: cd /home/opc/automation/src/automation/scripts/gmail && python3 oauth_monitor.py"
echo "  Force token refresh: cd /home/opc/automation/src/automation/scripts/gmail && python3 oauth_monitor.py --force-refresh"
echo "  Check logs: tail -f /home/opc/automation/src/automation/logs/gmail_oauth_monitor.log"