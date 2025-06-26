/**
 * HCP Response Cache Service
 * Handles intelligent caching of large API responses
 */
import { CacheConfig, CacheMetadata, CachedResponse } from './index.js';
export declare class CacheService {
    private config;
    constructor(config?: Partial<CacheConfig>);
    /**
     * Check if response should be cached based on thresholds
     */
    shouldCache(data: any, operation: string): boolean;
    /**
     * Cache response data to file system
     */
    cacheResponse<T>(data: T, operation: string, environment: 'dev' | 'prod', queryParams?: any): Promise<CachedResponse<T>>;
    /**
     * Get cached response summary for display
     */
    getSummary(data: any, operation: string): string;
    /**
     * List available cache files
     */
    listCacheFiles(environment: 'dev' | 'prod', operation?: string): Promise<CacheMetadata[]>;
    /**
     * Search through cached data with improved traversal
     */
    searchCache(filePath: string, searchTerm: string, fieldPath?: string): Promise<any[]>;
    /**
     * Cleanup old cache files
     */
    cleanup(environment?: 'dev' | 'prod'): Promise<number>;
    private generateHash;
    private getSubDirectory;
    private getRecordCount;
    private formatBytes;
    private getAllSubDirectories;
    private searchInObjectDeep;
    private matchesSearchTerm;
    private getNestedValue;
    private cleanupOldFiles;
}
//# sourceMappingURL=cacheService.d.ts.map