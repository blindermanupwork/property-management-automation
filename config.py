import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory - automatically detect from script location
BASE_DIR = Path(__file__).parent.absolute()

# Directory Configuration (relative to base)
CSV_PROCESS_DIR = BASE_DIR / "CSV_process"
CSV_DONE_DIR = BASE_DIR / "CSV_done"
LOGS_DIR = BASE_DIR / "logs"
BACKUPS_DIR = BASE_DIR / "backups"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Ensure directories exist
CSV_PROCESS_DIR.mkdir(exist_ok=True)
CSV_DONE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

# Log Files
CSV_SYNC_LOG = LOGS_DIR / "csv_sync.log"
HEALTH_LOG = LOGS_DIR / "health_check.log"
ALERTS_LOG = LOGS_DIR / "alerts.log"

# Environment Detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID") 
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Reservations")
PROPERTIES_TABLE_NAME = "Properties"
ICS_FEEDS_TABLE_NAME = "ICS Feeds"
PROPERTIES_NAME_FIELD = "Property Name"
PROPERTY_LINK_FIELD = "Property ID"

# Date Filtering (months)
FETCH_RESERVATIONS_MONTHS_BEFORE = int(os.getenv("FETCH_RESERVATIONS_MONTHS_BEFORE", "2"))
IGNORE_BLOCKS_MONTHS_AWAY = int(os.getenv("IGNORE_BLOCKS_MONTHS_AWAY", "6"))
IGNORE_EVENTS_ENDING_MONTHS_AWAY = int(os.getenv("IGNORE_EVENTS_ENDING_MONTHS_AWAY", "6"))
IGNORE_EVENTS_ENDING_BEFORE_TODAY = os.getenv("IGNORE_EVENTS_ENDING_BEFORE_TODAY", "True").lower() == "true"

# Gmail Configuration
GMAIL_CREDS_PATH = SCRIPTS_DIR / "gmail" / "credentials.json"
GMAIL_TOKEN_PATH = SCRIPTS_DIR / "gmail" / "token.pickle"

# HousecallPro Configuration
HCP_API_KEY = os.getenv("HCP_API_KEY")
HCP_COMPANY_ID = os.getenv("HCP_COMPANY_ID")

# Evolve Configuration
EVOLVE_USERNAME = os.getenv("EVOLVE_USERNAME")
EVOLVE_PASSWORD = os.getenv("EVOLVE_PASSWORD")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Email Alerts
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

# Validation function
def validate_config():
    """Validate that required configuration is present"""
    required_vars = {
        "AIRTABLE_API_KEY": AIRTABLE_API_KEY,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True

# Development vs Production settings
if ENVIRONMENT == "production":
    # Production: More conservative settings
    FETCH_RESERVATIONS_MONTHS_BEFORE = 2
    IGNORE_BLOCKS_MONTHS_AWAY = 6
else:
    # Development: Faster testing
    FETCH_RESERVATIONS_MONTHS_BEFORE = 1
    IGNORE_BLOCKS_MONTHS_AWAY = 3