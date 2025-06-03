/**
 * High-Speed Airtable ↔ Housecall Pro Batch Sync Script
 * Optimized for maximum throughput with minimal logging
 */

// 1) Load HCP token
let HCP_TOKEN = (await base.getTable("Secrets").selectRecordsAsync()).records.find(r => r.getCellValue("KeyName") === "hcpdev")?.getCellValue("KeyValue");

// 2) Minimal loggers - only important stuff
function logError(msg) { output.markdown(`❌ **Error:** ${msg}`); }
function logWarn(msg) { output.markdown(`⚠️ **Warning:** ${msg}`); }
function logSuccess(msg) { output.markdown(`✅ **Success:** ${msg}`); }
function logProgress(msg) { output.markdown(`🔄 **Progress:** ${msg}`); }

// 3) High-performance configuration
const CFG = {
  TABLE               : "Reservations",
  VIEW                : "HCP Create Jobs", 
  JOB_ID_FIELD        : "Service Job ID",
  APPOINTMENT_ID_FIELD: "Service Appointment ID",
  JOB_STATUS_FIELD    : "Job Status",
  SCHED_TIME_FIELD    : "Scheduled Service Time",
  SYNC_STATUS_FIELD   : "Sync Status",
  SYNC_DETAILS_FIELD  : "Sync Details", 
  SYNC_TIME_FIELD     : "Sync Date and Time",
  ASSIGNED_TECHS      : ["pro_4f14466de24748bbbeba8ad6fec02800"],
  RETRY_ATTEMPTS      : 2,  // Reduced retries for speed
  BATCH_SIZE          : 5, // Larger batches
  MAX_CONCURRENT      : 2, // High concurrency
};

// 4) Streamlined rate limiter
const rateLimiter = {
  queue: [],
  processing: 0,
  
  async submit(fn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      this.process();
    });
  },
  
  async process() {
    if (this.processing >= CFG.MAX_CONCURRENT || this.queue.length === 0) return;
    
    this.processing++;
    const { fn, resolve, reject } = this.queue.shift();
    
    try {
      const result = await fn();
      resolve(result);
    } catch (error) {
      if (error.status === 429) {
        // Requeue with short delay
        setTimeout(() => this.queue.unshift({ fn, resolve, reject }), 1000);
      } else {
        reject(error);
      }
    } finally {
      this.processing--;
      setTimeout(() => this.process(), 0);
    }
  }
};

// 5) Fast retry wrapper
async function withRetry(operation, maxAttempts = CFG.RETRY_ATTEMPTS) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxAttempts - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 100 * attempt)); // Minimal backoff
    }
  }
}

// 6) Minimal HCP fetch wrapper
async function hcpFetch(path, method = "GET", body) {
  return rateLimiter.submit(async () => {
    let res = await remoteFetchAsync(`https://api.housecallpro.com${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json", 
        Authorization: `Token ${HCP_TOKEN}`,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    
    if (res.status === 429) {
      const error = new Error(`Rate limited`);
      error.status = 429;
      throw error;
    }
    
    if (!res.ok) throw new Error(`${res.status} — ${await res.text()}`);
    return res.json();
  });
}

// 7) Fast appointment ID capture
async function captureAppointmentId(jobId) {
  try {
    const appointmentsResponse = await hcpFetch(`/jobs/${jobId}/appointments`);
    return appointmentsResponse.appointments?.[0]?.id || null;
  } catch (error) {
    return null; // Fail silently for speed
  }
}

// 8) Simplified date formatting
const fmtDate = d => {
  if (typeof d === 'string') {
    const parts = d.split('T')[0].split('-');
    if (parts.length === 3) {
      d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]), 12, 0, 0);
    } else {
      d = new Date(d);
    }
  }
  const month = d.toLocaleString('en-US', {month: 'long'});
  return `${month} ${d.getDate()}`;
};

const fmtTime = d => d.toLocaleTimeString("en-US", { hour:"numeric", minute:"2-digit", hour12:true });

// 9) Fast next reservation finder
function findNextReservation(propertyID, checkOutDate, allRecords) {
  const checkOutDateObj = new Date(checkOutDate);
  
  return allRecords
    .filter(record => {
      const propLinks = record.getCellValue("Property ID");
      if (!propLinks?.[0] || propLinks[0].id !== propertyID) return false;
      
      const entryType = record.getCellValue("Entry Type");
      if (entryType?.name !== "Reservation") return false;
      
      const status = record.getCellValue("Status");
      if (status?.name === "Old") return false;
      
      const checkIn = record.getCellValue("Check-in Date");
      if (!checkIn) return false;
      
      return new Date(checkIn) > checkOutDateObj;
    })
    .sort((a, b) => new Date(a.getCellValue("Check-in Date")) - new Date(b.getCellValue("Check-in Date")))[0] || null;
}

// 10) High-speed job creation
async function createJob(rec, finalTime, sameDay, allRecords) {
  const entrySourceObj = rec.getCellValue("Entry Source");
  const serviceTypeObj = rec.getCellValue("Service Type"); 
  const reservationUID = rec.getCellValue("Reservation UID");
  const entrySource = entrySourceObj?.name || 'Airbnb';
  const serviceType = serviceTypeObj?.name || 'Turnover';
  
  // Get property info
  const propertyLinks = rec.getCellValue("Property ID") || [];
  if (!propertyLinks.length) throw new Error("No linked Property");
  const propertyID = propertyLinks[0].id;
  
  // Build service name
 let svcName;
if (sameDay) {
  svcName = `${serviceType} STR SAME DAY`;
} else {
  const checkOutDate = rec.getCellValue("Check-out Date");
  const nextReservation = findNextReservation(propertyID, checkOutDate, allRecords);
  
  if (nextReservation) {
    const nextCheckInDate = nextReservation.getCellValue("Check-in Date");
    svcName = `${serviceType} STR Next Guest ${fmtDate(nextCheckInDate)}`;
  } else {
    svcName = `${serviceType} STR Next Guest Unknown`;
  }
}

  // Get job type ID
  const jobTypeId = serviceType === "Return Laundry"
    ? "jbt_434c62f58d154eb4a968531702b96e8e"
    : serviceType === "Inspection"
      ? "jbt_b5d9457caf694beab5f350d42de3e57f"  
      : "jbt_20319ca089124b00af1b8b40150424ed";

  // Get property details
  const propRec = await base.getTable("Properties").selectRecordAsync(propertyID);
  
  const tmplField = serviceType === "Return Laundry"
    ? "Return Laundry Job Template ID"
    : serviceType === "Inspection"
      ? "Inspection Job Template ID"
      : "Turnover Job Template ID";

  const custLinks = propRec.getCellValue("HCP Customer ID") || [];
  const custId = custLinks.length 
    ? (typeof custLinks[0] === "object" && custLinks[0].name) ? custLinks[0].name : custLinks[0]
    : "";
  const addrId = propRec.getCellValue("HCP Address ID");
  const tmplId = propRec.getCellValue(tmplField);
  
  if (!custId || !addrId || !tmplId) {
    await base.getTable(CFG.TABLE).updateRecordAsync(rec.id, {
      [CFG.SYNC_STATUS_FIELD]: {name:"Error"},
      [CFG.SYNC_DETAILS_FIELD]: "Missing HCP IDs",
      [CFG.SYNC_TIME_FIELD]: new Date().toISOString()
    });
    throw new Error("Missing HCP IDs");
  }

  // Create job and get appointment ID in parallel
  const isoStart = finalTime.toISOString();
  const isoEnd = new Date(finalTime.getTime() + 3600*1000).toISOString();

  const [job, tmplItems] = await Promise.all([
    hcpFetch("/jobs", "POST", {
      invoice_number: 0,
      customer_id: custId,
      address_id: addrId,
      schedule: { scheduled_start: isoStart, scheduled_end: isoEnd, arrival_window: 0 },
      assigned_employee_ids: CFG.ASSIGNED_TECHS,
      line_items: [],
      job_fields: { job_type_id: jobTypeId }
    }),
    hcpFetch(`/jobs/${tmplId}/line_items`).then(res => res.data || [])
  ]);

  // Update line items and get appointment ID in parallel
  const [, appointmentId] = await Promise.all([
    hcpFetch(`/jobs/${job.id}/line_items/bulk_update`, "PUT", {
      line_items: tmplItems.map((it,i) => ({
        name: i===0 ? svcName : it.name,
        description: it.description || "",
        unit_price: it.unit_price,
        unit_cost: it.unit_cost,
        quantity: it.quantity,
        kind: it.kind,
        taxable: it.taxable,
        service_item_id: it.service_item_id || null,
        service_item_type: it.service_item_type || null
      }))
    }),
    new Promise(resolve => setTimeout(resolve, 300)).then(() => captureAppointmentId(job.id)) // Short delay then fetch
  ]);

  // Update Airtable record
  const updateFields = {
    [CFG.JOB_ID_FIELD]: job.id,
    "Job Creation Time": new Date().toISOString()
  };
  if (appointmentId) updateFields[CFG.APPOINTMENT_ID_FIELD] = appointmentId;

  await base.getTable(CFG.TABLE).updateRecordAsync(rec.id, updateFields);
  return job.id;
}

// 11) Fast job sync
async function syncJob(rec, jobId, expectedTime, sameDay) {
  const job = await hcpFetch(`/jobs/${jobId}`);
  
  const statusMap = {
    unscheduled: "Unscheduled",
    scheduled: "Scheduled", 
    in_progress: "In Progress",
    completed: "Completed",
    canceled: "Canceled"
  };
  
  const atStatus = statusMap[job.work_status?.toLowerCase()] || null;
  const schedStart = new Date(job.schedule.scheduled_start);
  const prefix = sameDay ? "Same‑day Turnaround. " : "";

  let syncStatus, syncDetails;
  if (expectedTime.toDateString() !== schedStart.toDateString()) {
    syncStatus = "Wrong Date";
    syncDetails = `${prefix}Expected ${fmtDate(expectedTime)}, got ${fmtDate(schedStart)}`;
  } else if (expectedTime.getHours() !== schedStart.getHours() || expectedTime.getMinutes() !== schedStart.getMinutes()) {
    syncStatus = "Wrong Time"; 
    syncDetails = `${prefix}Expected ${fmtTime(expectedTime)}, got ${fmtTime(schedStart)}`;
  } else {
    syncStatus = "Synced";
    syncDetails = `${prefix}Matches ${fmtDate(schedStart)} ${fmtTime(schedStart)}`;
  }
  
  if (atStatus === "Canceled") {
    const when = new Date(job.updated_at || Date.now());
    syncDetails = `Canceled on ${fmtDate(when)} ${fmtTime(when)}`;
  }

  const updates = {
    [CFG.SCHED_TIME_FIELD]: schedStart.toISOString(),
    [CFG.SYNC_STATUS_FIELD]: { name: syncStatus },
    [CFG.SYNC_DETAILS_FIELD]: syncDetails,
    [CFG.SYNC_TIME_FIELD]: new Date().toISOString()
  };
  if (atStatus) updates[CFG.JOB_STATUS_FIELD] = { name: atStatus };

  // Try to get appointment ID if missing (no delay, fail fast)
  const existingAppointmentId = rec.getCellValueAsString(CFG.APPOINTMENT_ID_FIELD);
  if (!existingAppointmentId) {
    const appointmentId = await captureAppointmentId(jobId);
    if (appointmentId) updates[CFG.APPOINTMENT_ID_FIELD] = appointmentId;
  }

  await base.getTable(CFG.TABLE).updateRecordAsync(rec.id, updates);
  return syncStatus;
}

// 12) Process single reservation
async function processReservation(rec, allRecords) {
  return withRetry(async () => {
    const reservationUID = rec.getCellValue("Reservation UID");
    const statusVal = rec.getCellValueAsString("Status");
    const existingJob = rec.getCellValueAsString(CFG.JOB_ID_FIELD);
    const finalTimeVal = rec.getCellValue("Final Service Time");
    const sameDay = rec.getCellValue("Same-day Turnover");
  
    if (!finalTimeVal) throw new Error("Missing Final Service Time");
    const finalTime = new Date(finalTimeVal);
  
    let jobId = existingJob;
    if (!jobId && ["New","Modified"].includes(statusVal)) {
      jobId = await createJob(rec, finalTime, sameDay, allRecords);
      if (!jobId) return "Error";
    }
  
    if (jobId) {
      return await syncJob(rec, jobId, finalTime, sameDay);
    } else {
      await base.getTable(CFG.TABLE).updateRecordAsync(rec.id, {
        [CFG.SYNC_STATUS_FIELD]: { name: "Not Created" },
        [CFG.SYNC_DETAILS_FIELD]: `${sameDay ? "Same-day. " : ""}No HCP job.`,
        [CFG.SYNC_TIME_FIELD]: new Date().toISOString()
      });
      return "Not Created";
    }
  });
}

// 13) High-speed batch processor
async function processBatch(records, allRecords) {
  const results = [];
  const total = records.length;
  let processed = 0;

  // Process all records concurrently with controlled batching
  const promises = records.map(async (rec, index) => {
    try {
      const result = await processReservation(rec, allRecords);
      processed++;
      
      // Only log every 5 records or at end
      if (processed % 5 === 0 || processed === total) {
        logProgress(`${processed}/${total} records processed`);
      }
      
      return { 
        id: rec.id, 
        uid: rec.getCellValue("Reservation UID"), 
        result 
      };
    } catch (err) {
      processed++;
      logError(`${rec.getCellValue("Reservation UID")}: ${err.message}`);
      return { 
        id: rec.id, 
        uid: rec.getCellValue("Reservation UID"), 
        error: err.message 
      };
    }
  });

  return Promise.all(promises);
}

// 14) Main execution
async function main() {
  const startTime = Date.now();
  logProgress(`Starting high-speed sync...`);
  
  const tableObj = base.getTable(CFG.TABLE);

  // Fetch records in parallel
  const [allRecords, viewRecords] = await Promise.all([
    tableObj.selectRecordsAsync({
      sorts: [{ field: "Check-in Date", direction: "asc" }]
    }),
    tableObj.getView(CFG.VIEW).selectRecordsAsync()
  ]);

  logProgress(`Processing ${viewRecords.records.length} records with ${CFG.MAX_CONCURRENT} concurrent operations...`);

  // Process all records
  const results = await processBatch(viewRecords.records, allRecords.records);

  // Final summary
  const succeeded = results.filter(r => !r.error).length;
  const failed = results.filter(r => r.error).length;
  const duration = ((Date.now() - startTime) / 1000).toFixed(1);
  
  logSuccess(`Completed in ${duration}s: ${succeeded} succeeded, ${failed} failed`);
  
  if (failed > 0) {
    logWarn(`${failed} failures - check logs above for details`);
  }
}

// Execute
await main();