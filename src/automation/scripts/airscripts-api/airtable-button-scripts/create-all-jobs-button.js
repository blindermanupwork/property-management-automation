/**
 * Simplified Airtable Button Script - Create All Jobs
 * This replaces the complex createalljobs.js AirScript
 * 
 * Batch creates HCP jobs for all eligible records
 */

// Configuration - Update with your actual values
const API_URL = 'http://localhost:3002/api/jobs/create-batch';
const API_KEY = 'your-api-key-here';

// Get eligible records from the view
const table = base.getTable('Reservations');
const view = table.getView('HCP Create Jobs'); // Your view that filters eligible records

output.markdown(`## 🔄 Fetching eligible reservations...`);

const queryResult = await view.selectRecordsAsync({
  fields: ['Reservation UID', 'Property ID', 'Check-in Date', 'Service Job ID']
});

// Filter records without existing jobs
const recordsToProcess = queryResult.records.filter(record => 
  !record.getCellValue('Service Job ID')
);

if (recordsToProcess.length === 0) {
  output.text('No reservations need job creation');
  return;
}

output.markdown(`### Found ${recordsToProcess.length} reservations to process`);

// Show confirmation
const shouldProceed = await input.buttonsAsync(
  `Create ${recordsToProcess.length} jobs?`,
  [
    { label: 'Yes, create jobs', variant: 'primary' },
    { label: 'Cancel', variant: 'secondary' }
  ]
);

if (shouldProceed === 'Cancel') {
  output.text('Cancelled');
  return;
}

output.markdown(`### 🚀 Creating jobs...`);

try {
  // Make batch API call
  const response = await remoteFetchAsync(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      recordIds: recordsToProcess.map(r => r.id)
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Failed to create jobs');
  }

  // Process results
  const results = data.results;
  const successful = results.filter(r => !r.error).length;
  const failed = results.filter(r => r.error).length;

  output.markdown(`
### ✅ Batch Job Creation Complete!

- **Total Processed**: ${results.length}
- **Successful**: ${successful}
- **Failed**: ${failed}
  `);

  // Show failures if any
  if (failed > 0) {
    output.markdown(`### ❌ Failed Records:`);
    results.filter(r => r.error).forEach(r => {
      output.markdown(`- Record ${r.recordId}: ${r.error}`);
    });
  }

} catch (error) {
  output.markdown(`### ❌ Error: ${error.message}`);
}