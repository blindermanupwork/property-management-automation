#!/bin/bash
# Wrapper script for HCP job reconciliation

# Set the Python path
export PYTHONPATH=/home/opc/automation

# Run the reconciliation script with all passed arguments
python3 /home/opc/automation/src/automation/scripts/hcp/reconcile-jobs.py "$@"