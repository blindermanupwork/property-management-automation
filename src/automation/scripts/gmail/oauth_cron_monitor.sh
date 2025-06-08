#!/bin/bash
# Gmail OAuth Token Health Monitor - Cron Wrapper
# This script runs the OAuth monitor and handles logging for cron execution

# Change to the correct directory
cd "$(dirname "$0")"

# Set up environment variables if needed
export PYTHONPATH="/home/opc/automation:$PYTHONPATH"

# Run the OAuth monitor with quiet output (only errors)
# Exit codes: 0 = healthy, 1 = needs attention
python3 oauth_monitor.py --quiet --check-expiry 48 --notify

# Capture exit code
exit_code=$?

# Log the result for cron monitoring
if [ $exit_code -eq 0 ]; then
    echo "$(date): Gmail OAuth token is healthy" >> /home/opc/automation/src/automation/logs/gmail_oauth_cron.log
else
    echo "$(date): Gmail OAuth token requires attention (exit code: $exit_code)" >> /home/opc/automation/src/automation/logs/gmail_oauth_cron.log
fi

exit $exit_code