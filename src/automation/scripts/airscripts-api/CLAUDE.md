# AirScripts API - Claude Code Guidance

This file provides specific guidance for Claude Code when working with the AirScripts API service.

## Project Overview

The AirScripts API is a Node.js Express server that replaces complex Airtable embedded scripts with secure backend APIs. It provides HousecallPro job management functionality through authenticated HTTP endpoints.

## Architecture

- **Main Server**: `server.js` - Express server with environment-specific routing
- **Routes**: 
  - `/api/dev/jobs` - Development job endpoints
  - `/api/prod/jobs` - Production job endpoints  
  - `/api/dev/schedules` - Development schedule endpoints
  - `/api/prod/schedules` - Production schedule endpoints
- **Environment Separation**: Complete isolation between dev and prod Airtable bases
- **Security**: API key authentication, CORS protection, rate limiting

## Critical Files

### Core Application
- `server.js` - Main Express server (DO NOT MODIFY structure)
- `package.json` - Dependencies (safe to update dependencies)

### Business Logic
- `handlers/jobs.js` - Job management handlers including createJob, cancelJob functions (safe to modify)
- `handlers/schedules.js` - Schedule management (safe to modify)
- `routes/jobs.js` - Job routing (imports handlers from `handlers/jobs.js`)
- `routes/schedules.js` - Schedule routing (safe to modify routing logic)

### Services & Utilities
- `services/airtable.js` - Airtable API integration (safe to modify)
- `services/hcp.js` - HousecallPro API integration (safe to modify)
- `utils/config.js` - Environment configuration (safe to modify)
- `utils/datetime.js` - Date/time utilities (safe to modify)

### Configuration & Deployment
- `.env` - Environment variables (**NEVER COMMIT** - contains secrets)
- `deploy.sh` - Deployment script (safe to modify)
- `*.service` - Systemd service files (safe to modify)

### Test Scripts
- `scripts/dev-*.js` - Development test scripts (safe to modify/add)
- `scripts/prod-*.js` - Production test scripts (safe to modify/add)

## Environment Management

The service uses a dual environment system:
- `NODE_ENV=production` (always for systemd service)
- `ENVIRONMENT=development|production` (controls which Airtable base)

**Important**: When environment changes are made:
1. Restart the service: `sudo systemctl restart airscripts-api`
2. Check logs: `tail -f /var/log/airscripts-api.log`
3. Verify correct environment loaded

## Development Guidelines

### Safe Operations
✅ **Safe to modify**:
- Business logic in `handlers/`
- Route implementations
- Service integrations
- Utility functions
- Test scripts
- Documentation

✅ **Safe to add**:
- New handlers for additional functionality
- New utility functions
- New test scripts
- Additional middleware

### Dangerous Operations
⚠️ **Requires caution**:
- `server.js` structure changes
- Authentication middleware
- CORS configuration
- Rate limiting settings

❌ **Never do**:
- Commit `.env` files
- Remove environment separation
- Disable security features
- Hard-code credentials

## Testing

### Local Development
```bash
# Test in development mode
NODE_ENV=development npm run dev

# Test specific endpoints
node scripts/dev-create-job.js
node scripts/dev-update-schedule-single.js
```

### Production Testing
```bash
# Test production scripts
node scripts/prod-create-job.js
node scripts/prod-update-schedule-single.js
```

## Service Management

### Status & Logs
```bash
# Check service status
sudo systemctl status airscripts-api-https

# View logs
sudo journalctl -u airscripts-api-https -f
tail -f server.log
```

### Restart After Changes
```bash
# Restart service
sudo systemctl restart airscripts-api-https

# Verify environment
tail -5 server.log
```

## Security Notes

1. **API Keys**: Never commit API keys - use environment variables
2. **Environment Separation**: Maintain strict dev/prod isolation
3. **CORS**: Only allows Airtable domains - verify before modifying
4. **Rate Limiting**: 100 req/min per IP - adjust if needed
5. **Authentication**: All `/api/` endpoints require `X-API-Key` header

## Common Issues

### Wrong Environment
**Symptom**: API calls succeed but affect wrong Airtable base
**Solution**: Check `ENVIRONMENT` variable in `.env`, restart service

### Authentication Failures  
**Symptom**: 401 Unauthorized responses
**Solution**: Verify API key in request headers and `.env` file

### Port Conflicts
**Symptom**: Service won't start
**Solution**: Check for processes on port 3002: `ss -tlnp | grep :3002`

## Business Logic Integration

### HousecallPro Job Creation
- Uses HCP API v1 endpoints
- Requires valid HCP token and employee ID
- Handles appointment scheduling automatically
- Supports custom service line instructions (200 char limit)
- **Long-term Guest Detection**: Automatically adds "LONG TERM GUEST DEPARTING" prefix for 14+ day stays
- **Handler Location**: `handlers/jobs.js` (not createJob.js which was removed)

### Airtable Integration
- Environment-aware base selection
- Preserves HCP sync fields
- Updates job status and sync details
- Handles both dev and prod bases seamlessly

## Claude Code Specific Notes

When working with this codebase:
1. **Always check environment**: Verify which Airtable base is being used
2. **Test thoroughly**: Use both dev and prod test scripts
3. **Monitor logs**: Check service logs after changes
4. **Preserve security**: Don't disable authentication or CORS
5. **Restart service**: Required after any .env changes

This service is a critical production component that handles real customer data - test changes carefully in development first.