#!/usr/bin/env node

/**
 * PROD HCP Sync Script
 * Syncs HCP job data with PROD Airtable base for multiple reservations
 * With Service Line Custom Instructions support
 * 
 * ⚠️ PRODUCTION SCRIPT - DO NOT RUN WITHOUT APPROVAL ⚠️
 */

require('dotenv').config({ path: '/home/opc/automation/config/environments/prod/.env' });

const Airtable = require('airtable');
const fetch = require('node-fetch');

// Force PROD environment
process.env.NODE_ENV = 'production';
process.env.AIRTABLE_ENV = 'production';

// PROD Configuration
const AIRTABLE_API_KEY = process.env.PROD_AIRTABLE_API_KEY;
const AIRTABLE_BASE_ID = process.env.PROD_AIRTABLE_BASE_ID;
const HCP_TOKEN = process.env.PROD_HCP_TOKEN;
const HCP_EMPLOYEE_ID = process.env.PROD_HCP_EMPLOYEE_ID;

if (!AIRTABLE_API_KEY || !AIRTABLE_BASE_ID || !HCP_TOKEN || !HCP_EMPLOYEE_ID) {
  console.error('❌ Missing required PROD environment variables');
  console.error('Required: PROD_AIRTABLE_API_KEY, PROD_AIRTABLE_BASE_ID, PROD_HCP_TOKEN, PROD_HCP_EMPLOYEE_ID');
  process.exit(1);
}

console.log('⚠️  ⚠️  ⚠️  PRODUCTION ENVIRONMENT ⚠️  ⚠️  ⚠️');
console.log('🔧 Running HCP Sync in PRODUCTION environment');
console.log(`📊 Using PROD Airtable Base: ${AIRTABLE_BASE_ID}`);
console.log(`👤 Using PROD HCP Employee: ${HCP_EMPLOYEE_ID}`);

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

// Find next reservation helper
function findNextReservation(propertyId, checkOutDate, allRecords) {
  return allRecords.find(r => {
    if (!r.fields['Property ID'] || r.fields['Property ID'][0] !== propertyId) return false;
    if (r.fields['Entry Type'] !== 'Reservation') return false;
    if (r.fields['Status'] === 'Old') return false;
    const checkIn = r.fields['Check-in Date'];
    return checkIn && new Date(checkIn) > new Date(checkOutDate);
  });
}

// Main sync function
async function syncMultipleJobs() {
  try {
    console.log('\n🔍 Fetching all reservations from PRODUCTION Airtable...');
    
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
      const status = rec.fields['Status'];
      
      return !hasJob && serviceType && finalTime && status === 'New';
    });
    
    console.log(`🎯 ${recordsToProcess.length} reservations need job creation`);
    
    let successCount = 0;
    let errorCount = 0;
    
    // Process each record
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
        
        // Build service name based on service type and date logic
        let svcName;
        
        if (sameDayTurnover) {
          svcName = `${serviceType} STR SAME DAY`;
          console.log(`Same-day ${serviceType} -- Setting service name to: ${svcName}`);
        } else {
          const checkOutDate = rec.fields['Check-out Date'];
          console.log(`Finding next reservation for ${propertyName}`);
          const nextReservation = findNextReservation(propId, checkOutDate, allRecords);
          
          if (nextReservation) {
            const nextCheckInDate = nextReservation.fields['Check-in Date'];
            const nextResUID = nextReservation.fields['Reservation UID'] || nextReservation.id;
            svcName = `${serviceType} STR Next Guest ${fmtDate(nextCheckInDate)}`;
            console.log(`Res UID: ${nextResUID} with Check-in: ${nextCheckInDate} Found -- Setting service name to: ${svcName}`);
          } else {
            svcName = `${serviceType} STR Next Guest Unknown`;
            console.log(`No Res UID found -- Setting service name to: ${svcName}`);
          }
        }
        
        // Append Service Line Custom Instructions if present
        const serviceLineCustomInstructions = rec.fields['Service Line Custom Instructions'];
        if (serviceLineCustomInstructions && serviceLineCustomInstructions.trim()) {
          // Limit custom instructions length to prevent issues
          let customInstructions = serviceLineCustomInstructions.trim();
          const maxCustomLength = 200; // Leave room for base service name
          
          if (customInstructions.length > maxCustomLength) {
            customInstructions = customInstructions.substring(0, maxCustomLength - 3) + '...';
            console.log(`Truncated custom instructions from ${serviceLineCustomInstructions.length} to ${customInstructions.length} characters`);
          }
          
          svcName += ` - ${customInstructions}`;
          console.log(`Added custom instructions -- Final service name: ${svcName}`);
          console.log(`Final service name length: ${svcName.length} characters`);
        }
        
        // Get HCP IDs
        const custLinks = propRec.fields['HCP Customer ID'] || [];
        if (!custLinks.length) {
          console.log(`⚠️  Skipping - No HCP Customer ID`);
          errorCount++;
          continue;
        }
        
        const custId = custLinks[0];
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
        
        // Create HCP job
        const jobBody = {
          customer_id: custId,
          address_id: addrId,
          employee_ids: [HCP_EMPLOYEE_ID],
          schedule: {
            scheduled_start: finalTime,
            scheduled_end: new Date(new Date(finalTime).getTime() + 3 * 60 * 60 * 1000).toISOString()
          },
          work_status: 'scheduled'
        };
        
        const jobResp = await hcp('/jobs', 'POST', jobBody);
        const jobId = jobResp.id;
        
        console.log(`   ✅ Created job: ${jobId}`);
        
        // Copy template line items
        const templateItems = await hcp(`/jobs/${templateId}/line_items`);
        const lineItems = (templateItems.data || []).map((item, i) => ({
          name: i === 0 ? svcName : item.name,
          description: item.description || '',
          unit_price: item.unit_price,
          unit_cost: item.unit_cost,
          quantity: item.quantity,
          kind: item.kind,
          taxable: item.taxable,
          service_item_id: item.service_item_id || null
        }));
        
        if (lineItems.length > 0) {
          await hcp(`/jobs/${jobId}/line_items/bulk_update`, 'PUT', { line_items: lineItems });
          console.log(`   ✅ Updated ${lineItems.length} line items`);
        }
        
        // Update Airtable
        await base('Reservations').update(rec.id, {
          'Service Job ID': jobId,
          'Job Creation Time': new Date().toISOString(),
          'Job Status': 'Scheduled',
          'Sync Status': 'Synced',
          'Sync Date and Time': new Date().toISOString(),
          'Sync Details': `Created PROD job ${jobId} with service name: ${svcName}`
        });
        
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
    console.log(`❌ Errors: ${errorCount}`);
    console.log('\n⚠️  PRODUCTION sync completed ⚠️');
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  }
}

// Run the sync
syncMultipleJobs();