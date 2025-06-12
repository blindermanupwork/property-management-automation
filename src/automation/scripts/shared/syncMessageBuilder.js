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
 * Build clear, explicit sync status messages
 * @param {string} status - Status type (SYNCED, WRONG_DATE, WRONG_TIME, etc.)
 * @param {Object} data - Data for the message
 * @returns {string} Clear sync status message
 */
function buildSyncMessage(status, data) {
  switch (status) {
    case 'SYNCED':
      return `✅ Schedule is in sync. Both Airtable and HCP show ${formatArizonaDateTime(data.airtableValue)}`;
    
    case 'WRONG_DATE':
      return `⚠️ DATE MISMATCH: Airtable shows ${formatArizonaDate(data.airtableValue)} but HCP shows ${formatArizonaDate(data.hcpValue)}`;
    
    case 'WRONG_TIME':
      return `⚠️ TIME MISMATCH: Airtable shows ${formatArizonaTime(data.airtableValue)} but HCP shows ${formatArizonaTime(data.hcpValue)}`;
    
    case 'JOB_CANCELED':
      return `❌ Job was canceled on ${formatArizonaDateTime(data.canceledAt)}`;
    
    case 'SCHEDULE_UPDATED':
      return `✅ Schedule updated successfully. HCP now shows ${formatArizonaDateTime(data.newValue)}`;
    
    case 'SCHEDULE_UPDATE_FAILED':
      return `❌ Failed to update schedule: ${data.error}`;
    
    case 'NO_JOB':
      return `⚠️ No HCP job exists for this reservation`;
    
    case 'NO_APPOINTMENT':
      return `⚠️ HCP job exists but has no appointment scheduled`;
    
    case 'WEBHOOK_UPDATE':
      return `🔄 Updated from HCP webhook at ${formatArizonaDateTime(data.timestamp)} - ${data.details || 'Status change'}`;
    
    case 'WEBHOOK_ERROR':
      return `❌ Webhook processing error at ${formatArizonaDateTime(data.timestamp)}: ${data.error}`;
    
    case 'MANUAL_SYNC':
      return `🔄 Manual sync initiated at ${formatArizonaDateTime(data.timestamp)}`;
    
    case 'AUTO_SYNC':
      return `🔄 Automated sync at ${formatArizonaDateTime(data.timestamp)}`;
    
    default:
      return `Status: ${status} - ${JSON.stringify(data)}`;
  }
}

// Export for CommonJS
module.exports = {
  buildSyncMessage,
  formatArizonaDate,
  formatArizonaTime,
  formatArizonaDateTime
};