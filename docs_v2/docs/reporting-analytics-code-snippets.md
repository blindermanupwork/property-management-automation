# Reporting and Analytics Code Snippets

## 1. HCP MCP Analysis Tools (TypeScript/JavaScript)

### Laundry Job Analysis
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
async analyzeLaundryJobs() {
    const startTime = Date.now();
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
        const cacheFiles = await this.findValidCacheFiles(jobsDir);
        if (cacheFiles.length === 0) {
            throw new Error('No valid cached job files found. Run list_jobs first to populate cache.');
        }
        
        let totalReturnLaundry = 0;
        let totalLaundry = 0;
        let totalRevenue = 0;
        let filesProcessed = 0;
        let recordsAnalyzed = 0;
        let errorCount = 0;
        const customerStats = {};
        
        // Process each file with robust error handling
        for (const filePath of cacheFiles) {
            try {
                const fileContent = await fs.readFile(filePath, 'utf8');
                const data = JSON.parse(fileContent);
                const jobs = data.data || data.jobs || data;
                
                filesProcessed++;
                recordsAnalyzed += jobs.length;
                
                for (const job of jobs) {
                    // Enhanced laundry detection - check multiple fields
                    const isLaundryJob = this.isLaundryRelated(job);
                    const isReturnLaundry = this.isReturnLaundryJob(job);
                    
                    if (isLaundryJob) {
                        totalLaundry++;
                        if (isReturnLaundry) {
                            totalReturnLaundry++;
                        }
                        
                        // Revenue calculation with fallback options
                        const revenue = this.extractJobRevenue(job);
                        totalRevenue += revenue;
                        
                        // Customer tracking
                        const customerKey = this.extractCustomerName(job);
                        if (customerKey && customerKey !== 'Unknown Customer') {
                            if (!customerStats[customerKey]) {
                                customerStats[customerKey] = { jobCount: 0, revenue: 0 };
                            }
                            customerStats[customerKey].jobCount++;
                            customerStats[customerKey].revenue += revenue;
                        }
                    }
                }
            } catch (fileError) {
                errorCount++;
                console.error(`[${this.environment}] Error processing file ${filePath}:`, fileError);
            }
        }
        
        // Generate top customers
        const topCustomers = Object.entries(customerStats)
            .map(([customer, stats]) => ({
                customer,
                jobCount: stats.jobCount,
                revenue: stats.revenue
            }))
            .sort((a, b) => b.revenue - a.revenue)
            .slice(0, 10);
        
        const executionTime = Date.now() - startTime;
        
        return {
            returnLaundryJobs: totalReturnLaundry,
            laundryJobs: totalLaundry,
            totalRevenue,
            averageJobValue: totalLaundry > 0 ? totalRevenue / totalLaundry : 0,
            topCustomers,
            executionTime,
            dataQuality: {
                filesProcessed,
                recordsAnalyzed,
                errorCount
            }
        };
    } catch (error) {
        throw new Error(`Bulletproof laundry analysis failed: ${error}`);
    }
}
```

### Service Item Analysis
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
async analyzeServiceItems(itemPattern: string) {
    const startTime = Date.now();
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
        const cacheFiles = await this.findValidCacheFiles(jobsDir);
        console.log(`[${this.environment}] Analyzing service items matching "${itemPattern}" in ${cacheFiles.length} files`);
        
        let totalQuantity = 0;
        let totalCost = 0;
        let totalRevenue = 0;
        let filesProcessed = 0;
        let recordsFound = 0;
        const usage = [];
        
        for (const filePath of cacheFiles) {
            const fileContent = await fs.readFile(filePath, 'utf8');
            const data = JSON.parse(fileContent);
            const jobs = data.data || data.jobs || data;
            
            filesProcessed++;
            
            for (const job of jobs) {
                if (!job.line_items || !Array.isArray(job.line_items)) continue;
                
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
            }
        }
        
        const executionTime = Date.now() - startTime;
        
        return {
            itemName: itemPattern,
            totalQuantity,
            totalCost,
            totalRevenue,
            averagePrice: totalQuantity > 0 ? totalRevenue / totalQuantity : 0,
            jobCount: usage.length,
            usage,
            executionTime,
            dataQuality: {
                filesProcessed,
                recordsFound
            }
        };
    } catch (error) {
        throw new Error(`Enhanced service item analysis failed: ${error}`);
    }
}
```

### Job Statistics Analysis
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
async analyzeJobStatistics() {
    const startTime = Date.now();
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
        const cacheFiles = await this.findValidCacheFiles(jobsDir);
        console.log(`[${this.environment}] Analyzing job statistics from ${cacheFiles.length} cache files`);
        
        let totalJobs = 0;
        let totalRevenue = 0;
        let filesProcessed = 0;
        let recordsAnalyzed = 0;
        let errorCount = 0;
        const statusBreakdown = {};
        const revenueByStatus = {};
        const monthlyData = {};
        
        for (const filePath of cacheFiles) {
            const fileContent = await fs.readFile(filePath, 'utf8');
            const data = JSON.parse(fileContent);
            const jobs = data.data || data.jobs || data;
            
            filesProcessed++;
            recordsAnalyzed += jobs.length;
            
            for (const job of jobs) {
                totalJobs++;
                const revenue = this.extractJobRevenue(job);
                totalRevenue += revenue;
                
                const status = job.work_status || 'unknown';
                statusBreakdown[status] = (statusBreakdown[status] || 0) + 1;
                revenueByStatus[status] = (revenueByStatus[status] || 0) + revenue;
                
                // Monthly tracking
                const createdDate = job.created_at || job.scheduled_start;
                if (createdDate) {
                    const month = this.extractMonth(createdDate);
                    if (!monthlyData[month]) {
                        monthlyData[month] = { jobCount: 0, revenue: 0 };
                    }
                    monthlyData[month].jobCount++;
                    monthlyData[month].revenue += revenue;
                }
            }
        }
        
        // Convert monthly data to sorted array
        const monthlyTrends = Object.entries(monthlyData)
            .map(([month, data]) => ({
                month,
                jobCount: data.jobCount,
                revenue: data.revenue
            }))
            .sort((a, b) => a.month.localeCompare(b.month));
        
        const executionTime = Date.now() - startTime;
        
        return {
            totalJobs,
            totalRevenue,
            averageJobValue: totalJobs > 0 ? totalRevenue / totalJobs : 0,
            statusBreakdown,
            revenueByStatus,
            monthlyTrends,
            executionTime,
            dataQuality: {
                filesProcessed,
                recordsAnalyzed,
                errorCount
            }
        };
    } catch (error) {
        throw new Error(`Enhanced job statistics analysis failed: ${error}`);
    }
}
```

### Customer Revenue Analysis
```typescript
// From tools/hcp-mcp-common/src/analysisService.ts
async analyzeCustomerRevenue(customerId?: string): Promise<CustomerRevenueAnalysis[]> {
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
        const cacheFiles = await this.findValidCacheFiles(jobsDir);
        
        if (cacheFiles.length === 0) {
            throw new Error('No valid cached job files found.');
        }
        
        const customerData: Record<string, any> = {};
        
        for (const filePath of cacheFiles) {
            const fileContent = await fs.readFile(filePath, 'utf8');
            const data = JSON.parse(fileContent);
            const jobs = data.data || data.jobs || data;
            
            for (const job of jobs) {
                if (customerId && job.customer?.id !== customerId) continue;
                
                const cId = job.customer?.id;
                if (!cId) continue;
                
                const revenue = this.extractJobRevenue(job);
                const customerName = this.extractCustomerName(job);
                const status = job.work_status || 'unknown';
                
                if (!customerData[cId]) {
                    customerData[cId] = {
                        customerId: cId,
                        customerName,
                        totalJobs: 0,
                        totalRevenue: 0,
                        jobStatuses: {},
                        topServices: []
                    };
                }
                
                customerData[cId].totalJobs++;
                customerData[cId].totalRevenue += revenue;
                customerData[cId].jobStatuses[status] = (customerData[cId].jobStatuses[status] || 0) + 1;
            }
        }
        
        return Object.values(customerData).map((customer: any) => ({
            ...customer,
            averageJobValue: customer.totalJobs > 0 ? customer.totalRevenue / customer.totalJobs : 0
        }));
    } catch (error) {
        throw new Error(`Customer revenue analysis failed: ${error}`);
    }
}
```

## 2. CSV Processing Summary (Python)

### CSV Processing Report Generation
```python
# From src/automation/scripts/CSVtoAirtable/csvProcess.py
def generate_report(results, id_to_name):
    """Generate detailed and summary reports"""
    summary = results["summary"]
    
    # Skip if no reservations processed
    if not summary:
        logging.info("No reservations processed.")
        return
    
    # Log run digest (only goes to log file due to filter)
    logging.info("------------  Run digest  ------------")
    
    # Process all properties and collect stats
    for (entry_src, prop_id), rows in summary.items():
        prop_name = id_to_name.get(prop_id, "Unknown Property") 
        if not rows:
            continue
            
        # Count by outcome
        outcomes = {"New": 0, "Modified": 0, "Unchanged": 0}
        for row in rows:
            outcome = row["outcome"]
            if outcome in outcomes:
                outcomes[outcome] += 1
        
        # Log property information
        header = f"CSV -> {entry_src} for Property {prop_name} (ID: {prop_id})"
        logging.info(header)
        logging.info(f" * New: {outcomes['New']} reservations")
        logging.info(f" * Modified: {outcomes['Modified']} reservations")
        logging.info(f" * Unchanged: {outcomes['Unchanged']} reservations")
    
    # Count totals
    total_new = sum(row["outcome"] == "New" for rows in summary.values() for row in rows)
    total_modified = sum(row["outcome"] == "Modified" for rows in summary.values() for row in rows)
    total_unchanged = sum(row["outcome"] == "Unchanged" for rows in summary.values() for row in rows)
    
    # Print summary
    logging.info("------------  Summary  ------------")
    logging.info(f"Total new: {total_new}")
    logging.info(f"Total modified: {total_modified}")
    logging.info(f"Total unchanged: {total_unchanged}")
    logging.info("------------  End Summary  ------------")
```

## 3. ICS Processing Summary (Python)

### ICS Sync Report Generation
```python
# From src/automation/scripts/icsAirtableSync/icsProcess_optimized.py
def generate_report(overall_stats, id_to_name):
    """Generate a report of sync operations"""
    if not overall_stats:
        logging.info("No feeds processed.")
        return
    
    # Track counts for final summary
    total_unchanged = 0
    total_new = 0
    total_modified = 0
    total_removed = 0
    
    # Log run digest
    logging.info("------------  Run digest  ------------")
    
    # Process all feeds and collect stats
    for feed_url, stats in overall_stats.items():
        # Get property name if available
        prop_id = stats.get("property_id")
        prop_name = id_to_name.get(prop_id, "Unknown Property")
        
        # Update totals
        total_unchanged += stats.get("Unchanged", 0)
        total_new += stats.get("New", 0)
        total_modified += stats.get("Modified", 0)
        total_removed += stats.get("Removed", 0)
        
        # Log feed information
        header = f"Feed -> {feed_url} ({prop_name})"
        logging.info(header)
        logging.info(f" * New: {stats.get('New', 0)} reservations")
        logging.info(f" * Modified: {stats.get('Modified', 0)} reservations")
        logging.info(f" * Unchanged: {stats.get('Unchanged', 0)} reservations")
        logging.info(f" * Removed: {stats.get('Removed', 0)} reservations")
    
    # Print summary
    logging.info("------------  Summary  ------------")
    logging.info(f"Total unchanged: {total_unchanged}")
    logging.info(f"Total new: {total_new}")
    logging.info(f"Total modified: {total_modified}")
    logging.info(f"Total removed: {total_removed}")
    logging.info("------------  End Summary  ------------")

# Summary output for automation capture
print(f"ICS_SUMMARY: Feeds={total_feeds}, Success={success_feeds}, "
      f"Failed={failed_feeds}, New={total_new}, Modified={total_modified}, "
      f"Removed={total_removed}, Errors={failed_feeds}")
```

### ICS Statistics Extraction
```python
# From src/automation/scripts/run_automation.py
def extract_ics_stats(output):
    """Extract statistics from ICS sync output"""
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
                    elif key == 'new':
                        stats['new'] = int(value.strip())
                    elif key == 'modified':
                        stats['modified'] = int(value.strip())
                    elif key == 'removed':
                        stats['removed'] = int(value.strip())
                    elif key == 'errors':
                        stats['errors'] = int(value.strip())
        
        # Also look for legacy format
        elif "ICS Sync complete" in line:
            import re
            created_match = re.search(r'created (\d+)', line)
            modified_match = re.search(r'modified (\d+)', line)
            unchanged_match = re.search(r'unchanged (\d+)', line)
            removed_match = re.search(r'removed (\d+)', line)
            
            if created_match:
                stats['new'] = int(created_match.group(1))
            if modified_match:
                stats['modified'] = int(modified_match.group(1))
            if unchanged_match:
                stats['unchanged'] = int(unchanged_match.group(1))
            if removed_match:
                stats['removed'] = int(removed_match.group(1))
    
    return stats
```

## 4. Revenue Extraction Helper Functions

### Extract Job Revenue (Multiple Fallback Options)
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
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

### Extract Customer Name
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
private extractCustomerName(job: any): string {
    if (job.customer) {
        const firstName = job.customer.first_name || '';
        const lastName = job.customer.last_name || '';
        const company = job.customer.company || '';
        
        if (firstName || lastName) {
            return `${firstName} ${lastName}`.trim();
        }
        if (company) {
            return company;
        }
    }
    return 'Unknown Customer';
}
```

### Pattern Matching for Service Items
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
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

private matchesServiceItem(lineItem: any, pattern: string): boolean {
    const searchFields = [lineItem.name, lineItem.description];
    const regex = new RegExp(pattern, 'i');
    
    return searchFields.some(field => 
        field && typeof field === 'string' && regex.test(field)
    );
}
```

## 5. MCP Tool Definitions

### Analysis Tool Registration
```typescript
// From tools/hcp-mcp-dev/src/mcpServer.ts
{
    name: this.toolName(MCP_TOOL_NAMES.ANALYZE_LAUNDRY_JOBS),
    description: 'Analyze laundry-related jobs using Linux commands on cached data',
    inputSchema: {
        type: 'object',
        properties: {}
    }
},
{
    name: this.toolName(MCP_TOOL_NAMES.ANALYZE_SERVICE_ITEMS),
    description: 'Analyze specific service items (like towels, linens) from cached job data',
    inputSchema: {
        type: 'object',
        properties: {
            item_pattern: { type: 'string', description: 'Pattern to search for service items (e.g., "towel", "linen")' }
        },
        required: ['item_pattern']
    }
},
{
    name: this.toolName(MCP_TOOL_NAMES.ANALYZE_CUSTOMER_REVENUE),
    description: 'Analyze customer revenue and job statistics from cached data',
    inputSchema: {
        type: 'object',
        properties: {
            customer_id: { type: 'string', description: 'Optional specific customer ID to analyze' }
        }
    }
},
{
    name: this.toolName(MCP_TOOL_NAMES.ANALYZE_JOB_STATISTICS),
    description: 'Generate comprehensive job statistics from cached data',
    inputSchema: {
        type: 'object',
        properties: {}
    }
},
{
    name: this.toolName(MCP_TOOL_NAMES.ANALYZE_TOWEL_USAGE),
    description: 'Analyze towel usage and costs from service line items in cached data',
    inputSchema: {
        type: 'object',
        properties: {}
    }
}
```

## 6. Monthly Trend Analysis

### Extract Month for Trend Analysis
```typescript
// From tools/hcp-mcp-common/src/bulletproofAnalysisService.ts
private extractMonth(dateString: string): string {
    try {
        const date = new Date(dateString);
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    } catch (error) {
        return 'unknown';
    }
}

// Usage in job statistics
const monthlyTrends = Object.entries(monthlyData)
    .map(([month, data]) => ({
        month,
        jobCount: data.jobCount,
        revenue: data.revenue
    }))
    .sort((a, b) => a.month.localeCompare(b.month));
```

## Summary

These code snippets demonstrate the comprehensive reporting and analytics capabilities of the automation system:

1. **HCP Analysis Tools**: Bulletproof TypeScript analysis for laundry jobs, service items, customer revenue, and job statistics
2. **CSV Processing Reports**: Python-based summary generation for CSV imports
3. **ICS Sync Reports**: Python-based feed processing statistics
4. **Revenue Extraction**: Multiple fallback strategies for accurate revenue calculation
5. **Pattern Matching**: Flexible regex-based search for service items
6. **Monthly Trends**: Time-based analysis for business insights
7. **Error Handling**: Comprehensive error tracking and data quality metrics

All tools include execution time tracking, data quality metrics, and robust error handling to ensure reliable analytics even with incomplete or malformed data.