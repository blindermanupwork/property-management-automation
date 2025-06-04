/**
 * HCP Data Analysis Service
 * Provides advanced analysis tools using Linux commands on cached data
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import { CACHE_DEFAULTS } from './constants.js';

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

export class AnalysisService {
  private baseDir: string;
  
  constructor(environment: 'dev' | 'prod') {
    this.baseDir = path.join(CACHE_DEFAULTS.BASE_DIR, environment);
  }

  /**
   * Analyze laundry-related jobs using Linux commands
   */
  async analyzeLaundryJobs(): Promise<LaundryAnalysis> {
    const jobsDir = path.join(this.baseDir, 'jobs');
    const commands: string[] = [];
    
    try {
      // Find all job cache files
      const cacheFiles = await this.findCacheFiles(jobsDir, '*.json');
      
      if (cacheFiles.length === 0) {
        throw new Error('No cached job files found. Run list_jobs first to populate cache.');
      }

      // Create temporary analysis script
      const scriptPath = await this.createAnalysisScript('laundry', `
#!/bin/bash
total_return_laundry=0
total_laundry=0
total_revenue=0
declare -A customer_stats

for file in ${cacheFiles.join(' ')}; do
  # Count return laundry jobs
  return_count=$(jq '[.jobs[]? | select(.description | test("return.*laundry"; "i"))] | length' "$file" 2>/dev/null || echo 0)
  total_return_laundry=$((total_return_laundry + return_count))
  
  # Count all laundry jobs
  laundry_count=$(jq '[.jobs[]? | select(.description | test("laundry"; "i"))] | length' "$file" 2>/dev/null || echo 0)
  total_laundry=$((total_laundry + laundry_count))
  
  # Calculate revenue from laundry jobs
  revenue=$(jq '[.jobs[]? | select(.description | test("laundry"; "i")) | .total_amount] | add // 0' "$file" 2>/dev/null || echo 0)
  total_revenue=$((total_revenue + revenue))
  
  # Collect customer data
  jq -r '.jobs[]? | select(.description | test("laundry"; "i")) | "\\(.customer.first_name) \\(.customer.last_name),\\(.total_amount)"' "$file" 2>/dev/null | while IFS=',' read -r customer amount; do
    customer_stats["$customer"]=$((customer_stats["$customer"] + amount))
  done
done

echo "{\\"returnLaundryJobs\\": $total_return_laundry, \\"laundryJobs\\": $total_laundry, \\"totalRevenue\\": $total_revenue}"
      `);

      commands.push(`bash ${scriptPath}`);
      const result = execSync(`bash ${scriptPath}`, { encoding: 'utf8' });
      const data = JSON.parse(result.trim());
      
      // Get top customers using jq
      const topCustomersCmd = `find ${jobsDir} -name "*.json" -exec jq -r '.jobs[]? | select(.description | test("laundry"; "i")) | "\\(.customer.first_name) \\(.customer.last_name),\\(.total_amount)"' {} \\; | awk -F',' '{customer[$1]+=$2; count[$1]++} END {for(c in customer) print c","customer[c]","count[c]}' | sort -t',' -k2 -nr | head -5`;
      
      commands.push(topCustomersCmd);
      const topCustomersResult = execSync(topCustomersCmd, { encoding: 'utf8' });
      
      const topCustomers = topCustomersResult.trim().split('\\n').map(line => {
        const [customer, revenue, jobCount] = line.split(',');
        return {
          customer,
          jobCount: parseInt(jobCount) || 0,
          revenue: parseInt(revenue) || 0
        };
      });

      await fs.unlink(scriptPath);

      return {
        returnLaundryJobs: data.returnLaundryJobs,
        laundryJobs: data.laundryJobs,
        totalRevenue: data.totalRevenue,
        averageJobValue: data.laundryJobs > 0 ? data.totalRevenue / data.laundryJobs : 0,
        topCustomers
      };

    } catch (error) {
      throw new Error(`Laundry analysis failed: ${error}`);
    }
  }

  /**
   * Analyze specific service items (like towels)
   */
  async analyzeServiceItems(itemPattern: string): Promise<ServiceItemAnalysis> {
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
      const cacheFiles = await this.findCacheFiles(jobsDir, '*.json');
      
      if (cacheFiles.length === 0) {
        throw new Error('No cached job files found. Run list_jobs first to populate cache.');
      }

      // Create jq command to extract service items matching pattern
      const jqCmd = `find ${jobsDir} -name "*.json" -exec jq -r '.jobs[]? | select(.line_items) | .line_items[]? | select(.name | test("${itemPattern}"; "i")) | "\\(.name),\\(.quantity),\\(.unit_price),\\(.unit_cost // 0),\\(.. | .customer.first_name // "")_\\(.. | .customer.last_name // ""),\\(.. | .id // "")"' {} \\;`;
      
      const result = execSync(jqCmd, { encoding: 'utf8' });
      const lines = result.trim().split('\\n').filter(line => line.length > 0);
      
      let totalQuantity = 0;
      let totalCost = 0;
      let totalRevenue = 0;
      const usage: any[] = [];
      
      lines.forEach(line => {
        const [, quantity, unitPrice, unitCost, customer, jobId] = line.split(',');
        const qty = parseInt(quantity) || 0;
        const price = parseFloat(unitPrice) || 0;
        const cost = parseFloat(unitCost) || 0;
        
        totalQuantity += qty;
        totalCost += cost * qty;
        totalRevenue += price * qty;
        
        usage.push({
          jobId,
          customer: customer.replace('_', ' '),
          quantity: qty,
          unitPrice: price,
          total: price * qty
        });
      });

      return {
        itemName: itemPattern,
        totalQuantity,
        totalCost,
        averagePrice: totalQuantity > 0 ? totalRevenue / totalQuantity : 0,
        jobCount: usage.length,
        usage
      };

    } catch (error) {
      throw new Error(`Service item analysis failed: ${error}`);
    }
  }

  /**
   * Analyze customer revenue and job statistics
   */
  async analyzeCustomerRevenue(customerId?: string): Promise<CustomerRevenueAnalysis[]> {
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
      const cacheFiles = await this.findCacheFiles(jobsDir, '*.json');
      
      if (cacheFiles.length === 0) {
        throw new Error('No cached job files found. Run list_jobs first to populate cache.');
      }

      const customerFilter = customerId ? `select(.customer.id == "${customerId}") |` : '';
      
      // Get customer revenue data
      const jqCmd = `find ${jobsDir} -name "*.json" -exec jq -r '.jobs[]? | ${customerFilter} "\\(.customer.id),\\(.customer.first_name) \\(.customer.last_name),\\(.total_amount),\\(.work_status)"' {} \\;`;
      
      const result = execSync(jqCmd, { encoding: 'utf8' });
      const lines = result.trim().split('\\n').filter(line => line.length > 0);
      
      const customerData: Record<string, any> = {};
      
      lines.forEach(line => {
        const [id, name, amount, status] = line.split(',');
        const revenue = parseInt(amount) || 0;
        
        if (!customerData[id]) {
          customerData[id] = {
            customerId: id,
            customerName: name,
            totalJobs: 0,
            totalRevenue: 0,
            jobStatuses: {},
            topServices: []
          };
        }
        
        customerData[id].totalJobs++;
        customerData[id].totalRevenue += revenue;
        customerData[id].jobStatuses[status] = (customerData[id].jobStatuses[status] || 0) + 1;
      });

      return Object.values(customerData).map((customer: any) => ({
        ...customer,
        averageJobValue: customer.totalJobs > 0 ? customer.totalRevenue / customer.totalJobs : 0
      }));

    } catch (error) {
      throw new Error(`Customer revenue analysis failed: ${error}`);
    }
  }

  /**
   * Get comprehensive job statistics
   */
  async analyzeJobStatistics(): Promise<any> {
    const jobsDir = path.join(this.baseDir, 'jobs');
    
    try {
      const cacheFiles = await this.findCacheFiles(jobsDir, '*.json');
      
      if (cacheFiles.length === 0) {
        throw new Error('No cached job files found. Run list_jobs first to populate cache.');
      }

      // Create comprehensive statistics script
      const scriptPath = await this.createAnalysisScript('job_stats', `
#!/bin/bash
declare -A status_counts
declare -A monthly_counts
total_jobs=0
total_revenue=0

for file in ${cacheFiles.join(' ')}; do
  # Count by status
  for status in "unscheduled" "scheduled" "in_progress" "completed" "canceled"; do
    count=$(jq "[.jobs[]? | select(.work_status == \\"$status\\")]| length" "$file" 2>/dev/null || echo 0)
    status_counts["$status"]=$((status_counts["$status"] + count))
  done
  
  # Total jobs and revenue
  job_count=$(jq '.jobs | length' "$file" 2>/dev/null || echo 0)
  revenue=$(jq '[.jobs[]? | .total_amount] | add // 0' "$file" 2>/dev/null || echo 0)
  
  total_jobs=$((total_jobs + job_count))
  total_revenue=$((total_revenue + revenue))
done

echo "{"
echo "\\"totalJobs\\": $total_jobs,"
echo "\\"totalRevenue\\": $total_revenue,"
echo "\\"averageJobValue\\": $(( total_jobs > 0 ? total_revenue / total_jobs : 0 )),"
echo "\\"statusBreakdown\\": {"
for status in "unscheduled" "scheduled" "in_progress" "completed" "canceled"; do
  echo "\\"$status\\": \${status_counts[$status]},"
done | sed '$ s/,$//'
echo "}"
echo "}"
      `);

      const result = execSync(`bash ${scriptPath}`, { encoding: 'utf8' });
      await fs.unlink(scriptPath);
      
      return JSON.parse(result.trim());

    } catch (error) {
      throw new Error(`Job statistics analysis failed: ${error}`);
    }
  }

  /**
   * Generate analysis report for all cached data
   */
  async generateAnalysisReport(): Promise<any> {
    try {
      const [laundryAnalysis, jobStats] = await Promise.all([
        this.analyzeLaundryJobs().catch(err => ({ error: err.message })),
        this.analyzeJobStatistics().catch(err => ({ error: err.message }))
      ]);

      const towelAnalysis = await this.analyzeServiceItems('towel').catch(err => ({ error: err.message }));
      const customerRevenue = await this.analyzeCustomerRevenue().catch(err => ({ error: err.message }));

      return {
        generatedAt: new Date().toISOString(),
        laundryAnalysis,
        jobStatistics: jobStats,
        towelUsage: towelAnalysis,
        topCustomers: Array.isArray(customerRevenue) ? customerRevenue.slice(0, 10) : [],
        cacheLocation: this.baseDir
      };

    } catch (error) {
      throw new Error(`Analysis report generation failed: ${error}`);
    }
  }

  // Private helper methods
  private async findCacheFiles(directory: string, pattern: string): Promise<string[]> {
    try {
      const cmd = `find ${directory} -name "${pattern}" -type f 2>/dev/null || true`;
      const result = execSync(cmd, { encoding: 'utf8' });
      return result.trim().split('\\n').filter(file => file.length > 0);
    } catch (error) {
      return [];
    }
  }

  private async createAnalysisScript(name: string, content: string): Promise<string> {
    const tmpDir = '/tmp';
    const scriptPath = path.join(tmpDir, `hcp_analysis_${name}_${Date.now()}.sh`);
    await fs.writeFile(scriptPath, content, { mode: 0o755 });
    return scriptPath;
  }
}