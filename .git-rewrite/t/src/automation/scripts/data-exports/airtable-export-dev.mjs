#!/usr/bin/env node

/**
 * REAL Airtable Data Export Script - Development
 * Exports ALL development Airtable data using real API key
 * Uses actual MCP dev connection to fetch hundreds of records
 */

import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

class RealAirtableExporter {
  constructor() {
    // REAL development configuration from .env file
    this.apiKey = 'patyXgxqzJQYBgE2e.1e83544d7d123c91f3f6bb00cef9a14a073d734f152944c9a24fe18ae27bfdbb'
    this.baseId = 'app67yWFv0hKdl6jM' // Development base
    this.reservationsTableId = 'tblaPnk0jxF47xWhL'
    this.exportDir = path.join(__dirname, '../app/public/api/dev/data/exports')
    
    // Airtable API endpoints
    this.baseUrl = `https://api.airtable.com/v0/${this.baseId}`
  }

  async exportAllRealData() {
    try {
      console.log('🚀 Starting REAL Airtable export from development...')
      console.log(`📊 Base ID: ${this.baseId}`)
      console.log(`📋 Table ID: ${this.reservationsTableId}`)
      
      // Create export directory
      await this.ensureExportDirectory()
      
      // Fetch ALL real reservations from Airtable API
      const allReservations = await this.fetchAllReservations()
      
      // Prepare export data
      const exportData = {
        exportDate: new Date().toISOString(),
        totalRecords: allReservations.length,
        dataSource: 'airtable_dev_api_live',
        baseId: this.baseId,
        tableId: this.reservationsTableId,
        environment: 'development',
        apiUsed: 'airtable_rest_api',
        records: allReservations
      }
      
      // Create metadata
      const metadata = {
        lastExport: exportData.exportDate,
        totalRecords: exportData.totalRecords,
        dataSource: exportData.dataSource,
        baseId: this.baseId,
        tableId: this.reservationsTableId,
        environment: 'development',
        exportMethod: 'airtable_rest_api_batched'
      }
      
      // Write export files
      await this.writeExportFiles(exportData, metadata)
      
      console.log(`✅ REAL data export completed: ${allReservations.length} reservations exported`)
      console.log(`📁 Export location: ${this.exportDir}`)
      
      return metadata
      
    } catch (error) {
      console.error('❌ REAL data export failed:', error)
      throw error
    }
  }

  async fetchAllReservations() {
    console.log('📡 Fetching ALL reservations from Airtable API...')
    
    const allRecords = []
    let offset = null
    let pageCount = 0
    
    do {
      try {
        pageCount++
        console.log(`📄 Fetching page ${pageCount}${offset ? ` (offset: ${offset.substring(0, 10)}...)` : ''}`)
        
        // Build API URL with pagination
        const url = new URL(`${this.baseUrl}/${this.reservationsTableId}`)
        url.searchParams.set('pageSize', '100') // Max page size
        if (offset) {
          url.searchParams.set('offset', offset)
        }
        
        // Make API request
        const response = await fetch(url.toString(), {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (!response.ok) {
          throw new Error(`Airtable API error: ${response.status} ${response.statusText}`)
        }
        
        const data = await response.json()
        
        // Add records to collection
        allRecords.push(...data.records)
        console.log(`📋 Fetched ${data.records.length} records (total: ${allRecords.length})`)
        
        // Check for more pages
        offset = data.offset || null
        
        // Rate limiting - be nice to Airtable
        if (offset) {
          await new Promise(resolve => setTimeout(resolve, 200)) // 200ms delay between requests
        }
        
      } catch (error) {
        console.error(`❌ Error fetching page ${pageCount}:`, error)
        throw error
      }
      
    } while (offset)
    
    console.log(`✅ Fetched ALL ${allRecords.length} reservation records from Airtable`)
    return allRecords
  }

  async ensureExportDirectory() {
    try {
      await fs.mkdir(this.exportDir, { recursive: true })
      console.log(`📁 Export directory ready: ${this.exportDir}`)
    } catch (error) {
      console.error('❌ Failed to create export directory:', error)
      throw error
    }
  }

  async writeExportFiles(exportData, metadata) {
    try {
      // Write reservations data
      const reservationsPath = path.join(this.exportDir, 'reservations.json')
      await fs.writeFile(reservationsPath, JSON.stringify(exportData, null, 2))
      console.log(`📄 Wrote ${exportData.totalRecords} reservations to: ${reservationsPath}`)
      
      // Write metadata
      const metadataPath = path.join(this.exportDir, 'metadata.json')
      await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2))
      console.log(`📄 Wrote metadata to: ${metadataPath}`)
      
      // Write summary for quick reference
      const summary = {
        lastExport: metadata.lastExport,
        totalRecords: metadata.totalRecords,
        dataSource: metadata.dataSource,
        environment: metadata.environment,
        exportFiles: ['reservations.json', 'metadata.json'],
        sampleRecord: exportData.records[0] || null, // First record for preview
        recordFields: exportData.records[0] ? Object.keys(exportData.records[0].fields || {}) : []
      }
      
      const summaryPath = path.join(this.exportDir, 'summary.json')
      await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2))
      console.log(`📄 Wrote summary to: ${summaryPath}`)
      
      // Write a simple status file for the React Native app
      const statusPath = path.join(this.exportDir, 'status.json')
      const status = {
        status: 'ready',
        lastExport: metadata.lastExport,
        totalRecords: metadata.totalRecords,
        environment: 'development'
      }
      await fs.writeFile(statusPath, JSON.stringify(status, null, 2))
      console.log(`📄 Wrote status to: ${statusPath}`)
      
    } catch (error) {
      console.error('❌ Failed to write export files:', error)
      throw error
    }
  }
}

// CLI interface
async function main() {
  const exporter = new RealAirtableExporter()
  
  try {
    console.log('🎯 REAL Airtable Export - Development Environment')
    console.log('===============================================')
    
    const result = await exporter.exportAllRealData()
    
    console.log('✅ REAL data export completed successfully!')
    console.log('📊 Export Summary:')
    console.log(`   🗂️  Environment: ${result.environment}`)
    console.log(`   📊 Total Records: ${result.totalRecords}`)
    console.log(`   📅 Export Date: ${result.lastExport}`)
    console.log(`   🔗 Base ID: ${result.baseId}`)
    console.log(`   📋 Table ID: ${result.tableId}`)
    
    process.exit(0)
  } catch (error) {
    console.error('❌ REAL data export failed:', error)
    process.exit(1)
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
}

export default RealAirtableExporter