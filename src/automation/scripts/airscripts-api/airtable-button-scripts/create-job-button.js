/**
 * Simplified Airtable Button Script - Create HCP Job
 * This replaces the complex createjob.js AirScript
 * 
 * All business logic is now on the API server
 * This script just makes the API call
 */

// Configuration - Update with your actual values
const API_URL = 'http://localhost:3002/api/jobs/create'; // Update with your actual URL
const API_KEY = 'your-api-key-here'; // Use your actual API key

// Get the selected record
const table = base.getTable('Reservations');
const record = await input.recordAsync('Select a reservation:', table);

if (!record) {
  output.text('No record selected');
  return;
}

output.markdown(`## 🔄 Creating HCP Job...`);

try {
  // Make API call to create job
  const response = await remoteFetchAsync(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      recordId: record.id
    })
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.error || 'Failed to create job');
  }

  // Display success message
  output.markdown(`
### ✅ Job Created Successfully!

- **Job ID**: ${result.jobId}
- **Service Line**: ${result.serviceLine}
- **Scheduled Time**: ${new Date(result.scheduledTime).toLocaleString()}
- **Status**: ${result.status}

${result.appointmentId ? `- **Appointment ID**: ${result.appointmentId}` : ''}
  `);

} catch (error) {
  output.markdown(`### ❌ Error: ${error.message}`);
}