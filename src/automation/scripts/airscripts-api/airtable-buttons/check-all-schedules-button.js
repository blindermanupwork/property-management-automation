/**
 * Airtable Button Script: Check All Schedules
 * This simplified script replaces the complex checkallschedules.js script
 * It calls the external API to handle all the business logic
 */

// Configuration - Store these in Airtable Secrets table
const API_ENDPOINT = 'https://your-domain.com/api/airscripts/check-schedules';
const API_KEY_SECRET = await base
  .getTable("Secrets")
  .selectRecordsAsync()
  .then(result => 
    result.records.find(r => r.getCellValue("KeyName") === "airscripts_check_schedules_key")
      ?.getCellValue("KeyValue")
  );

if (!API_KEY_SECRET) {
  output.text('❌ API key not found in Secrets table');
  return;
}

output.markdown("## 📅 Check All Service Schedules");
output.text("This will check and sync all active reservations with HousecallPro.");

// Optional: Show count of records to be checked
const reservationsTable = base.getTable("Reservations");
const query = await reservationsTable.selectRecordsAsync({
  fields: ["Service Job ID", "Status"],
  recordIds: [] // Empty to get all records
});

const activeRecords = query.records.filter(record => {
  const jobId = record.getCellValue("Service Job ID");
  const status = record.getCellValue("Status");
  return jobId && status && (status.name === "New" || status.name === "Modified");
});

output.text(`Found ${activeRecords.length} active reservations with Service Job IDs to check.`);

if (activeRecords.length === 0) {
  output.text("No active reservations to check. Exiting.");
  return;
}

// Confirm before proceeding
const proceed = await input.buttonsAsync(
  `Check ${activeRecords.length} reservations?`,
  [
    {label: 'Check All', variant: 'primary'},
    {label: 'Cancel', variant: 'secondary'}
  ]
);

if (proceed === 'Cancel') {
  output.text("Operation cancelled.");
  return;
}

output.text("🔄 Checking schedules...");
output.text("This may take a few minutes for large batches.");

try {
  // Call the API
  const response = await remoteFetchAsync(API_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY_SECRET
    },
    body: JSON.stringify({
      baseId: base.id,
      viewName: 'HCP Create Jobs' // Optional: specify a view to limit records
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText}`);
  }

  const result = await response.json();
  
  if (result.success) {
    output.markdown(`## ✅ Schedule Check Complete!`);
    
    // Display summary
    output.markdown(`
### Summary:
- **Total Checked**: ${result.summary.total}
- **Synced**: ${result.summary.synced} ✅
- **Wrong Date**: ${result.summary.wrongDate} 📅
- **Wrong Time**: ${result.summary.wrongTime} ⏰
- **Not Created**: ${result.summary.notCreated} ❌
- **Errors**: ${result.summary.errors} ⚠️
    `);
    
    // Show details if there are issues
    if (result.issues && result.issues.length > 0) {
      output.markdown("### Issues Found:");
      result.issues.forEach(issue => {
        output.text(`${issue.reservationUID}: ${issue.status} - ${issue.details}`);
      });
    }
    
    output.text(`\nCompleted at: ${new Date().toLocaleString()}`);
    
  } else {
    output.text(`❌ Error: ${result.error}`);
    if (result.details) {
      output.text(`Details: ${JSON.stringify(result.details, null, 2)}`);
    }
  }

} catch (error) {
  output.markdown(`## ❌ Failed to check schedules`);
  output.text(`Error: ${error.message}`);
  
  // For timeout errors (Airtable scripts have 30-second limit)
  if (error.message.includes('timeout')) {
    output.text(`
⚠️ The operation timed out. This can happen with large batches.

Suggestions:
1. Try checking schedules in smaller batches using a filtered view
2. Run the check during off-peak hours
3. Contact support if the issue persists
    `);
  } else {
    output.text(`
Troubleshooting:
1. Check if the API service is running
2. Verify the API endpoint URL is correct
3. Ensure the API key is valid
4. Try checking a smaller batch of records
    `);
  }
}