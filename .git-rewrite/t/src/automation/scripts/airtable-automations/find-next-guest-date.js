// Airtable Automation Script: Find Next Guest Date
// Purpose: Finds the next guest checking in at the same property and determines if it's a same-day turnover
// Updates: Next Guest Date field and Same-day Turnover checkbox
// Author: Automation System
// Last Updated: June 2025

// Get trigger record data
let inputConfig = input.config();
let recordId = inputConfig.recordId;

console.log("Starting script for record:", recordId);

// Get the table
let table = base.getTable("Reservations");

// Get the trigger record
let triggerRecord = await table.selectRecordAsync(recordId);

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

// Query ALL records
let query = await table.selectRecordsAsync({
    fields: ["Property ID", "Check-in Date", "Entry Type", "Status", "Reservation UID"]
});

// Filter for this property's records
let propertyRecords = query.records.filter(record => {
    let recPropertyId = record.getCellValue("Property ID");
    if (!recPropertyId || recPropertyId.length === 0) return false;
    return recPropertyId[0].id === propertyRecordId;
});

console.log("Records for this property:", propertyRecords.length);

// Filter for next reservations - FIXED to use >= instead of >
let nextReservations = propertyRecords.filter(record => {
    if (record.id === recordId) return false;
    
    let recEntryType = record.getCellValue("Entry Type");
    if (!recEntryType || recEntryType.name !== "Reservation") return false;
    
    let recStatus = record.getCellValue("Status");
    if (recStatus && recStatus.name === "Old") return false;
    
    let recCheckIn = record.getCellValue("Check-in Date");
    if (!recCheckIn) return false;
    
    // Use >= to include same-day check-ins
    return new Date(recCheckIn) >= new Date(checkOutDate);
});

console.log("Found next reservations:", nextReservations.length);

// Sort by check-in date
nextReservations.sort((a, b) => {
    let dateA = new Date(a.getCellValue("Check-in Date"));
    let dateB = new Date(b.getCellValue("Check-in Date"));
    return dateA - dateB;
});

// Get the next guest info
let nextGuestDate = null;
let isSameDayTurnover = false;

if (nextReservations.length > 0) {
    nextGuestDate = nextReservations[0].getCellValue("Check-in Date");
    let nextUID = nextReservations[0].getCellValue("Reservation UID");
    console.log("Next guest check-in:", nextGuestDate);
    console.log("Next guest UID:", nextUID);
    
    // Check same-day
    const checkOutDateObj = new Date(checkOutDate);
    const nextCheckInDateObj = new Date(nextGuestDate);
    
    checkOutDateObj.setHours(0, 0, 0, 0);
    nextCheckInDateObj.setHours(0, 0, 0, 0);
    
    isSameDayTurnover = checkOutDateObj.getTime() === nextCheckInDateObj.getTime();
    console.log("Same-day turnover:", isSameDayTurnover);
}

// Update the record
await table.updateRecordAsync(recordId, {
    "Next Guest Date": nextGuestDate,
    "Same-day Turnover": isSameDayTurnover
});

output.set('success', true);
output.set('nextGuestDate', nextGuestDate);
output.set('isLongTermGuest', isLongTermGuest);
output.set('stayDurationDays', stayDurationDays);
output.set('isSameDayTurnover', isSameDayTurnover);