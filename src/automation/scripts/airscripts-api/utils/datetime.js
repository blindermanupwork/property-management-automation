/**
 * Date/time utility functions
 * Handles Arizona timezone for business operations
 */

// Get current time in UTC (for Airtable which expects UTC timestamps)
function getArizonaTime() {
  // Return UTC time as Airtable expects UTC timestamps
  return new Date().toISOString();
}

// Format date like "January 15"
function formatDate(dateString) {
  const date = new Date(dateString);
  const month = date.toLocaleString('en-US', { month: 'long' });
  const day = date.getDate();
  return `${month} ${day}`;
}

// Format time like "10:00 AM"
function formatTime(date) {
  return date.toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit', 
    hour12: true 
  });
}

// Parse date string safely
function parseDate(dateString) {
  if (typeof dateString === 'string') {
    const parts = dateString.split('T')[0].split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0]);
      const month = parseInt(parts[1]) - 1;
      const day = parseInt(parts[2]);
      return new Date(year, month, day, 12, 0, 0);
    }
  }
  return new Date(dateString);
}

module.exports = {
  getArizonaTime,
  formatDate,
  formatTime,
  parseDate
};