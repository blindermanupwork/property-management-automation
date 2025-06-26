# Airtable Job Reconciliation Button Setup Guide

This guide explains how to set up the "Run Now" button in Airtable for the Job Reconciliation automation.

## Overview

The Job Reconciliation feature matches unlinked HousecallPro jobs to Airtable reservations based on:
- Property (customer/address match)
- Scheduled time (within 1 hour window)
- No existing Service Job ID

## Prerequisites

1. **Automation Control Table**: You must have an "Automation Control" table in your Airtable base with:
   - `Name` field (text)
   - `Active` field (checkbox)
   - `Last Ran Time` field (date/time)
   - `Sync Details` field (long text)

2. **Job Reconciliation Record**: Add a record with:
   - Name: `Job Reconciliation`
   - Active: ✓ (checked)

3. **API Access**: Ensure the AirScripts API server is running:
   ```bash
   sudo systemctl status airscripts-api-https
   ```

## Button Configuration

### Development Environment

1. **Add Button Field** to your Automation Control table:
   - Field Type: Button
   - Field Name: `Run Reconciliation (Dev)`

2. **Configure Button**:
   - Label: `Run Reconciliation`
   - Action: `Run webhook`
   - URL: `https://servativ.themomentcatchers.com/api/dev/reconcile-jobs`
   - HTTP Method: `POST`
   - Add Header:
     - Header Name: `X-API-Key`
     - Header Value: `[Your API Key from .env]`
   - Request Body:
     ```json
     {
       "mode": "execute"
     }
     ```

### Production Environment

1. **Add Button Field** to your Automation Control table:
   - Field Type: Button
   - Field Name: `Run Reconciliation (Prod)`

2. **Configure Button**:
   - Label: `Run Reconciliation`
   - Action: `Run webhook`
   - URL: `https://servativ.themomentcatchers.com/api/prod/reconcile-jobs`
   - HTTP Method: `POST`
   - Add Header:
     - Header Name: `X-API-Key`
     - Header Value: `[Your API Key from .env]`
   - Request Body:
     ```json
     {
       "mode": "execute"
     }
     ```

## Usage

### Manual Execution via Button

1. Navigate to your Automation Control table
2. Find the "Job Reconciliation" record
3. Click the "Run Reconciliation" button
4. Check the `Sync Details` field for results

### Automatic Execution (Every 4 Hours)

The reconciliation automatically runs after main automations complete if:
- The "Job Reconciliation" record is marked as Active (✓)
- The main automation suite runs (every 4 hours via cron)

### Dry-Run Testing

To test without making changes, run from command line:

```bash
# Development dry-run
python3 /home/opc/automation/src/automation/scripts/hcp/reconcile-jobs.py --env dev

# Production dry-run
python3 /home/opc/automation/src/automation/scripts/hcp/reconcile-jobs.py --env prod
```

## Response Format

The button webhook returns a JSON response:

```json
{
  "success": true,
  "environment": "dev",
  "mode": "execute",
  "results": {
    "total": 15,
    "matched": 3,
    "already_linked": 10,
    "no_match": 2,
    "errors": 0,
    "matches": [
      {
        "job_id": "job_123",
        "reservation_id": "rec_456",
        "property": "Property Name",
        "time_diff_minutes": 15.5
      }
    ]
  },
  "message": "Successfully executed reconciliation"
}
```

## Monitoring

### Check Logs

```bash
# API server logs
sudo journalctl -u airscripts-api-https -f

# Automation logs (includes reconciliation)
tail -f /home/opc/automation/src/automation/logs/automation_dev*.log
tail -f /home/opc/automation/src/automation/logs/automation_prod*.log
```

### Verify Results

After reconciliation:
1. Check the `Sync Details` field in Automation Control
2. Look for updated `Service Job ID` fields in your Reservations table
3. Verify `Sync Status` changed to "Matched" for reconciled records

## Troubleshooting

### Button Not Working

1. **Check API Key**: Ensure the X-API-Key header matches your .env file
2. **Verify URL**: Confirm you're using the correct environment endpoint
3. **Test API**: 
   ```bash
   curl -X POST https://servativ.themomentcatchers.com/api/dev/reconcile-jobs \
     -H "X-API-Key: YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"mode": "execute"}'
   ```

### No Matches Found

1. **Time Window**: Jobs must be within 1 hour of reservation time
2. **Property Setup**: Ensure properties have HCP Customer ID and HCP Address ID
3. **Job Status**: Only unlinked jobs (no Service Job ID) are considered

### Performance

- Reconciliation typically processes 50-100 jobs per second
- Large datasets (1000+ jobs) may take 10-30 seconds
- The process is optimized to minimize API calls

## Security Notes

- Never expose your API key in Airtable formulas or public fields
- The API endpoint requires authentication
- All actions are logged for audit purposes