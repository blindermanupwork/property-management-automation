/**
 * Unified timestamp utilities for consistent date/time formatting across the system.
 * 
 * This module provides a single source of truth for timestamp generation to fix
 * inconsistencies between webhook, CSV processing, and HCP sync timestamps.
 * 
 * Standard format: ISO 8601 with seconds precision and proper timezone
 * Example: 2025-06-11T23:42:05-07:00
 */

/**
 * Get current timestamp in Arizona timezone with consistent formatting.
 * 
 * Note: This implementation correctly uses timezone-aware dates instead of
 * manually adjusting UTC time.
 * 
 * @returns {string} ISO 8601 formatted timestamp with proper timezone
 *                   Example: "2025-06-11T23:42:05-07:00"
 */
function getArizonaTimestamp() {
  // Create a date in Arizona timezone (MST, UTC-7, no DST)
  const now = new Date();
  
  // Format with Intl.DateTimeFormat for proper timezone handling
  const options = {
    timeZone: 'America/Phoenix',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  };
  
  const formatter = new Intl.DateTimeFormat('en-US', options);
  const parts = formatter.formatToParts(now);
  
  // Build ISO format from parts
  const dateParts = {};
  parts.forEach(part => {
    dateParts[part.type] = part.value;
  });
  
  // Construct ISO string with Arizona timezone offset (-07:00)
  const isoString = `${dateParts.year}-${dateParts.month}-${dateParts.day}T${dateParts.hour}:${dateParts.minute}:${dateParts.second}-07:00`;
  
  return isoString;
}

/**
 * Get current timestamp with space separator (for backward compatibility).
 * 
 * @returns {string} Timestamp with space separator
 *                   Example: "2025-06-11 23:42:05-07:00"
 */
function getArizonaTimestampSpace() {
  return getArizonaTimestamp().replace('T', ' ');
}

/**
 * DEPRECATED: Old function that incorrectly shows UTC timezone.
 * Kept for reference - DO NOT USE in new code.
 * 
 * @deprecated Use getArizonaTimestamp() instead
 */
function getArizonaTimeOld() {
  const now = new Date();
  // This is WRONG - it adjusts the time but shows 'Z' (UTC) suffix
  const arizonaTime = new Date(now.getTime() - (7 * 60 * 60 * 1000));
  return arizonaTime.toISOString();
}

/**
 * Parse an ISO timestamp string and return a Date object
 * 
 * @param {string} timestamp - ISO timestamp string
 * @returns {Date} Date object
 */
function parseTimestamp(timestamp) {
  return new Date(timestamp);
}

/**
 * Format a Date object to Arizona timezone ISO string
 * 
 * @param {Date} date - Date object to format
 * @returns {string} ISO 8601 formatted timestamp
 */
function formatDateToArizona(date) {
  const options = {
    timeZone: 'America/Phoenix',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  };
  
  const formatter = new Intl.DateTimeFormat('en-US', options);
  const parts = formatter.formatToParts(date);
  
  const dateParts = {};
  parts.forEach(part => {
    dateParts[part.type] = part.value;
  });
  
  return `${dateParts.year}-${dateParts.month}-${dateParts.day}T${dateParts.hour}:${dateParts.minute}:${dateParts.second}-07:00`;
}

// Export functions for use in other modules
module.exports = {
  getArizonaTimestamp,
  getArizonaTimestampSpace,
  parseTimestamp,
  formatDateToArizona,
  // Deprecated - do not use
  getArizonaTimeOld
};

// Test the functions if run directly
if (require.main === module) {
  console.log('Timestamp Utils Test:');
  console.log(`Standard format: ${getArizonaTimestamp()}`);
  console.log(`Space format:    ${getArizonaTimestampSpace()}`);
  console.log(`Old format (WRONG): ${getArizonaTimeOld()}`);
  
  console.log('\nParsing test:');
  const testTimestamp = '2025-06-11T23:42:05-07:00';
  const parsed = parseTimestamp(testTimestamp);
  console.log(`  ${testTimestamp} -> ${parsed}`);
  console.log(`  Reformatted: ${formatDateToArizona(parsed)}`);
}