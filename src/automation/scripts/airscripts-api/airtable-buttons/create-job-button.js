/**
 * Airtable Button Script: Create Job
 * This simplified script replaces the complex createjob.js script
 * It calls the external API to handle all the business logic
 */

// Configuration - Store these in Airtable Secrets table
const API_ENDPOINT = 'https://your-domain.com/api/airscripts/create-job';
const API_KEY_SECRET = await base
  .getTable("Secrets")
  .selectRecordsAsync()
  .then(result => 
    result.records.find(r => r.getCellValue("KeyName") === "airscripts_create_job_key")
      ?.getCellValue("KeyValue")
  );

if (!API_KEY_SECRET) {
  output.text('❌ API key not found in Secrets table');
  return;
}

// Get the Reservations table
const reservationsTable = base.getTable("Reservations");

// Prompt user to select a reservation
output.markdown("## 🔎 Select a reservation to create HCP job");
const record = await input.recordAsync("Select Reservation:", reservationsTable);

if (!record) {
  output.text("No record selected – exiting.");
  return;
}

// Display reservation details
const reservationUID = record.getCellValue("Reservation UID");
const finalServiceTime = record.getCellValue("Final Service Time");
const existingJobId = record.getCellValue("Service Job ID");

output.markdown(`### Selected Reservation: ${reservationUID}`);

if (existingJobId) {
  output.text(`⚠️ This reservation already has a job ID: ${existingJobId}`);
  const proceed = await input.buttonsAsync(
    'Do you want to check the job status instead?',
    [
      {label: 'Check Status', variant: 'primary'},
      {label: 'Cancel', variant: 'secondary'}
    ]
  );
  
  if (proceed === 'Cancel') {
    return;
  }
}

if (!finalServiceTime) {
  output.text("❌ No Final Service Time set for this reservation");
  return;
}

output.text(`📅 Final Service Time: ${new Date(finalServiceTime).toLocaleString()}`);
output.text("🔄 Creating HCP job...");

try {
  // Call the API
  const response = await remoteFetchAsync(API_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY_SECRET
    },
    body: JSON.stringify({
      recordId: record.id,
      baseId: base.id
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText}`);
  }

  const result = await response.json();
  
  if (result.success) {
    output.markdown(`## ✅ Success!`);
    output.text(`Job ID: **${result.jobId}**`);
    if (result.appointmentId) {
      output.text(`Appointment ID: **${result.appointmentId}**`);
    }
    output.text(`Message: ${result.message}`);
    
    // The API already updated the Airtable record, so just show confirmation
    output.markdown(`
### Next Steps:
1. The job has been created in HousecallPro
2. The Airtable record has been updated with the job details
3. You can now use the "Check Schedule" button to verify the sync status
    `);
  } else {
    output.text(`❌ Error: ${result.error}`);
    if (result.details) {
      output.text(`Details: ${JSON.stringify(result.details, null, 2)}`);
    }
  }

} catch (error) {
  output.markdown(`## ❌ Failed to create job`);
  output.text(`Error: ${error.message}`);
  output.text(`
Troubleshooting:
1. Check if the API service is running
2. Verify the API endpoint URL is correct
3. Ensure the API key is valid
4. Check the reservation has all required fields (Property ID, Final Service Time)
  `);
}