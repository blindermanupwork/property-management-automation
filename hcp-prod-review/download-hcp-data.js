#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');

// Mock MCP client - in reality this would connect to your MCP server
class MCPClient {
  constructor() {
    this.customers = [];
    this.jobs = [];
  }
  
  async downloadAllCustomers() {
    console.log('Downloading customers from HCP Production...');
    let page = 1;
    const pageSize = 50;
    let totalPages = 1;
    
    while (page <= totalPages) {
      console.log(`Fetching customers page ${page}...`);
      
      // Here you would call the actual MCP function
      // For now, we'll save the data we already have
      
      page++;
    }
    
    return this.customers;
  }
  
  async downloadAllJobs() {
    console.log('\nDownloading jobs from HCP Production...');
    let page = 1;
    const pageSize = 20;
    let totalPages = 1;
    
    while (page <= totalPages) {
      console.log(`Fetching jobs page ${page}...`);
      
      // Here you would call the actual MCP function
      
      page++;
    }
    
    return this.jobs;
  }
  
  createCustomerPropertyMapping(customers) {
    const mapping = {};
    
    customers.forEach(customer => {
      const customerName = `${customer.first_name || ''} ${customer.last_name || ''}`.trim();
      
      const serviceAddresses = (customer.addresses || [])
        .filter(addr => addr.type === 'service')
        .map(addr => {
          let fullAddress = addr.street || '';
          if (addr.street_line_2) fullAddress += `, ${addr.street_line_2}`;
          fullAddress += `, ${addr.city || ''}, ${addr.state || ''} ${addr.zip || ''}`;
          
          return {
            id: addr.id,
            full_address: fullAddress.trim(),
            street: addr.street,
            street_line_2: addr.street_line_2,
            city: addr.city,
            state: addr.state,
            zip: addr.zip
          };
        });
      
      if (customerName && serviceAddresses.length > 0) {
        mapping[customerName] = {
          customer_id: customer.id,
          addresses: serviceAddresses,
          email: customer.email,
          phone: customer.mobile_number
        };
      }
    });
    
    return mapping;
  }
}

async function main() {
  const outputDir = path.join(__dirname, 'hcp-prod');
  await fs.mkdir(outputDir, { recursive: true });
  
  const client = new MCPClient();
  
  try {
    // Download all data
    const customers = await client.downloadAllCustomers();
    const jobs = await client.downloadAllJobs();
    
    // Save raw data
    await fs.writeFile(
      path.join(outputDir, 'customers.json'),
      JSON.stringify(customers, null, 2)
    );
    
    await fs.writeFile(
      path.join(outputDir, 'jobs.json'),
      JSON.stringify(jobs, null, 2)
    );
    
    // Create mapping
    const mapping = client.createCustomerPropertyMapping(customers);
    await fs.writeFile(
      path.join(outputDir, 'customer_property_mapping.json'),
      JSON.stringify(mapping, null, 2)
    );
    
    console.log('\nDownload complete!');
    console.log(`Files saved in: ${outputDir}`);
    
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}