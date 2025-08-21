#!/bin/bash

# Archive script for unused files in automation project
# Created: 2025-08-11
# This script moves verified unused files to archive directory

ARCHIVE_DIR="/home/opc/automation/archive/2025-08-11-cleanup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/home/opc/automation/archive_${TIMESTAMP}.log"

# Create archive directory
echo "Creating archive directory: $ARCHIVE_DIR" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR"

# Function to safely move files/directories
safe_move() {
    local source="$1"
    local dest_name="$2"
    
    if [ -e "$source" ]; then
        echo "Archiving: $source" | tee -a "$LOG_FILE"
        mv "$source" "$ARCHIVE_DIR/$dest_name" 2>>"$LOG_FILE"
        if [ $? -eq 0 ]; then
            echo "  ✓ Archived successfully" | tee -a "$LOG_FILE"
        else
            echo "  ✗ Failed to archive" | tee -a "$LOG_FILE"
        fi
    else
        echo "Skipping (not found): $source" | tee -a "$LOG_FILE"
    fi
}

echo "========================================" | tee -a "$LOG_FILE"
echo "Starting archive process at $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Archive directories
echo -e "\n### Archiving Directories ###" | tee -a "$LOG_FILE"
safe_move "/home/opc/automation/src/automation/scripts/gmail" "gmail"
safe_move "/home/opc/automation/app" "app"
safe_move "/home/opc/automation/src/automation/bin" "bin"
safe_move "/home/opc/automation/src/automation/scripts/data-exports" "data-exports"
safe_move "/home/opc/automation/src/automation/tests" "tests"
safe_move "/home/opc/automation/testing" "testing"
safe_move "/home/opc/automation/docs" "docs"
safe_move "/home/opc/automation/docs_github" "docs_github"
safe_move "/home/opc/automation/reports" "reports"
safe_move "/home/opc/automation/.git-rewrite" "git-rewrite"
safe_move "/home/opc/automation/.eggs" "eggs"

# Archive HCP scripts that are not used
echo -e "\n### Archiving Unused HCP Scripts ###" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR/hcp-unused"
safe_move "/home/opc/automation/src/automation/scripts/hcp/reconcile-jobs-dev.py" "hcp-unused/reconcile-jobs-dev.py"
safe_move "/home/opc/automation/src/automation/scripts/hcp/reconcile-jobs.py" "hcp-unused/reconcile-jobs.py"
safe_move "/home/opc/automation/src/automation/scripts/hcp/check-service-line-differences.py" "hcp-unused/check-service-line-differences.py"
safe_move "/home/opc/automation/src/automation/scripts/hcp/download-hcp-service-lines.py" "hcp-unused/download-hcp-service-lines.py"
safe_move "/home/opc/automation/src/automation/scripts/hcp/add-batching-to-sync.js" "hcp-unused/add-batching-to-sync.js"
safe_move "/home/opc/automation/src/automation/scripts/hcp/add-simple-delay.patch" "hcp-unused/add-simple-delay.patch"
safe_move "/home/opc/automation/src/automation/scripts/hcp/batch-sync-patch.js" "hcp-unused/batch-sync-patch.js"
safe_move "/home/opc/automation/src/automation/scripts/hcp/dev-hcp-sync-batched.cjs" "hcp-unused/dev-hcp-sync-batched.cjs"
safe_move "/home/opc/automation/src/automation/scripts/hcp/prod-hcp-sync-batched.cjs" "hcp-unused/prod-hcp-sync-batched.cjs"
safe_move "/home/opc/automation/src/automation/scripts/hcp/fix-batched-sync.js" "hcp-unused/fix-batched-sync.js"

# Archive root level files
echo -e "\n### Archiving Root Level Files ###" | tee -a "$LOG_FILE"
safe_move "/home/opc/automation/package.json" "root-package.json"
safe_move "/home/opc/automation/package-lock.json" "root-package-lock.json"
safe_move "/home/opc/automation/node_modules" "root-node_modules"
safe_move "/home/opc/automation/pyproject.toml" "pyproject.toml"
safe_move "/home/opc/automation/setup.py" "setup.py"
safe_move "/home/opc/automation/logrotate.conf" "logrotate.conf"

# Archive test/debug files in tools
echo -e "\n### Archiving Test Scripts ###" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR/tools-test"
safe_move "/home/opc/automation/tools/test-airtable-mcp.js" "tools-test/test-airtable-mcp.js"
safe_move "/home/opc/automation/tools/test-mcp-connection.js" "tools-test/test-mcp-connection.js"
safe_move "/home/opc/automation/tools/test-trello-mcp.cjs" "tools-test/test-trello-mcp.cjs"
safe_move "/home/opc/automation/tools/hcp_mcp_client.py" "tools-test/hcp_mcp_client.py"
safe_move "/home/opc/automation/tools/start-airtable-mcp.sh" "tools-test/start-airtable-mcp.sh"
safe_move "/home/opc/automation/tools/start-trello-mcp.sh" "tools-test/start-trello-mcp.sh"

# Archive backup files
echo -e "\n### Archiving Backup Files ###" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR/backups"
safe_move "/home/opc/automation/src/automation/scripts/run_automation_backup.py" "backups/run_automation_backup.py"
safe_move "/home/opc/automation/src/automation/scripts/CSVtoAirtable/csvProcess_best.py" "backups/csvProcess_best.py"
safe_move "/home/opc/automation/src/automation/scripts/CSVtoAirtable/csvProcess_enhanced.py" "backups/csvProcess_enhanced.py"

# Archive old CSV files from July
echo -e "\n### Archiving Old CSV Files ###" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR/old-csv-july"
find /home/opc/automation/src/automation/scripts/CSV_done_development -name "07-*.csv" -o -name "07-*_tab2.csv" | while read f; do
    if [ -f "$f" ]; then
        mv "$f" "$ARCHIVE_DIR/old-csv-july/" 2>>"$LOG_FILE"
        echo "Moved: $(basename $f)" >> "$LOG_FILE"
    fi
done
find /home/opc/automation/src/automation/scripts/CSV_done_production -name "07-*.csv" -o -name "07-*_tab2.csv" | while read f; do
    if [ -f "$f" ]; then
        mv "$f" "$ARCHIVE_DIR/old-csv-july/" 2>>"$LOG_FILE"
        echo "Moved: $(basename $f)" >> "$LOG_FILE"
    fi
done

# Clean Python cache directories
echo -e "\n### Cleaning Python Cache ###" | tee -a "$LOG_FILE"
find /home/opc/automation -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "Removed all __pycache__ directories" | tee -a "$LOG_FILE"

# Archive compressed logs
echo -e "\n### Archiving Compressed Logs ###" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR/old-logs"
find /home/opc/automation/src/automation/logs -name "*.gz" -o -name "*.log.[1-9]" | while read f; do
    if [ -f "$f" ]; then
        mv "$f" "$ARCHIVE_DIR/old-logs/" 2>>"$LOG_FILE"
        echo "Moved log: $(basename $f)" >> "$LOG_FILE"
    fi
done

# Archive old test/log files from root
echo -e "\n### Archiving Root Test/Log Files ###" | tee -a "$LOG_FILE"
safe_move "/home/opc/automation/CSV_COMPLETE_TESTING_REPORT.md" "CSV_COMPLETE_TESTING_REPORT.md"
safe_move "/home/opc/automation/CSV_ORIGINAL_PROCESSOR_TEST_REPORT.md" "CSV_ORIGINAL_PROCESSOR_TEST_REPORT.md"
safe_move "/home/opc/automation/ITRIP_NEXT_GUEST_SOLUTION.md" "ITRIP_NEXT_GUEST_SOLUTION.md"
safe_move "/home/opc/automation/MIGRATION_GUIDE.md" "MIGRATION_GUIDE.md"
safe_move "/home/opc/automation/test_modifications.log" "test_modifications.log"
safe_move "/home/opc/automation/test_original_processor.log" "test_original_processor.log"
safe_move "/home/opc/automation/test_original_processor_run2.log" "test_original_processor_run2.log"

# Archive unused cleanup scripts
echo -e "\n### Archiving Unused Scripts ###" | tee -a "$LOG_FILE"
mkdir -p "$ARCHIVE_DIR/unused-scripts"
safe_move "/home/opc/automation/src/automation/scripts/cleanup-duplicate-reservations.py" "unused-scripts/cleanup-duplicate-reservations.py"
safe_move "/home/opc/automation/src/automation/scripts/find-duplicate-active-uids.py" "unused-scripts/find-duplicate-active-uids.py"
safe_move "/home/opc/automation/src/automation/scripts/fix-uid-duplicates.py" "unused-scripts/fix-uid-duplicates.py"
safe_move "/home/opc/automation/src/automation/scripts/find-property-date-duplicates-active.py" "unused-scripts/find-property-date-duplicates-active.py"
safe_move "/home/opc/automation/src/automation/scripts/cleanup-old-evolve-csvs.sh" "unused-scripts/cleanup-old-evolve-csvs.sh"
safe_move "/home/opc/automation/src/automation/scripts/system/monitor-disk-space.py" "unused-scripts/monitor-disk-space.py"

# Remove symlinks (keeping actual files in system/)
echo -e "\n### Removing Symlinks ###" | tee -a "$LOG_FILE"
if [ -L "/home/opc/automation/cron_setup_dev.sh" ]; then
    rm "/home/opc/automation/cron_setup_dev.sh"
    echo "Removed symlink: cron_setup_dev.sh" | tee -a "$LOG_FILE"
fi
if [ -L "/home/opc/automation/cron_setup_prod.sh" ]; then
    rm "/home/opc/automation/cron_setup_prod.sh"
    echo "Removed symlink: cron_setup_prod.sh" | tee -a "$LOG_FILE"
fi
if [ -L "/home/opc/automation/cron_remove.sh" ]; then
    rm "/home/opc/automation/cron_remove.sh"
    echo "Removed symlink: cron_remove.sh" | tee -a "$LOG_FILE"
fi

# Archive old backups
echo -e "\n### Archiving Old Backups ###" | tee -a "$LOG_FILE"
safe_move "/home/opc/automation/backups" "old-backups-may-2025"
safe_move "/home/opc/automation/src/property_management_automation.egg-info" "egg-info"

echo -e "\n========================================" | tee -a "$LOG_FILE"
echo "Archive process completed at $(date)" | tee -a "$LOG_FILE"
echo "Archive location: $ARCHIVE_DIR" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"

# Calculate space saved
echo -e "\n### Space Analysis ###" | tee -a "$LOG_FILE"
if [ -d "$ARCHIVE_DIR" ]; then
    ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
    echo "Total archived: $ARCHIVE_SIZE" | tee -a "$LOG_FILE"
fi

echo -e "\nTo permanently delete the archive and free space, run:" | tee -a "$LOG_FILE"
echo "  rm -rf $ARCHIVE_DIR" | tee -a "$LOG_FILE"
echo -e "\nTo restore any files, move them back from the archive directory." | tee -a "$LOG_FILE"