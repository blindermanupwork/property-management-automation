#!/bin/bash
# Production Automation Status Checker
# Shows when automations ran and their success status

AUTOMATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.."
LOG_DIR="$AUTOMATION_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to format timestamps
format_time() {
    date -d "$1" "+%Y-%m-%d %I:%M %p PST" 2>/dev/null || echo "$1"
}

# Function to get file modification time in PST
get_file_time() {
    if [ -f "$1" ]; then
        # Get modification time in PST
        TZ='America/Los_Angeles' stat -c %y "$1" 2>/dev/null | cut -d'.' -f1
    else
        echo "Never"
    fi
}

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Property Management Automation Status                     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Current time in PST
echo -e "${BLUE}🕐 Current Time (PST):${NC} $(TZ='America/Los_Angeles' date '+%Y-%m-%d %I:%M %p PST')"
echo ""

# Check if cron is scheduled
echo -e "${YELLOW}📅 Scheduled Jobs:${NC}"
if crontab -l 2>/dev/null | grep -q "run_anywhere.py"; then
    echo -e "  ✅ Production automation is scheduled"
    crontab -l | grep "run_anywhere.py" | head -1 | sed 's/^/    /'
else
    echo -e "  ❌ No automation scheduled (run ./bin/setup_prod_schedule.sh)"
fi
echo ""

# Last Automation Run
echo -e "${YELLOW}🚀 Last Automation Runs:${NC}"

# Check cron log
CRON_LOG="$LOG_DIR/automation_cron.log"
if [ -f "$CRON_LOG" ]; then
    LAST_CRON_RUN=$(get_file_time "$CRON_LOG")
    echo -e "  📝 Cron Log Updated: ${GREEN}$LAST_CRON_RUN${NC}"
    
    # Get last few log entries
    echo -e "  📊 Recent Cron Results:"
    tail -10 "$CRON_LOG" 2>/dev/null | grep -E "(Results:|📊)" | tail -3 | sed 's/^/    /'
else
    echo -e "  ❌ No cron automation log found"
fi

# Check Airtable status via API
echo ""
echo -e "${YELLOW}📋 Airtable Automation Status:${NC}"
cd "$AUTOMATION_DIR"
python3 run_anywhere.py --list 2>/dev/null | grep -E "(✅|❌)" | sed 's/^/  /'

echo ""

# Backup Status
echo -e "${YELLOW}💾 Backup Status:${NC}"
BACKUP_LOG="$LOG_DIR/backup_cron.log"
BACKUP_DIR="$AUTOMATION_DIR/backups"

if [ -f "$BACKUP_LOG" ]; then
    LAST_BACKUP=$(get_file_time "$BACKUP_LOG")
    echo -e "  📝 Last Backup: ${GREEN}$LAST_BACKUP${NC}"
    
    # Count backups
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
        LATEST_BACKUP=$(ls -1t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
        if [ ! -z "$LATEST_BACKUP" ]; then
            BACKUP_SIZE=$(du -h "$LATEST_BACKUP" 2>/dev/null | cut -f1)
            BACKUP_NAME=$(basename "$LATEST_BACKUP")
            echo -e "  📁 Latest Backup: ${GREEN}$BACKUP_NAME${NC} (${BACKUP_SIZE})"
            echo -e "  📊 Total Backups: ${GREEN}$BACKUP_COUNT${NC}"
        fi
    fi
else
    echo -e "  ❌ No backup log found"
fi

echo ""

# Health Check
echo -e "${YELLOW}🏥 System Health:${NC}"
MONITOR_LOG="$LOG_DIR/monitor_cron.log"
if [ -f "$MONITOR_LOG" ]; then
    # Get last health status
    LAST_HEALTH=$(tail -20 "$MONITOR_LOG" 2>/dev/null | grep -E "(All systems healthy|issues detected)" | tail -1)
    if echo "$LAST_HEALTH" | grep -q "All systems healthy"; then
        echo -e "  ✅ ${GREEN}System Health: Good${NC}"
    elif echo "$LAST_HEALTH" | grep -q "issues detected"; then
        echo -e "  ⚠️  ${YELLOW}System Health: Issues Detected${NC}"
    else
        echo -e "  ❓ System Health: Unknown"
    fi
    
    # Disk usage
    DISK_USAGE=$(df /home/opc | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 80 ]; then
        echo -e "  💾 Disk Usage: ${GREEN}${DISK_USAGE}%${NC}"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "  💾 Disk Usage: ${YELLOW}${DISK_USAGE}%${NC}"
    else
        echo -e "  💾 Disk Usage: ${RED}${DISK_USAGE}%${NC}"
    fi
else
    echo -e "  ❌ No monitoring log found"
fi

echo ""

# Recent Errors
echo -e "${YELLOW}🚨 Recent Issues:${NC}"
ERROR_COUNT=0

# Check for errors in recent logs
for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        # Look for errors in last 24 hours
        RECENT_ERRORS=$(find "$log_file" -mtime -1 -exec grep -l -i "error\|failed\|exception" {} \; 2>/dev/null)
        if [ ! -z "$RECENT_ERRORS" ]; then
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "  ✅ ${GREEN}No recent errors detected${NC}"
else
    echo -e "  ⚠️  ${YELLOW}Found errors in $ERROR_COUNT log files${NC}"
    echo -e "     Run: ${CYAN}grep -i error $LOG_DIR/*.log${NC} for details"
fi

echo ""

# Next Scheduled Run
echo -e "${YELLOW}⏰ Next Scheduled Runs:${NC}"
if crontab -l 2>/dev/null | grep -q "run_anywhere.py"; then
    echo -e "  🚀 Next Automation:"
    
    # Get current time in PST
    CURRENT_PST_HOUR=$(TZ='America/Los_Angeles' date '+%H')
    CURRENT_PST_MIN=$(TZ='America/Los_Angeles' date '+%M')
    CURRENT_MINUTES=$(( $CURRENT_PST_HOUR * 60 + $CURRENT_PST_MIN ))
    CURRENT_DAY=$(TZ='America/Los_Angeles' date '+%d')
    CURRENT_MONTH=$(TZ='America/Los_Angeles' date '+%m')
    
    # Parse actual cron schedule from crontab
    CRON_LINES=$(crontab -l 2>/dev/null | grep "run_anywhere.py" | grep -v "^#")
    
    NEXT_RUN=""
    EARLIEST_MINUTES=99999
    
    while IFS= read -r line; do
        if [ ! -z "$line" ]; then
            # Extract cron fields (minute hour day month dayofweek)
            CRON_MIN=$(echo "$line" | awk '{print $1}')
            CRON_HOUR=$(echo "$line" | awk '{print $2}')
            CRON_DAY=$(echo "$line" | awk '{print $3}')
            CRON_MONTH=$(echo "$line" | awk '{print $4}')
            
            # Handle different cron formats
            if [[ "$CRON_HOUR" == "*/"* ]]; then
                # Every N hours format (e.g., "*/4")
                INTERVAL=$(echo "$CRON_HOUR" | cut -d'/' -f2)
                
                # Find next occurrence
                NEXT_HOUR_CANDIDATE=0
                FOUND_NEXT=false
                for (( h=0; h<=23; h++ )); do
                    if [ $((h % INTERVAL)) -eq 0 ]; then
                        SCHEDULED_MINUTES=$(( h * 60 + CRON_MIN ))
                        if [ $SCHEDULED_MINUTES -gt $CURRENT_MINUTES ]; then
                            # Convert to 12h format
                            if [ $h -eq 0 ]; then
                                NEXT_RUN="12:$(printf "%02d" $CRON_MIN) AM PST"
                            elif [ $h -lt 12 ]; then
                                NEXT_RUN="${h}:$(printf "%02d" $CRON_MIN) AM PST"
                            elif [ $h -eq 12 ]; then
                                NEXT_RUN="12:$(printf "%02d" $CRON_MIN) PM PST"
                            else
                                NEXT_RUN="$((h - 12)):$(printf "%02d" $CRON_MIN) PM PST"
                            fi
                            FOUND_NEXT=true
                            break
                        fi
                    fi
                done
                
                # If no run found today, get first run tomorrow
                if [ "$FOUND_NEXT" = false ]; then
                    # First valid hour tomorrow (starting at 0)
                    for (( h=0; h<=23; h++ )); do
                        if [ $((h % INTERVAL)) -eq 0 ]; then
                            if [ $h -eq 0 ]; then
                                NEXT_RUN="12:$(printf "%02d" $CRON_MIN) AM PST (tomorrow)"
                            elif [ $h -lt 12 ]; then
                                NEXT_RUN="${h}:$(printf "%02d" $CRON_MIN) AM PST (tomorrow)"
                            elif [ $h -eq 12 ]; then
                                NEXT_RUN="12:$(printf "%02d" $CRON_MIN) PM PST (tomorrow)"
                            else
                                NEXT_RUN="$((h - 12)):$(printf "%02d" $CRON_MIN) PM PST (tomorrow)"
                            fi
                            break
                        fi
                    done
                fi
                break
            elif [[ "$CRON_HOUR" == *","* ]]; then
                # Multiple hours specified (e.g., "14,18,22,2")
                IFS=',' read -ra HOURS <<< "$CRON_HOUR"
                for hour in "${HOURS[@]}"; do
                    SCHEDULED_MINUTES=$(( $hour * 60 + $CRON_MIN ))
                    
                    # Check if this run is today and in the future
                    if [ "$CRON_DAY" == "*" ] || [ "$CRON_DAY" == "$CURRENT_DAY" ]; then
                        if [ "$CRON_MONTH" == "*" ] || [ "$CRON_MONTH" == "$CURRENT_MONTH" ]; then
                            if [ $SCHEDULED_MINUTES -gt $CURRENT_MINUTES ] && [ $SCHEDULED_MINUTES -lt $EARLIEST_MINUTES ]; then
                                EARLIEST_MINUTES=$SCHEDULED_MINUTES
                                # Convert 24h to 12h format
                                if [ $hour -eq 0 ]; then
                                    HOUR_12="12"
                                    AMPM="AM"
                                elif [ $hour -lt 12 ]; then
                                    HOUR_12="$hour"
                                    AMPM="AM"
                                elif [ $hour -eq 12 ]; then
                                    HOUR_12="12"
                                    AMPM="PM"
                                else
                                    HOUR_12=$((hour - 12))
                                    AMPM="PM"
                                fi
                                
                                # Format minutes
                                if [ $CRON_MIN -lt 10 ]; then
                                    MIN_FORMAT="0$CRON_MIN"
                                else
                                    MIN_FORMAT="$CRON_MIN"
                                fi
                                
                                NEXT_RUN="${HOUR_12}:${MIN_FORMAT} ${AMPM} PST"
                            fi
                        fi
                    fi
                done
            else
                # Single hour or wildcard
                if [ "$CRON_HOUR" == "*" ]; then
                    # Every hour - find next hour
                    NEXT_HOUR=$(( $CURRENT_PST_HOUR + 1 ))
                    if [ $NEXT_HOUR -gt 23 ]; then
                        NEXT_HOUR=0
                        NEXT_RUN="12:$(printf "%02d" $CRON_MIN) AM PST (tomorrow)"
                    else
                        if [ $NEXT_HOUR -eq 0 ]; then
                            NEXT_RUN="12:$(printf "%02d" $CRON_MIN) AM PST"
                        elif [ $NEXT_HOUR -lt 12 ]; then
                            NEXT_RUN="${NEXT_HOUR}:$(printf "%02d" $CRON_MIN) AM PST"
                        elif [ $NEXT_HOUR -eq 12 ]; then
                            NEXT_RUN="12:$(printf "%02d" $CRON_MIN) PM PST"
                        else
                            NEXT_RUN="$((NEXT_HOUR - 12)):$(printf "%02d" $CRON_MIN) PM PST"
                        fi
                    fi
                    break
                else
                    # Specific hour
                    SCHEDULED_MINUTES=$(( $CRON_HOUR * 60 + $CRON_MIN ))
                    if [ $SCHEDULED_MINUTES -gt $CURRENT_MINUTES ]; then
                        # Convert to 12h format
                        if [ $CRON_HOUR -eq 0 ]; then
                            NEXT_RUN="12:$(printf "%02d" $CRON_MIN) AM PST"
                        elif [ $CRON_HOUR -lt 12 ]; then
                            NEXT_RUN="${CRON_HOUR}:$(printf "%02d" $CRON_MIN) AM PST"
                        elif [ $CRON_HOUR -eq 12 ]; then
                            NEXT_RUN="12:$(printf "%02d" $CRON_MIN) PM PST"
                        else
                            NEXT_RUN="$((CRON_HOUR - 12)):$(printf "%02d" $CRON_MIN) PM PST"
                        fi
                        break
                    fi
                fi
            fi
        fi
    done <<< "$CRON_LINES"
    
    # If no run found today, check for first run tomorrow
    if [ -z "$NEXT_RUN" ]; then
        # Get first scheduled time from cron
        FIRST_LINE=$(echo "$CRON_LINES" | head -1)
        if [ ! -z "$FIRST_LINE" ]; then
            FIRST_MIN=$(echo "$FIRST_LINE" | awk '{print $1}')
            FIRST_HOUR=$(echo "$FIRST_LINE" | awk '{print $2}')
            
            if [[ "$FIRST_HOUR" == *","* ]]; then
                # Get first hour from comma-separated list
                FIRST_HOUR=$(echo "$FIRST_HOUR" | cut -d',' -f1)
            fi
            
            # Convert to 12h format for tomorrow
            if [ "$FIRST_HOUR" -eq 0 ]; then
                NEXT_RUN="12:$(printf "%02d" $FIRST_MIN) AM PST (tomorrow)"
            elif [ "$FIRST_HOUR" -lt 12 ]; then
                NEXT_RUN="${FIRST_HOUR}:$(printf "%02d" $FIRST_MIN) AM PST (tomorrow)"
            elif [ "$FIRST_HOUR" -eq 12 ]; then
                NEXT_RUN="12:$(printf "%02d" $FIRST_MIN) PM PST (tomorrow)"
            else
                NEXT_RUN="$((FIRST_HOUR - 12)):$(printf "%02d" $FIRST_MIN) PM PST (tomorrow)"
            fi
        fi
    fi
    
    if [ ! -z "$NEXT_RUN" ]; then
        echo -e "     ${GREEN}$NEXT_RUN${NC}"
    else
        echo -e "     ${YELLOW}Unable to determine next run time${NC}"
    fi
fi

echo ""
echo -e "${CYAN}──────────────────────────────────────────────────────────────────────────────${NC}"
echo -e "${BLUE}💡 Quick Commands:${NC}"
echo -e "  🚀 Run now: ${CYAN}python3 run_anywhere.py${NC}"
echo -e "  📊 Health check: ${CYAN}./bin/monitor.sh${NC}"
echo -e "  💾 Manual backup: ${CYAN}./bin/backup.sh${NC}"
echo -e "  📝 View logs: ${CYAN}tail -f logs/*.log${NC}"
echo -e "${CYAN}──────────────────────────────────────────────────────────────────────────────${NC}"