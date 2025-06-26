boris to do
- added 6-7-25: clean up md's in root director
- added 6-7-25: check custom service line instruction for dev and test if it works
- added 6-11-25: create "Schedule Sync Details" and rename "Sync Details" to "Service Sync Details" in PRODUCTION Airtable with same field descriptions
- added 6-15-25: REVIEW Site Configuration table in dev Airtable - 22 BUSINESS CONFIGURATIONS ready for review:
  
  **BUSINESS CONFIGURATIONS THAT AFFECT DAILY OPERATIONS:**
  
  **Time Thresholds (3):**
  * Long Term Guest Days: 14 (when to add "LONG TERM GUEST DEPARTING" prefix)
  * Service Duration Minutes: 60 (default cleaning time in HCP)
  * ICS Lookahead Months: 3 (how far ahead to import calendar events)
  
  **Service Names & Patterns (8):**
  * Service Type Turnover: "Turnover"
  * Service Type Return Laundry: "Return Laundry"
  * Service Type Inspection: "Inspection"
  * Default Service Type: "Turnover" (when no type specified)
  * Service Name Pattern - STR SAME DAY: "STR SAME DAY"
  * Service Name Pattern - STR Next Guest: "STR Next Guest"
  * Service Name Pattern - STR Next Guest Unknown: "STR Next Guest Unknown"
  * Long Term Guest Prefix: "LONG TERM GUEST DEPARTING"
  
  **HCP Job Statuses (5) - What cleaners see in the app:**
  * Unscheduled
  * Scheduled
  * In Progress
  * Completed
  * Canceled
  
  **Text Limits (3) - Affects what cleaners see:**
  * Service Line Custom Instructions Max Length: 200 characters
  * Description Truncation Limit: 250 characters
  * Truncation Suffix: "..."
  
  **Schedule Settings (3):**
  * Business Timezone: "America/Phoenix" (Arizona - no daylight saving)
  * Default Arrival Window Minutes: 0 (no arrival window)
  * Same Day Turnover Detection: "Check-in >= Checkout"
  
  After review, Claude will update code to read from this config table instead of hardcoded values
- added 6-15-25: UPDATE Site Configuration table in dev Airtable - ADDED FIELD NAMES AND REACTIVATED JOB TYPE IDS:
  
  **NEW FIELD NAME CONFIGURATIONS ADDED (15):**
  * Field Name - Property ID: "Property ID"
  * Field Name - Service Job ID: "Service Job ID"
  * Field Name - Service Type: "Service Type"
  * Field Name - Final Service Time: "Final Service Time"
  * Field Name - Custom Service Line Instructions: "Custom Service Line Instructions"
  * Field Name - Property Name: "Property Name"
  * Field Name - Same-day Turnover: "Same-day Turnover"
  * Field Name - Check-in Date: "Check-in Date"
  * Field Name - Check-out Date: "Check-out Date"
  * Field Name - Entry Type: "Entry Type"
  * Field Name - Status: "Status"
  * Field Name - Reservation UID: "Reservation UID"
  * Field Name - Turnover Job Template ID: "Turnover Job Template ID"
  * Field Name - Return Laundry Job Template ID: "Return Laundry Job Template ID"
  * Field Name - Inspection Job Template ID: "Inspection Job Template ID"
  
  **REACTIVATED JOB TYPE IDS (3):**
  * Dev Job Type ID - Turnover: "jbt_20319ca089124b00af1b8b40150424ed"
  * Dev Job Type ID - Return Laundry: "jbt_434c62f58d154eb4a968531702b96e8e"
  * Dev Job Type ID - Inspection: "jbt_b5d9457caf694beab5f350d42de3e57f"

claude to do

done

- added 6-12-25: update prod-hcp-sync.js to match dev-hcp-sync.js functionality (sync message verification, Schedule Sync Details field, etc) - completed 6-12-25
- added 6-7-25: clean up /home/opc/automation/src/automation/scripts/airscripts-api and add claude.md of necessary things - completed 6-7-25
- added 6-7-25: gitignore task_tracker.md - completed 6-7-25
- added 6-7-25: fix dev create job api - ❌ Error 400: {"success":false,"error":"You should provide valid api key to perform this operation"} /home/opc/automation/src/automation/scripts/airscripts-api/scripts/dev-create-job.js - completed 6-7-25
- added 6-7-25: review if we need /home/opc/automation/ystemctl status airscripts-api-https - completed 6-7-25
- added 6-7-25: gitignore ~/archive - completed 6-7-25
- added 6-7-25: move /home/opc/automation/src/automation/scripts/airscripts to archive - completed 6-7-25