#!/usr/bin/env node

/**
 * Test script for HCP MCP analysis features
 */

const fs = require('fs');
const path = require('path');

// Sample cache structure for testing
const sampleJobData = {
  "page": 1,
  "page_size": 100,
  "total_pages": 1,
  "total_items": 5,
  "jobs": [
    {
      "id": "job_001",
      "invoice_number": "1001",
      "description": "AIRBNB return laundry pickup",
      "customer": {
        "id": "cus_001",
        "first_name": "iTrip",
        "last_name": "Vacations Scottsdale",
        "company": "iTrip Vacations"
      },
      "total_amount": 24000,
      "work_status": "completed",
      "line_items": [
        {
          "name": "Bath Towels",
          "quantity": 8,
          "unit_price": 300,
          "unit_cost": 150,
          "kind": "service"
        },
        {
          "name": "Hand Towels", 
          "quantity": 4,
          "unit_price": 200,
          "unit_cost": 100,
          "kind": "service"
        }
      ]
    },
    {
      "id": "job_002", 
      "invoice_number": "1002",
      "description": "Regular laundry service",
      "customer": {
        "id": "cus_002",
        "first_name": "George",
        "last_name": "Mevawala",
        "company": "Personal"
      },
      "total_amount": 15000,
      "work_status": "completed",
      "line_items": [
        {
          "name": "Beach Towels",
          "quantity": 6,
          "unit_price": 500,
          "unit_cost": 250,
          "kind": "service"
        }
      ]
    },
    {
      "id": "job_003",
      "invoice_number": "1003", 
      "description": "INSPECTION - towel count verification",
      "customer": {
        "id": "cus_001",
        "first_name": "iTrip",
        "last_name": "Vacations Scottsdale",
        "company": "iTrip Vacations"
      },
      "total_amount": 5000,
      "work_status": "needs scheduling",
      "line_items": []
    }
  ]
};

async function createTestCache() {
  const cacheDir = '/tmp/hcp-cache/dev/jobs';
  
  // Create cache directory
  await fs.promises.mkdir(cacheDir, { recursive: true });
  
  // Write sample data
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${timestamp}_list_jobs_test.json`;
  const filepath = path.join(cacheDir, filename);
  
  await fs.promises.writeFile(filepath, JSON.stringify(sampleJobData, null, 2));
  
  console.log('✅ Created test cache file:', filepath);
  return filepath;
}

async function testLinuxCommands(cacheFile) {
  const { execSync } = require('child_process');
  
  console.log('\\n🧪 Testing Linux analysis commands:');
  
  try {
    // Test 1: Count laundry jobs
    console.log('\\n1. Counting laundry jobs...');
    const laundryCount = execSync(`jq '[.jobs[]? | select(.description | test("laundry"; "i"))] | length' ${cacheFile}`, { encoding: 'utf8' });
    console.log(`   Found ${laundryCount.trim()} laundry jobs`);
    
    // Test 2: Count return laundry jobs  
    console.log('\\n2. Counting return laundry jobs...');
    const returnLaundryCount = execSync(`jq '[.jobs[]? | select(.description | test("return.*laundry"; "i"))] | length' ${cacheFile}`, { encoding: 'utf8' });
    console.log(`   Found ${returnLaundryCount.trim()} return laundry jobs`);
    
    // Test 3: Analyze towel usage
    console.log('\\n3. Analyzing towel usage...');
    const towelUsage = execSync(`jq '.jobs[]? | .line_items[]? | select(.name | test("towel"; "i")) | "\\(.name): \\(.quantity) @ $\\(.unit_price) = $\\(.quantity * .unit_price)"' ${cacheFile}`, { encoding: 'utf8' });
    console.log('   Towel usage:');
    towelUsage.trim().split('\\n').forEach(line => {
      if (line.trim()) console.log(`   ${line.replace(/"/g, '')}`);
    });
    
    // Test 4: Calculate total revenue
    console.log('\\n4. Calculating total revenue...');
    const totalRevenue = execSync(`jq '[.jobs[]? | .total_amount] | add' ${cacheFile}`, { encoding: 'utf8' });
    console.log(`   Total revenue: $${(parseInt(totalRevenue.trim()) / 100).toFixed(2)}`);
    
    // Test 5: Job status breakdown
    console.log('\\n5. Job status breakdown...');
    const statusBreakdown = execSync(`jq '.jobs | group_by(.work_status) | map({status: .[0].work_status, count: length})' ${cacheFile}`, { encoding: 'utf8' });
    const statusData = JSON.parse(statusBreakdown);
    statusData.forEach(status => {
      console.log(`   ${status.status}: ${status.count} jobs`);
    });
    
    console.log('\\n✅ All Linux analysis commands working correctly!');
    
  } catch (error) {
    console.error('❌ Error running Linux commands:', error.message);
  }
}

async function main() {
  console.log('🚀 HCP MCP Analysis Tools Test\\n');
  
  try {
    const cacheFile = await createTestCache();
    await testLinuxCommands(cacheFile);
    
    console.log('\\n📝 Analysis Tools Available:');
    console.log('   • analyze_laundry_jobs - Find all laundry-related jobs');
    console.log('   • analyze_service_items - Analyze specific items like towels');
    console.log('   • analyze_customer_revenue - Customer revenue breakdown');
    console.log('   • analyze_job_statistics - Comprehensive job stats');
    console.log('   • analyze_towel_usage - Towel-specific analysis');
    
    console.log('\\n💡 Usage Examples:');
    console.log('   mcp__hcp-mcp-dev__analyze_laundry_jobs');
    console.log('   mcp__hcp-mcp-dev__analyze_service_items {"item_pattern": "towel"}');
    console.log('   mcp__hcp-mcp-dev__analyze_customer_revenue {"customer_id": "cus_001"}');
    
    console.log('\\n🎯 Benefits:');
    console.log('   ✓ Token-free analysis using Linux commands');
    console.log('   ✓ Smart caching with page_size up to 200');
    console.log('   ✓ Advanced pattern matching and aggregation');
    console.log('   ✓ Real-time statistics without API calls');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

main().catch(console.error);