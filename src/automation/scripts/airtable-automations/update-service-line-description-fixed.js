// Airtable Automation Script: Update Service Line Description
// Purpose: Builds the complete service line description including same-day, long-term guest, and custom instructions
// Updates: Service Line Description field
// Dependencies: Should run after find-next-guest-date.js
// Author: Automation System
// Last Updated: July 2025 - Fixed to match codebase logic

// Get trigger record data
let inputConfig = input.config();
let recordId = inputConfig.recordId;

console.log("Processing record:", recordId);

// Get the table
let table = base.getTable("Reservations");

// In Airtable automations, we need to query all records and find the one we want
// Query with the fields we need
let query = await table.selectRecordsAsync({
    fields: ["Service Type", "Same-day Turnover", "Next Entry Is Block", "Custom Service Line Instructions", 
             "Check-in Date", "Check-out Date", "Next Guest Date", "Property ID", "Entry Type", "Status", "Reservation UID"]
});

// Find our trigger record
let triggerRecord = query.records.find(record => record.id === recordId);

// Check if record was found
if (!triggerRecord) {
    console.log("Error: Record not found with ID:", recordId);
    output.set('success', false);
    output.set('error', 'Record not found');
    throw new Error("Record not found");
}

// Get service type - use whatever is in the field, default to "Turnover" only if empty
let serviceTypeField = triggerRecord.getCellValue("Service Type");
let serviceType = serviceTypeField?.name || "Turnover";

// Check if it's same-day turnover
let sameDayTurnover = triggerRecord.getCellValue("Same-day Turnover");

// Check if owner is arriving (from checkbox)
// Try both the checkbox and the text field for backward compatibility
let isOwnerArriving = false;
try {
    // First try the new checkbox field
    isOwnerArriving = triggerRecord.getCellValue("Owner Arriving") || false;
} catch (e) {
    console.log("Owner Arriving checkbox not found, trying Next Entry Is Block field");
    try {
        // Fall back to the text field
        isOwnerArriving = triggerRecord.getCellValue("Next Entry Is Block") || false;
    } catch (e2) {
        console.log("Next Entry Is Block field not found, defaulting to false");
    }
}

// Get custom instructions
let customInstructions = triggerRecord.getCellValue("Custom Service Line Instructions");

// Get dates for long-term guest check
let checkInDate = triggerRecord.getCellValue("Check-in Date");
let checkOutDate = triggerRecord.getCellValue("Check-out Date");

// Calculate if long-term guest
let isLongTermGuest = false;
let stayDurationDays = 0;
if (checkInDate && checkOutDate) {
    const checkIn = new Date(checkInDate);
    const checkOut = new Date(checkOutDate);
    stayDurationDays = (checkOut - checkIn) / (1000 * 60 * 60 * 24);

    if (stayDurationDays >= 14) {
        isLongTermGuest = true;
        console.log(`Long-term guest detected - ${stayDurationDays} days stay`);
    }
}

// Build base service line description - FIXED TO MATCH CODEBASE
let baseSvcName;

if (sameDayTurnover) {
    // FIXED: Same day format - "SAME DAY" comes first
    baseSvcName = `SAME DAY ${serviceType} STR`;
    console.log("Same-day turnover detected");
} else {
    // Check if we have Next Guest Date already calculated
    let nextGuestDate = triggerRecord.getCellValue("Next Guest Date");
    
    if (nextGuestDate) {
        // Use the pre-calculated Next Guest Date
        let date = new Date(nextGuestDate);
        let month = date.toLocaleString('en-US', { month: 'long' });
        let day = date.getDate();
        
        // FIXED: Check if owner is arriving and format accordingly
        if (isOwnerArriving) {
            baseSvcName = `OWNER ARRIVING ${serviceType} STR ${month} ${day}`;
            console.log("Owner arriving - including in base service name");
        } else {
            baseSvcName = `${serviceType} STR Next Guest ${month} ${day}`;
        }
        console.log("Using pre-calculated next guest date:", month, day);
    } else {
        // Fallback: find next guest manually (shouldn't happen if first script runs properly)
        if (!checkOutDate) {
            baseSvcName = `${serviceType} STR Next Guest Unknown`;
        } else {
            // Get property ID
            let propertyLinkedRecords = triggerRecord.getCellValue("Property ID");
            let propertyRecordId = propertyLinkedRecords && propertyLinkedRecords.length > 0
                ? propertyLinkedRecords[0].id
                : null;

            // Query all records to find next guest
            let query = await table.selectRecordsAsync({
                fields: ["Property ID", "Check-in Date", "Entry Type", "Status", "Reservation UID"]
            });

            // Filter for next reservations - FIXED to use >= for same-day detection
            let nextReservations = query.records
                .filter(record => {
                    if (record.id === recordId) return false;

                    let recPropertyId = record.getCellValue("Property ID");
                    let recCheckIn = record.getCellValue("Check-in Date");
                    let recEntryType = record.getCellValue("Entry Type");
                    let recStatus = record.getCellValue("Status");

                    let recPropId = recPropertyId && recPropertyId.length > 0 ? recPropertyId[0].id : null;

                    return recPropId === propertyRecordId &&
                           recCheckIn && new Date(recCheckIn) >= new Date(checkOutDate) &&
                           recStatus?.name !== "Old";
                })
                .sort((a, b) => {
                    let dateA = new Date(a.getCellValue("Check-in Date"));
                    let dateB = new Date(b.getCellValue("Check-in Date"));
                    return dateA - dateB;
                });

            // Build description based on whether we found a next guest
            if (nextReservations.length > 0) {
                let nextCheckIn = nextReservations[0].getCellValue("Check-in Date");
                let nextEntryType = nextReservations[0].getCellValue("Entry Type");
                let isBlock = nextEntryType?.name === "Block";
                
                let date = new Date(nextCheckIn);
                let month = date.toLocaleString('en-US', { month: 'long' });
                let day = date.getDate();
                
                // FIXED: Include OWNER ARRIVING in base name when next entry is block
                if (isBlock) {
                    baseSvcName = `OWNER ARRIVING ${serviceType} STR ${month} ${day}`;
                    console.log("Next entry is a block (owner arriving)");
                } else {
                    baseSvcName = `${serviceType} STR Next Guest ${month} ${day}`;
                    console.log("Next guest found:", month, day);
                }
            } else {
                baseSvcName = `${serviceType} STR Next Guest Unknown`;
                console.log("No next guest found");
            }
        }
    }
}

// Build final service line description with custom instructions and long-term guest logic
let serviceLineDescription;

// Trim and limit custom instructions length
if (customInstructions && customInstructions.trim()) {
    customInstructions = customInstructions.trim();
    const maxCustomLength = 200;

    if (customInstructions.length > maxCustomLength) {
        customInstructions = customInstructions.substring(0, maxCustomLength - 3) + '...';
        console.log(`Truncated custom instructions to ${maxCustomLength} characters`);
    }
}

// FIXED: Build service line description matching codebase hierarchy:
// 1. Custom Instructions
// 2. LONG TERM GUEST DEPARTING (if stay >= 14 days AND owner is NOT already in base name)
// 3. Base service name (which may already include OWNER ARRIVING)

let parts = [];

// Add custom instructions if present
if (customInstructions) {
    parts.push(customInstructions);
}

// FIXED: Only add LONG TERM GUEST DEPARTING if owner is NOT already in the base name
// This matches the codebase logic where OWNER ARRIVING is part of baseSvcName
if (isLongTermGuest && !baseSvcName.includes("OWNER ARRIVING")) {
    parts.push("LONG TERM GUEST DEPARTING");
}

// Add base service name
parts.push(baseSvcName);

// Join all parts with " - " if there are multiple parts, otherwise just use the single part
if (parts.length > 1) {
    serviceLineDescription = parts.join(" - ");
} else {
    serviceLineDescription = parts[0];
}

console.log("Service Type:", serviceType);
console.log("Base Service Name:", baseSvcName);
console.log("Is Long-term Guest:", isLongTermGuest);
console.log("Is Owner Arriving:", isOwnerArriving);
console.log("Custom Instructions:", customInstructions);
console.log("Final Service Line Description:", serviceLineDescription);

// Update the record
await table.updateRecordAsync(recordId, {
    "Service Line Description": serviceLineDescription
});

output.set('success', true);
output.set('serviceLineDescription', serviceLineDescription);
output.set('isLongTermGuest', isLongTermGuest);
output.set('stayDurationDays', stayDurationDays);