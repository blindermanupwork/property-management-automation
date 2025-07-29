// Airtable Automation Script: Find Next Guest Date
// Purpose: Finds the next guest checking in at the same property and determines if it's a same-day turnover
// Updates: Next Guest Date field and Same-day Turnover checkbox
// Author: Automation System
// Last Updated: July 2025
//
// Note: When an owner is arriving (block checking in same/next day), we do NOT mark it as
// same-day turnover to prevent creating modified records when syncing. The Final Service Time
// should be set to 10:00 AM for owner arrivals (vs 10:15 AM default) via an Airtable formula.

// Get trigger record data
let inputConfig = input.config();
let recordId = inputConfig.recordId;

console.log("Starting script for record:", recordId);

// Get the table
let table = base.getTable("Reservations");

// In Airtable automations, we need to query all records and find the one we want
// This is the standard pattern for automation scripts
let query = await table.selectRecordsAsync({
    fields: ["Check-out Date", "Check-in Date", "Property ID", "Entry Type", "Status", "Reservation UID", "Same-day Turnover", "Next Guest Date", "Next Entry Is Block", "iTrip Next Guest Date", "Entry Source"]
});

// Find our trigger record
let triggerRecord = query.records.find(record => record.id === recordId);

if (!triggerRecord) {
    console.log("Error: Record not found with ID:", recordId);
    output.set('success', false);
    throw new Error("Record not found");
}

// Get dates
let checkOutDate = triggerRecord.getCellValue("Check-out Date");
let checkInDate = triggerRecord.getCellValue("Check-in Date");

console.log("Check-out date:", checkOutDate);
console.log("Check-in date:", checkInDate);

if (!checkOutDate) {
    console.log("No check-out date available");
    output.set('success', false);
    return;
}

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

// Get property ID
let propertyLinkedRecords = triggerRecord.getCellValue("Property ID");
if (!propertyLinkedRecords || propertyLinkedRecords.length === 0) {
    console.log("No property linked");
    output.set('success', false);
    return;
}

let propertyRecordId = propertyLinkedRecords[0].id;
console.log("Property record ID:", propertyRecordId);

// Check if this is an iTrip reservation with next guest date
let iTripNextGuestDate = triggerRecord.getCellValue("iTrip Next Guest Date");
let entrySource = triggerRecord.getCellValue("Entry Source");

// If this is an iTrip reservation with next guest date, use it directly
if (entrySource && entrySource.name === "iTrip" && iTripNextGuestDate) {
    // Use iTrip's provided date
    let nextGuestDate = iTripNextGuestDate;
    
    // Still calculate same-day turnover
    const checkOutDateObj = new Date(checkOutDate);
    const nextCheckInDateObj = new Date(iTripNextGuestDate);
    
    checkOutDateObj.setHours(0, 0, 0, 0);
    nextCheckInDateObj.setHours(0, 0, 0, 0);
    
    let isSameDayTurnover = checkOutDateObj.getTime() === nextCheckInDateObj.getTime();
    
    console.log("Using iTrip provided next guest date:", iTripNextGuestDate);
    console.log("Same-day turnover:", isSameDayTurnover);
    
    // Update the record with iTrip data
    try {
        await table.updateRecordAsync(recordId, {
            "Next Guest Date": nextGuestDate,
            "Same-day Turnover": isSameDayTurnover,
            "Next Entry Is Block": false,  // iTrip next booking is always a guest
            "Owner Arriving": false
        });
    } catch (e) {
        // If that fails, try without new fields
        console.log("Failed to update with new fields, trying without:", e.message);
        await table.updateRecordAsync(recordId, {
            "Next Guest Date": nextGuestDate,
            "Same-day Turnover": isSameDayTurnover
        });
    }
    
    output.set('success', true);
    output.set('nextGuestDate', nextGuestDate);
    output.set('isLongTermGuest', isLongTermGuest);
    output.set('stayDurationDays', stayDurationDays);
    output.set('isSameDayTurnover', isSameDayTurnover);
    output.set('isNextEntryBlock', false);
    return;  // Exit early since we used iTrip data
}

// Query ALL records
query = await table.selectRecordsAsync({
    fields: ["Property ID", "Check-in Date", "Entry Type", "Status", "Reservation UID"]
});

// Filter for this property's records
let propertyRecords = query.records.filter(record => {
    let recPropertyId = record.getCellValue("Property ID");
    if (!recPropertyId || recPropertyId.length === 0) return false;
    return recPropertyId[0].id === propertyRecordId;
});

console.log("Records for this property:", propertyRecords.length);

// Filter for next reservations AND blocks
let nextEntries = propertyRecords.filter(record => {
    if (record.id === recordId) return false;
    
    let recEntryType = record.getCellValue("Entry Type");
    if (!recEntryType || (recEntryType.name !== "Reservation" && recEntryType.name !== "Block")) return false;
    
    let recStatus = record.getCellValue("Status");
    if (recStatus && recStatus.name === "Old") return false;
    
    let recCheckIn = record.getCellValue("Check-in Date");
    if (!recCheckIn) return false;
    
    // Use >= to include same-day check-ins
    return new Date(recCheckIn) >= new Date(checkOutDate);
});

console.log("Found next entries (reservations + blocks):", nextEntries.length);

// Sort by check-in date
nextEntries.sort((a, b) => {
    let dateA = new Date(a.getCellValue("Check-in Date"));
    let dateB = new Date(b.getCellValue("Check-in Date"));
    return dateA - dateB;
});

// Get the next guest info
let nextGuestDate = null;
let isSameDayTurnover = false;
let isNextEntryBlock = false;

if (nextEntries.length > 0) {
    nextGuestDate = nextEntries[0].getCellValue("Check-in Date");
    let nextEntryType = nextEntries[0].getCellValue("Entry Type");
    let isBlock = nextEntryType && nextEntryType.name === "Block";
    
    // Check same-day
    const checkOutDateObj = new Date(checkOutDate);
    const nextCheckInDateObj = new Date(nextGuestDate);
    
    checkOutDateObj.setHours(0, 0, 0, 0);
    nextCheckInDateObj.setHours(0, 0, 0, 0);
    
    // Check if dates are the same
    const datesAreSame = checkOutDateObj.getTime() === nextCheckInDateObj.getTime();
    
    // Only mark as same-day turnover if it's NOT an owner arrival
    // Owner arrivals should not be marked as same-day to avoid creating modified records
    isSameDayTurnover = datesAreSame && !isBlock;
    
    // Calculate days between checkout and next checkin
    const daysBetween = Math.floor((nextCheckInDateObj - checkOutDateObj) / (1000 * 60 * 60 * 24));
    
    // Only set isNextEntryBlock if it's a block AND checking in same day or next day
    if (isBlock && daysBetween <= 1) {
        isNextEntryBlock = true;
        console.log("Next entry is a BLOCK checking in within 1 day (owner arriving)");
    } else if (isBlock) {
        console.log(`Next entry is a BLOCK but checking in ${daysBetween} days later (not owner arriving)`);
    } else {
        let nextUID = nextEntries[0].getCellValue("Reservation UID");
        console.log("Next guest UID:", nextUID);
    }
    
    console.log("Next entry check-in:", nextGuestDate);
    console.log("Same-day turnover:", isSameDayTurnover);
}

// Update the record
try {
    // Try to update with all fields including Next Entry Is Block and Owner Arriving
    await table.updateRecordAsync(recordId, {
        "Next Guest Date": nextGuestDate,
        "Same-day Turnover": isSameDayTurnover,
        "Next Entry Is Block": isNextEntryBlock,
        "Owner Arriving": isNextEntryBlock  // Set checkbox based on block detection
    });
} catch (e) {
    // If that fails, try without new fields
    console.log("Failed to update with new fields, trying without:", e.message);
    await table.updateRecordAsync(recordId, {
        "Next Guest Date": nextGuestDate,
        "Same-day Turnover": isSameDayTurnover
    });
}

output.set('success', true);
output.set('nextGuestDate', nextGuestDate);
output.set('isLongTermGuest', isLongTermGuest);
output.set('stayDurationDays', stayDurationDays);
output.set('isSameDayTurnover', isSameDayTurnover);
output.set('isNextEntryBlock', isNextEntryBlock);