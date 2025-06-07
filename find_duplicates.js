const fs = require('fs');

// This script will collect all iTrip and Evolve records and find duplicates
class DuplicateFinder {
    constructor() {
        this.allRecords = [];
        this.duplicates = {};
        this.processedCount = 0;
    }

    // Simulate collecting records (we'll populate this manually from multiple API calls)
    addRecords(records) {
        this.allRecords.push(...records);
        this.processedCount += records.length;
        console.log(`Added ${records.length} records. Total: ${this.allRecords.length}`);
    }

    // Find duplicates based on Reservation UID
    findDuplicates() {
        const uidGroups = {};
        
        // Group records by Reservation UID
        this.allRecords.forEach(record => {
            const uid = record.fields['Reservation UID'];
            if (uid) {
                if (!uidGroups[uid]) {
                    uidGroups[uid] = [];
                }
                uidGroups[uid].push(record);
            }
        });

        // Find groups with more than one record (duplicates)
        Object.entries(uidGroups).forEach(([uid, records]) => {
            if (records.length > 1) {
                this.duplicates[uid] = records;
            }
        });

        return this.duplicates;
    }

    // Generate detailed report
    generateReport() {
        const duplicates = this.findDuplicates();
        const report = {
            summary: {
                totalRecordsProcessed: this.allRecords.length,
                totalUniqueUIDs: Object.keys(this.duplicates).length,
                totalDuplicateRecords: Object.values(this.duplicates).reduce((sum, group) => sum + group.length, 0),
                duplicateGroupsCount: Object.keys(this.duplicates).length
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
                    id: record.fields.ID,
                    entrySource: record.fields['Entry Source'],
                    status: record.fields.Status,
                    checkInDate: record.fields['Check-in Date'],
                    checkOutDate: record.fields['Check-out Date'],
                    propertyAddress: record.fields['HCP Address (from Property ID)'],
                    serviceType: record.fields['Service Type'],
                    lastUpdated: record.fields['Last Updated'],
                    finalServiceTime: record.fields['Final Service Time']
                }))
            };
        });

        return report;
    }

    // Save report to file
    saveReport(filename = 'duplicate_report.json') {
        const report = this.generateReport();
        fs.writeFileSync(filename, JSON.stringify(report, null, 2));
        console.log(`Report saved to ${filename}`);
        
        // Also save a CSV summary
        this.saveDuplicateRecordsList(`duplicate_records_list.csv`);
        
        return report;
    }

    // Save list of duplicate record IDs to CSV
    saveDuplicateRecordsList(filename) {
        const duplicates = this.findDuplicates();
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
}

// Export for use
module.exports = DuplicateFinder;

// If run directly, create instance for interactive use
if (require.main === module) {
    const finder = new DuplicateFinder();
    console.log('DuplicateFinder created. Use finder.addRecords(records) to add data.');
    global.finder = finder;
}