/**
 * HCP Response Cache Service
 * Handles intelligent caching of large API responses
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { CacheConfig, CacheMetadata, CachedResponse, CACHE_DEFAULTS } from './index.js';

export class CacheService {
  private config: CacheConfig;

  constructor(config?: Partial<CacheConfig>) {
    this.config = {
      enabled: config?.enabled ?? true,
      baseDir: config?.baseDir ?? CACHE_DEFAULTS.BASE_DIR,
      retentionHours: config?.retentionHours ?? CACHE_DEFAULTS.RETENTION_HOURS,
      maxSizeMB: config?.maxSizeMB ?? CACHE_DEFAULTS.MAX_SIZE_MB,
      thresholds: {
        jobs: config?.thresholds?.jobs ?? CACHE_DEFAULTS.THRESHOLDS.JOBS,
        customers: config?.thresholds?.customers ?? CACHE_DEFAULTS.THRESHOLDS.CUSTOMERS,
        lineItems: config?.thresholds?.lineItems ?? CACHE_DEFAULTS.THRESHOLDS.LINE_ITEMS,
        characters: config?.thresholds?.characters ?? CACHE_DEFAULTS.THRESHOLDS.CHARACTERS,
      }
    };
  }

  /**
   * Check if response should be cached based on thresholds
   */
  shouldCache(data: any, operation: string): boolean {
    if (!this.config.enabled) return false;

    try {
      const dataStr = JSON.stringify(data);
      const charCount = dataStr.length;

      // Check character threshold first
      if (charCount > this.config.thresholds.characters) {
        return true;
      }

      // Check operation-specific thresholds
      if (data.data && Array.isArray(data.data)) {
        const count = data.data.length;
        
        if (operation.includes('job') && !operation.includes('line_item')) {
          return count > this.config.thresholds.jobs;
        }
        
        if (operation.includes('customer')) {
          return count > this.config.thresholds.customers;
        }
        
        if (operation.includes('line_item')) {
          return count > this.config.thresholds.lineItems;
        }
      }

      // Check if it's a direct array (like line items)
      if (Array.isArray(data)) {
        if (operation.includes('line_item')) {
          return data.length > this.config.thresholds.lineItems;
        }
      }

      return false;
    } catch (error) {
      console.error('Error checking cache threshold:', error);
      return false;
    }
  }

  /**
   * Cache response data to file system
   */
  async cacheResponse<T>(
    data: T, 
    operation: string, 
    environment: 'dev' | 'prod',
    queryParams?: any
  ): Promise<CachedResponse<T>> {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const hash = this.generateHash(data, operation, queryParams);
      
      // Determine subdirectory based on operation
      const subDir = this.getSubDirectory(operation);
      const cacheDir = path.join(this.config.baseDir, environment, subDir);
      
      // Create directory if it doesn't exist
      await fs.mkdir(cacheDir, { recursive: true });
      
      const fileName = `${timestamp}_${operation}_${hash}.json`;
      const filePath = path.join(cacheDir, fileName);
      
      // Prepare data for caching
      const dataStr = JSON.stringify(data, null, 2);
      const sizeBytes = Buffer.byteLength(dataStr, 'utf8');
      
      // Create metadata
      const metadata: CacheMetadata = {
        timestamp: new Date().toISOString(),
        operation,
        environment,
        queryParams,
        recordCount: this.getRecordCount(data),
        sizeBytes,
        filePath
      };
      
      // Write data file
      await fs.writeFile(filePath, dataStr, { mode: CACHE_DEFAULTS.FILE_PERMISSIONS });
      
      // Write metadata file
      const metaPath = filePath.replace('.json', '.meta.json');
      await fs.writeFile(
        metaPath, 
        JSON.stringify(metadata, null, 2), 
        { mode: CACHE_DEFAULTS.FILE_PERMISSIONS }
      );
      
      // Clean up old files asynchronously
      this.cleanupOldFiles(cacheDir).catch(err => 
        console.error('Cache cleanup error:', err)
      );
      
      // Include actual data if it's small enough for better UX
      const includeData = sizeBytes < (500 * 1024); // Include if less than 500KB
      
      return {
        _cached: true,
        _filePath: filePath,
        _metadata: metadata,
        _summary: {
          count: metadata.recordCount,
          operation,
          timestamp: metadata.timestamp
        },
        ...(includeData && { data })
      };
      
    } catch (error) {
      console.error('Cache write error:', error);
      // Fallback: return original data without caching
      throw error;
    }
  }

  /**
   * Get cached response summary for display
   */
  getSummary(data: any, operation: string): string {
    const count = this.getRecordCount(data);
    const size = JSON.stringify(data).length;
    
    return `${count} records (${this.formatBytes(size)}) from ${operation} cached for efficient searching`;
  }

  /**
   * List available cache files
   */
  async listCacheFiles(environment: 'dev' | 'prod', operation?: string): Promise<CacheMetadata[]> {
    try {
      const envDir = path.join(this.config.baseDir, environment);
      const files: CacheMetadata[] = [];
      
      const searchDirs = operation 
        ? [path.join(envDir, this.getSubDirectory(operation))]
        : await this.getAllSubDirectories(envDir);
      
      for (const dir of searchDirs) {
        try {
          const dirFiles = await fs.readdir(dir);
          for (const file of dirFiles) {
            if (file.endsWith('.meta.json')) {
              const metaPath = path.join(dir, file);
              const metaContent = await fs.readFile(metaPath, 'utf8');
              files.push(JSON.parse(metaContent));
            }
          }
        } catch (err) {
          // Directory might not exist, continue
        }
      }
      
      return files.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
    } catch (error) {
      console.error('Error listing cache files:', error);
      return [];
    }
  }

  /**
   * Search through cached data with improved traversal
   */
  async searchCache(filePath: string, searchTerm: string, fieldPath?: string): Promise<any[]> {
    try {
      const content = await fs.readFile(filePath, 'utf8');
      const data = JSON.parse(content);
      
      let searchData = [];
      
      // Better data extraction logic
      if (Array.isArray(data)) {
        searchData = data;
      } else if (data.data && Array.isArray(data.data)) {
        searchData = data.data;
      } else if (data.jobs && Array.isArray(data.jobs)) {
        searchData = data.jobs;
      } else if (data.customers && Array.isArray(data.customers)) {
        searchData = data.customers;
      } else if (data.employees && Array.isArray(data.employees)) {
        searchData = data.employees;
      } else if (data.line_items && Array.isArray(data.line_items)) {
        searchData = data.line_items;
      } else {
        // For single object responses (like get_customer), still wrap in array for search
        searchData = [data];
      }
      
      const results = searchData.filter((item: any) => {
        if (fieldPath) {
          // Support JSONPath-like queries
          const fieldValue = this.getNestedValue(item, fieldPath);
          return fieldValue && this.matchesSearchTerm(fieldValue, searchTerm);
        } else {
          // Enhanced deep search with better handling
          return this.searchInObjectDeep(item, searchTerm.toLowerCase());
        }
      });
      
      console.log(`Cache search: Found ${results.length} matches for "${searchTerm}" in ${searchData.length} items`);
      return results;
      
    } catch (error) {
      console.error('Error searching cache:', error);
      return [];
    }
  }

  /**
   * Cleanup old cache files
   */
  async cleanup(environment?: 'dev' | 'prod'): Promise<number> {
    let deletedCount = 0;
    const cutoffTime = Date.now() - (this.config.retentionHours * 60 * 60 * 1000);
    
    try {
      const searchDirs = environment 
        ? [path.join(this.config.baseDir, environment)]
        : [path.join(this.config.baseDir, 'dev'), path.join(this.config.baseDir, 'prod')];
      
      for (const envDir of searchDirs) {
        const subDirs = await this.getAllSubDirectories(envDir);
        
        for (const dir of subDirs) {
          try {
            const files = await fs.readdir(dir);
            
            for (const file of files) {
              const filePath = path.join(dir, file);
              const stats = await fs.stat(filePath);
              
              if (stats.mtime.getTime() < cutoffTime) {
                await fs.unlink(filePath);
                deletedCount++;
              }
            }
          } catch (err) {
            // Directory might not exist, continue
          }
        }
      }
    } catch (error) {
      console.error('Error during cleanup:', error);
    }
    
    return deletedCount;
  }

  // Private helper methods
  private generateHash(data: any, operation: string, queryParams?: any): string {
    const content = JSON.stringify({ data, operation, queryParams });
    return crypto.createHash('md5').update(content).digest('hex').substring(0, 8);
  }

  private getSubDirectory(operation: string): string {
    if (operation.includes('customer')) return 'customers';
    if (operation.includes('employee')) return 'employees';
    if (operation.includes('job_type')) return 'job_types';
    if (operation.includes('appointment')) return 'appointments';
    if (operation.includes('line_item')) return 'line_items';
    if (operation.includes('job')) return 'jobs';
    return 'misc';
  }

  private getRecordCount(data: any): number {
    if (Array.isArray(data)) return data.length;
    if (data.data && Array.isArray(data.data)) return data.data.length;
    if (data.jobs && Array.isArray(data.jobs)) return data.jobs.length;
    if (data.customers && Array.isArray(data.customers)) return data.customers.length;
    if (data.employees && Array.isArray(data.employees)) return data.employees.length;
    if (data.line_items && Array.isArray(data.line_items)) return data.line_items.length;
    return 1;
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  private async getAllSubDirectories(baseDir: string): Promise<string[]> {
    try {
      const items = await fs.readdir(baseDir, { withFileTypes: true });
      return items
        .filter(item => item.isDirectory())
        .map(item => path.join(baseDir, item.name));
    } catch (error) {
      return [];
    }
  }

  // Enhanced search methods
  private searchInObjectDeep(obj: any, term: string, depth: number = 0): boolean {
    // Prevent infinite recursion
    if (depth > 10) return false;
    
    if (typeof obj === 'string') {
      return obj.toLowerCase().includes(term);
    }
    
    if (typeof obj === 'number') {
      return obj.toString().includes(term);
    }
    
    if (Array.isArray(obj)) {
      return obj.some(item => this.searchInObjectDeep(item, term, depth + 1));
    }
    
    if (typeof obj === 'object' && obj !== null) {
      // Search both keys and values
      for (const [key, value] of Object.entries(obj)) {
        if (key.toLowerCase().includes(term) || 
            this.searchInObjectDeep(value, term, depth + 1)) {
          return true;
        }
      }
    }
    
    return false;
  }

  private matchesSearchTerm(value: any, searchTerm: string): boolean {
    if (value == null) return false;
    
    const valueStr = value.toString().toLowerCase();
    const termLower = searchTerm.toLowerCase();
    
    // Support partial matching and exact matching
    return valueStr.includes(termLower) || valueStr === termLower;
  }

  private getNestedValue(obj: any, path: string): any {
    // Support JSONPath-like syntax and array access
    const parts = path.split(/[.\[\]]/).filter(Boolean);
    let current = obj;
    
    for (const part of parts) {
      if (current == null) return null;
      
      // Handle array access
      if (/^\d+$/.test(part)) {
        current = current[parseInt(part)];
      } else if (part === '*' && Array.isArray(current)) {
        // Wildcard array access - return all values
        return current.map(item => this.getNestedValue(item, parts.slice(parts.indexOf('*') + 1).join('.'))).filter(Boolean);
      } else {
        current = current[part];
      }
    }
    
    return current;
  }

  private async cleanupOldFiles(directory: string): Promise<void> {
    const cutoffTime = Date.now() - (this.config.retentionHours * 60 * 60 * 1000);
    
    try {
      const files = await fs.readdir(directory);
      
      for (const file of files) {
        const filePath = path.join(directory, file);
        const stats = await fs.stat(filePath);
        
        if (stats.mtime.getTime() < cutoffTime) {
          await fs.unlink(filePath);
        }
      }
    } catch (error) {
      // Ignore cleanup errors
    }
  }
}