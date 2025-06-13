// Airtable Automation Script: Update Service Line Description
// Purpose: Builds the complete service line description including same-day, long-term guest, and custom instructions
// Updates: Service Line Description field
// Dependencies: Should run after find-next-guest-date.js
// Author: Automation System
// Last Updated: June 2025

// Get trigger record data
let inputConfig = input.config();
let recordId = inputConfig.recordId;

console.log("Processing record:", recordId);

// Get the table
let table = base.getTable("Reservations");

// Get the trigger record with all needed fields
let triggerRecord = await table.selectRecordAsync(recordId, {
    fields: ["Property ID", "Check-out Date", "Check-in Date", "Entry Type", "Status",
             "Service Type", "Same-day Turnover", "Custom Service Line Instructions", "Next Guest Date"]
});

// Get service type - use whatever is in the field, default to "Turnover" only if empty
let serviceTypeField = triggerRecord.getCellValue("Service Type");
let serviceType = serviceTypeField?.name || "Turnover";

// Check if it's same-day turnover
let sameDayTurnover = triggerRecord.getCellValue("Same-day Turnover");

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

// Build base service line description
let baseSvcName;

if (sameDayTurnover) {
    // Same day format
    baseSvcName = `${serviceType} STR SAME DAY`;
    console.log("Same-day turnover detected");
} else {
    // Check if we have Next Guest Date already calculated
    let nextGuestDate = triggerRecord.getCellValue("Next Guest Date");
    
    if (nextGuestDate) {
        // Use the pre-calculated Next Guest Date
        let date = new Date(nextGuestDate);
        let month = date.toLocaleString('en-US', { month: 'long' });
        let day = date.getDate();
        baseSvcName = `${serviceType} STR Next Guest ${month} ${day}`;
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
                           recEntryType?.name === "Reservation" &&
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
                let date = new Date(nextCheckIn);
                let month = date.toLocaleString('en-US', { month: 'long' });
                let day = date.getDate();
                baseSvcName = `${serviceType} STR Next Guest ${month} ${day}`;
                console.log("Next guest found:", month, day);
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

// Apply the same logic as the sync scripts
if (customInstructions && isLongTermGuest) {
    serviceLineDescription = `${customInstructions} - LONG TERM GUEST DEPARTING ${baseSvcName}`;
} else if (customInstructions && !isLongTermGuest) {
    serviceLineDescription = `${customInstructions} - ${baseSvcName}`;
} else if (!customInstructions && isLongTermGuest) {
    serviceLineDescription = `LONG TERM GUEST DEPARTING ${baseSvcName}`;
} else {
    serviceLineDescription = baseSvcName;
}

console.log("Service Type:", serviceType);
console.log("Base Service Name:", baseSvcName);
console.log("Is Long-term Guest:", isLongTermGuest);
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