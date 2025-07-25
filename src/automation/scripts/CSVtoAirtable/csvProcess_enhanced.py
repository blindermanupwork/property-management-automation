#!/usr/bin/env python3
"""
Enhanced CSV to Airtable sync - wrapper that calls the original stable processor.
Version: 2.2.9 (reverted to stable)
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

def main():
    """Main entry point - calls the original CSV processor."""
    from src.automation.scripts.CSVtoAirtable.csvProcess import main as original_main
    original_main()

if __name__ == "__main__":
    main()