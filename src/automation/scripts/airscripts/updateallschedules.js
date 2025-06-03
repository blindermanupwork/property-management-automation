// Update All Service Schedules
// This script checks all active reservations and updates their Service schedules in HCP if needed
// 1) Load your HCP token as a script input
let HCP_TOKEN = (await base.getTable("Secrets").selectRecordsAsync()).records.find(r => r.getCellValue("KeyName") === "hcpdev")?.getCellValue("KeyValue");
 
// Get the Reservations table
let reservationsTable = base.getTable("Reservations");
output.text("Running batch update for all Service schedules...");

// Helper function for HCP API calls
async function hcpFetch(endpoint, method, body) {
  let url = "https://api.housecallpro.com" + endpoint;
  output.text(`Calling HCP: ${method} ${url}`);
  let response = await remoteFetchAsync(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "Authorization": "Token " + HCP_TOKEN
    },
    body: body ? JSON.stringify(body) : undefined
  });
  output.text(`Response status: ${response.status}`);
  if (!response.ok) {
    let errText = await response.text();
    throw new Error(errText);
  }
  return await response.json();
}

// Helper function to check and update a single record
async function checkAndUpdateRecord(record) {
  let recordId = record.id;
  output.text(`Processing record ID: ${recordId}`);
  
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
    output.text(`Job ${ServiceJobId} currently scheduled for: ${scheduledStart.toString()}`);
    
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
    
    // Determine initial sync status and details
    let syncStatus, syncDetails;
    let needsUpdate = false;
    
    if (expectedDate !== jobDate) {
      // Date mismatch
      syncStatus = "Wrong Date";
      syncDetails = `${prefix}Final Service Time is ${expectedFormattedDate} at ${expectedFormattedTime} but the Service Date is ${jobFormattedDate} at ${jobFormattedTime}. Service Date should be changed to ${expectedFormattedDate}.`;
      needsUpdate = true;
    } 
    else if (
      finalServiceTime.getHours() !== scheduledStart.getHours() || 
      finalServiceTime.getMinutes() !== scheduledStart.getMinutes()
    ) {
      // Time mismatch
      syncStatus = "Wrong Time";
      syncDetails = `${prefix}Final Service Time is ${expectedFormattedDate} at ${expectedFormattedTime} but the Service Time is ${jobFormattedTime}. Service Time should be changed to ${expectedFormattedTime}.`;
      needsUpdate = true;
    } 
    else {
      // Everything matches
      syncStatus = "Synced";
      syncDetails = `${prefix}Final Service Time is ${expectedFormattedDate} at ${expectedFormattedTime} and matches the Service Date and Time.`;
    }
    
    // If an update is needed, do it before setting the final status
    if (needsUpdate) {
      output.text(`${syncStatus} detected for record ${recordId}. Updating job schedule...`);
      
      try {
        // First get the appointment ID
        let appointmentsResp = await hcpFetch(`/jobs/${ServiceJobId}/appointments`, "GET");
        
        if (!appointmentsResp.appointments || appointmentsResp.appointments.length === 0) {
          output.text(`No appointments found for job ${ServiceJobId}. Cannot update schedule.`);
        } else {
          // For simplicity, use the first appointment
          let appointment = appointmentsResp.appointments[0];
          output.text(`Found appointment ID: ${appointment.id}`);
          
          // Prepare ISO format dates for the API
          let isoStart = finalServiceTime.toISOString();
          let isoEnd = new Date(finalServiceTime);
          isoEnd.setHours(finalServiceTime.getHours() + 1);
          let isoEndStr = isoEnd.toISOString();
          
          // Update the appointment
          let updatePayload = {
            start_time: isoStart,
            end_time: isoEndStr,
            arrival_window_minutes: 60,
            dispatched_employees_ids: ["pro_4f14466de24748bbbeba8ad6fec02800"]
          };
          
          output.text(`Updating appointment ${appointment.id} with new schedule`);
          
          let updateResponse = await hcpFetch(`/jobs/${ServiceJobId}/appointments/${appointment.id}`, "PUT", updatePayload);
          
          // Update the Scheduled Service Time in Airtable to the new time
          await reservationsTable.updateRecordAsync(record, {
            "Scheduled Service Time": finalServiceTime.toISOString()
          });
          
          // After successful update, change status to Synced
          syncStatus = "Synced";
          syncDetails = `${prefix}Service schedule has been updated to match Final Service Time: ${expectedFormattedDate} at ${expectedFormattedTime}.`;
        }
      } catch (updateErr) {
        output.text(`Error updating appointment for record ${recordId}: ${updateErr.message}`);
        // Keep the original status and details since the update failed
      }
    }
    
    // Now update the sync status, whether it was updated or not
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
async function updateAllSchedules() {
  // Query for all active records with Service Job IDs
  const query = await reservationsTable.selectRecordsAsync({
    filterByFormula: 'AND(Service Job ID != "", OR(Status = "New", Status = "Modified"))'
  });
  
  const records = query.records;
  output.text(`Found ${records.length} active records with Service Job IDs`);
  
  // Process records with a small delay between each to avoid rate limiting
  for (let i = 0; i < records.length; i++) {
    const record = records[i];
    output.text(`Processing record ${i+1} of ${records.length}`);
    
    await checkAndUpdateRecord(record);
    
    // Add a small delay between requests to prevent overwhelming the API
    if (i < records.length - 1) {
      output.text("Waiting 1 second before processing next record...");
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  
  output.text("Batch update complete!");
}

// Run the main function
await updateAllSchedules();