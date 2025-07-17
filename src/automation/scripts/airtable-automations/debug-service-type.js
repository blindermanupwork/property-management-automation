// Debug script to understand Service Type field issues
let inputConfig = input.config();
let recordId = inputConfig.recordId;

console.log("=== DEBUG START ===");
console.log("Input Record ID:", recordId);

// Get the table
let table = base.getTable("Reservations");

// Method 1: Query specific record
console.log("\n--- Method 1: Query Specific Record ---");
let query1 = await table.selectRecordsAsync({
    fields: ["ID", "Service Type", "Reservation UID"],
    recordIds: [recordId]
});
let record1 = query1.records[0];
if (record1) {
    console.log("Record found:", record1.id);
    console.log("ID field:", record1.getCellValue("ID"));
    console.log("Service Type raw:", record1.getCellValue("Service Type"));
    console.log("Service Type JSON:", JSON.stringify(record1.getCellValue("Service Type")));
}

// Method 2: Query all and filter
console.log("\n--- Method 2: Query All and Filter ---");
let query2 = await table.selectRecordsAsync({
    fields: ["ID", "Service Type", "Reservation UID"]
});
let record2 = query2.records.find(r => r.id === recordId);
if (record2) {
    console.log("Record found via filter:", record2.id);
    console.log("ID field:", record2.getCellValue("ID"));
    console.log("Service Type raw:", record2.getCellValue("Service Type"));
    console.log("Service Type JSON:", JSON.stringify(record2.getCellValue("Service Type")));
}

// Method 3: Check field configuration
console.log("\n--- Field Configuration ---");
let fields = table.fields;
let serviceTypeField = fields.find(f => f.name === "Service Type");
if (serviceTypeField) {
    console.log("Field ID:", serviceTypeField.id);
    console.log("Field Type:", serviceTypeField.type);
    console.log("Field Config:", JSON.stringify(serviceTypeField.config));
    
    // If it's a single select, show options
    if (serviceTypeField.options && serviceTypeField.options.choices) {
        console.log("Available choices:");
        serviceTypeField.options.choices.forEach(choice => {
            console.log(`  - ${choice.name} (${choice.id})`);
        });
    }
}

// Method 4: Try getting by field ID
console.log("\n--- Direct Field Access ---");
if (record1 && serviceTypeField) {
    let cellValue = record1.getCellValueAsString(serviceTypeField.id);
    console.log("Service Type via field ID:", cellValue);
}

console.log("\n=== DEBUG END ===");

output.set('success', true);
output.set('recordId', recordId);
output.set('serviceType', record1 ? record1.getCellValue("Service Type") : null);