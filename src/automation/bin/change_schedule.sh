#!/bin/bash
# Quick Schedule Changer for Production Automation

AUTOMATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🕐 Current Automation Schedule:${NC}"
crontab -l | grep "run_anywhere.py" | head -5

echo ""
echo -e "${YELLOW}Choose a new schedule:${NC}"
echo "1) Every 2 hours starting at 8:00 AM PST"
echo "2) Every 4 hours starting at 9:00 AM PST" 
echo "3) Every 6 hours starting at 6:00 AM PST"
echo "4) Every 8 hours starting at 8:00 AM PST"
echo "5) Every 12 hours at 8:00 AM & 8:00 PM PST"
echo "6) Once daily at 9:00 AM PST"
echo "7) Custom schedule"
echo ""

read -p "Select option (1-7): " choice

case $choice in
    1)
        SCHEDULE="0 8,10,12,14,16,18,20,22,0,2,4,6 * * *"
        DESCRIPTION="Every 2 hours starting at 8:00 AM PST"
        ;;
    2)
        SCHEDULE="0 9,13,17,21 * * *"
        DESCRIPTION="Every 4 hours starting at 9:00 AM PST"
        ;;
    3)
        SCHEDULE="0 6,12,18 * * *"
        DESCRIPTION="Every 6 hours starting at 6:00 AM PST"
        ;;
    4)
        SCHEDULE="0 8,16,0 * * *"
        DESCRIPTION="Every 8 hours starting at 8:00 AM PST"
        ;;
    5)
        SCHEDULE="0 8,20 * * *"
        DESCRIPTION="Twice daily at 8:00 AM & 8:00 PM PST"
        ;;
    6)
        SCHEDULE="0 9 * * *"
        DESCRIPTION="Once daily at 9:00 AM PST"
        ;;
    7)
        echo ""
        echo "Enter custom schedule in cron format (minute hour * * *):"
        echo "Examples:"
        echo "  0 9,15,21 * * *  = 9 AM, 3 PM, 9 PM daily"
        echo "  30 */6 * * *     = Every 6 hours at 30 minutes past"
        echo "  0 8 * * 1-5      = 8 AM Monday through Friday"
        echo ""
        read -p "Custom schedule: " SCHEDULE
        DESCRIPTION="Custom schedule: $SCHEDULE"
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

# Backup current cron
crontab -l > /tmp/cron_backup_$(date +%Y%m%d_%H%M%S)

# Create new crontab
cat > /tmp/new_cron << EOF
# Property Management Automation - $DESCRIPTION
$SCHEDULE cd $AUTOMATION_DIR && python3 run_anywhere.py >> $AUTOMATION_DIR/logs/automation_cron.log 2>&1

# Daily backup at 1:00 AM PST
0 1 * * * $AUTOMATION_DIR/bin/backup.sh >> $AUTOMATION_DIR/logs/backup_cron.log 2>&1

# Health monitoring every 30 minutes
*/30 * * * * $AUTOMATION_DIR/bin/monitor.sh >> $AUTOMATION_DIR/logs/monitor_cron.log 2>&1

# Log cleanup - daily at 3:00 AM PST
0 3 * * * find $AUTOMATION_DIR/logs -name "*.log" -mtime +30 -delete

# Weekly CSV cleanup - Sundays at 4:00 AM PST
0 4 * * 0 find $AUTOMATION_DIR/CSV_done -name "*.csv" -mtime +7 -exec mv {} $AUTOMATION_DIR/backups/old_csv/ \;

EOF

# Install new schedule
crontab /tmp/new_cron

echo ""
echo -e "${GREEN}✅ Schedule updated successfully!${NC}"
echo -e "${YELLOW}New schedule:${NC} $DESCRIPTION"
echo ""
echo -e "${BLUE}Updated crontab:${NC}"
crontab -l | grep "run_anywhere.py"
echo ""
echo -e "${YELLOW}Run './bin/status' to see the next scheduled time${NC}"