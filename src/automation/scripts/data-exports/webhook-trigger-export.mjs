#!/usr/bin/env node

/**
 * Webhook Trigger for Airtable Export
 * Sets up a simple webhook endpoint that triggers re-export
 * when Airtable data changes via webhooks
 */

import express from 'express'
import { execSync } from 'child_process'
import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

class WebhookExportTrigger {
  constructor() {
    this.app = express()
    this.port = process.env.WEBHOOK_PORT || 3001
    this.lastExport = null
    this.isExporting = false
    
    // Setup middleware
    this.app.use(express.json())
    this.app.use(express.urlencoded({ extended: true }))
    
    this.setupRoutes()
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        service: 'airtable-export-webhook',
        lastExport: this.lastExport,
        isExporting: this.isExporting,
        timestamp: new Date().toISOString()
      })
    })

    // Airtable webhook receiver
    this.app.post('/webhooks/airtable', async (req, res) => {
      console.log('📥 Airtable webhook received:', new Date().toISOString())
      console.log('📋 Payload:', JSON.stringify(req.body, null, 2))
      
      try {
        // Always respond 200 to prevent webhook retries
        res.status(200).json({ 
          status: 'received', 
          message: 'Webhook processed successfully' 
        })
        
        // Trigger export asynchronously
        this.triggerExport('airtable_webhook')
        
      } catch (error) {
        console.error('❌ Error processing webhook:', error)
        res.status(200).json({ 
          status: 'error', 
          message: 'Error processing webhook but accepted' 
        })
      }
    })

    // Manual trigger endpoint
    this.app.post('/trigger/export', async (req, res) => {
      console.log('🔄 Manual export trigger received')
      
      try {
        const result = await this.triggerExport('manual_trigger')
        res.json({
          status: 'success',
          message: 'Export triggered successfully',
          result
        })
      } catch (error) {
        console.error('❌ Manual export trigger failed:', error)
        res.status(500).json({
          status: 'error',
          message: 'Export trigger failed',
          error: error.message
        })
      }
    })

    // Get export status
    this.app.get('/status', async (req, res) => {
      try {
        const statusPath = path.join(__dirname, '../app/public/api/dev/data/exports/status.json')
        const status = await fs.readFile(statusPath, 'utf8')
        res.json(JSON.parse(status))
      } catch (error) {
        res.status(404).json({
          status: 'unknown',
          message: 'No export status available'
        })
      }
    })
  }

  async triggerExport(source = 'unknown') {
    if (this.isExporting) {
      console.log('⏳ Export already in progress, skipping...')
      return { status: 'skipped', reason: 'export_in_progress' }
    }

    try {
      this.isExporting = true
      console.log(`🚀 Triggering Airtable export (source: ${source})...`)
      
      // Run the export script
      const exportScriptPath = path.join(__dirname, 'airtable-export-dev.mjs')
      const result = execSync(`node ${exportScriptPath}`, {
        cwd: __dirname,
        encoding: 'utf8',
        maxBuffer: 1024 * 1024 * 10 // 10MB buffer
      })
      
      this.lastExport = new Date().toISOString()
      
      console.log('✅ Export completed successfully')
      console.log('📄 Export output:', result)
      
      return {
        status: 'success',
        triggeredBy: source,
        completedAt: this.lastExport,
        output: result
      }
      
    } catch (error) {
      console.error('❌ Export failed:', error)
      throw error
    } finally {
      this.isExporting = false
    }
  }

  start() {
    this.app.listen(this.port, () => {
      console.log(`🎯 Airtable Export Webhook Server Started`)
      console.log(`🌐 Listening on port: ${this.port}`)
      console.log(`📡 Webhook endpoint: http://localhost:${this.port}/webhooks/airtable`)
      console.log(`🔄 Manual trigger: POST http://localhost:${this.port}/trigger/export`)
      console.log(`📊 Status check: GET http://localhost:${this.port}/status`)
      console.log(`💚 Health check: GET http://localhost:${this.port}/health`)
      console.log('===============================================')
    })
  }
}

// Start the webhook server
const webhookServer = new WebhookExportTrigger()
webhookServer.start()

export default WebhookExportTrigger