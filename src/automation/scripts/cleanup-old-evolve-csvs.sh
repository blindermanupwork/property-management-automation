#!/bin/bash
# Script to clean up old Evolve CSV files with random names

echo "Cleaning up old Evolve CSV files..."

# Remove files with 8-character random names in production
find /home/opc/automation/src/automation/scripts/CSV_process_production/ -name "[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9].csv" -type f -exec rm -v {} \;

# Remove files with 8-character random names in development  
find /home/opc/automation/src/automation/scripts/CSV_process_development/ -name "[a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9].csv" -type f -exec rm -v {} \;

echo "Cleanup complete!"