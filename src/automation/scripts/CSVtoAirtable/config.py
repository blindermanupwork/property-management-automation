import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the main config
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import from main config file - all credentials come from environment variables
from config import *

# Legacy compatibility - these are now imported from main config
# AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
# AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID") 
# AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Reservations")

# Additional CSVtoAirtable specific config
ICS_CRON_TABLE_NAME = "ICS Cron"

# Legacy settings (now controlled by main config)
IGNORE_PAST_ROWS = IGNORE_EVENTS_ENDING_BEFORE_TODAY
IGNORE_ROWS_MONTHS_AHEAD = IGNORE_EVENTS_ENDING_MONTHS_AWAY  
FETCH_ROWS_MONTHS_BEFORE = FETCH_RESERVATIONS_MONTHS_BEFORE