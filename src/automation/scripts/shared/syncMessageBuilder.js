// Sync Message Builder for clear, explicit sync status messages
// Used by development environment to provide better clarity for operations

const { formatInTimeZone } = require('date-fns-tz');

/**
 * Format date in Arizona time zone
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted date string
 */
function formatArizonaDate(date) {
  const d = new Date(date);
  return formatInTimeZone(d, 'America/Phoenix', 'MMMM d');
}

/**
 * Format time in Arizona time zone
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted time string
 */
function formatArizonaTime(date) {
  const d = new Date(date);
  return formatInTimeZone(d, 'America/Phoenix', 'h:mm a');
}

/**
 * Format full datetime in Arizona time zone
 * @param {Date|string} date - Date to format
 * @returns {string} Formatted datetime string
 */
function formatArizonaDateTime(date) {
  const d = new Date(date);
  return formatInTimeZone(d, 'America/Phoenix', 'MMMM d \'at\' h:mm a');
}

/**
 * Get current timestamp in Arizona time zone for sync details
 * @returns {string} Formatted timestamp string
 */
function getArizonaTimestamp() {
  const now = new Date();
  return formatInTimeZone(now, 'America/Phoenix', 'MMM d, h:mm a');
}

/**
 * Build clear, explicit sync status messages
 * @param {string} status - Status type (SYNCED, WRONG_DATE, WRONG_TIME, etc.)
 * @param {Object} data - Data for the message
 * @returns {string} Clear sync status message
 */
function buildSyncMessage(status, data) {
  const timestamp = ` - ${getArizonaTimestamp()}`;
  
  switch (status) {
    case 'SYNCED':
      return `Schedules in sync: ${formatArizonaDateTime(data.airtableValue)}${timestamp}`;
    
    case 'WRONG_DATE':
      return `Airtable shows ${formatArizonaDate(data.airtableValue)} but HCP shows ${formatArizonaDate(data.hcpValue)}${timestamp}`;
    
    case 'WRONG_TIME':
      return `Airtable shows ${formatArizonaTime(data.airtableValue)} but HCP shows ${formatArizonaTime(data.hcpValue)}${timestamp}`;
    
    case 'JOB_CANCELED':
      return `Job canceled on ${formatArizonaDateTime(data.canceledAt)}${timestamp}`;
    
    case 'SCHEDULE_UPDATED':
      return `✅ Schedule updated successfully. HCP now shows ${formatArizonaDateTime(data.newValue)}${timestamp}`;
    
    case 'SCHEDULE_UPDATE_FAILED':
      return `❌ Failed to update schedule: ${data.error}${timestamp}`;
    
    case 'NO_JOB':
      return `⚠️ No HCP job exists for this reservation${timestamp}`;
    
    case 'NO_APPOINTMENT':
      return `⚠️ HCP job exists but has no appointment scheduled${timestamp}`;
    
    case 'WEBHOOK_UPDATE':
      return `🔄 Updated from HCP webhook - ${data.details || 'Status change'} - ${formatArizonaDateTime(data.timestamp)}`;
    
    case 'WEBHOOK_ERROR':
      return `❌ Webhook processing error: ${data.error} - ${formatArizonaDateTime(data.timestamp)}`;
    
    case 'MANUAL_SYNC':
      return `🔄 Manual sync initiated - ${formatArizonaDateTime(data.timestamp)}`;
    
    case 'AUTO_SYNC':
      return `🔄 Automated sync - ${formatArizonaDateTime(data.timestamp)}`;
    
    default:
      return `Status: ${status} - ${JSON.stringify(data)}`;
  }
}

// Export for CommonJS
module.exports = {
  buildSyncMessage,
  formatArizonaDate,
  getArizonaTimestamp,
  formatArizonaTime,
  formatArizonaDateTime
};