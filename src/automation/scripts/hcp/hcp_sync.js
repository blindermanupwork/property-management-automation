#!/usr/bin/env node
import 'dotenv/config';
import Airtable from 'airtable';
import fetch from 'node-fetch';

// Timezone utility for Arizona time (for Airtable data)
function getArizonaTime() {
  const now = new Date();
  // Arizona is UTC-7 (MST, no daylight saving)
  const arizonaTime = new Date(now.getTime() - (7 * 60 * 60 * 1000));
  return arizonaTime.toISOString();
}

// ── 1) CONFIG ────────────────────────────────────────────────────────────────
// Environment-aware Airtable configuration
const ENVIRONMENT = process.env.ENVIRONMENT || 'development';
const getAirtableConfig = () => {
  if (ENVIRONMENT === 'production') {
    return {
      API_KEY: process.env.PROD_AIRTABLE_API_KEY,
      BASE_ID: process.env.PROD_AIRTABLE_BASE_ID
    };
  } else {
    return {
      API_KEY: process.env.DEV_AIRTABLE_API_KEY,
      BASE_ID: process.env.DEV_AIRTABLE_BASE_ID
    };
  }
};

const airtableConfig = getAirtableConfig();
console.log(`Using ${ENVIRONMENT.toUpperCase()} environment`);

const CFG = {
  AIRTABLE_API_KEY   : airtableConfig.API_KEY,
  AIRTABLE_BASE_ID   : airtableConfig.BASE_ID,
  HCP_TOKEN          : process.env.HCP_TOKEN,
  TABLE              : 'Reservations',
  VIEW               : 'HCP Create Jobs',
  JOB_ID_FIELD       : 'Service Job ID',
  APPOINTMENT_ID_FIELD: 'Service Appointment ID',  // NEW: Add this line
  JOB_STATUS_FIELD   : 'Job Status',
  SCHED_TIME_FIELD   : 'Scheduled Service Time',
  SYNC_STATUS_FIELD  : 'Sync Status',
  SYNC_DETAILS_FIELD : 'Sync Details',
  SYNC_TIME_FIELD    : 'Sync Date and Time',
  ASSIGNED_TECHS     : ['pro_4f14466de24748bbbeba8ad6fec02800'],
  CONCURRENCY        : 5,
  DELAY_MS           : 500,
  RETRY_ATTEMPTS     : 3,
  RETRY_BACKOFF_MS   : 5000
};

// ── 2) AIRTABLE INIT ─────────────────────────────────────────────────────────
Airtable.configure({ apiKey: CFG.AIRTABLE_API_KEY });
const base  = Airtable.base(CFG.AIRTABLE_BASE_ID);
const table = base(CFG.TABLE);

// ── 3) HELPERS ────────────────────────────────────────────────────────────────
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const fmtDate = d => {
  if (typeof d === 'string') {
    const parts = d.split('T')[0].split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0]);
      const month = parseInt(parts[1]) - 1;
      const day = parseInt(parts[2]);
      d = new Date(year, month, day, 12, 0, 0);
    } else {
      d = new Date(d);
    }
  }
  const month = d.toLocaleString('en-US', {month: 'long'});
  const day = d.getDate();
  return `${month} ${day}`;
};

const fmtTime = d => d.toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit', hour12:true });

async function withRetry(operation, errorMessage, maxAttempts = CFG.RETRY_ATTEMPTS) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      if (attempt > 0) {
        const backoffTime = CFG.RETRY_BACKOFF_MS * Math.pow(2, attempt - 1);
        console.log(`Retrying in ${backoffTime}ms... (Attempt ${attempt + 1}/${maxAttempts})`);
        await delay(backoffTime);
      }
      return await operation();
    } catch (error) {
      console.error(`Attempt ${attempt + 1}/${maxAttempts} failed: ${error.message}`);
      if (attempt === maxAttempts - 1) {
        throw new Error(`${errorMessage}: ${error.message}`);
      }
    }
  }
}

async function hcpFetch(path, method = 'GET', body) {
  let attempt = 0;
  const maxAttempts = CFG.RETRY_ATTEMPTS;
  
  while (attempt < maxAttempts) {
    try {
      const res = await fetch(`https://api.housecallpro.com${path}`, {
  method,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    Authorization: `Token ${CFG.HCP_TOKEN}`,  // ← CORRECT
  },
  body: body ? JSON.stringify(body) : undefined,
});
      
      if (res.status === 429) {
        attempt++;
        const resetHeader = res.headers.get('RateLimit-Reset');
        if (resetHeader) {
          const resetTime = new Date(resetHeader);
          const now = new Date();
          const waitMs = Math.max(resetTime - now, 1000);
          console.log(`Rate limited (429). Waiting until: ${resetTime.toISOString()} (${waitMs}ms)`);
          await delay(waitMs);
          continue;
        } else {
          const backoffTime = CFG.RETRY_BACKOFF_MS * Math.pow(2, attempt);
          console.log(`Rate limited (429) but no reset header. Backing off for ${backoffTime}ms`);
          await delay(backoffTime);
          continue;
        }
      }
      
      if (!res.ok) {
        throw new Error(`${res.status} - ${await res.text()}`);
      }
      
      return res.json();
    } catch (error) {
      attempt++;
      console.error(`Attempt ${attempt}/${maxAttempts} failed: ${error.message}`);
      
      if (attempt === maxAttempts) {
        throw new Error(`Failed to fetch ${path}: ${error.message}`);
      }
      
      const backoffTime = CFG.RETRY_BACKOFF_MS * Math.pow(2, attempt - 1);
      console.log(`Retrying in ${backoffTime}ms... (Attempt ${attempt + 1}/${maxAttempts})`);
      await delay(backoffTime);
    }
  }
}

// Enhanced findNextReservation with consistent API handler logic
function findNextReservation(propertyID, checkOutDate, allRecords) {
  const propertyReservations = allRecords.filter(record => {
    const recordPropLinks = record.fields['Property ID'] || [];
    if (!recordPropLinks.length) return false;
    const recordPropID = recordPropLinks[0];
    if (recordPropID !== propertyID) return false;
    
    let entryType = record.fields['Entry Type'];
    if (typeof entryType === 'object' && entryType.name) {
      entryType = entryType.name;
    }
    if (entryType !== 'Reservation') return false;
    
    let status = record.fields['Status'];
    if (typeof status === 'object' && status.name) {
      status = status.name;
    }
    if (status === 'Old') return false;
    
    const recordCheckIn = record.fields['Check-in Date'];
    if (!recordCheckIn) return false;
    
    const recordCheckInDate = new Date(recordCheckIn);
    const checkOutDateObj = new Date(checkOutDate);
    if (recordCheckInDate <= checkOutDateObj) return false;
    
    return true;
  });
  
  propertyReservations.sort((a, b) => {
    const aDate = new Date(a.fields['Check-in Date']);
    const bDate = new Date(b.fields['Check-in Date']);
    return aDate - bDate;
  });
  
  return propertyReservations.length > 0 ? propertyReservations[0] : null;
}

// ── 4) CREATE A JOB ───────────────────────────────────────────────────────────
async function createJob(rec, finalTime, sameDayTurnover, allRecords) {
  // Extract record data
  let entrySource = 'Airbnb';
  let serviceType = 'Turnover';
  const reservationUID = rec.fields['Reservation UID'] || rec.id;
  
  if (rec.fields['Entry Source']) {
    if (typeof rec.fields['Entry Source'] === 'object' && rec.fields['Entry Source'].name) {
      entrySource = rec.fields['Entry Source'].name;
    } else if (typeof rec.fields['Entry Source'] === 'string') {
      entrySource = rec.fields['Entry Source'];
    }
  }
  
  if (rec.fields['Service Type']) {
    if (typeof rec.fields['Service Type'] === 'object' && rec.fields['Service Type'].name) {
      serviceType = rec.fields['Service Type'].name;
    } else if (typeof rec.fields['Service Type'] === 'string') {
      serviceType = rec.fields['Service Type'];
    }
  }
  
  // Get property details
  const propLinks = rec.fields['Property ID'] || [];
  if (!propLinks.length) throw new Error('No linked Property');
  const propId = propLinks[0];

  const propRec = await withRetry(
    () => base('Properties').find(propId),
    `Failed to fetch property record ${propId}`
  );
  
  const propertyName = propRec.fields['Property Name'] || propId;
  
  // Enhanced service name generation logic - matches API handler logic
  let baseSvcName;
  
  if (sameDayTurnover) {
    baseSvcName = `${serviceType} STR SAME DAY`;
    console.log(`Same-day ${serviceType} -- Setting base service name to: ${baseSvcName}`);
  } else {
    const checkOutDate = rec.fields['Check-out Date'];
    
    // Only do next guest lookup for Turnover services like API handler
    if (serviceType === 'Turnover' && checkOutDate) {
      console.log(`Finding next reservation for ${propertyName}`);
      const nextReservation = findNextReservation(propId, checkOutDate, allRecords);
      
      if (nextReservation) {
        const nextCheckInDate = nextReservation.fields['Check-in Date'];
        const nextResUID = nextReservation.fields['Reservation UID'] || nextReservation.id;
        const nextCheckIn = new Date(nextCheckInDate);
        const month = nextCheckIn.toLocaleString('en-US', { month: 'long' });
        const day = nextCheckIn.getDate();
        baseSvcName = `${serviceType} STR Next Guest ${month} ${day}`;
        console.log(`Res UID: ${nextResUID} with Check-in: ${nextCheckInDate} Found -- Setting base service name to: ${baseSvcName}`);
      } else {
        baseSvcName = `${serviceType} STR Next Guest Unknown`;
        console.log(`No Res UID found -- Setting base service name to: ${baseSvcName}`);
      }
    } else {
      // For non-Turnover services or when no checkout date, use fallback
      baseSvcName = `${serviceType} STR Next Guest Unknown`;
      console.log(`Non-turnover service or no checkout date -- Setting base service name to: ${baseSvcName}`);
    }
  }
  
  // Build final service name with Service Line Custom Instructions first
  let svcName;
  const serviceLineCustomInstructions = rec.fields['Service Line Custom Instructions'];
  console.log(`DEBUG: baseSvcName = "${baseSvcName}"`);
  console.log(`DEBUG: serviceLineCustomInstructions = "${serviceLineCustomInstructions}"`);
  
  if (serviceLineCustomInstructions && serviceLineCustomInstructions.trim()) {
    // Limit custom instructions length to prevent issues
    let customInstructions = serviceLineCustomInstructions.trim();
    const maxCustomLength = 200; // Leave room for base service name
    
    if (customInstructions.length > maxCustomLength) {
      customInstructions = customInstructions.substring(0, maxCustomLength - 3) + '...';
      console.log(`Truncated custom instructions from ${serviceLineCustomInstructions.length} to ${customInstructions.length} characters`);
    }
    
    console.log(`DEBUG: customInstructions = "${customInstructions}"`);
    svcName = `${customInstructions} - ${baseSvcName}`;
    console.log(`Added custom instructions first -- Final service name: ${svcName}`);
    console.log(`Final service name length: ${svcName.length} characters`);
  } else {
    svcName = baseSvcName;
    console.log(`No custom instructions -- Final service name: ${svcName}`);
  }
  console.log(`DEBUG: FINAL svcName = "${svcName}"`);

  const custLinks = propRec.fields['HCP Customer ID'] || [];
  let custId = '';
  if (custLinks.length) {
    // Get the Airtable record ID from the Properties table lookup field
    const custRecordId = typeof custLinks[0] === 'object' ? custLinks[0].id : custLinks[0];
    
    // Fetch the linked record from the Customers table
    const custRecord = await withRetry(
      () => base('Customers').find(custRecordId),
      `Failed to fetch customer record ${custRecordId}`
    );
    
    // Get the actual HCP Customer ID field value from the Customers record
    custId = custRecord.fields['HCP Customer ID'];
    
    console.log(`Airtable record ID: ${custRecordId}, HCP Customer ID: ${custId}`);
  }

  // Address ID is simpler
  const addrId = propRec.fields['HCP Address ID'];

  console.log(`Customer ID: "${custId}", Address ID: "${addrId}"`);

  if (!custId || !addrId) {
    throw new Error('Property missing HCP Customer ID or Address ID');
  }

  // Enhanced template and job type handling - matches API handler logic
  let tmplId, jobTypeId;
  
  // Normalize service type to match API handler logic
  let normalizedServiceType;
  if (serviceType === 'Return Laundry') {
    normalizedServiceType = 'Return Laundry';
    tmplId = propRec.fields['Return Laundry Job Template ID'];
    jobTypeId = "jbt_434c62f58d154eb4a968531702b96e8e"; // Return Laundry job type
  } else if (serviceType === 'Inspection') {
    normalizedServiceType = 'Inspection';
    tmplId = propRec.fields['Inspection Job Template ID'];
    jobTypeId = "jbt_b5d9457caf694beab5f350d42de3e57f"; // Inspection job type
  } else {
    // Default to Turnover for any other service type
    normalizedServiceType = 'Turnover';
    tmplId = propRec.fields['Turnover Job Template ID'];
    jobTypeId = "jbt_20319ca089124b00af1b8b40150424ed"; // Turnover job type
  }
  
  // Update serviceType to use normalized value for consistency
  serviceType = normalizedServiceType;
  
  // If template doesn't exist, skip job creation
  if (!tmplId) {
    console.log(`⚠ No ${serviceType} template ID found for property - skipping job creation`);
    return null;
  }
  
  console.log(`Using ${serviceType} template ${tmplId} and job type ${jobTypeId} for ${reservationUID}`);
  
  // Check for required IDs
  if (!custId || !addrId) {
    throw new Error('Property missing HCP Customer ID or Address ID');
  }

  // Create job with enhanced data structure - matches API handler
  const isoStart = finalTime.toISOString();
  const isoEnd   = new Date(finalTime.getTime() + 3600*1000).toISOString();

  await delay(CFG.DELAY_MS);

  const jobData = {
    invoice_number        : 0,
    customer_id           : custId,
    address_id            : addrId,
    schedule              : { scheduled_start: isoStart, scheduled_end: isoEnd, arrival_window: 0 },
    assigned_employee_ids : CFG.ASSIGNED_TECHS,
    line_items            : [],
    job_fields            : { job_type_id: jobTypeId }
  };
  
  console.log('Creating HCP job with data:', JSON.stringify(jobData, null, 2));
  const job = await hcpFetch('/jobs', 'POST', jobData);
  console.log('Created job ID:', job.id);

  await delay(CFG.DELAY_MS);

  // Copy template line items
  const tmplItems = (await hcpFetch(`/jobs/${tmplId}/line_items`)).data || [];
  
  await delay(CFG.DELAY_MS);
  
  // Enhanced line items update with error handling - matches API handler
  const lineItems = tmplItems.map((it, i) => ({
    name              : i===0? svcName : it.name,
    description       : it.description || '',
    unit_price        : it.unit_price,
    unit_cost         : it.unit_cost,
    quantity          : it.quantity,
    kind              : it.kind,
    taxable           : it.taxable,
    service_item_id   : it.service_item_id   || null,
    service_item_type : it.service_item_type || null
  }));
  
  if (lineItems.length > 0) {
    console.log(`DEBUG: Updating ${lineItems.length} line items for job ${job.id}`);
    console.log(`DEBUG: First line item name length: ${lineItems[0].name.length} characters`);
    console.log(`DEBUG: First line item name: "${lineItems[0].name.substring(0, 100)}${lineItems[0].name.length > 100 ? '...' : ''}"`);
    
    try {
      await hcpFetch(`/jobs/${job.id}/line_items/bulk_update`, 'PUT', {
        line_items: lineItems
      });
      console.log('Successfully copied', lineItems.length, 'line items from template');
    } catch (updateError) {
      console.error(`ERROR updating line items: ${updateError.message}`);
      // Check if it's a length issue
      if (lineItems[0].name.length > 255) {
        console.log(`WARNING: Service name is ${lineItems[0].name.length} characters, may exceed HCP limit`);
        // Try with truncated name
        const truncatedName = lineItems[0].name.substring(0, 250) + '...';
        lineItems[0].name = truncatedName;
        console.log(`Retrying with truncated name: "${truncatedName}"`);
        
        try {
          await hcpFetch(`/jobs/${job.id}/line_items/bulk_update`, 'PUT', {
            line_items: lineItems
          });
          console.log('Successfully updated line items with truncated name');
        } catch (retryError) {
          console.error(`ERROR on retry: ${retryError.message}`);
        }
      }
    }
  }

  // NEW: Fetch job details to get appointment information
  await delay(CFG.DELAY_MS);
  
  let appointmentId = null;
  try {
    // Fetch the job details which should include appointment information
    const jobDetails = await hcpFetch(`/jobs/${job.id}`);
    
    // Try to get appointment ID from job details
    if (jobDetails.appointments && jobDetails.appointments.length > 0) {
      appointmentId = jobDetails.appointments[0].id;
      console.log(`📅 ${reservationUID}: found appointment ID: ${appointmentId}`);
    } else {
      // Alternative: Try fetching appointments directly for this job
      console.log(`📅 ${reservationUID}: no appointments in job details, fetching separately...`);
      
      await delay(CFG.DELAY_MS);
      const appointmentsResponse = await hcpFetch(`/jobs/${job.id}/appointments`);
      
      if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
        appointmentId = appointmentsResponse.appointments[0].id;
        console.log(`📅 ${reservationUID}: found appointment ID via separate fetch: ${appointmentId}`);
      } else {
        console.log(`⚠ ${reservationUID}: no appointment found for job ${job.id}`);
      }
    }
  } catch (error) {
    console.error(`⚠ ${reservationUID}: failed to fetch appointment ID: ${error.message}`);
  }

  // Save job ID and appointment ID back to Airtable
  const updateFields = {
    [CFG.JOB_ID_FIELD]: job.id,
    'Job Creation Time': getArizonaTime() // Arizona time for Airtable data
  };

  // Add appointment ID if we found one
  if (appointmentId) {
    updateFields[CFG.APPOINTMENT_ID_FIELD] = appointmentId;
  }

  await withRetry(
    () => table.update(rec.id, updateFields),
    `Failed to update record ${rec.id} with job and appointment IDs`
  );

  if (appointmentId) {
    console.log(`➕ ${reservationUID}: created job id: ${job.id}, appointment id: ${appointmentId}`);
  } else {
    console.log(`➕ ${reservationUID}: created job id: ${job.id} (no appointment ID found)`);
  }
  
  return job.id;
}
// ── 5) SYNC JOB STATUS & SCHEDULE ────────────────────────────────────────────
async function syncJob(rec, jobId, expectedTime, sameDayTurnover) {
  const reservationUID = rec.fields['Reservation UID'] || rec.id;
  
  await delay(CFG.DELAY_MS);
  
  const job = await hcpFetch(`/jobs/${jobId}`);

  const statusMap = {
    unscheduled : 'Unscheduled',
    scheduled   : 'Scheduled',
    in_progress : 'In Progress',
    completed   : 'Completed',
    canceled    : 'Canceled'
  };
  
  const atStatus   = statusMap[job.work_status?.toLowerCase()] || null;
  const schedStart = new Date(job.schedule.scheduled_start);
  let syncStatus, syncDetails;
  const prefix = sameDayTurnover? 'Same‑day Turnaround. ' : '';

  if (expectedTime.toDateString() !== schedStart.toDateString()) {
    syncStatus  = 'Wrong Date';
    syncDetails = `${prefix}Final ${fmtDate(expectedTime)} ${fmtTime(expectedTime)}, got ${fmtDate(schedStart)} ${fmtTime(schedStart)}`;
  } else if (
    expectedTime.getHours()   !== schedStart.getHours() ||
    expectedTime.getMinutes() !== schedStart.getMinutes()
  ) {
    syncStatus  = 'Wrong Time';
    syncDetails = `${prefix}Final ${fmtTime(expectedTime)}, got ${fmtTime(schedStart)}`;
  } else {
    syncStatus  = 'Synced';
    syncDetails = `${prefix}Matches service date & time.`;
  }

  const updates = {
    [CFG.SCHED_TIME_FIELD]  : schedStart.toISOString(),
    [CFG.SYNC_STATUS_FIELD] : syncStatus,
    [CFG.SYNC_DETAILS_FIELD]: syncDetails,
    [CFG.SYNC_TIME_FIELD]   : getArizonaTime() // Arizona time for Airtable data
  };
  
  if (atStatus) updates[CFG.JOB_STATUS_FIELD] = atStatus;

  // NEW: Check if we need to capture/update appointment ID
  const existingAppointmentId = rec.fields[CFG.APPOINTMENT_ID_FIELD];
  
  if (!existingAppointmentId) {
    console.log(`📅 ${reservationUID}: missing appointment ID, attempting to fetch...`);
    
    try {
      let appointmentId = null;
      
      // Try to get appointment ID from job details
      if (job.appointments && job.appointments.length > 0) {
        appointmentId = job.appointments[0].id;
        console.log(`📅 ${reservationUID}: found appointment ID in job details: ${appointmentId}`);
      } else {
        // Alternative: Try fetching appointments directly for this job
        await delay(CFG.DELAY_MS);
        const appointmentsResponse = await hcpFetch(`/jobs/${jobId}/appointments`);
        
        if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
          appointmentId = appointmentsResponse.appointments[0].id;
          console.log(`📅 ${reservationUID}: found appointment ID via separate fetch: ${appointmentId}`);
        }
      }
      
      // Add appointment ID to updates if found
      if (appointmentId) {
        updates[CFG.APPOINTMENT_ID_FIELD] = appointmentId;
        console.log(`📅 ${reservationUID}: updating record with appointment ID: ${appointmentId}`);
      }
    } catch (error) {
      console.error(`⚠ ${reservationUID}: failed to fetch appointment ID during sync: ${error.message}`);
    }
  }

  await withRetry(
    () => table.update(rec.id, updates),
    `Failed to update record ${rec.id} with sync status`
  );
  
  console.log(`🗸 ${reservationUID}: ${syncStatus}`);
}

// ── 6) PROCESS A SINGLE RESERVATION ─────────────────────────────────────────
async function processReservation(rec, allRecords){
  return withRetry(async () => {
    const reservationUID = rec.fields['Reservation UID'] || rec.id;
    let status;
    let serviceType = 'Turnover';
    
    if (rec.fields['Status']) {
      if (typeof rec.fields['Status'] === 'object' && rec.fields['Status'].name) {
        status = rec.fields['Status'].name;
      } else if (typeof rec.fields['Status'] === 'string') {
        status = rec.fields['Status'];
      }
    }
    
    if (rec.fields['Service Type']) {
      if (typeof rec.fields['Service Type'] === 'object' && rec.fields['Service Type'].name) {
        serviceType = rec.fields['Service Type'].name;
      } else if (typeof rec.fields['Service Type'] === 'string') {
        serviceType = rec.fields['Service Type'];
      }
    }
    
    const existingJob  = rec.fields[CFG.JOB_ID_FIELD];
    const finalTimeVal = rec.fields['Final Service Time'];
    const sameDay      = rec.fields['Same-day Turnover'];
  
    console.log(`Processing reservation uid: ${reservationUID}`);
    
    if (!finalTimeVal) throw new Error('Missing Final Service Time');
    const finalTime = new Date(finalTimeVal);
  
    let jobId = existingJob;
    if (!jobId && ['New','Modified'].includes(status)) {
      jobId = await createJob(rec, finalTime, sameDay, allRecords);
      
      // If createJob returned null, it means template was missing
if (jobId === null) {
  // Use "Not Created" instead of trying to create "Missing Template"
  await withRetry(
    () => table.update(rec.id, {
      [CFG.SYNC_STATUS_FIELD]  : 'Not Created', // Use existing option
      [CFG.SYNC_DETAILS_FIELD] : `Template not found for ${serviceType} service type.`,
      [CFG.SYNC_TIME_FIELD]    : getArizonaTime() // Arizona time for Airtable data
    }),
    `Failed to update record ${rec.id} status`
  );
  console.log(`⚠ ${reservationUID}: missing template for ${serviceType}`);
  return;
}
    }
  
    if (jobId) {
      await syncJob(rec, jobId, finalTime, sameDay);
    } else {
      await withRetry(
        () => table.update(rec.id, {
          [CFG.SYNC_STATUS_FIELD]  : 'Not Created',
          [CFG.SYNC_DETAILS_FIELD] : `${sameDay?'Same-day. ':''}No HCP job.`,
          [CFG.SYNC_TIME_FIELD]    : getArizonaTime() // Arizona time for Airtable data
        }),
        `Failed to update record ${rec.id} with 'Not Created' status`
      );
      console.log(`⚠ ${reservationUID}: no HCP job`);
    }
  }, `Failed to process reservation ${rec.fields['Reservation UID'] || rec.id}`, CFG.RETRY_ATTEMPTS);
}

// ── 7) MAIN FUNCTION ────────────────────────────────────────────────────────
async function main(){
  console.log(`🔍 Fetching all records from ${CFG.TABLE}...`);
  const allRecords = await withRetry(
    () => table.select({
      sort: [{ field: 'Check-in Date', direction: 'asc' }]
    }).all(),
    "Failed to fetch all records"
  );
  
  console.log(`🔄 Fetching records from the view ${CFG.VIEW}...`);
  const viewRecords = await withRetry(
    () => table.select({ view: CFG.VIEW }).all(),
    "Failed to fetch records from view"
  );
  
  console.log(`🔄 Processing ${viewRecords.length} record(s) from view…`);

  const CONCURRENCY = CFG.CONCURRENCY;
  let idx = 0;

  const workers = Array.from({ length: CONCURRENCY }, () =>
    (async function worker(){
      while (true) {
        const i = idx++;
        if (i >= viewRecords.length) break;
        const rec = viewRecords[i];
        try {
          await processReservation(rec, allRecords);
          await delay(500);
        } catch (e) {
          console.error(`❌ ${rec.fields['Reservation UID'] || rec.id}:`, e.message);
          await delay(2000);
        }
      }
    })()
  );

  await Promise.all(workers);
  console.log("✅ All done!");
}

main().catch(err => {
  console.error("Fatal error:", err);
  process.exit(1);
});