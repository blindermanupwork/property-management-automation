#!/usr/bin/env python3
"""
Enhanced ICS to Airtable sync - wrapper that calls the best version.
This is a placeholder that simply delegates to the best implementation.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

def main():
    """Main entry point - just call the best version."""
    from src.automation.scripts.icsAirtableSync.icsProcess_best import main as best_main
    best_main()

if __name__ == "__main__":
    main()