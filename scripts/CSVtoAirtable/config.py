# config.py



# Airtable configuration
AIRTABLE_API_KEY = "REDACTED_API_KEY"
AIRTABLE_BASE_ID = "app67yWFv0hKdl6jM"
AIRTABLE_TABLE_NAME = "Reservations"  # Make sure this table exists in your Airtable base
PROPERTIES_TABLE_NAME = "Properties"
ICS_FEEDS_TABLE_NAME = "ICS Feeds"
ICS_CRON_TABLE_NAME ="ICS Cron"

PROPERTIES_NAME_FIELD = "Property Name"        # e.g. "Property Name"
PROPERTY_LINK_FIELD = "Property ID"        # e.g. "Property ID"

# config.py  (new lines)
IGNORE_PAST_ROWS          = True          # skip rows ending before today
IGNORE_ROWS_MONTHS_AHEAD  = 6             # skip rows > 6 months out
FETCH_ROWS_MONTHS_BEFORE  = 0             # include X months historical

