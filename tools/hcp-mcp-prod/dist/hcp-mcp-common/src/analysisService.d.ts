/**
 * HCP Data Analysis Service
 * Provides advanced analysis tools using Linux commands on cached data
 */
export interface AnalysisResult {
    query: string;
    resultCount: number;
    totalValue?: number;
    summary: string;
    details: any[];
    cacheFiles: string[];
    linuxCommands: string[];
}
export interface LaundryAnalysis {
    returnLaundryJobs: number;
    laundryJobs: number;
    totalRevenue: number;
    averageJobValue: number;
    topCustomers: Array<{
        customer: string;
        jobCount: number;
        revenue: number;
    }>;
}
export interface ServiceItemAnalysis {
    itemName: string;
    totalQuantity: number;
    totalCost: number;
    averagePrice: number;
    jobCount: number;
    usage: Array<{
        jobId: string;
        customer: string;
        quantity: number;
        unitPrice: number;
        total: number;
    }>;
}
export interface CustomerRevenueAnalysis {
    customerId: string;
    customerName: string;
    totalJobs: number;
    totalRevenue: number;
    averageJobValue: number;
    jobStatuses: Record<string, number>;
    topServices: Array<{
        service: string;
        count: number;
        revenue: number;
    }>;
}
export declare class AnalysisService {
    private baseDir;
    constructor(environment: 'dev' | 'prod');
    /**
     * Analyze laundry-related jobs using Linux commands
     */
    analyzeLaundryJobs(): Promise<LaundryAnalysis>;
    /**
     * Analyze specific service items (like towels)
     */
    analyzeServiceItems(itemPattern: string): Promise<ServiceItemAnalysis>;
    /**
     * Analyze customer revenue and job statistics
     */
    analyzeCustomerRevenue(customerId?: string): Promise<CustomerRevenueAnalysis[]>;
    /**
     * Get comprehensive job statistics
     */
    analyzeJobStatistics(): Promise<any>;
    /**
     * Generate analysis report for all cached data
     */
    generateAnalysisReport(): Promise<any>;
    private findCacheFiles;
    private createAnalysisScript;
}
//# sourceMappingURL=analysisService.d.ts.map