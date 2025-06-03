# AirScripts Migration Guide - COMPLETED ✅

This guide documents the **completed migration** of AirScripts from Airtable's scripting environment to a secure, self-hosted API service.

## 🎉 Migration Status: COMPLETE

The API server is **deployed and running** as a systemd service on port 3002 with full environment awareness.

## 📊 Migration Results

### ✅ Completed
- **API Server**: Deployed as systemd service on port 3002
- **Environment Configuration**: Development/production awareness working
- **Security**: HCP tokens moved from Airtable to server environment
- **Custom Service Line Support**: Implemented in all handlers
- **Logging**: Comprehensive logging with file and systemd integration
- **Health Monitoring**: Health endpoint and service status tracking

### 🔄 Current State

| Component | Status | Details |
|-----------|--------|---------|
| API Server | ✅ Running | Port 3002, systemd service |
| Environment | ✅ Development | Using dev Airtable base |
| Authentication | ✅ Working | API key protection enabled |
| Health Check | ✅ Active | `/health` endpoint responding |
| Logging | ✅ Active | File and systemd logs working |

## 🏗️ Architecture Achieved

```
Airtable Button → Simple Script → API Server (Port 3002) → HCP/Airtable APIs
```

**Before**: 600+ line scripts in Airtable with exposed HCP tokens  
**After**: 50-line button scripts + secure API backend with environment isolation

## 📡 API Endpoints Ready

### ✅ Implemented & Tested
- `GET /health` - Health check ✅
- `POST /api/jobs/create` - Create single HCP job ✅  
- `POST /api/jobs/create-batch` - Create multiple jobs ✅
- `DELETE /api/jobs/:jobId` - Delete a job ✅
- `POST /api/schedules/check` - Check all schedules ✅
- `POST /api/schedules/update` - Update single schedule ✅
- `POST /api/schedules/update-batch` - Update multiple schedules ✅

### 🔧 Features Implemented
- **Custom Service Line Description** support
- **Environment-aware** Airtable base selection
- **Appointment ID** capture and storage
- **Same-day turnover** detection
- **Next guest date** logic
- **Comprehensive error handling**

## 🚀 How to Use (Production Ready)

### 1. Check Current Status
```bash
# Verify service is running
sudo systemctl status airscripts-api

# Check current environment
tail -5 /var/log/airscripts-api.log
```

### 2. Switch Environments
```bash
# Edit environment setting
sudo nano /home/opc/automation/src/automation/scripts/airscripts-api/.env

# Change this line:
ENVIRONMENT=development  # Uses dev Airtable base
# Or:
ENVIRONMENT=production   # Uses prod Airtable base

# Apply changes
sudo systemctl restart airscripts-api

# Verify change
tail -5 /var/log/airscripts-api.log
```

### 3. Create Airtable Button Scripts

Replace your complex AirScripts with simple API calls:

```javascript
// Example: Create Job Button (50 lines vs 600+ before)
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

  output.markdown(`
### ✅ Job Created Successfully!
- **Job ID**: ${result.jobId}
- **Service Line**: ${result.serviceLine}
- **Scheduled Time**: ${new Date(result.scheduledTime).toLocaleString()}
${result.appointmentId ? `- **Appointment ID**: ${result.appointmentId}` : ''}
  `);
} catch (error) {
  output.markdown(`### ❌ Error: ${error.message}`);
}
```

## 🔒 Security Improvements Achieved

### ✅ Before vs After

| Security Aspect | Before | After |
|-----------------|--------|-------|
| HCP Token Storage | ❌ Visible in Airtable | ✅ Secure environment variables |
| API Key Management | ❌ Hardcoded in scripts | ✅ Server-side authentication |
| Code Version Control | ❌ No versioning | ✅ Full Git integration |
| Error Logging | ❌ Limited visibility | ✅ Comprehensive server logs |
| Environment Isolation | ❌ Mixed dev/prod | ✅ Separate configurations |

## 📱 Button Migration Strategy

### Recommended Approach
1. **Start with one button** (e.g., Create Job)
2. **Test thoroughly** in development environment
3. **Monitor logs** for any issues
4. **Gradually migrate** other buttons
5. **Keep originals** as backup during transition

### Priority Order
1. **Create Job** (most used)
2. **Batch Create Jobs** (high impact)
3. **Update Schedule** (frequent)
4. **Check Schedules** (monitoring)
5. **Delete Job** (less frequent)

## 🔍 Monitoring & Maintenance

### Daily Checks
```bash
# Service health
sudo systemctl status airscripts-api

# Recent activity
tail -20 /var/log/airscripts-api.log

# Error check
tail -10 /var/log/airscripts-api.error.log
```

### Weekly Maintenance
```bash
# Log rotation (if needed)
sudo journalctl --vacuum-time=7d

# Service restart (optional, for updates)
sudo systemctl restart airscripts-api
```

## 🛠️ Making Changes

### Environment Changes
```bash
# 1. Edit configuration
sudo nano /home/opc/automation/src/automation/scripts/airscripts-api/.env

# 2. Restart service
sudo systemctl restart airscripts-api

# 3. Verify changes
tail -5 /var/log/airscripts-api.log
```

### Code Changes
```bash
# 1. Edit files in the airscripts-api directory
# 2. Test changes if needed
# 3. Restart service
sudo systemctl restart airscripts-api

# 4. Monitor logs
tail -f /var/log/airscripts-api.log
```

## ⚠️ Important Operational Notes

1. **Environment Changes Require Restart**: Always restart after changing `.env`
2. **Check Logs After Changes**: Verify correct environment is loaded
3. **Test in Development First**: Use `ENVIRONMENT=development` for testing
4. **Monitor Performance**: Watch logs during high usage periods
5. **Backup Strategy**: Original AirScripts preserved for rollback if needed

## 🎯 Next Steps (Optional Enhancements)

### Short Term
- [ ] Add SSL/HTTPS support with nginx reverse proxy
- [ ] Implement more detailed error responses
- [ ] Add request/response logging for debugging

### Medium Term
- [ ] Add Sentry integration for error tracking
- [ ] Implement API response caching
- [ ] Add Prometheus metrics endpoint

### Long Term
- [ ] Multiple environment support (staging, etc.)
- [ ] API versioning
- [ ] Automated testing suite

## 🆘 Emergency Procedures

### Service Down
```bash
# Quick restart
sudo systemctl restart airscripts-api

# Check for issues
sudo journalctl -u airscripts-api --no-pager -l

# Verify service is running
curl http://localhost:3002/health
```

### Wrong Environment
```bash
# Check current environment
tail -5 /var/log/airscripts-api.log

# Should show correct base ID:
# Development: app67yWFv0hKdl6jM
# Production: appZzebEIqCU5R9ER
```

### Rollback to Original AirScripts
Original AirScripts are preserved in `/home/opc/automation/src/automation/scripts/airscripts/` and can be re-deployed to Airtable if needed.

## 🏆 Migration Success Metrics

✅ **Security**: HCP tokens secured (no longer in Airtable)  
✅ **Reliability**: Service running as systemd daemon  
✅ **Maintainability**: All code in Git with version control  
✅ **Performance**: Environment-aware configuration working  
✅ **Monitoring**: Comprehensive logging implemented  
✅ **Functionality**: All original features preserved and enhanced  

The migration is **complete and production-ready**! 🎉