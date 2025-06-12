#!/usr/bin/env node
/**
 * AirScripts API Server with HTTPS
 * Provides secure endpoints for Airtable button automations
 */

require('dotenv').config();
const express = require('express');
const https = require('https');
const fs = require('fs');
const morgan = require('morgan');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

// Import route handlers
const jobRoutes = require('./routes/jobs');
const scheduleRoutes = require('./routes/schedules');

const app = express();
const PORT = process.env.HTTPS_PORT || 3443;

// Middleware
app.use(morgan('combined'));

// More permissive CORS for Airtable
app.use((req, res, next) => {
  const origin = req.headers.origin;
  
  // Log all requests for debugging
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path} from origin: ${origin}`);
  
  // Allow Airtable and common origins
  if (!origin || 
      origin.includes('airtable.com') || 
      origin.includes('localhost') ||
      origin === 'https://servativ.themomentcatchers.com') {
    res.setHeader('Access-Control-Allow-Origin', origin || '*');
    res.setHeader('Access-Control-Allow-Credentials', 'true');
  } else {
    // For other origins, still allow but log it
    res.setHeader('Access-Control-Allow-Origin', '*');
    console.log('WARNING: Request from unexpected origin:', origin);
  }
  
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, HEAD');
  res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, X-API-Key');
  res.setHeader('Access-Control-Max-Age', '86400');
  
  // Handle preflight immediately
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  next();
});

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
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

// Test endpoint for debugging
app.get('/api/test', (req, res) => {
  res.json({ 
    success: true, 
    message: 'API is working',
    timestamp: new Date().toISOString(),
    headers: req.headers
  });
});


// Routes - Environment-specific endpoints
app.use('/api/dev/jobs', (req, res, next) => { req.forceEnvironment = 'development'; next(); }, jobRoutes);
app.use('/api/dev/schedules', (req, res, next) => { req.forceEnvironment = 'development'; next(); }, scheduleRoutes);
app.use('/api/prod/jobs', (req, res, next) => { req.forceEnvironment = 'production'; next(); }, jobRoutes);
app.use('/api/prod/schedules', (req, res, next) => { req.forceEnvironment = 'production'; next(); }, scheduleRoutes);

// Legacy routes (use current ENVIRONMENT setting)
app.use('/api/jobs', jobRoutes);
app.use('/api/schedules', scheduleRoutes);

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

// Root redirect
app.get('/', (req, res) => {
  res.redirect('/health');
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});

// HTTPS server options - Using Let's Encrypt certificates
const httpsOptions = {
  key: fs.readFileSync('./certs/letsencrypt-key.pem'),
  cert: fs.readFileSync('./certs/letsencrypt-cert.pem')
};

// Start HTTPS server
https.createServer(httpsOptions, app).listen(PORT, () => {
  const { getAirtableConfig, getHCPConfig } = require('./utils/config');
  const airtableConfig = getAirtableConfig();
  const hcpConfig = getHCPConfig();
  
  console.log(`🔐 AirScripts API server running with HTTPS on port ${PORT}`);
  console.log(`🌐 https://servativ.themomentcatchers.com:${PORT}`);
  console.log(`Node Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`Airtable Environment: ${process.env.ENVIRONMENT || 'development'}`);
  console.log(`Using Airtable Base: ${airtableConfig.baseId}`);
  console.log(`Using HCP Employee: ${hcpConfig.employeeId}`);
});