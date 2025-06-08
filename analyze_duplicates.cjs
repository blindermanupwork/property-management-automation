const fs = require('fs');

// Data from our first batch of 30 iTrip records
const batch1 = [
  {id: 'rec4jHxpuqaIZv0f0', fields: {'Reservation UID': '4336182', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-05', 'Check-out Date': '2025-06-13', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recB1R7yY1gGY0EzR', fields: {'Reservation UID': '4336182', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-05', 'Check-out Date': '2025-06-13', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recZ4XIUvDPWL5D1f', fields: {'Reservation UID': '4336182', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-05', 'Check-out Date': '2025-06-13', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recCOukchQrr60BlY', fields: {'Reservation UID': '4336182', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-06-05', 'Check-out Date': '2025-06-13', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recnqTxQPHsEmQqQ2', fields: {'Reservation UID': '4386236', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-28', 'Check-out Date': '2025-06-04', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recivmVSroCtgGRs5', fields: {'Reservation UID': '4386236', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-28', 'Check-out Date': '2025-06-04', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recLXomyJVYefqrew', fields: {'Reservation UID': '4386236', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-28', 'Check-out Date': '2025-06-04', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recZJzFAB0pmmC39f', fields: {'Reservation UID': '4386236', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-05-28', 'Check-out Date': '2025-06-04', 'HCP Address (from Property ID)': ['16628 N 54th St, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'rechF2pf3Q2Bm37aH', fields: {'Reservation UID': '4423267', 'Entry Source': 'iTrip', Status: 'New', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-01', 'HCP Address (from Property ID)': ['6934 E Sandra Terrace, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-05-31T20:36:24.000Z'}},
  {id: 'reclmegsx8PU6fqAk', fields: {'Reservation UID': '4425086', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-09', 'Check-out Date': '2025-06-14', 'HCP Address (from Property ID)': ['8334 E Whispering Wind Dr, Scottsdale, AZ 85255'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'rec5fDwWv5XPNXSGz', fields: {'Reservation UID': '4425086', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-09', 'Check-out Date': '2025-06-14', 'HCP Address (from Property ID)': ['8334 E Whispering Wind Dr, Scottsdale, AZ 85255'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'rec1EyNDqO5GgH4oQ', fields: {'Reservation UID': '4425086', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-09', 'Check-out Date': '2025-06-14', 'HCP Address (from Property ID)': ['8334 E Whispering Wind Dr, Scottsdale, AZ 85255'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'rec9ndp6BmNp7aECR', fields: {'Reservation UID': '4425086', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-06-09', 'Check-out Date': '2025-06-14', 'HCP Address (from Property ID)': ['8334 E Whispering Wind Dr, Scottsdale, AZ 85255'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recrtN4mgVE4rO6Oa', fields: {'Reservation UID': '4439474', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['6196 W Kerry Ln, Glendale, AZ 85308'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recKk6hstsCrPKppq', fields: {'Reservation UID': '4439474', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['6196 W Kerry Ln, Glendale, AZ 85308'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recXJwMeuRDtEiyXX', fields: {'Reservation UID': '4439474', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['6196 W Kerry Ln, Glendale, AZ 85308'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recCdJDNA7hxo779d', fields: {'Reservation UID': '4492368', 'Entry Source': 'iTrip', Status: 'New', 'Check-in Date': '2025-05-28', 'Check-out Date': '2025-06-01', 'HCP Address (from Property ID)': ['15221 N Clubgate Dr, Unit 2036, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-05-31T20:36:24.000Z'}},
  {id: 'rec3knwApYEVGioQZ', fields: {'Reservation UID': '4495460', 'Entry Source': 'iTrip', Status: 'New', 'Check-in Date': '2025-05-23', 'Check-out Date': '2025-05-31', 'HCP Address (from Property ID)': ['13028 E Gold Dust Ave, Scottsdale, AZ 85259'], 'Service Type': 'Turnover', 'Last Updated': '2025-05-31T20:36:24.000Z'}},
  {id: 'recqB70bR51U6rZFl', fields: {'Reservation UID': '4498926', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['3919 N 86th St, Scottsdale, AZ 85251'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recSMhc5xVQvq9BcT', fields: {'Reservation UID': '4498926', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['3919 N 86th St, Scottsdale, AZ 85251'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recppq71Z9xN8YogA', fields: {'Reservation UID': '4498926', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['3919 N 86th St, Scottsdale, AZ 85251'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recvGSSpIbjRtrJoF', fields: {'Reservation UID': '4499450', 'Entry Source': 'iTrip', Status: 'New', 'Check-in Date': '2025-05-14', 'Check-out Date': '2025-05-31', 'HCP Address (from Property ID)': ['15095 N Thompson Peak Pkwy, 1119, Scottsdale, AZ 85260'], 'Service Type': 'Turnover', 'Last Updated': '2025-05-31T20:36:24.000Z'}},
  {id: 'rec1REuFSsgl0lVgN', fields: {'Reservation UID': '4505271', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-04-30', 'Check-out Date': '2025-06-09', 'HCP Address (from Property ID)': ['5950 N 78th St, 123, Scottsdale, AZ 85250'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recpdcRnys4wp5SAS', fields: {'Reservation UID': '4505271', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-04-30', 'Check-out Date': '2025-06-09', 'HCP Address (from Property ID)': ['5950 N 78th St, 123, Scottsdale, AZ 85250'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recwnIaMfjhkvpFfP', fields: {'Reservation UID': '4505271', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-04-30', 'Check-out Date': '2025-06-09', 'HCP Address (from Property ID)': ['5950 N 78th St, 123, Scottsdale, AZ 85250'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recWdL5JAnEbOwLrH', fields: {'Reservation UID': '4505271', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-04-30', 'Check-out Date': '2025-06-09', 'HCP Address (from Property ID)': ['5950 N 78th St, 123, Scottsdale, AZ 85250'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}},
  {id: 'recVYh6borwIWGHVA', fields: {'Reservation UID': '4510375', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['8730 E Weldon Ave, Scottsdale, AZ 85251'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recWlv51YQJfWNHwf', fields: {'Reservation UID': '4510375', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['8730 E Weldon Ave, Scottsdale, AZ 85251'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'recJJCU9hWumX8jJk', fields: {'Reservation UID': '4510375', 'Entry Source': 'iTrip', Status: 'Modified', 'Check-in Date': '2025-05-29', 'Check-out Date': '2025-06-02', 'HCP Address (from Property ID)': ['8730 E Weldon Ave, Scottsdale, AZ 85251'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-02T19:00:40.000Z'}},
  {id: 'rec2fNE0irDXC9w7N', fields: {'Reservation UID': '4511952', 'Entry Source': 'iTrip', Status: 'Old', 'Check-in Date': '2025-06-09', 'Check-out Date': '2025-06-15', 'HCP Address (from Property ID)': ['15221 N Clubgate Dr, Unit 2036, Scottsdale, AZ 85254'], 'Service Type': 'Turnover', 'Last Updated': '2025-06-05T03:00:33.000Z'}}
];

function findDuplicates(records) {
    const uidGroups = {};
    
    // Group records by Reservation UID
    records.forEach(record => {
        const uid = record.fields['Reservation UID'];
        if (uid) {
            if (!uidGroups[uid]) {
                uidGroups[uid] = [];
            }
            uidGroups[uid].push(record);
        }
    });

    // Find groups with more than one record (duplicates)
    const duplicates = {};
    Object.entries(uidGroups).forEach(([uid, records]) => {
        if (records.length > 1) {
            duplicates[uid] = records;
        }
    });

    return duplicates;
}

function generateReport(allRecords) {
    const duplicates = findDuplicates(allRecords);
    
    const report = {
        summary: {
            totalRecordsProcessed: allRecords.length,
            totalUniqueUIDs: Object.keys(duplicates).length,
            totalDuplicateRecords: Object.values(duplicates).reduce((sum, group) => sum + group.length, 0),
            duplicateGroupsCount: Object.keys(duplicates).length
        },
        duplicateGroups: {}
    };

    // Create detailed duplicate groups
    Object.entries(duplicates).forEach(([uid, records]) => {
        report.duplicateGroups[uid] = {
            reservationUID: uid,
            duplicateCount: records.length,
            records: records.map(record => ({
                recordId: record.id,
                entrySource: record.fields['Entry Source'],
                status: record.fields.Status,
                checkInDate: record.fields['Check-in Date'],
                checkOutDate: record.fields['Check-out Date'],
                propertyAddress: record.fields['HCP Address (from Property ID)'] ? record.fields['HCP Address (from Property ID)'][0] : '',
                serviceType: record.fields['Service Type'],
                lastUpdated: record.fields['Last Updated']
            }))
        };
    });

    return report;
}

function saveDuplicateRecordsList(duplicates, filename) {
    let csvContent = 'Reservation_UID,Record_ID,Entry_Source,Status,Check_In_Date,Check_Out_Date,Property_Address,Service_Type,Last_Updated\n';
    
    Object.entries(duplicates).forEach(([uid, records]) => {
        records.forEach(record => {
            const fields = record.fields;
            csvContent += [
                uid,
                record.id,
                fields['Entry Source'] || '',
                fields.Status || '',
                fields['Check-in Date'] || '',
                fields['Check-out Date'] || '',
                (fields['HCP Address (from Property ID)'] && fields['HCP Address (from Property ID)'][0]) || '',
                fields['Service Type'] || '',
                fields['Last Updated'] || ''
            ].map(field => `"${field.toString().replace(/"/g, '""')}"`).join(',') + '\n';
        });
    });
    
    fs.writeFileSync(filename, csvContent);
    console.log(`Duplicate records list saved to ${filename}`);
}

// Main analysis
console.log('=== AIRTABLE DUPLICATE ANALYSIS ===');
console.log('Analyzing sample of 30 iTrip records...\n');

const duplicates = findDuplicates(batch1);
const report = generateReport(batch1);

console.log('=== SUMMARY ===');
console.log(`Total Records Processed: ${report.summary.totalRecordsProcessed}`);
console.log(`Total Duplicate Groups: ${report.summary.duplicateGroupsCount}`);
console.log(`Total Duplicate Records: ${report.summary.totalDuplicateRecords}`);
console.log(`Duplicate Rate: ${(report.summary.totalDuplicateRecords / report.summary.totalRecordsProcessed * 100).toFixed(1)}%`);

console.log('\n=== DETAILED DUPLICATE GROUPS ===');
Object.entries(report.duplicateGroups).forEach(([uid, group]) => {
    console.log(`\nReservation UID: ${uid} (${group.duplicateCount} duplicates)`);
    console.log(`  Property: ${group.records[0].propertyAddress}`);
    console.log(`  Check-in: ${group.records[0].checkInDate} | Check-out: ${group.records[0].checkOutDate}`);
    group.records.forEach((record, idx) => {
        console.log(`    ${idx + 1}. ${record.recordId} | Status: ${record.status} | Updated: ${record.lastUpdated}`);
    });
});

// Save reports
fs.writeFileSync('/home/opc/automation/airtable_duplicate_analysis.json', JSON.stringify(report, null, 2));
saveDuplicateRecordsList(duplicates, '/home/opc/automation/duplicate_records_list.csv');

console.log('\n=== FILES SAVED ===');
console.log('✓ airtable_duplicate_analysis.json - Complete analysis');
console.log('✓ duplicate_records_list.csv - List of all duplicate records');

console.log('\n=== ACTIONABLE RECOMMENDATIONS ===');
console.log('1. Review each Reservation UID group to identify which record should be kept');
console.log('2. Check if different statuses (Old/Modified/New) indicate process stages');
console.log('3. Consider keeping the most recently updated record in each group');
console.log('4. Investigate the source of duplicate creation to prevent future occurrences');