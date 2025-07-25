# Disk Space Management Guide

## Overview

This guide documents the disk space management and cleanup strategies implemented for the automation system.

## Current Disk Usage

As of July 2025, the root filesystem is at 86% capacity (31GB used of 36GB total). Major space consumers include:

- `/home/opc`: 7.5GB total
  - `automation`: 1.8GB (includes node_modules, logs, archives)
  - `.cache`: 1.6GB (browser caches, pip, npm)
  - `.local`: 1.2GB (Python packages)
- `/var`: 2.9GB (logs, cache, temp files)
- `/tmp`: 1.5GB (mostly Chrome profiles from Selenium)

## Automated Cleanup Tools

### 1. System Cleanup Script
**Location**: `/home/opc/automation/src/automation/scripts/system/cleanup-system.py`

**Features**:
- Chrome profile cleanup (removes profiles older than 1 day)
- Old CSV file removal (30+ days)
- Log file archival (30+ days)
- Export archive cleanup (60+ days)
- NPM/pip cache cleaning
- Browser cache removal

**Usage**:
```bash
# Dry run (see what would be cleaned)
python3 cleanup-system.py --dry-run

# Run full cleanup
python3 cleanup-system.py

# Custom retention periods
python3 cleanup-system.py --chrome-days 2 --csv-days 45 --log-days 60

# Clean specific components
python3 cleanup-system.py --chrome-days 1  # Only Chrome profiles
```

### 2. Disk Space Monitor
**Location**: `/home/opc/automation/src/automation/scripts/system/monitor-disk-space.py`

**Features**:
- Filesystem usage analysis
- Largest directories identification
- Large file detection (>100MB)
- Chrome profile usage tracking
- Old log file detection
- Cleanup recommendations

**Usage**:
```bash
python3 monitor-disk-space.py
```

### 3. Log Rotation Configuration
**Location**: `/etc/logrotate.d/automation`

**Configured Logs**:
- Automation logs: Daily rotation, 7 days retention
- CSV/ICS sync logs: Daily rotation, 14 days retention, 10MB size limit
- Webhook logs: Daily rotation, 14 days retention, 5MB size limit
- Backup logs: Weekly rotation, 4 weeks retention

## Cron Schedule

The following cleanup jobs run automatically:

1. **Daily Chrome Cleanup** (2:30 AM)
   - Removes Chrome profiles older than 1 day
   - Prevents /tmp from filling up

2. **Weekly Full Cleanup** (Sundays 3:00 AM)
   - Runs comprehensive system cleanup
   - Removes old CSVs, logs, and archives
   - Cleans caches

3. **Log Rotation** (Daily)
   - Handled by system logrotate
   - Compresses and archives old logs

## Manual Cleanup Commands

When disk space is critical:

```bash
# 1. Run full system cleanup
python3 /home/opc/automation/src/automation/scripts/system/cleanup-system.py

# 2. Force log rotation
sudo logrotate -f /etc/logrotate.d/automation

# 3. Clean all Chrome profiles
rm -rf /tmp/chrome-profile-*

# 4. Clear npm cache
npm cache clean --force

# 5. Clear pip cache
pip cache purge

# 6. Clean old export archives
find /home/opc/automation/export/archive -mtime +30 -delete
```

## Space-Saving Best Practices

1. **Chrome Profiles**: The Evolve scraper creates Chrome profiles that accumulate in /tmp. The daily cleanup removes these automatically.

2. **Log Files**: All automation logs are configured with size limits and rotation policies to prevent unlimited growth.

3. **CSV Archives**: Processed CSV files are kept for 30 days for auditing, then automatically removed.

4. **Export Archives**: Large JSON exports are cleaned after 60 days.

5. **Cache Management**: Browser, npm, and pip caches are cleared weekly.

## Monitoring

To monitor disk usage trends:

```bash
# Check current usage
df -h /

# Run disk monitor for detailed analysis
python3 /home/opc/automation/src/automation/scripts/system/monitor-disk-space.py

# View cleanup logs
tail -f /home/opc/automation/src/automation/logs/cleanup_cron.log

# Check what's using space
du -h --max-depth=2 /home/opc | sort -hr | head -20
```

## Troubleshooting

If disk space runs critically low:

1. **Immediate Actions**:
   - Run `cleanup-system.py` without dry-run
   - Remove all Chrome profiles: `rm -rf /tmp/chrome-profile-*`
   - Clear caches: `npm cache clean --force && pip cache purge`

2. **Investigation**:
   - Run `monitor-disk-space.py` to identify culprits
   - Check for large log files: `find / -name "*.log" -size +100M 2>/dev/null`
   - Look for core dumps: `find / -name "core.*" 2>/dev/null`

3. **Long-term Solutions**:
   - Adjust retention periods in cleanup script
   - Increase cleanup frequency in cron
   - Consider archiving old data to external storage

## Configuration Files

- Cleanup script: `/home/opc/automation/src/automation/scripts/system/cleanup-system.py`
- Monitor script: `/home/opc/automation/src/automation/scripts/system/monitor-disk-space.py`
- Cron setup: `/home/opc/automation/src/automation/scripts/system/cron_cleanup.sh`
- Logrotate config: `/etc/logrotate.d/automation`

## Notes

- The system is configured to maintain a balance between data retention for debugging and available disk space
- All cleanup operations log their actions for auditing
- Critical threshold is set at 90% disk usage
- Warning threshold is set at 85% disk usage