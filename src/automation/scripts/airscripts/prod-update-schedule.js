/* ────────────────────────────── CONSTANTS ────────────────────────── */
const HCP_TOKEN = (await base
  .getTable("Secrets")
  .selectRecordsAsync())
  .records.find(r => r.getCellValue("KeyName") === "hcpprod")
  ?.getCellValue("KeyValue");

if (!HCP_TOKEN) {
  output.text("❌ Error: Could not find HCP token in Secrets table (KeyName: 'hcpprod')");
  return;
}

// Get the selected record from the Reservations table
let reservationsTable = base.getTable("Reservations");
output.text("Running schedule update (PRODUCTION)...");
let currentRecord = await input.recordAsync(
  "Select a Reservation to Update Schedule",
  reservationsTable
);
if (!currentRecord) {
  output.text("No record selected. Exiting.");
  return;
}
output.text("Updating schedule for record ID: " + currentRecord.id);

// Get the Final Service Time
let finalServiceTimeVal = currentRecord.getCellValue("Final Service Time");
if (!finalServiceTimeVal) {
  output.text("No Final Service Time found. Exiting.");
  return;
}
let finalServiceTime = new Date(finalServiceTimeVal);
output.text("Final Service Time: " + finalServiceTime.toString());

// Get the Service Job ID and see if job exists
let ServiceJobId = currentRecord.getCellValueAsString("Service Job ID");
if (!ServiceJobId) {
  output.text("No Service Job ID found.");
  try {
    await reservationsTable.updateRecordAsync(currentRecord.id, {
      "Sync Status": { name: "Not Created" },
      "Sync Details": "No Service Job Created",
      "Sync Date and Time": new Date().toISOString()
    });
  } catch (statusError) {
    output.text("⚠️ Could not set Sync Status - updating details only");
    await reservationsTable.updateRecordAsync(currentRecord.id, {
      "Sync Details": "No Service Job Created",
      "Sync Date and Time": new Date().toISOString()
    });
  }
  output.text("Updated record: No Service Job Created");
  return;
}

// Get Same-day Turnover for prefix
let sameDayTurnover = currentRecord.getCellValue("Same-day Turnover");
let prefix = sameDayTurnover ? "Same-day Turnaround. " : "";

// Format expected Service time
let expectedDateStr = finalServiceTime.toLocaleDateString("en-US", {
  month: "long",
  day: "numeric"
});
let expectedTimeStr = finalServiceTime.toLocaleTimeString("en-US", {
  hour: "numeric",
  minute: "2-digit",
  hour12: true
});

// HCP API helper
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
    throw new Error(`HCP API Error: ${response.status} - ${errText}`);
  }
  return await response.json();
}

try {
  // Fetch job details
  let jobDetails = await hcpFetch(`/jobs/${ServiceJobId}`, "GET");
  output.text(`Job work_status: ${jobDetails.work_status}`);
  
  let scheduledStart = null;
  let needsScheduleCreation = false;
  
  // Check if job has a schedule
  if (!jobDetails.schedule.scheduled_start) {
    output.text("❌ No schedule found in HCP. Creating schedule from Final Service Time...");
    needsScheduleCreation = true;
    
    // Create schedule using Final Service Time
    let endTime = new Date(finalServiceTime);
    endTime.setHours(finalServiceTime.getHours() + 1); // 1 hour duration
    
    let schedulePayload = {
      start_time: finalServiceTime.toISOString(),
      end_time: endTime.toISOString(),
      arrival_window_in_minutes: 60,
      notify: true,
      notify_pro: true,
      dispatched_employees: [
        {
          employee_id: "pro_4f14466de24748bbbeba8ad6fec02800" // Your default employee
        }
      ]
    };
    
    output.text("Creating schedule with payload:");
    output.inspect(schedulePayload);
    
    // Create the schedule in HCP
    let scheduleResponse = await hcpFetch(`/jobs/${ServiceJobId}/schedule`, "PUT", schedulePayload);
    output.text("✅ Schedule created successfully in PRODUCTION!");
    output.text("HCP Response:");
    output.inspect(scheduleResponse);
    
    // Handle different response formats
    let startTimeValue = scheduleResponse.start_time || scheduleResponse.scheduled_start;
    if (!startTimeValue) {
      output.text("⚠️ No start_time in response, using our sent time");
      scheduledStart = finalServiceTime;
    } else {
      scheduledStart = new Date(startTimeValue);
      if (isNaN(scheduledStart)) {
        output.text("⚠️ Invalid date from HCP, using our sent time");
        scheduledStart = finalServiceTime;
      }
    }
    
  } else {
    scheduledStart = new Date(jobDetails.schedule.scheduled_start);
    output.text(`✅ Existing schedule found: ${scheduledStart}`);
  }

  // Write back the Scheduled Service Time to Airtable
  await reservationsTable.updateRecordAsync(currentRecord.id, {
    "Scheduled Service Time": scheduledStart.toISOString()
  });

  // Format HCP schedule for comparison
  let jobDateStr = scheduledStart.toDateString();
  let expectedDateOnly = finalServiceTime.toDateString();

  let syncStatus, syncDetails;
  let needsUpdate = false;

  if (needsScheduleCreation) {
    // We just created the schedule, so it should match
    syncStatus = "Synced";
    syncDetails = `${prefix}Schedule created in HCP for ${expectedDateStr} at ${expectedTimeStr}.`;
    
  } else if (jobDateStr !== expectedDateOnly) {
    // Date mismatch - update needed
    let jobFriendlyDate = scheduledStart.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric"
    });
    let jobFriendlyTime = scheduledStart.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true
    });
    syncStatus = "Wrong Date";
    syncDetails = `${prefix}Final Service Time is ${expectedDateStr} at ${expectedTimeStr} but Service Date is ${jobFriendlyDate}.`;
    needsUpdate = true;

  } else if (
    finalServiceTime.getHours() !== scheduledStart.getHours() ||
    finalServiceTime.getMinutes() !== scheduledStart.getMinutes()
  ) {
    // Time mismatch - update needed
    let jobFriendlyTime = scheduledStart.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true
    });
    syncStatus = "Wrong Time";
    syncDetails = `${prefix}Final Service Time is ${expectedDateStr} at ${expectedTimeStr} but Service Time is ${jobFriendlyTime}.`;
    needsUpdate = true;

  } else {
    // Perfect match
    syncStatus = "Synced";
    syncDetails = `${prefix}Final Service Time matches the Service schedule (${expectedDateStr} at ${expectedTimeStr}).`;
  }

  // If we need to update existing schedule
  if (needsUpdate) {
    output.text(`${syncStatus} detected. Updating HCP schedule in PRODUCTION...`);
    
    let endTime = new Date(finalServiceTime);
    endTime.setHours(finalServiceTime.getHours() + 1);

    let updatePayload = {
      start_time: finalServiceTime.toISOString(),
      end_time: endTime.toISOString(),
      arrival_window_in_minutes: 60,
      notify: true,
      notify_pro: true,
      dispatched_employees: [
        {
          employee_id: "pro_4f14466de24748bbbeba8ad6fec02800"
        }
      ]
    };
    
    output.inspect(updatePayload);
    await hcpFetch(`/jobs/${ServiceJobId}/schedule`, "PUT", updatePayload);
    output.text("✅ Schedule updated in HCP (PRODUCTION).");

    // Update Airtable with new schedule
    await reservationsTable.updateRecordAsync(currentRecord.id, {
      "Scheduled Service Time": finalServiceTime.toISOString()
    });
    
    syncStatus = "Synced";
    syncDetails = `${prefix}Service schedule updated to ${expectedDateStr} at ${expectedTimeStr}.`;
  }

  // Finally, write back sync status
  try {
    await reservationsTable.updateRecordAsync(currentRecord.id, {
      "Sync Status": { name: syncStatus },
      "Sync Details": syncDetails,
      "Sync Date and Time": new Date().toISOString()
    });
  } catch (statusError) {
    output.text(`⚠️ Could not set Sync Status to '${syncStatus}' - field may not have this option`);
    output.text("Available Sync Status options:");
    let field = reservationsTable.getField("Sync Status");
    if (field.options && field.options.choices) {
      field.options.choices.forEach(choice => output.text(`- ${choice.name}`));
    }
    
    // Update without Sync Status
    await reservationsTable.updateRecordAsync(currentRecord.id, {
      "Sync Details": syncDetails,
      "Sync Date and Time": new Date().toISOString()
    });
  }

  output.text(`✅ Sync complete: ${syncStatus} (PRODUCTION)`);
  output.text(syncDetails);

} catch (err) {
  output.text("❌ Error: " + err.message);
  await reservationsTable.updateRecordAsync(currentRecord.id, {
    "Sync Status": { name: "Error" },
    "Sync Details": err.message,
    "Sync Date and Time": new Date().toISOString()
  });
}

output.text("Schedule update finished (PRODUCTION).");