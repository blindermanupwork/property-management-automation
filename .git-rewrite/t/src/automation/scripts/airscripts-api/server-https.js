#!/usr/bin/env node
/**
 * AirScripts API Server with HTTPS/Let's Encrypt
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

// Middleware
app.use(morgan('combined'));
app.use(cors({
  origin: ['https://airtable.com', 'https://blocks.airtable.com'],
  credentials: true
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
  if (!apiKey || apiKey !== process.env.API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});

// Routes - Environment-specific endpoints
app.use('/api/dev/jobs', (req, res, next) => { req.forceEnvironment = 'development'; next(); }, jobRoutes);
app.use('/api/dev/schedules', (req, res, next) => { req.forceEnvironment = 'development'; next(); }, scheduleRoutes);
app.use('/api/prod/jobs', (req, res, next) => { req.forceEnvironment = 'production'; next(); }, jobRoutes);
app.use('/api/prod/schedules', (req, res, next) => { req.forceEnvironment = 'production'; next(); }, scheduleRoutes);

// Legacy routes (use current ENVIRONMENT setting)
app.use('/api/jobs', jobRoutes);
app.use('/api/schedules', scheduleRoutes);

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

// Use Greenlock for automatic HTTPS
const greenlock = require('greenlock-express').init({
  packageRoot: __dirname,
  configDir: './greenlock.d',
  cluster: false,
  maintainerEmail: 'admin@themomentcatchers.com',
  agreeTos: true,
  sites: [{
    subject: 'servativ.themomentcatchers.com',
    altnames: ['servativ.themomentcatchers.com']
  }]
});

// Start HTTPS server
greenlock.serve(app).ready((glx) => {
  const { getAirtableConfig, getHCPConfig } = require('./utils/config');
  const airtableConfig = getAirtableConfig();
  const hcpConfig = getHCPConfig();
  
  console.log('🔐 AirScripts API server running with HTTPS');
  console.log(`🌐 https://servativ.themomentcatchers.com`);
  console.log(`Node Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`Airtable Environment: ${process.env.ENVIRONMENT || 'development'}`);
  console.log(`Using Airtable Base: ${airtableConfig.baseId}`);
  console.log(`Using HCP Employee: ${hcpConfig.employeeId}`);
});