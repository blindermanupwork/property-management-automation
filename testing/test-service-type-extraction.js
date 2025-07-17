// Test script to verify Service Type extraction logic
// This simulates how Airtable single select fields work

console.log("Testing Service Type extraction logic...\n");

// Test cases simulating different field structures
const testCases = [
    {
        name: "Single Select Object (normal case)",
        field: { id: "sel123", name: "Initial Service", color: "blue" },
        expected: "Initial Service"
    },
    {
        name: "String value",
        field: "Deep Clean",
        expected: "Deep Clean"
    },
    {
        name: "Object with value property",
        field: { value: "Inspection" },
        expected: "Inspection"
    },
    {
        name: "Null field",
        field: null,
        expected: "Turnover"
    },
    {
        name: "Undefined field",
        field: undefined,
        expected: "Turnover"
    },
    {
        name: "Empty object",
        field: {},
        expected: "Turnover"
    }
];

// Run tests
testCases.forEach(test => {
    console.log(`Test: ${test.name}`);
    console.log(`Input:`, test.field);
    
    // This is the logic from update-service-line-description.js
    let serviceTypeField = test.field;
    let serviceType = "Turnover"; // default
    if (serviceTypeField) {
        if (typeof serviceTypeField === 'string') {
            serviceType = serviceTypeField;
        } else if (serviceTypeField.name) {
            serviceType = serviceTypeField.name;
        } else if (serviceTypeField.value) {
            serviceType = serviceTypeField.value;
        }
    }
    
    console.log(`Result: "${serviceType}"`);
    console.log(`Expected: "${test.expected}"`);
    console.log(`✅ Pass:`, serviceType === test.expected);
    console.log("---\n");
});

// Test service line generation
console.log("\nTesting complete service line generation:");

const serviceTypes = ["Initial Service", "Deep Clean", "Inspection", "Return Laundry", "Turnover"];
const scenarios = [
    { name: "Regular", sameDay: false, ownerArriving: false },
    { name: "Same Day", sameDay: true, ownerArriving: false },
    { name: "Owner Arriving", sameDay: false, ownerArriving: true }
];

scenarios.forEach(scenario => {
    console.log(`\n${scenario.name} scenario:`);
    serviceTypes.forEach(serviceType => {
        let baseSvcName;
        if (scenario.sameDay) {
            baseSvcName = `SAME DAY ${serviceType} STR`;
        } else if (scenario.ownerArriving) {
            baseSvcName = `OWNER ARRIVING ${serviceType} STR July 10`;
        } else {
            baseSvcName = `${serviceType} STR Next Guest July 10`;
        }
        console.log(`  ${serviceType}: ${baseSvcName}`);
    });
});