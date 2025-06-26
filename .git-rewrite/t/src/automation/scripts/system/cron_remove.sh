#!/bin/bash
# Remove Automation Cron Jobs
# This script removes the old single automation cron job

echo "Removing old automation cron jobs..."

# Remove lines containing run_automation.py (old single automation)
crontab -l 2>/dev/null | grep -v "run_automation.py" | crontab -

echo "✅ Old automation cron jobs removed"
echo ""
echo "Current crontab:"
crontab -l