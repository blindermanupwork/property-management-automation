#!/usr/bin/env node
/**
 * AirScripts API Server
 * Provides secure endpoints for Airtable button automations
 */

require('dotenv').config();
const express = require('express');
const morgan = require('morgan');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

// Import route handlers
const jobRoutes = require('./routes/jobs');
const scheduleRoutes = require('./routes/schedules');

const app = express();
const PORT = process.env.PORT || 3000;

// Trust proxy (nginx)
app.set('trust proxy', true);

// Middleware
app.use(morgan('combined'));
app.use(cors({
  origin: [
    'https://airtable.com',
    'https://blocks.airtable.com',
    'https://block--com.airtableblocks.com',
    /^https:\/\/.*\.airtableblocks\.com$/
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'X-API-Key', 'Authorization'],
  maxAge: 86400 // 24 hours
}));
app.use(express.json());

// Rate limiting
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100 // limit each IP to 100 requests per minute
});
app.use('/api/', limiter);

// API key authentication middleware
app.use('/api/', (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  console.log(`Auth check - Path: ${req.path}, API Key received: ${apiKey ? 'Yes' : 'No'}, Expected: ${process.env.API_KEY}`);
  if (!apiKey || apiKey !== process.env.API_KEY) {
    console.log(`Auth failed - Received: "${apiKey}", Expected: "${process.env.API_KEY}"`);
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

// Routes - Environment-specific endpoints ONLY
app.use('/api/dev/jobs', (req, res, next) => { req.forceEnvironment = 'development'; next(); }, jobRoutes);
app.use('/api/dev/schedules', (req, res, next) => { req.forceEnvironment = 'development'; next(); }, scheduleRoutes);
app.use('/api/prod/jobs', (req, res, next) => { req.forceEnvironment = 'production'; next(); }, jobRoutes);
app.use('/api/prod/schedules', (req, res, next) => { req.forceEnvironment = 'production'; next(); }, scheduleRoutes);

// Catch-all for legacy routes - return error
app.use('/api/jobs', (req, res) => {
  res.status(410).json({ 
    error: 'Legacy endpoint removed. Please use /api/dev/jobs or /api/prod/jobs instead.' 
  });
});
app.use('/api/schedules', (req, res) => {
  res.status(410).json({ 
    error: 'Legacy endpoint removed. Please use /api/dev/schedules or /api/prod/schedules instead.' 
  });
});

// Serve test data files (no authentication required for testing)
app.use('/test-data', express.static('/home/opc/automation/test_data', {
  setHeaders: (res, path) => {
    if (path.endsWith('.ics')) {
      res.setHeader('Content-Type', 'text/calendar; charset=utf-8');
    }
  }
}));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server
app.listen(PORT, () => {
  const { getAirtableConfig, getHCPConfig } = require('./utils/config');
  const airtableConfig = getAirtableConfig();
  const hcpConfig = getHCPConfig();
  
  console.log(`AirScripts API server running on port ${PORT}`);
  console.log(`Node Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`Environment endpoints available:`);
  console.log(`  - DEV:  /api/dev/jobs, /api/dev/schedules`);
  console.log(`  - PROD: /api/prod/jobs, /api/prod/schedules`);
  console.log(`Legacy endpoints (/api/jobs, /api/schedules) have been removed.`);
});