/**
 * Bulletproof HCP Data Analysis Service
 * Provides robust analysis tools with enhanced error handling and efficiency
 */
export interface BulletproofAnalysisResult {
    query: string;
    resultCount: number;
    totalValue?: number;
    summary: string;
    details: any[];
    cacheFiles: string[];
    executionTime: number;
    dataQuality: {
        filesProcessed: number;
        recordsFound: number;
        errorCount: number;
    };
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
    executionTime: number;
    dataQuality: {
        filesProcessed: number;
        recordsAnalyzed: number;
        errorCount: number;
    };
}
export interface ServiceItemAnalysis {
    itemName: string;
    totalQuantity: number;
    totalCost: number;
    totalRevenue: number;
    averagePrice: number;
    jobCount: number;
    usage: Array<{
        jobId: string;
        customer: string;
        quantity: number;
        unitPrice: number;
        total: number;
    }>;
    executionTime: number;
    dataQuality: {
        filesProcessed: number;
        recordsFound: number;
    };
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
export interface JobStatistics {
    totalJobs: number;
    totalRevenue: number;
    averageJobValue: number;
    statusBreakdown: Record<string, number>;
    revenueByStatus: Record<string, number>;
    monthlyTrends: Array<{
        month: string;
        jobCount: number;
        revenue: number;
    }>;
    executionTime: number;
    dataQuality: {
        filesProcessed: number;
        recordsAnalyzed: number;
        errorCount: number;
    };
}
export declare class AnalysisService {
    private baseDir;
    private environment;
    constructor(environment: 'dev' | 'prod');
    /**
     * Bulletproof laundry analysis with enhanced error handling
     */
    analyzeLaundryJobs(): Promise<LaundryAnalysis>;
    /**
     * Enhanced service item analysis
     */
    analyzeServiceItems(itemPattern: string): Promise<ServiceItemAnalysis>;
    /**
     * Analyze customer revenue and job statistics
     */
    analyzeCustomerRevenue(customerId?: string): Promise<CustomerRevenueAnalysis[]>;
    /**
     * Comprehensive job statistics with enhanced insights
     */
    analyzeJobStatistics(): Promise<JobStatistics>;
    /**
     * Generate analysis report for all cached data
     */
    generateAnalysisReport(): Promise<any>;
    private findValidCacheFiles;
    private isLaundryRelated;
    private isReturnLaundryJob;
    private matchesServiceItem;
    private extractJobRevenue;
    private extractCustomerName;
    private extractMonth;
}
//# sourceMappingURL=analysisService.d.ts.map