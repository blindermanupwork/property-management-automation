# AirScripts API Service

Secure API service that replaces Airtable's embedded scripts with a proper backend implementation. Eliminates the need to store HCP tokens in Airtable and provides better error handling, logging, and version control.

## 🚀 Quick Start

The API server is already deployed and running as a systemd service on port 3002.

### Check Status
```bash
# Check if service is running
sudo systemctl status airscripts-api

# View real-time logs
sudo journalctl -u airscripts-api -f

# View log file
tail -f /var/log/airscripts-api.log
```

### Environment Management
```bash
# View current configuration
tail -5 /var/log/airscripts-api.log

# Switch between dev/prod Airtable bases
sudo nano /home/opc/automation/src/automation/scripts/airscripts-api/.env
# Change: ENVIRONMENT=development  (uses dev base)
# Or:     ENVIRONMENT=production   (uses prod base)

# Restart to apply changes
sudo systemctl restart airscripts-api
```

## 🏗️ Architecture

```
Airtable Button → Simple Script → API Endpoint → Business Logic → HCP/Airtable APIs
```

**Before Migration**: Complex 600+ line scripts in Airtable with exposed secrets  
**After Migration**: Simple 50-line button scripts + secure API backend

## 📡 API Endpoints

### Jobs Management
- `POST /api/jobs/create` - Create single HCP job
  ```json
  { "recordId": "recXXXXXXXXXXXXXX" }
  ```
- `POST /api/jobs/create-batch` - Create multiple jobs
  ```json
  { "recordIds": ["recXXX...", "recYYY..."] }
  ```
- `DELETE /api/jobs/:jobId` - Delete a job
  ```json
  { "recordId": "recXXXXXXXXXXXXXX" }
  ```

### Schedule Management
- `POST /api/schedules/check` - Check all schedules (no body required)
- `POST /api/schedules/update` - Update single schedule
  ```json
  { "recordId": "recXXXXXXXXXXXXXX" }
  ```
- `POST /api/schedules/update-batch` - Update multiple schedules
  ```json
  { "recordIds": ["recXXX...", "recYYY..."] }
  ```

### System
- `GET /health` - Health check (no auth required)

## 🔒 Security Features

- **API Key Authentication**: All endpoints require `X-API-Key` header
- **CORS Protection**: Only allows requests from Airtable domains
- **Rate Limiting**: 100 requests per minute per IP
- **Environment Isolation**: Separate dev/prod configurations
- **Secure Secrets**: All tokens in environment variables, not Airtable

## 🔧 Configuration

### Environment Variables (.env)
```bash
# API Server
NODE_ENV=production                           # Node environment (always production for systemd)
PORT=3002                                     # Server port
API_KEY=your-secure-api-key-here             # API authentication key

# Environment Selection (THIS controls which Airtable base to use)
ENVIRONMENT=development                       # 'development' or 'production'

# Development Airtable
DEV_AIRTABLE_API_KEY=pat...                  # Your dev API key
DEV_AIRTABLE_BASE_ID=app...                  # Your dev base ID

# Production Airtable  
PROD_AIRTABLE_API_KEY=pat...                 # Your prod API key
PROD_AIRTABLE_BASE_ID=app...                 # Your prod base ID

# HousecallPro
HCP_TOKEN=your-hcp-token-here                # Your HCP API token
HCP_EMPLOYEE_ID=pro_...                      # Your HCP employee ID
```

### Switching Environments
1. Edit the `.env` file: `sudo nano .env`
2. Change `ENVIRONMENT=development` or `ENVIRONMENT=production`
3. Restart service: `sudo systemctl restart airscripts-api`
4. Verify in logs: `tail -5 /var/log/airscripts-api.log`

## 📱 Airtable Button Integration

### Replace Complex AirScripts
Instead of 600+ line scripts in Airtable, use simple API calls:

```javascript
// Example: Create Job Button Script
const API_URL = 'http://localhost:3002/api/jobs/create';
const API_KEY = 'your-api-key-here';

const table = base.getTable('Reservations');
const record = await input.recordAsync('Select reservation:', table);

if (!record) {
  output.text('No record selected');
  return;
}

try {
  const response = await remoteFetchAsync(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({ recordId: record.id })
  });

  const result = await response.json();
  
  if (!response.ok) {
    throw new Error(result.error);
  }

  output.markdown(`✅ Job created: ${result.jobId}`);
} catch (error) {
  output.markdown(`❌ Error: ${error.message}`);
}
```

### Sample Button Scripts Available
- `airtable-button-scripts/create-job-button.js` - Create single job
- `airtable-button-scripts/create-all-jobs-button.js` - Batch create jobs

## 🔍 Monitoring & Debugging

### Service Management
```bash
# Service status
sudo systemctl status airscripts-api

# Start/stop/restart
sudo systemctl start airscripts-api
sudo systemctl stop airscripts-api
sudo systemctl restart airscripts-api

# Enable/disable auto-start
sudo systemctl enable airscripts-api
sudo systemctl disable airscripts-api
```

### Logging
```bash
# Real-time logs
sudo journalctl -u airscripts-api -f

# Application logs
tail -f /var/log/airscripts-api.log

# Error logs  
tail -f /var/log/airscripts-api.error.log

# View specific number of log lines
tail -50 /var/log/airscripts-api.log
```

### Health Checks
```bash
# Basic health check
curl http://localhost:3002/health

# Test API authentication
curl -X POST http://localhost:3002/api/jobs/create \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"recordId": "test"}'
```

## 🚀 Features & Benefits

### ✅ What This Solves
- **Security**: HCP tokens no longer exposed in Airtable
- **Reliability**: Better error handling and retry logic
- **Maintainability**: All code in Git with version control
- **Performance**: Optimized API calls and connection pooling
- **Debugging**: Comprehensive logging and error tracking

### 🔧 Smart Features
- **Custom Service Line Support**: Uses "Custom Service Line Description" field if populated
- **Environment Awareness**: Automatically switches between dev/prod Airtable bases
- **Appointment ID Capture**: Automatically fetches and stores appointment IDs
- **Same-day Detection**: Handles same-day turnarounds appropriately
- **Next Guest Logic**: Automatically determines next guest dates

### 📊 Supported Operations
- ✅ Create single HCP jobs
- ✅ Batch create multiple jobs  
- ✅ Delete jobs
- ✅ Sync job schedules
- ✅ Update job statuses
- ✅ Handle appointment IDs
- ✅ Process custom service lines

## 🛠️ Development

### Making Changes
1. Edit files in `/home/opc/automation/src/automation/scripts/airscripts-api/`
2. Test locally: `npm run dev` (on different port)
3. Deploy changes: `sudo systemctl restart airscripts-api`
4. Monitor logs: `tail -f /var/log/airscripts-api.log`

### Adding New Endpoints
1. Add route in `routes/` directory
2. Add handler in `handlers/` directory
3. Update this README
4. Restart service

### File Structure
```
/home/opc/automation/src/automation/scripts/airscripts-api/
├── server.js                           # Main Express server
├── package.json                        # Dependencies
├── .env                               # Environment configuration
├── routes/
│   ├── jobs.js                        # Job endpoints
│   └── schedules.js                   # Schedule endpoints
├── handlers/
│   ├── jobs.js                        # Job business logic
│   └── schedules.js                   # Schedule business logic
├── utils/
│   ├── config.js                      # Environment-aware config
│   └── datetime.js                    # Date/time utilities
└── airtable-button-scripts/           # Sample button scripts
    ├── create-job-button.js
    └── create-all-jobs-button.js
```

## ⚠️ Important Notes

1. **Always restart after .env changes**: Environment variables are only loaded at startup
2. **Check logs after changes**: Verify correct environment is loaded
3. **Test in development first**: Use `ENVIRONMENT=development` for testing
4. **API key security**: Never commit the API key to Git or share in documentation
5. **Port conflicts**: Service runs on port 3002 by default
6. **Replace placeholder values**: All examples use placeholder values - update with your actual credentials

## 🆘 Troubleshooting

### Service Won't Start
```bash
# Check for port conflicts
ss -tlnp | grep :3002

# Check service logs
sudo journalctl -u airscripts-api --no-pager

# Verify .env file
cat .env
```

### Wrong Airtable Base
```bash
# Check current environment
tail -5 /var/log/airscripts-api.log

# Should show: "Airtable Environment: development" or "production"
# And: "Using Airtable Base: app67yWFv0hKdl6jM" (dev) or "appZzebEIqCU5R9ER" (prod)
```

### API Calls Failing
```bash
# Test health endpoint
curl http://localhost:3002/health

# Test authentication
curl -H "X-API-Key: your-api-key-here" http://localhost:3002/api/jobs/create

# Check error logs
tail -20 /var/log/airscripts-api.error.log
```