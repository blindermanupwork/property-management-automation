/**
 * Bulletproof HCP Data Analysis Service
 * Provides robust analysis tools with enhanced error handling and efficiency
 */
import { promises as fs } from 'fs';
import * as path from 'path';
import { CACHE_DEFAULTS } from './constants.js';
export class BulletproofAnalysisService {
    baseDir;
    environment;
    constructor(environment) {
        this.environment = environment;
        this.baseDir = path.join(CACHE_DEFAULTS.BASE_DIR, environment);
    }
    /**
     * Bulletproof laundry analysis with enhanced error handling
     */
    async analyzeLaundryJobs() {
        const startTime = Date.now();
        const jobsDir = path.join(this.baseDir, 'jobs');
        try {
            // Find and validate cache files
            const cacheFiles = await this.findValidCacheFiles(jobsDir);
            if (cacheFiles.length === 0) {
                throw new Error('No valid cached job files found. Run list_jobs first to populate cache.');
            }
            console.log(`[${this.environment}] Analyzing ${cacheFiles.length} cache files for laundry data`);
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
                    // Handle different data structures (data array vs direct jobs array)
                    const jobs = data.data || data.jobs || data;
                    if (!Array.isArray(jobs)) {
                        console.warn(`[${this.environment}] Skipping ${filePath}: No job array found`);
                        continue;
                    }
                    filesProcessed++;
                    recordsAnalyzed += jobs.length;
                    for (const job of jobs) {
                        try {
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
                        catch (jobError) {
                            errorCount++;
                            console.warn(`[${this.environment}] Error processing job in ${filePath}:`, jobError);
                        }
                    }
                }
                catch (fileError) {
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
        }
        catch (error) {
            throw new Error(`Bulletproof laundry analysis failed: ${error}`);
        }
    }
    /**
     * Enhanced service item analysis
     */
    async analyzeServiceItems(itemPattern) {
        const startTime = Date.now();
        const jobsDir = path.join(this.baseDir, 'jobs');
        try {
            const cacheFiles = await this.findValidCacheFiles(jobsDir);
            if (cacheFiles.length === 0) {
                throw new Error('No valid cached job files found.');
            }
            console.log(`[${this.environment}] Analyzing service items matching "${itemPattern}" in ${cacheFiles.length} files`);
            let totalQuantity = 0;
            let totalCost = 0;
            let totalRevenue = 0;
            let filesProcessed = 0;
            let recordsFound = 0;
            const usage = [];
            for (const filePath of cacheFiles) {
                try {
                    const fileContent = await fs.readFile(filePath, 'utf8');
                    const data = JSON.parse(fileContent);
                    const jobs = data.data || data.jobs || data;
                    if (!Array.isArray(jobs))
                        continue;
                    filesProcessed++;
                    for (const job of jobs) {
                        if (!job.line_items || !Array.isArray(job.line_items))
                            continue;
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
                catch (fileError) {
                    console.error(`[${this.environment}] Error processing file ${filePath}:`, fileError);
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
        }
        catch (error) {
            throw new Error(`Enhanced service item analysis failed: ${error}`);
        }
    }
    /**
     * Comprehensive job statistics with enhanced insights
     */
    async analyzeJobStatistics() {
        const startTime = Date.now();
        const jobsDir = path.join(this.baseDir, 'jobs');
        try {
            const cacheFiles = await this.findValidCacheFiles(jobsDir);
            if (cacheFiles.length === 0) {
                throw new Error('No valid cached job files found.');
            }
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
                try {
                    const fileContent = await fs.readFile(filePath, 'utf8');
                    const data = JSON.parse(fileContent);
                    const jobs = data.data || data.jobs || data;
                    if (!Array.isArray(jobs))
                        continue;
                    filesProcessed++;
                    recordsAnalyzed += jobs.length;
                    for (const job of jobs) {
                        try {
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
                        catch (jobError) {
                            errorCount++;
                            console.warn(`[${this.environment}] Error processing job:`, jobError);
                        }
                    }
                }
                catch (fileError) {
                    errorCount++;
                    console.error(`[${this.environment}] Error processing file ${filePath}:`, fileError);
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
        }
        catch (error) {
            throw new Error(`Enhanced job statistics analysis failed: ${error}`);
        }
    }
    /**
     * Analyze towel usage with detailed insights
     */
    async analyzeTowelUsage() {
        return this.analyzeServiceItems('towel');
    }
    // Private helper methods with enhanced robustness
    async findValidCacheFiles(directory) {
        try {
            await fs.access(directory);
            const files = await fs.readdir(directory);
            const validFiles = [];
            for (const file of files) {
                if (file.endsWith('.json') && !file.endsWith('.meta.json')) {
                    const filePath = path.join(directory, file);
                    try {
                        const stats = await fs.stat(filePath);
                        if (stats.isFile() && stats.size > 10) { // Must be at least 10 bytes
                            validFiles.push(filePath);
                        }
                    }
                    catch (statError) {
                        console.warn(`[${this.environment}] Cannot access file ${filePath}:`, statError);
                    }
                }
            }
            return validFiles.sort();
        }
        catch (error) {
            console.error(`[${this.environment}] Error accessing directory ${directory}:`, error);
            return [];
        }
    }
    isLaundryRelated(job) {
        const searchFields = [
            job.description,
            job.note,
            job.notes,
            job.service_type,
            ...(job.line_items || []).map((item) => item.name),
            ...(job.line_items || []).map((item) => item.description)
        ];
        return searchFields.some(field => field && typeof field === 'string' &&
            /laundry|linen|towel|wash|clean/i.test(field));
    }
    isReturnLaundryJob(job) {
        const searchFields = [
            job.description,
            job.note,
            job.notes,
            ...(job.line_items || []).map((item) => item.name)
        ];
        return searchFields.some(field => field && typeof field === 'string' &&
            /return.*laundry|laundry.*return/i.test(field));
    }
    matchesServiceItem(lineItem, pattern) {
        const searchFields = [lineItem.name, lineItem.description];
        const regex = new RegExp(pattern, 'i');
        return searchFields.some(field => field && typeof field === 'string' && regex.test(field));
    }
    extractJobRevenue(job) {
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
    extractCustomerName(job) {
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
    extractMonth(dateString) {
        try {
            const date = new Date(dateString);
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        }
        catch (error) {
            return 'unknown';
        }
    }
}
