"""
Automation Scripts Package

Contains the automation functions and related scripts.
"""

from .run_automation import (
    run_gmail_automation, 
    run_evolve_automation, 
    run_csv_automation, 
    run_ics_automation, 
    run_hcp_automation
)

__all__ = [
    'run_gmail_automation', 
    'run_evolve_automation', 
    'run_csv_automation', 
    'run_ics_automation', 
    'run_hcp_automation'
]