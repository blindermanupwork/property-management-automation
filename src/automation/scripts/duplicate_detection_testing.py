#!/usr/bin/env python3
"""
Duplicate Detection Testing Integration
======================================
This module provides a simple interface for ICS and CSV processors
to run duplicate detection tests after each processing run.
"""

import logging
from pathlib import Path
import sys

# Add parent directories to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.automation.scripts.test_duplicate_detection_framework import AutomatedTestFramework


def run_duplicate_detection_tests(processor_type: str, environment: str = None) -> bool:
    """
    Run duplicate detection tests and report results to Airtable.
    
    Args:
        processor_type: Either "ICS" or "CSV" to identify which processor is running
        environment: Optional environment override (development/production)
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    try:
        # Create framework instance
        framework = AutomatedTestFramework(environment)
        
        # Run tests integrated with processor
        all_passed = framework.integrate_with_processor(processor_type)
        
        return all_passed
        
    except Exception as e:
        logging.error(f"❌ Error running duplicate detection tests: {e}")
        return False


def get_test_summary(results: dict) -> str:
    """Get a brief summary of test results for logging."""
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        return f"✅ All {total} tests passed"
    else:
        return f"⚠️ {passed}/{total} tests passed"