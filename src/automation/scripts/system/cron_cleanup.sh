#!/bin/bash
# Setup cron job for system cleanup

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Add cleanup cron jobs
echo "Setting up system cleanup cron jobs..."

# Create a temporary file with the new cron jobs
TEMP_CRON=$(mktemp)

# Get existing crontab (if any)
crontab -l 2>/dev/null > "$TEMP_CRON" || true

# Remove any existing cleanup jobs
grep -v "cleanup-system.py" "$TEMP_CRON" > "$TEMP_CRON.new" || true
mv "$TEMP_CRON.new" "$TEMP_CRON"

# Add new cleanup jobs
echo "" >> "$TEMP_CRON"
echo "# System cleanup jobs" >> "$TEMP_CRON"
echo "# Daily cleanup of Chrome profiles (runs at 2:30 AM)" >> "$TEMP_CRON"
echo "30 2 * * * /usr/bin/python3 $SCRIPT_DIR/cleanup-system.py --chrome-days 1 >> /home/opc/automation/src/automation/logs/cleanup_cron.log 2>&1" >> "$TEMP_CRON"
echo "" >> "$TEMP_CRON"
echo "# Weekly comprehensive cleanup (runs Sunday at 3:00 AM)" >> "$TEMP_CRON"
echo "0 3 * * 0 /usr/bin/python3 $SCRIPT_DIR/cleanup-system.py >> /home/opc/automation/src/automation/logs/cleanup_cron.log 2>&1" >> "$TEMP_CRON"

# Install the new crontab
crontab "$TEMP_CRON"

# Clean up
rm -f "$TEMP_CRON"

echo "Cleanup cron jobs have been set up successfully!"
echo ""
echo "Cron schedule:"
echo "- Daily: Chrome profile cleanup at 2:30 AM"
echo "- Weekly: Full system cleanup on Sundays at 3:00 AM"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove cleanup jobs: crontab -l | grep -v cleanup-system.py | crontab -"