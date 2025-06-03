// Check All Service Schedules
// This script checks all active reservations and updates their sync status without making any changes to HCP
// 1) Load your HCP token as a script input
let HCP_TOKEN = (await base.getTable("Secrets").selectRecordsAsync()).records.find(r => r.getCellValue("KeyName") === "hcpdev")?.getCellValue("KeyValue");
 
// Get the Reservations table
let reservationsTable = base.getTable("Reservations");
output.text("Running batch check for all Service schedules...");

// Helper function for HCP API calls
async function hcpFetch(endpoint, method) {
  let url = "https://api.housecallpro.com" + endpoint;
  output.text(`Calling HCP: ${method} ${url}`);
  let response = await remoteFetchAsync(url, {
    method,
    headers: {
      "Accept": "application/json",
      "Authorization": "Token " + HCP_TOKEN,
    }
  });
  output.text(`Response status: ${response.status}`);
  if (!response.ok) {
    let errText = await response.text();
    throw new Error(errText);
  }
  return await response.json();
}

// Helper function to check a single record
async function checkRecord(record) {
  let recordId = record.id;
  output.text(`Checking record ID: ${recordId}`);
  
  // Get the Final Service Time - this is what we should be using for comparison
  let finalServiceTimeVal = record.getCellValue("Final Service Time");
  if (!finalServiceTimeVal) {
    output.text(`No Final Service Time found for record ${recordId}. Skipping.`);
    return;
  }
  let finalServiceTime = new Date(finalServiceTimeVal);
  
  // Get the Service Job ID and see if job exists
  let ServiceJobId = record.getCellValueAsString("Service Job ID");
  if (!ServiceJobId) {
    output.text(`No Service Job ID found for record ${recordId}.`);
    await reservationsTable.updateRecordAsync(record, {
      "Sync Status": {name: "Not Created"},
      "Sync Details": "No Service Job Created",
      "Sync Date and Time": new Date().toISOString()
    });
    return;
  }
  
  // Get Same-day Turnover value for the prefix in the message
  let sameDayTurnover = record.getCellValue("Same-day Turnover");
  let prefix = sameDayTurnover ? "Same-day Turnaround. " : "";
  
  // Format the expected Service time for display
  let expectedFormattedDate = finalServiceTime.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric"
  });
  let expectedFormattedTime = finalServiceTime.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true
  });
  
  try {
    // Get the job details from HCP
    let jobDetails = await hcpFetch(`/jobs/${ServiceJobId}`, "GET");
    let scheduledStart = new Date(jobDetails.schedule.scheduled_start);
    output.text(`Job ${ServiceJobId} scheduled for: ${scheduledStart.toString()}`);
    
    // Update the Scheduled Service Time in Airtable
    await reservationsTable.updateRecordAsync(record, {
      "Scheduled Service Time": scheduledStart.toISOString()
    });
    
    // Format actual job schedule for display
    let jobFormattedDate = scheduledStart.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric"
    });
    let jobFormattedTime = scheduledStart.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true
    });
    
    // Compare dates and times
    let expectedDate = finalServiceTime.toDateString();
    let jobDate = scheduledStart.toDateString();
    
    // Determine sync status and details
    let syncStatus, syncDetails;
    
    if (expectedDate !== jobDate) {
      // Date mismatch
      syncStatus = "Wrong Date";
      syncDetails = `${prefix}Final Service Time is ${expectedFormattedDate} at ${expectedFormattedTime} but the Service Date is ${jobFormattedDate} at ${jobFormattedTime}. Service Date should be changed to ${expectedFormattedDate}.`;
    } 
    else if (
      finalServiceTime.getHours() !== scheduledStart.getHours() || 
      finalServiceTime.getMinutes() !== scheduledStart.getMinutes()
    ) {
      // Time mismatch
      syncStatus = "Wrong Time";
      syncDetails = `${prefix}Final Service Time is ${expectedFormattedDate} at ${expectedFormattedTime} but the Service Time is ${jobFormattedTime}. Service Time should be changed to ${expectedFormattedTime}.`;
    } 
    else {
      // Everything matches
      syncStatus = "Synced";
      syncDetails = `${prefix}Final Service Time is ${expectedFormattedDate} at ${expectedFormattedTime} and matches the Service Date and Time.`;
    }
    
    // Update Sync Status, Sync Details, and record the sync time
    await reservationsTable.updateRecordAsync(record, {
      "Sync Status": {name: syncStatus},
      "Sync Details": syncDetails,
      "Sync Date and Time": new Date().toISOString()
    });
    
    output.text(`Updated record ${recordId} sync status to: ${syncStatus}`);
    
  } catch (err) {
    output.text(`Error checking job in HCP for record ${recordId}: ${err.message}`);
    await reservationsTable.updateRecordAsync(record, {
      "Sync Status": {name: "Not Created"},
      "Sync Details": `Error checking job in HCP: ${err.message}`,
      "Sync Date and Time": new Date().toISOString()
    });
  }
}

// Main execution
async function checkAllSchedules() {
  // Query for all active records with Service Job IDs
  const query = await reservationsTable.selectRecordsAsync({
    filterByFormula: 'AND(Service Job ID != "", OR(Status = "New", Status = "Modified"))'
  });
  
  const records = query.records;
  output.text(`Found ${records.length} active records with Service Job IDs`);
  
  // Counters for reporting
  let synced = 0;
  let wrongDate = 0;
  let wrongTime = 0;
  let notCreated = 0;
  let errors = 0;
  
  // Process records with a small delay between each to avoid rate limiting
  for (let i = 0; i < records.length; i++) {
    const record = records[i];
    output.text(`Checking record ${i+1} of ${records.length}`);
    
    await checkRecord(record);
    
    // Update counters based on the updated sync status
    const updatedRecord = await reservationsTable.selectRecordAsync(record.id);
    const syncStatus = updatedRecord.getCellValue("Sync Status");
    if (syncStatus) {
      const statusName = syncStatus.name;
      if (statusName === "Synced") synced++;
      else if (statusName === "Wrong Date") wrongDate++;
      else if (statusName === "Wrong Time") wrongTime++;
      else if (statusName === "Not Created") notCreated++;
      else errors++;
    }
    
    // Add a small delay between requests to prevent overwhelming the API
    if (i < records.length - 1) {
      output.text("Waiting 1 second before checking next record...");
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  // Output summary
  output.text("\n=== SUMMARY ===");
  output.text(`Total records checked: ${records.length}`);
  output.text(`Synced: ${synced}`);
  output.text(`Wrong Date: ${wrongDate}`);
  output.text(`Wrong Time: ${wrongTime}`);
  output.text(`Not Created: ${notCreated}`);
  output.text(`Errors: ${errors}`);
  output.text("Batch check complete!");
}

// Run the main function
await checkAllSchedules();