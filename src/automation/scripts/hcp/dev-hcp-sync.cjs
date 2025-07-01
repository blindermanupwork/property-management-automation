#!/usr/bin/env node

/**
 * DEV HCP Sync Script
 * Syncs HCP job data with DEV Airtable base for multiple reservations
 * With Service Line Custom Instructions support
 */

require('dotenv').config({ path: '/home/opc/automation/config/environments/dev/.env' });

const Airtable = require('airtable');
// Use native fetch in Node 18+
const { fetch } = globalThis;

// Import sync message builder for dev environment
let buildSyncMessage = null;
try {
  const syncMessageBuilder = require('../shared/syncMessageBuilder');
  buildSyncMessage = syncMessageBuilder.buildSyncMessage;
  console.log('✅ Loaded sync message builder for dev environment');
} catch (e) {
  console.warn('⚠️ Could not load sync message builder for dev environment:', e.message);
}

// Force DEV environment
process.env.NODE_ENV = 'development';
process.env.AIRTABLE_ENV = 'development';

// DEV Configuration
const AIRTABLE_API_KEY = process.env.DEV_AIRTABLE_API_KEY;
const AIRTABLE_BASE_ID = process.env.DEV_AIRTABLE_BASE_ID;
const HCP_TOKEN = process.env.DEV_HCP_TOKEN;
const HCP_EMPLOYEE_ID = process.env.DEV_HCP_EMPLOYEE_ID;

if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID || !HCP_TOKEN || !HCP_EMPLOYEE_ID) {
  console.error('❌ Missing required DEV environment variables');
  console.error('Required: DEV_AIRTABLE_API_KEY, DEV_AIRTABLE_BASE_ID, DEV_HCP_TOKEN, DEV_HCP_EMPLOYEE_ID');
  process.exit(1);
}

console.log('🔧 Running HCP Sync in DEV environment');
console.log(`📊 Using DEV Airtable Base: ${AIRTABLE_BASE_ID}`);
console.log(`👤 Using DEV HCP Employee: ${HCP_EMPLOYEE_ID}`);

// Initialize Airtable
const base = new Airtable({ apiKey: AIRTABLE_API_KEY }).base(AIRTABLE_BASE_ID);

// Arizona timezone helpers
const AZ_TZ = 'America/Phoenix';
const fmtDate = (d) => {
  const dt = new Date(d);
  const mon = dt.toLocaleString('en-US', { month: 'long', timeZone: AZ_TZ });
  const day = dt.getDate();
  return `${mon} ${day}`;
};

// HCP API helper with rate limiting
async function hcp(path, method = 'GET', body = null) {
  const maxRetries = 3;
  let retry = 0;
  
  while (true) {
    const res = await fetch(`https://api.housecallpro.com${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Token ${HCP_TOKEN}`
      },
      body: body ? JSON.stringify(body) : undefined
    });

    const raw = await res.text();
    
    if (res.status === 429 && retry < maxRetries) {
      retry++;
      const reset = res.headers.get('RateLimit-Reset');
      const wait = reset
        ? Math.max(new Date(reset) - new Date(), 1000)
        : 1000 * (2 ** retry);
      console.log(`⏳ Rate limited, waiting ${wait / 1000}s...`);
      await new Promise(resolve => setTimeout(resolve, wait));
      continue;
    }

    if (!res.ok) {
      throw new Error(`HCP API Error: ${res.status} - ${raw}`);
    }

    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  }
}

// Find next entry (reservation or block) helper
function findNextEntry(propertyId, checkOutDate, allRecords) {
  const nextEntries = allRecords
    .filter(r => {
      if (!r.fields['Property ID'] || r.fields['Property ID'][0] !== propertyId) return false;
      const entryType = r.fields['Entry Type'];
      if (entryType !== 'Reservation' && entryType !== 'Block') return false;
      if (r.fields['Status'] === 'Old') return false;
      const checkIn = r.fields['Check-in Date'];
      return checkIn && new Date(checkIn) >= new Date(checkOutDate);
    })
    .sort((a, b) => new Date(a.fields['Check-in Date']) - new Date(b.fields['Check-in Date']));
  
  return nextEntries.length > 0 ? nextEntries[0] : null;
}

// Main sync function
async function syncMultipleJobs() {
  try {
    console.log('\n🔍 Fetching all reservations from DEV Airtable...');
    
    // Fetch ALL records for next guest lookup
    const allRecords = await base('Reservations').select({
      view: 'HCP Create Jobs'
    }).all();
    
    console.log(`📊 Found ${allRecords.length} total reservations`);
    
    // Filter records that need job creation
    const recordsToProcess = allRecords.filter(rec => {
      const hasJob = rec.fields['Service Job ID'];
      const serviceType = rec.fields['Service Type'];
      const finalTime = rec.fields['Final Service Time'];
      
      // Create job if: NO job ID exists AND has service type AND has final time
      return !hasJob && serviceType && finalTime;
    });
    
    console.log(`🎯 ${recordsToProcess.length} reservations need job creation`);
    
    // Check ALL records that have jobs for sync verification
    const recordsToVerify = allRecords.filter(rec => {
      const hasJob = rec.fields['Service Job ID'];
      const finalTime = rec.fields['Final Service Time'];
      
      // Verify sync for: ANY record with job ID AND final time
      return hasJob && finalTime;
    });
    
    console.log(`🔍 ${recordsToVerify.length} existing jobs will be checked for sync status`);
    
    let successCount = 0;
    let errorCount = 0;
    let verifyCount = 0;
    
    // First, verify existing jobs
    for (const rec of recordsToVerify) {
      const jobId = rec.fields['Service Job ID'];
      const finalTime = rec.fields['Final Service Time'];
      const resUID = rec.fields['Reservation UID'] || rec.id;
      
      console.log(`\n🔍 Verifying sync for: ${resUID} - Job ${jobId}`);
      
      try {
        // Get current job schedule from HCP
        const jobDetails = await hcp(`/jobs/${jobId}`);
        const schedLive = new Date(jobDetails.schedule.scheduled_start);
        const schedExpected = new Date(finalTime);
        
        // Compare times in Arizona timezone
        const azDate = d => d.toLocaleDateString('en-US', {
          timeZone: AZ_TZ, month: 'long', day: 'numeric'
        });
        const azTime = d => d.toLocaleTimeString('en-US', {
          timeZone: AZ_TZ, hour: 'numeric', minute: '2-digit', hour12: true
        });
        
        const dateMatch = azDate(schedLive) === azDate(schedExpected);
        const timeMatch = azTime(schedLive) === azTime(schedExpected);
        
        // Build sync status and details
        let syncStatus, syncDetails;
        
        if (buildSyncMessage) {
          if (!dateMatch) {
            syncStatus = 'Wrong Date';
            syncDetails = buildSyncMessage('WRONG_DATE', {
              airtableValue: finalTime,
              hcpValue: schedLive.toISOString()
            });
          } else if (!timeMatch) {
            syncStatus = 'Wrong Time';
            syncDetails = buildSyncMessage('WRONG_TIME', {
              airtableValue: finalTime,
              hcpValue: schedLive.toISOString()
            });
          } else {
            syncStatus = 'Synced';
            syncDetails = buildSyncMessage('SYNCED', {
              airtableValue: finalTime
            });
          }
        } else {
          syncStatus = dateMatch && timeMatch ? 'Synced' : (!dateMatch ? 'Wrong Date' : 'Wrong Time');
          syncDetails = `Schedule verification: ${dateMatch && timeMatch ? 'In sync' : 'Mismatch detected'}`;
        }
        
        // Update Airtable with verification results
        await base('Reservations').update(rec.id, {
          'Sync Status': syncStatus,
          'Service Sync Details': syncDetails,
          'Sync Date and Time': new Date().toISOString(),
          'Scheduled Service Time': schedLive.toISOString()
        });
        
        console.log(`   ✅ Updated sync status: ${syncStatus}`);
        if (syncStatus !== 'Synced') {
          console.log(`      Expected: ${azDate(schedExpected)} at ${azTime(schedExpected)}`);
          console.log(`      Actual:   ${azDate(schedLive)} at ${azTime(schedLive)}`);
        }
        verifyCount++;
        
      } catch (error) {
        console.error(`   ❌ Error verifying job ${jobId}: ${error.message}`);
      }
    }
    
    // Process each record that needs job creation
    for (const rec of recordsToProcess) {
      const resUID = rec.fields['Reservation UID'] || rec.id;
      const serviceType = rec.fields['Service Type'];
      const finalTime = rec.fields['Final Service Time'];
      const propLinks = rec.fields['Property ID'] || [];
      const sameDayTurnover = rec.fields['Same-day Turnover'];
      
      console.log(`\n📌 Processing: ${resUID} - ${serviceType}`);
      
      if (!propLinks.length) {
        console.log(`⚠️  Skipping - No property linked`);
        errorCount++;
        continue;
      }
      
      try {
        // Get property details
        const propId = propLinks[0];
        const propRec = await base('Properties').find(propId);
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
            console.log(`Finding next entry for ${propertyName}`);
            const nextEntry = findNextEntry(propId, checkOutDate, allRecords);
            
            if (nextEntry) {
              const nextCheckInDate = nextEntry.fields['Check-in Date'];
              const nextEntryType = nextEntry.fields['Entry Type'];
              const isBlock = nextEntryType === 'Block';
              
              if (isBlock) {
                console.log(`Next entry is a BLOCK (owner arriving) on ${nextCheckInDate}`);
              } else {
                const nextResUID = nextEntry.fields['Reservation UID'] || nextEntry.id;
                console.log(`Next entry is reservation ${nextResUID} on ${nextCheckInDate}`);
              }
              
              const nextCheckIn = new Date(nextCheckInDate);
              const month = nextCheckIn.toLocaleString('en-US', { month: 'long' });
              const day = nextCheckIn.getDate();
              baseSvcName = `${serviceType} STR Next Guest ${month} ${day}`;
              console.log(`Setting base service name to: ${baseSvcName}`);
              
              // Store block status for later use
              rec.isNextEntryBlock = isBlock;
            } else {
              baseSvcName = `${serviceType} STR Next Guest Unknown`;
              console.log(`No next entry found -- Setting base service name to: ${baseSvcName}`);
              rec.isNextEntryBlock = false;
            }
          } else {
            // For non-Turnover services or when no checkout date, use fallback
            baseSvcName = `${serviceType} STR Next Guest Unknown`;
            console.log(`Non-turnover service or no checkout date -- Setting base service name to: ${baseSvcName}`);
            rec.isNextEntryBlock = false;
          }
        }
        
        // Build final service name with Service Line Custom Instructions first
        let svcName;
        const serviceLineCustomInstructions = rec.fields['Custom Service Line Instructions'];
        console.log(`DEBUG: baseSvcName = "${baseSvcName}"`);
        console.log(`DEBUG: serviceLineCustomInstructions = "${serviceLineCustomInstructions}"`);
        
        // Check for long-term guest (2+ weeks) and modify service name accordingly
        let isLongTermGuest = false;
        const checkInDate = rec.fields['Check-in Date'];
        const checkOutDate = rec.fields['Check-out Date'];
        
        if (checkInDate && checkOutDate) {
          const checkIn = new Date(checkInDate);
          const checkOut = new Date(checkOutDate);
          const stayDurationDays = (checkOut - checkIn) / (1000 * 60 * 60 * 24);
          
          if (stayDurationDays >= 14) {
            isLongTermGuest = true;
            console.log(`DEBUG: Long-term guest detected - ${stayDurationDays} days stay`);
          }
        }
        
        // Build service line description with new hierarchy:
        // 1. Custom Instructions
        // 2. OWNER ARRIVING (if next entry is block)
        // 3. LONG TERM GUEST DEPARTING (if stay >= 14 days)
        // 4. Base service name
        
        let parts = [];
        
        // Add custom instructions if present
        if (serviceLineCustomInstructions && serviceLineCustomInstructions.trim()) {
          // Limit custom instructions length to prevent issues
          let customInstructions = serviceLineCustomInstructions.trim();
          const maxCustomLength = 200;
          
          if (customInstructions.length > maxCustomLength) {
            customInstructions = customInstructions.substring(0, maxCustomLength - 3) + '...';
            console.log(`Truncated custom instructions from ${serviceLineCustomInstructions.length} to ${customInstructions.length} characters`);
          }
          
          parts.push(customInstructions);
          console.log(`Added custom instructions: "${customInstructions}"`);
        }
        
        // Add OWNER ARRIVING if next entry is a block
        if (rec.isNextEntryBlock) {
          parts.push("OWNER ARRIVING");
          console.log(`Added OWNER ARRIVING flag`);
        }
        
        // Add LONG TERM GUEST DEPARTING if applicable
        if (isLongTermGuest) {
          parts.push("LONG TERM GUEST DEPARTING");
          console.log(`Added long-term guest flag`);
        }
        
        // Add base service name
        parts.push(baseSvcName);
        
        // Join all parts
        if (parts.length > 1) {
          svcName = parts.join(" - ");
        } else {
          svcName = parts[0];
        }
        
        console.log(`Final service name: ${svcName} (${svcName.length} characters)`);
        console.log(`DEBUG: FINAL svcName = "${svcName}"`);
        
        // Enhanced HCP ID retrieval - matches API handler logic
        const custLinks = propRec.fields['HCP Customer ID'] || [];
        let custId = '';
        if (custLinks.length) {
          // Get the Airtable record ID from the Properties table lookup field
          const custRecordId = typeof custLinks[0] === 'object' ? custLinks[0].id : custLinks[0];
          
          try {
            // Fetch the linked record from the Customers table
            const custRecord = await base('Customers').find(custRecordId);
            
            // Get the actual HCP Customer ID field value from the Customers record
            custId = custRecord.fields['HCP Customer ID'];
            
            console.log(`Airtable record ID: ${custRecordId}, HCP Customer ID: ${custId}`);
          } catch (error) {
            console.log(`⚠️  Error fetching customer record: ${error.message}`);
            errorCount++;
            continue;
          }
        }
        
        if (!custId) {
          console.log(`⚠️  Skipping - No HCP Customer ID`);
          errorCount++;
          continue;
        }
        
        const addrId = propRec.fields['HCP Address ID'];
        
        if (!addrId) {
          console.log(`⚠️  Skipping - No HCP Address ID`);
          errorCount++;
          continue;
        }
        
        // Get template ID
        const templateMap = {
          'Turnover': propRec.fields['Turnover Job Template ID'],
          'Return Laundry': propRec.fields['Return Laundry Job Template ID'],
          'Inspection': propRec.fields['Inspection Job Template ID']
        };
        
        const templateId = templateMap[serviceType];
        if (!templateId) {
          console.log(`⚠️  Skipping - No template ID for ${serviceType}`);
          errorCount++;
          continue;
        }
        
        console.log(`✅ Creating ${serviceType} job with template ${templateId}`);
        console.log(`   Service Name: ${svcName}`);
        console.log(`   Customer: ${custId}, Address: ${addrId}`);
        console.log(`   Employee: ${HCP_EMPLOYEE_ID}`);
        console.log(`   Scheduled: ${finalTime}`);
        
        // Enhanced job creation with job type IDs from environment
        let jobTypeId;
        if (serviceType === 'Return Laundry') {
          jobTypeId = process.env.DEV_HCP_RETURN_LAUNDRY_JOB_TYPE;
        } else if (serviceType === 'Inspection') {
          jobTypeId = process.env.DEV_HCP_INSPECTION_JOB_TYPE;
        } else {
          // Default to Turnover for any other service type
          jobTypeId = process.env.DEV_HCP_TURNOVER_JOB_TYPE;
        }
        
        // Fallback to Turnover if job type ID is not found
        if (!jobTypeId) {
          console.log(`⚠️  No job type ID found for ${serviceType}, defaulting to Turnover`);
          jobTypeId = process.env.DEV_HCP_TURNOVER_JOB_TYPE;
        }
        
        console.log(`Using ${serviceType} job type ${jobTypeId}`);
        
        // Create HCP job with job type ID
        const jobBody = {
          invoice_number: 0,
          customer_id: custId,
          address_id: addrId,
          assigned_employee_ids: [HCP_EMPLOYEE_ID],
          schedule: {
            scheduled_start: finalTime,
            scheduled_end: new Date(new Date(finalTime).getTime() + 60 * 60 * 1000).toISOString(), // 1 hour duration like API
            arrival_window: 0
          },
          line_items: [],
          job_fields: {
            job_type_id: jobTypeId
          }
        };
        
        const jobResp = await hcp('/jobs', 'POST', jobBody);
        const jobId = jobResp.id;
        
        console.log(`   ✅ Created job: ${jobId}`);
        
        // Enhanced line items handling with error recovery - matches API handler
        const templateItems = await hcp(`/jobs/${templateId}/line_items`);
        const lineItems = (templateItems.data || []).map((item, i) => ({
          name: i === 0 ? svcName : item.name,
          description: item.description || '',
          unit_price: item.unit_price,
          unit_cost: item.unit_cost,
          quantity: item.quantity,
          kind: item.kind,
          taxable: item.taxable,
          service_item_id: item.service_item_id || null,
          service_item_type: item.service_item_type || null
        }));
        
        if (lineItems.length > 0) {
          console.log(`   DEBUG: Updating ${lineItems.length} line items for job ${jobId}`);
          console.log(`   DEBUG: First line item name length: ${lineItems[0].name.length} characters`);
          console.log(`   DEBUG: First line item name: "${lineItems[0].name.substring(0, 100)}${lineItems[0].name.length > 100 ? '...' : ''}"`);
          
          try {
            await hcp(`/jobs/${jobId}/line_items/bulk_update`, 'PUT', { line_items: lineItems });
            console.log(`   ✅ Successfully copied ${lineItems.length} line items from template`);
          } catch (updateError) {
            console.error(`   ERROR updating line items: ${updateError.message}`);
            // Check if it's a length issue
            if (lineItems[0].name.length > 255) {
              console.log(`   WARNING: Service name is ${lineItems[0].name.length} characters, may exceed HCP limit`);
              // Try with truncated name
              const truncatedName = lineItems[0].name.substring(0, 250) + '...';
              lineItems[0].name = truncatedName;
              console.log(`   Retrying with truncated name: "${truncatedName}"`);
              
              try {
                await hcp(`/jobs/${jobId}/line_items/bulk_update`, 'PUT', { line_items: lineItems });
                console.log(`   ✅ Successfully updated line items with truncated name`);
              } catch (retryError) {
                console.error(`   ERROR on retry: ${retryError.message}`);
              }
            }
          }
        }
        
        // Enhanced Airtable update with appointment ID capture - matches API handler
        let appointmentId = null;
        
        // Give HCP time to create the appointment
        await new Promise(resolve => setTimeout(resolve, 700));
        
        // Try to get appointment ID
        try {
          const jobDetails = await hcp(`/jobs/${jobId}`);
          
          if (jobDetails.appointments && jobDetails.appointments.length > 0) {
            appointmentId = jobDetails.appointments[0].id;
            console.log(`   📅 Found appointment ID: ${appointmentId}`);
          } else {
            console.log(`   📅 No appointments in job details, fetching separately...`);
            await new Promise(resolve => setTimeout(resolve, 500));
            
            const appointmentsResponse = await hcp(`/jobs/${jobId}/appointments`);
            
            if (appointmentsResponse.appointments && appointmentsResponse.appointments.length > 0) {
              appointmentId = appointmentsResponse.appointments[0].id;
              console.log(`   📅 Found appointment ID via separate fetch: ${appointmentId}`);
            } else {
              console.log(`   ⚠ No appointment found for job ${jobId}`);
            }
          }
        } catch (error) {
          console.log(`   ⚠ Failed to fetch appointment ID: ${error.message}`);
        }
        
        // Verify the job schedule matches what we requested
        await new Promise(resolve => setTimeout(resolve, 500));
        const finalJob = await hcp(`/jobs/${jobId}`);
        const schedLive = new Date(finalJob.schedule.scheduled_start);
        const schedExpected = new Date(finalTime);
        
        // Compare times in Arizona timezone
        const azDate = d => d.toLocaleDateString('en-US', {
          timeZone: AZ_TZ, month: 'long', day: 'numeric'
        });
        const azTime = d => d.toLocaleTimeString('en-US', {
          timeZone: AZ_TZ, hour: 'numeric', minute: '2-digit', hour12: true
        });
        
        const dateMatch = azDate(schedLive) === azDate(schedExpected);
        const timeMatch = azTime(schedLive) === azTime(schedExpected);
        
        // Update Airtable with enhanced fields
        // Use clear sync messaging for dev environment
        let syncStatus, syncDetails;
        
        if (buildSyncMessage) {
          if (!dateMatch) {
            syncStatus = 'Wrong Date';
            syncDetails = buildSyncMessage('WRONG_DATE', {
              airtableValue: finalTime,
              hcpValue: schedLive.toISOString()
            });
          } else if (!timeMatch) {
            syncStatus = 'Wrong Time';
            syncDetails = buildSyncMessage('WRONG_TIME', {
              airtableValue: finalTime,
              hcpValue: schedLive.toISOString()
            });
          } else {
            syncStatus = 'Synced';
            syncDetails = buildSyncMessage('SYNCED', {
              airtableValue: finalTime
            });
          }
        } else {
          // Fallback for prod environment
          syncStatus = dateMatch && timeMatch ? 'Synced' : (!dateMatch ? 'Wrong Date' : 'Wrong Time');
          syncDetails = `Created DEV job ${jobId} with service name: ${svcName}`;
        }
        
        const updateFields = {
          'Service Job ID': jobId,
          'Job Creation Time': new Date().toISOString(),
          'Job Status': 'Scheduled',
          'Sync Status': syncStatus,
          'Sync Date and Time': new Date().toISOString(),
          'Service Sync Details': syncDetails,  // Use the new field name for dev
          'Scheduled Service Time': schedLive.toISOString()
        };
        
        if (appointmentId) {
          updateFields['Service Appointment ID'] = appointmentId;
        }
        
        await base('Reservations').update(rec.id, updateFields);
        
        console.log(`   ✅ Updated Airtable record`);
        successCount++;
        
        // Small delay between jobs
        await new Promise(resolve => setTimeout(resolve, 500));
        
      } catch (error) {
        console.error(`❌ Error processing ${resUID}: ${error.message}`);
        errorCount++;
      }
    }
    
    console.log('\n📊 Sync Summary:');
    console.log(`✅ Successfully created: ${successCount} jobs`);
    console.log(`🔍 Verified sync status: ${verifyCount} jobs`);
    console.log(`❌ Errors: ${errorCount}`);
    console.log(`📋 Total records in view: ${allRecords.length}`);
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  }
}

// Run the sync
syncMultipleJobs();