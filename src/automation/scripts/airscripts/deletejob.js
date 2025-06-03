// Airtable Scripting: Delete HCP Job Schedule for one Reservation
// ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
// 1) Load your HCP token as a script input
const HCP_TOKEN = (await base.getTable("Secrets").selectRecordsAsync()).records.find(r => r.getCellValue("KeyName") === "hcpdev")?.getCellValue("KeyValue");
 
/***********************************
 * 1. Select record
 ***********************************/
let reservationsTable = base.getTable("Reservations");
let record = await input.recordAsync("Select reservation to clear its HCP schedule", reservationsTable);
if (!record) {
  output.text("No record selected. Exiting.");
  return;
}

let jobId = record.getCellValueAsString("Service Job ID");
if (!jobId) {
  output.text(`Record ${record.id} has no Service Job ID. Exiting.`);
  return;
}

output.text(`Deleting schedule for HCP job ${jobId}…`);

/***********************************
 * 2. Call HCP DELETE /jobs/{job_id}/schedule
 ***********************************/
// Replace with your real token
let resp = await remoteFetchAsync(
  `https://api.housecallpro.com/jobs/${jobId}/schedule`,
  {
    method: "DELETE",
    headers: {
      "Accept": "application/json",
      "Authorization": `Token ${HCP_TOKEN}`,
    },
  }
);

if (!resp.ok) {
  let body = await resp.text();
  output.markdown(`❌ Failed to delete schedule (HTTP ${resp.status}):\n\`\`\`\n${body}\n\`\`\``);
  return;
}

let data = await resp.json();
output.text(`✅ HCP responded: ${data.deleted ? "schedule deleted" : "nothing to delete"}`);

/***********************************
 * 3. Update Airtable fields
 ***********************************/
let updates = {
  // clear out your schedule field
  "Scheduled Service Time": null,
  // mark that you deleted it
  "Sync Status": { name: "Not Created" },
  "Service Type": { name: "Canceled" },
  "Service Job ID": null,
  "Job Status" : { name: "Canceled"},
  "Sync Details": `HCP schedule erased on ${new Date().toLocaleString()}`,
  "Sync Date and Time": new Date().toISOString(),
};

await reservationsTable.updateRecordAsync(record.id, updates);
output.text("✅ Airtable record updated.");
