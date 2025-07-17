# Reporting & Analytics - Business Logic A-Z

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Complete alphabetical documentation of reporting and analytics business rules and implementation

---

## 🎯 **BUSINESS RULES BY ALPHABETICAL ORDER**

### **A - Average Value Calculations**

**Condition**: When calculating average job values or service prices  
**Action**: Divide total revenue by count with zero-check protection  
**Implementation**: 
```typescript
// From bulletproofAnalysisService.ts
averageJobValue: totalLaundry > 0 ? totalRevenue / totalLaundry : 0,
averagePrice: totalQuantity > 0 ? totalRevenue / totalQuantity : 0,
```
**Exception**: Returns 0 instead of infinity/NaN when dividing by zero  
**Business Impact**: Prevents dashboard errors and provides meaningful default values

### **B - Bulletproof Analysis Architecture**

**Condition**: When performing any HCP data analysis  
**Action**: Use native TypeScript processing with multiple fallback strategies  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
async analyzeLaundryJobs() {
    const startTime = Date.now();
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
        const cacheFiles = await this.findValidCacheFiles(jobsDir);
        if (cacheFiles.length === 0) {
            throw new Error('No valid cached job files found. Run list_jobs first to populate cache.');
        }
        
        // Process each file with robust error handling
        for (const filePath of cacheFiles) {
            try {
                const fileContent = await fs.readFile(filePath, 'utf8');
                const data = JSON.parse(fileContent);
                const jobs = data.data || data.jobs || data;
                filesProcessed++;
                recordsAnalyzed += jobs.length;
            } catch (fileError) {
                errorCount++;
                console.error(`[${this.environment}] Error processing file ${filePath}:`, fileError);
            }
        }
    } catch (error) {
        throw new Error(`Bulletproof laundry analysis failed: ${error}`);
    }
}
```
**Exception**: Individual file failures don't stop overall analysis  
**Business Impact**: Ensures analytics continue even with partial data corruption

### **C - Customer Revenue Tracking**

**Condition**: When analyzing revenue by customer  
**Action**: Aggregate job revenue and maintain customer statistics  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const customerStats = {};
// Customer tracking
const customerKey = this.extractCustomerName(job);
if (customerKey && customerKey !== 'Unknown Customer') {
    if (!customerStats[customerKey]) {
        customerStats[customerKey] = { jobCount: 0, revenue: 0 };
    }
    customerStats[customerKey].jobCount++;
    customerStats[customerKey].revenue += revenue;
}
```
**Exception**: Unknown customers excluded from top customer rankings  
**Business Impact**: Provides accurate customer lifetime value analysis

### **D - Data Quality Metrics**

**Condition**: When returning any analysis results  
**Action**: Include data quality metrics in response  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
dataQuality: {
    filesProcessed,
    recordsAnalyzed,
    errorCount
}
```
**Exception**: Always included even if all values are zero  
**Business Impact**: Enables confidence assessment in analytics results

### **E - Execution Time Tracking**

**Condition**: When performing any analysis operation  
**Action**: Measure and report execution time in milliseconds  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const startTime = Date.now();
// ... analysis operations ...
const executionTime = Date.now() - startTime;
return {
    // ... other results ...
    executionTime,
}
```
**Exception**: None - always tracked for performance monitoring  
**Business Impact**: Identifies performance bottlenecks and optimization opportunities

### **F - Feed Processing Statistics**

**Condition**: When processing ICS calendar feeds  
**Action**: Generate structured summary for automation capture  
**Implementation**:
```python
# From icsProcess_optimized.py
# Summary output for automation capture
print(f"ICS_SUMMARY: Feeds={total_feeds}, Success={success_feeds}, "
      f"Failed={failed_feeds}, New={total_new}, Modified={total_modified}, "
      f"Removed={total_removed}, Errors={failed_feeds}")
```
**Exception**: Printed even if all values are zero  
**Business Impact**: Enables automated monitoring of feed health

### **G - Graceful Error Handling**

**Condition**: When individual analysis operations fail  
**Action**: Continue processing remaining data and track errors  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
for (const filePath of cacheFiles) {
    try {
        // Process file
    } catch (fileError) {
        errorCount++;
        console.error(`[${this.environment}] Error processing file ${filePath}:`, fileError);
        // Continue with next file
    }
}
```
**Exception**: Critical initialization errors still throw  
**Business Impact**: Maximizes data availability despite partial failures

### **H - Historical Trend Analysis**

**Condition**: When analyzing job data over time  
**Action**: Extract monthly trends and sort chronologically  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const monthlyData = {};
const createdDate = job.created_at || job.scheduled_start;
if (createdDate) {
    const month = this.extractMonth(createdDate);
    if (!monthlyData[month]) {
        monthlyData[month] = { jobCount: 0, revenue: 0 };
    }
    monthlyData[month].jobCount++;
    monthlyData[month].revenue += revenue;
}

// Convert to sorted array
const monthlyTrends = Object.entries(monthlyData)
    .map(([month, data]) => ({
        month,
        jobCount: data.jobCount,
        revenue: data.revenue
    }))
    .sort((a, b) => a.month.localeCompare(b.month));
```
**Exception**: Invalid dates result in 'unknown' month  
**Business Impact**: Enables seasonal pattern identification and forecasting

### **I - Item Pattern Matching**

**Condition**: When searching for specific service items  
**Action**: Use case-insensitive regex matching across multiple fields  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
private matchesServiceItem(lineItem: any, pattern: string): boolean {
    const searchFields = [lineItem.name, lineItem.description];
    const regex = new RegExp(pattern, 'i');
    
    return searchFields.some(field => 
        field && typeof field === 'string' && regex.test(field)
    );
}
```
**Exception**: Null/undefined fields safely ignored  
**Business Impact**: Enables flexible inventory analysis

### **J - Job Statistics Aggregation**

**Condition**: When generating comprehensive job statistics  
**Action**: Track multiple dimensions simultaneously  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
let totalJobs = 0;
let totalRevenue = 0;
const statusBreakdown = {};
const revenueByStatus = {};
const monthlyData = {};

for (const job of jobs) {
    totalJobs++;
    const revenue = this.extractJobRevenue(job);
    totalRevenue += revenue;
    
    const status = job.work_status || 'unknown';
    statusBreakdown[status] = (statusBreakdown[status] || 0) + 1;
    revenueByStatus[status] = (revenueByStatus[status] || 0) + revenue;
}
```
**Exception**: Unknown status grouped separately  
**Business Impact**: Provides multi-dimensional business intelligence

### **K - Key Performance Indicators**

**Condition**: When reporting automation performance  
**Action**: Track success rates, processing times, and volumes  
**Implementation**:
```python
# From controller.py
successful = sum(1 for _, success in results if success)
total = len(results)

print(f"📊 Results: {successful}/{total} successful")
print(f"⏱️  Total duration: {duration.total_seconds():.1f}s")
```
**Exception**: None - always calculated  
**Business Impact**: Enables system performance monitoring

### **L - Laundry Service Detection**

**Condition**: When identifying laundry-related jobs  
**Action**: Search multiple fields for laundry keywords  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
private isLaundryRelated(job: any): boolean {
    const searchFields = [
        job.description,
        job.note,
        job.notes,
        job.service_type,
        ...(job.line_items || []).map((item: any) => item.name),
        ...(job.line_items || []).map((item: any) => item.description)
    ];
    
    return searchFields.some(field => 
        field && typeof field === 'string' && 
        /laundry|linen|towel|wash|clean/i.test(field)
    );
}
```
**Exception**: Empty arrays handled gracefully  
**Business Impact**: Enables specialized service analysis

### **M - Monthly Extraction Logic**

**Condition**: When extracting month from date strings  
**Action**: Convert to YYYY-MM format for sorting  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
private extractMonth(dateString: string): string {
    try {
        const date = new Date(dateString);
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    } catch (error) {
        return 'unknown';
    }
}
```
**Exception**: Invalid dates return 'unknown'  
**Business Impact**: Ensures consistent monthly grouping

### **N - New vs Modified Detection**

**Condition**: When processing CSV or ICS data  
**Action**: Track creation vs modification statistics  
**Implementation**:
```python
# From csvProcess.py
outcomes = {"New": 0, "Modified": 0, "Unchanged": 0}
for row in rows:
    outcome = row["outcome"]
    if outcome in outcomes:
        outcomes[outcome] += 1

logging.info(f" * New: {outcomes['New']} reservations")
logging.info(f" * Modified: {outcomes['Modified']} reservations")
logging.info(f" * Unchanged: {outcomes['Unchanged']} reservations")
```
**Exception**: Unknown outcomes ignored in counts  
**Business Impact**: Tracks data freshness and change velocity

### **O - Output Format Standardization**

**Condition**: When generating any report output  
**Action**: Use consistent structure with headers and summaries  
**Implementation**:
```python
# From csvProcess.py
logging.info("------------  Run digest  ------------")
# ... detailed output ...
logging.info("------------  Summary  ------------")
logging.info(f"Total new: {total_new}")
logging.info(f"Total modified: {total_modified}")
logging.info(f"Total unchanged: {total_unchanged}")
logging.info("------------  End Summary  ------------")
```
**Exception**: None - always follows format  
**Business Impact**: Enables automated report parsing

### **P - Property-Level Reporting**

**Condition**: When reporting reservation statistics  
**Action**: Group by property with name resolution  
**Implementation**:
```python
# From csvProcess.py
for (entry_src, prop_id), rows in summary.items():
    prop_name = id_to_name.get(prop_id, "Unknown Property") 
    header = f"CSV -> {entry_src} for Property {prop_name} (ID: {prop_id})"
    logging.info(header)
```
**Exception**: Unknown properties still reported with ID  
**Business Impact**: Enables property-specific performance analysis

### **Q - Query Performance Metrics**

**Condition**: When performing database or API operations  
**Action**: Track operation count and timing  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
let filesProcessed = 0;
let recordsAnalyzed = 0;
// Track each operation
filesProcessed++;
recordsAnalyzed += jobs.length;
```
**Exception**: None - always tracked  
**Business Impact**: Identifies data processing bottlenecks

### **R - Revenue Extraction Strategy**

**Condition**: When calculating job revenue  
**Action**: Try multiple field names with fallback to line items  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
private extractJobRevenue(job: any): number {
    // Try multiple revenue field options
    const revenueFields = [
        job.total,
        job.total_amount,
        job.invoice_total,
        job.amount,
        job.price,
        job.subtotal
    ];
    
    for (const field of revenueFields) {
        if (typeof field === 'number' && !isNaN(field)) {
            return field;
        }
        if (typeof field === 'string') {
            const parsed = parseFloat(field);
            if (!isNaN(parsed)) {
                return parsed;
            }
        }
    }
    
    // Fallback: sum line items
    if (job.line_items && Array.isArray(job.line_items)) {
        return job.line_items.reduce((sum, item) => {
            const itemTotal = (parseFloat(item.unit_price) || 0) * (parseInt(item.quantity) || 0);
            return sum + itemTotal;
        }, 0);
    }
    
    return 0;
}
```
**Exception**: Returns 0 if no revenue found  
**Business Impact**: Maximizes revenue capture accuracy

### **S - Service Item Analysis**

**Condition**: When analyzing specific service items like towels  
**Action**: Track quantity, cost, revenue, and usage patterns  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
for (const lineItem of job.line_items) {
    if (this.matchesServiceItem(lineItem, itemPattern)) {
        recordsFound++;
        const quantity = parseInt(lineItem.quantity) || 0;
        const unitPrice = parseFloat(lineItem.unit_price) || 0;
        const unitCost = parseFloat(lineItem.unit_cost) || 0;
        
        totalQuantity += quantity;
        totalCost += unitCost * quantity;
        totalRevenue += unitPrice * quantity;
        
        usage.push({
            jobId: job.id || 'unknown',
            customer: this.extractCustomerName(job),
            quantity,
            unitPrice,
            total: unitPrice * quantity
        });
    }
}
```
**Exception**: Invalid numbers default to 0  
**Business Impact**: Enables inventory optimization and cost analysis

### **T - Top Customer Rankings**

**Condition**: When identifying highest-value customers  
**Action**: Sort by revenue and limit to top 10  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const topCustomers = Object.entries(customerStats)
    .map(([customer, stats]) => ({
        customer,
        jobCount: stats.jobCount,
        revenue: stats.revenue
    }))
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 10);
```
**Exception**: Fewer than 10 customers returns all available  
**Business Impact**: Focuses retention efforts on high-value relationships

### **U - Usage Pattern Tracking**

**Condition**: When analyzing service item consumption  
**Action**: Build detailed usage array with customer context  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
usage.push({
    jobId: job.id || 'unknown',
    customer: this.extractCustomerName(job),
    quantity,
    unitPrice,
    total: unitPrice * quantity
});
```
**Exception**: Unknown job IDs labeled as 'unknown'  
**Business Impact**: Enables per-customer usage analysis

### **V - Validation Cache Files**

**Condition**: Before processing cached data files  
**Action**: Verify files exist and are valid JSON  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const cacheFiles = await this.findValidCacheFiles(jobsDir);
if (cacheFiles.length === 0) {
    throw new Error('No valid cached job files found. Run list_jobs first to populate cache.');
}
```
**Exception**: Throws if no valid cache exists  
**Business Impact**: Prevents analysis on stale or missing data

### **W - Work Status Breakdown**

**Condition**: When analyzing job distribution  
**Action**: Track jobs and revenue by status  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const status = job.work_status || 'unknown';
statusBreakdown[status] = (statusBreakdown[status] || 0) + 1;
revenueByStatus[status] = (revenueByStatus[status] || 0) + revenue;
```
**Exception**: Missing status defaults to 'unknown'  
**Business Impact**: Identifies workflow bottlenecks

### **X - eXtraction Statistics**

**Condition**: When parsing automation output  
**Action**: Extract structured statistics from text output  
**Implementation**:
```python
# From run_automation.py
def extract_ics_stats(output):
    stats = {
        'feeds': 0,
        'new': 0,
        'modified': 0,
        'removed': 0,
        'unchanged': 0,
        'errors': 0
    }
    
    # Look for summary line
    for line in output.split('\n'):
        if "ICS_SUMMARY:" in line:
            # Parse structured summary
            parts = line.split("ICS_SUMMARY:")[1].strip()
            for part in parts.split(","):
                if "=" in part:
                    key, value = part.split("=")
                    key = key.strip().lower()
                    if key == 'feeds':
                        stats['feeds'] = int(value.strip())
```
**Exception**: Missing values default to 0  
**Business Impact**: Enables automated monitoring integration

### **Y - Yearly Revenue Tracking**

**Condition**: When dates span multiple years  
**Action**: Include year in monthly grouping  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
const date = new Date(dateString);
return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
// Results in: "2025-07" format for proper sorting
```
**Exception**: Invalid years handled by Date object  
**Business Impact**: Enables multi-year trend analysis

### **Z - Zero-Value Handling**

**Condition**: When metrics calculate to zero  
**Action**: Return explicit zero instead of null/undefined  
**Implementation**:
```typescript
// From bulletproofAnalysisService.ts
return {
    totalQuantity,      // May be 0
    totalCost,          // May be 0
    totalRevenue,       // May be 0
    averagePrice: totalQuantity > 0 ? totalRevenue / totalQuantity : 0,
    jobCount: usage.length,  // May be 0
}
```
**Exception**: None - zeros are valid values  
**Business Impact**: Prevents null reference errors in dashboards

---

## 🔧 **REPORTING PATTERNS SUMMARY**

### **Analysis Categories**
- **Operational**: Performance, timing, success rates
- **Financial**: Revenue, costs, profitability
- **Inventory**: Service items, usage patterns
- **Customer**: Rankings, lifetime value
- **Temporal**: Monthly trends, seasonal patterns

### **Data Quality Assurance**
1. **File validation**: Check before processing
2. **Error tracking**: Count but continue
3. **Fallback strategies**: Multiple field attempts
4. **Default values**: Zeros not nulls
5. **Execution metrics**: Always included

### **Output Standards**
1. **Structured headers**: Consistent delimiters
2. **Property grouping**: With name resolution
3. **Summary sections**: Totals at end
4. **Machine parseable**: For automation
5. **Human readable**: For debugging

---

*This business logic documentation provides comprehensive coverage of all reporting and analytics mechanisms, ensuring reliable business intelligence throughout the property management automation system.*