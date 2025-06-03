/**********************************************************************
 *  Airbnb Turn-over  ←→  Housecall Pro one-click automator
 *  — Creates an HCP job from a selected "Reservations" record
 *  — Copies template line-items
 *  — Writes back Service Job ID, Service Appointment ID, schedule, status & sync fields
 *  Timezone-safe (always America/Phoenix ↔ ISO-UTC for API)
 *********************************************************************/

/* ────────────────────────────── CONSTANTS ────────────────────────── */
const HCP_TOKEN = (await base
  .getTable("Secrets")
  .selectRecordsAsync())
  .records.find(r => r.getCellValue("KeyName") === "hcpdev")
  ?.getCellValue("KeyValue");

/* ────────────────────────────── CONFIG ───────────────────────────── */
const AZ_TZ       = "America/Phoenix";
const EMPLOYEE_ID = "pro_78945c979905480996c6c85d7a925eb9";

const reservationsTable = base.getTable("Reservations");
const propertiesTable   = base.getTable("Properties");

/* ─ Utility – delay ─────────────────────────────────────────────── */
const delay = ms => new Promise(r => setTimeout(r, ms));

/* ─ Helpers for AZ-local strings ───────────────────────────────── */
const azDate = d => d.toLocaleDateString("en-US", {
  timeZone: AZ_TZ, month: "long", day: "numeric"
});
const azTime = d => d.toLocaleTimeString("en-US", {
  timeZone: AZ_TZ, hour: "numeric", minute: "2-digit", hour12: true
});

/* ─ 1) pick reservation ────────────────────────────────────────── */
output.markdown("## 🔎 Select a reservation to sync");
const rec = await input.recordAsync("Reservation", reservationsTable);
if (!rec) { output.text("No record selected – exit."); return; }

/* ─ 2) Final Service Time & schedule window ──────────────────── */
const finalRaw = rec.getCellValue("Final Service Time");
if (!finalRaw) { output.text("❌ No Final Service Time – exit."); return; }
const finalTime  = new Date(finalRaw);
const schedStart = finalTime;
const schedEnd   = new Date(finalTime.getTime() + 60*60*1000);
const isoStart   = schedStart.toISOString();
const isoEnd     = schedEnd.toISOString();

/* ─ 3) pull HCP IDs from linked property ──────────────────────── */
const propLinks = rec.getCellValue("Property ID") || [];
if (!propLinks.length) { output.text("❌ No linked property – exit."); return; }
const propRec = await propertiesTable.selectRecordAsync(propLinks[0].id);

let custLinks = propRec.getCellValue("HCP Customer ID") || [];
let custId = "";
if (custLinks.length) {
  custId = (typeof custLinks[0] === "object" && custLinks[0].name)
    ? custLinks[0].name
    : custLinks[0];
}

const addrId = propRec.getCellValue("HCP Address ID");

if (!(custId && addrId)) {
  output.text("❌ Property missing HCP IDs – exit.");
  return;
}

/* ─ 4) extract other fields and normalize service type ───────── */
const entrySourceObj  = rec.getCellValue("Entry Source");
const serviceTypeObj  = rec.getCellValue("Service Type");
const reservationUID  = rec.getCellValue("Reservation UID");
const entrySource     = entrySourceObj ? entrySourceObj.name : "Airbnb";
const rawServiceType  = serviceTypeObj ? serviceTypeObj.name : "";
const sameDay         = rec.getCellValue("Same-day Turnover");

// Normalize service type - if it's not Return Laundry or Inspection, default to Turnover
let serviceType;
if (rawServiceType === "Return Laundry") {
  serviceType = "Return Laundry";
} else if (rawServiceType === "Inspection") {
  serviceType = "Inspection";
} else {
  serviceType = "Turnover";
}

/* ─ 5) choose template & job type based on normalized service type ─ */
let tmplId;
let jobTypeId;

if (serviceType === "Return Laundry") {
  tmplId = propRec.getCellValue("Return Laundry Job Template ID");
  jobTypeId = "jbt_01d29f7695404f5bb57ed7e8c5708afc";
} else if (serviceType === "Inspection") {
  tmplId = propRec.getCellValue("Inspection Job Template ID");
  jobTypeId = "jbt_7234d0af0a734f10bf155d2238cf92b7";
} else {
  // Default to Turnover for everything else
  tmplId = propRec.getCellValue("Turnover Job Template ID");
  jobTypeId = "jbt_3744a354599d4d2fa54041a4cda4bd13";
}

/* ─ 6) determine serviceName ──────────────────────────────────── */
let serviceName;
const serviceLineDescription = rec.getCellValue("Service Line Description");
const serviceLineCustomInstructions = rec.getCellValue("Service Line Custom Instructions");

if (serviceLineDescription?.trim()) {
  serviceName = serviceLineDescription.trim();
  if (serviceLineCustomInstructions?.trim()) {
    serviceName += ` - ${serviceLineCustomInstructions.trim()}`;
  }
} else if (sameDay) {
  serviceName = `${serviceType} STR SAME DAY`;
} else {
  const query = await reservationsTable.selectRecordsAsync({
    sorts: [{ field: "Check-in Date", direction: "asc" }]
  });
  const potentialNext = query.records.filter(r => {
    if (r.id === rec.id) return false;
    const pl = r.getCellValue("Property ID") || [];
    if (!pl.length || pl[0].id !== propLinks[0].id) return false;
    const et = r.getCellValue("Entry Type")?.name;
    if (et !== "Reservation") return false;
    const st = r.getCellValue("Status")?.name;
    if (st === "Old") return false;
    const ci = r.getCellValue("Check-in Date");
    if (!ci || new Date(ci) <= new Date(rec.getCellValue("Check-out Date"))) return false;
    return true;
  });
  const next = potentialNext[0];
  if (next) {
    const [y,m,d] = next.getCellValue("Check-in Date").split("-").map(Number);
    const dt = new Date(y, m-1, d);
    const mon = dt.toLocaleString("en-US",{month:"long"});
    serviceName = `${serviceType} STR Next Guest ${mon} ${dt.getDate()}`;
  } else {
    serviceName = `${serviceType} STR Next Guest Unknown`;
  }
}

/* ─ 7) hcp helper (minimal, read body once, proper JSON parse) ─── */
async function hcp(path, method="GET", body=null) {
  const maxRetries = 3;
  let retry = 0;
  while (true) {
    const res = await remoteFetchAsync(
      "https://api.housecallpro.com" + path,
      {
        method,
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "Authorization": "Token " + HCP_TOKEN
        },
        body: body ? JSON.stringify(body) : undefined
      }
    );
    const raw = await res.text();
    if (res.status === 429 && retry < maxRetries) {
      retry++;
      const reset = res.headers.get("RateLimit-Reset");
      const wait = reset
        ? Math.max(new Date(reset) - new Date(), 1000)
        : 1000 * (2 ** retry);
      await delay(wait);
      continue;
    }
    if (!res.ok) {
      throw new Error(`${res.status}: ${raw}`);
    }
    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  }
}

/* ─ 8) create or reuse job ─────────────────────────────────────── */
let jobId = rec.getCellValueAsString("Service Job ID");
let appointmentId = rec.getCellValueAsString("Service Appointment ID");

if (!jobId) {
  const job = await hcp("/jobs", "POST", {
    invoice_number: 0,
    customer_id:    custId,
    address_id:     addrId,
    schedule:       { scheduled_start: isoStart, scheduled_end: isoEnd, arrival_window: 0 },
    assigned_employee_ids: [EMPLOYEE_ID],
    line_items:     [],
    job_fields:     { job_type_id: jobTypeId }
  });
  jobId = job.id;
  
  // NEW: Capture appointment ID after job creation
  await delay(700); // Give HCP time to create the appointment
  
  try {
    // Try to get appointment from the job details first
    const jobDetails = await hcp(`/jobs/${jobId}`);
    
    if (jobDetails.appointments && jobDetails.appointments.length > 0) {
      appointmentId = jobDetails.appointments[0].id;
      output.text(`📅 Found appointment ID in job details: ${appointmentId}`);
    } else {
      // Try fetching appointments separately
      output.text(`📅 No appointments in job details, fetching separately...`);
      await delay(500);
      const appointmentsResponse = await hcp(`/jobs/${jobId}/appointments`);
      
      if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
        appointmentId = appointmentsResponse.appointments[0].id;
        output.text(`📅 Found appointment ID via separate fetch: ${appointmentId}`);
      } else {
        output.text(`⚠ No appointment found for job ${jobId}`);
      }
    }
  } catch (error) {
    output.text(`⚠ Failed to fetch appointment ID: ${error.message}`);
  }
  
  // Update record with job ID and appointment ID (if found)
  const initialUpdatePayload = {
    "Service Job ID": jobId,
    "Job Creation Time": new Date().toISOString()
  };
  
  if (appointmentId) {
    initialUpdatePayload["Service Appointment ID"] = appointmentId;
  }
  
  await reservationsTable.updateRecordAsync(rec.id, initialUpdatePayload);
  
  // Copy template line items
  const tmplItems = (await hcp(`/jobs/${tmplId}/line_items`)).data || [];
  await hcp(
    `/jobs/${jobId}/line_items/bulk_update`,
    "PUT",
    { line_items: tmplItems.map((it,i) => ({
        name:  i===0 ? serviceName : it.name,
        description: it.description || "",
        unit_price:  it.unit_price,
        unit_cost:   it.unit_cost,
        quantity:    it.quantity,
        kind:        it.kind,
        taxable:     it.taxable,
        service_item_id:   it.service_item_id   || null,
        service_item_type: it.service_item_type || null
    })) }
  );
  
  if (appointmentId) {
    output.text(`➕ Created job ${jobId} with appointment ${appointmentId}`);
  } else {
    output.text(`➕ Created job ${jobId} (no appointment ID found)`);
  }
}

/* ─ 9) fetch live job & sync Airtable ─────────────────────────── */
await delay(700);
const live = await hcp(`/jobs/${jobId}`);
const schedLive = new Date(live.schedule.scheduled_start);

// NEW: If we still don't have appointment ID, try to capture it during sync
if (!appointmentId) {
  output.text(`📅 Missing appointment ID, attempting to fetch during sync...`);
  
  try {
    if (live.appointments && live.appointments.length > 0) {
      appointmentId = live.appointments[0].id;
      output.text(`📅 Found appointment ID in sync job details: ${appointmentId}`);
    } else {
      // Try fetching appointments separately
      await delay(500);
      const appointmentsResponse = await hcp(`/jobs/${jobId}/appointments`);
      
      if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
        appointmentId = appointmentsResponse.appointments[0].id;
        output.text(`📅 Found appointment ID via sync separate fetch: ${appointmentId}`);
      }
    }
  } catch (error) {
    output.text(`⚠ Failed to fetch appointment ID during sync: ${error.message}`);
  }
}

function mapStatus(ws) {
  ws = (ws || "").toLowerCase();
  if (ws.includes("cancel"))      return "Canceled";
  if (ws.includes("complete"))    return "Completed";
  if (ws.includes("in_progress")) return "In Progress";
  if (ws.includes("scheduled"))   return "Scheduled";
  if (!ws || ws.includes("unscheduled")) return "Unscheduled";
  return null;
}

const atStatus = mapStatus(live.work_status);
const dateMatch = azDate(schedLive) === azDate(schedStart);
const timeMatch = azTime(schedLive) === azTime(schedStart);

let syncStatus, syncDetails;
if (!dateMatch) {
  syncStatus  = "Wrong Date";
  syncDetails = `Final Service Time is **${azDate(schedStart)}** but service is **${azDate(schedLive)}**.`;
} else if (!timeMatch) {
  syncStatus  = "Wrong Time";
  syncDetails = `Final Service Time is **${azTime(schedStart)}** but service is **${azTime(schedLive)}**.`;
} else {
  syncStatus  = "Synced";
  syncDetails = `Service matches **${azDate(schedLive)} at ${azTime(schedLive)}**.`;
}
if (atStatus === "Canceled") {
  const when = new Date(live.updated_at || Date.now());
  syncDetails = `Job canceled on ${azDate(when)} at ${azTime(when)}.`;
}

/* ─ 10) write back to Airtable ───────────────────────────────────*/
const updatePayload = {
  "Scheduled Service Time": schedLive.toISOString(),
  "Sync Status":              { name: syncStatus },
  "Sync Details":             syncDetails,
  "Sync Date and Time":       new Date().toISOString()
};

if (atStatus) {
  updatePayload["Job Status"] = { name: atStatus };
}

// NEW: Add appointment ID to update if we found one
if (appointmentId && !rec.getCellValueAsString("Service Appointment ID")) {
  updatePayload["Service Appointment ID"] = appointmentId;
  output.text(`📅 Updating record with appointment ID: ${appointmentId}`);
}

await reservationsTable.updateRecordAsync(rec.id, updatePayload);

output.text(`🗸 ${reservationUID}: ${syncStatus}`);