# Master Documentation Index - Property Management Automation System
**Version Date: July 11, 2025**
**System Version: 2.2.8**

## Executive Summary

This index consolidates all documentation for the property management automation system. The system processes 300+ reservations daily from multiple sources (CloudMailin, Evolve, ICS feeds) and integrates with Airtable and HousecallPro for comprehensive property management.

---

## 📚 Primary Documentation (Created July 11, 2025)

### 1. **[Comprehensive Business Rules Guide](./COMPREHENSIVE_BUSINESS_RULES_GUIDE_7-11-25.md)**
- Complete catalog of all business logic
- Reservation management rules
- Service type determination
- Scheduling and synchronization rules
- Customer and financial management

### 2. **[Technical Setup and Architecture Guide](./TECHNICAL_SETUP_AND_ARCHITECTURE_GUIDE_7-11-25.md)**
- Infrastructure requirements
- System setup procedures
- Architecture diagrams
- Deployment instructions
- Troubleshooting guide

---

## 📁 Existing Documentation

### System Overview
- **[SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md)** - High-level architecture and design
- **[sync-field-business-rules.md](./sync-field-business-rules.md)** - Field update rules and message formatting
- **[/home/opc/automation/README.md](../README.md)** - Project introduction and quick start
- **[/home/opc/automation/CLAUDE.md](../CLAUDE.md)** - AI assistant instructions (v2.2.8)
- **[/home/opc/automation/TASK_TRACKER.md](../TASK_TRACKER.md)** - Active development tasks

### API Documentation
- **[docs/api/](./api/)** - API endpoint specifications
- **[src/automation/scripts/airscripts-api/README.md](../src/automation/scripts/airscripts-api/README.md)** - API server documentation

### Deployment Guides
- **[docs/deployment/](./deployment/)** - Production deployment procedures
- **[src/automation/scripts/system/](../src/automation/scripts/system/)** - Cron setup scripts

### Testing Documentation
- **[docs/testing/](./testing/)** - Test procedures and scenarios
- **[testing/test-scenarios/](../testing/test-scenarios/)** - Test data files

---

## 🗂️ Key Configuration Files

### Environment Configuration
```
config/environments/
├── dev/
│   └── .env          # Development environment variables
└── prod/
    └── .env          # Production environment variables
```

### Templates
- **[hcp_job_templates.json](../src/automation/config/templates/hcp_job_templates.json)** - HCP job templates

---

## 🚨 Critical Information for Handoff

### 1. **Environment Separation**
- **Development**: Airtable base `app67yWFv0hKdl6jM`
- **Production**: Airtable base `appZzebEIqCU5R9ER`
- Complete isolation - no shared credentials or data

### 2. **Key Credentials (Store Securely)**
- Airtable API keys (separate for dev/prod)
- HousecallPro API keys and webhook secrets
- CloudMailin webhook authentication
- Evolve portal credentials

### 3. **Critical URLs**
- **Production Webhook**: `https://servativ.themomentcatchers.com/webhooks/hcp`
- **Development Webhook**: `https://servativ.themomentcatchers.com/webhooks/hcp-dev`
- **API Server**: `https://servativ.themomentcatchers.com/api/`

### 4. **Service Management**
```bash
# Key services
sudo systemctl status airscripts-api-https   # API server
sudo systemctl status webhook                # Production webhooks
sudo systemctl status webhook-dev            # Development webhooks
sudo systemctl status nginx                  # Web server

# View logs
tail -f /home/opc/automation/src/automation/logs/automation_prod.log
tail -f /home/opc/automation/src/automation/logs/webhook.log
```

### 5. **Daily Operations**
- Automation runs every 4 hours (prod on hour, dev at :10)
- CSV files process immediately via CloudMailin
- Webhook updates process within 30 seconds
- ICS feeds sync with 4-hour cycle

---

## 🗑️ Obsolete Files to Clean Up

### Debug Scripts (Can be removed)
- `/home/opc/automation/debug-*.py`
- `/home/opc/automation/find-*.py`
- `/home/opc/automation/track-*.py`

### Old Documentation
- Various reconciliation reports and logs
- Cleanup shell scripts
- Old Airtable table references

### Complete list in: [Comprehensive Business Rules Guide - Section 7](./COMPREHENSIVE_BUSINESS_RULES_GUIDE_7-11-25.md#7-identify-unnecessaryobsolete-files-and-components)

---

## 🔧 Quick Reference Commands

### Run Automation Manually
```bash
# Development
python3 /home/opc/automation/src/run_automation_dev.py

# Production
python3 /home/opc/automation/src/run_automation_prod.py
```

### Test Specific Components
```bash
# Test CSV processing
python3 src/automation/scripts/CSVtoAirtable/csvProcess.py --file test.csv --dry-run

# Test ICS sync
python3 src/automation/scripts/icsAirtableSync/icsProcess.py --dry-run

# Run Evolve scraper
ENVIRONMENT=production python3 src/automation/scripts/evolve/evolveScrape.py --headless
```

### Check System Health
```bash
# API health check
curl https://servativ.themomentcatchers.com/api/health

# Test webhooks
curl -X POST https://servativ.themomentcatchers.com/webhooks/hcp-dev \
  -H "Content-Type: application/json" -d '{"test":true}'
```

---

## 📊 System Metrics

### Current Scale (as of July 2025)
- **Daily Reservations**: 300+
- **ICS Feeds**: 246 (production), 255 (development)
- **Properties**: 150+ active
- **Service Jobs**: 100+ daily
- **Data Volume**: 1.69GB total

### Performance Targets
- CSV processing: < 2 minutes per file
- ICS sync: < 10 minutes for all feeds
- Webhook processing: < 30 seconds
- API response: < 200ms average

---

## 👥 Contact Information

### System Architecture
- Original design and implementation by Boris
- Enhanced documentation July 11, 2025

### Support Resources
- GitHub Issues: Report bugs and feature requests
- Logs: Primary debugging resource
- MCP Servers: Enhanced analysis capabilities

---

## 🚀 Next Steps for New Maintainer

1. **Review Primary Documentation**
   - Start with Business Rules Guide
   - Then Technical Setup Guide

2. **Set Up Development Environment**
   - Clone repository
   - Configure environment variables
   - Test each component

3. **Understand Data Flow**
   - Trace a reservation from CSV to HCP job
   - Review webhook processing
   - Examine sync mechanisms

4. **Practice Common Operations**
   - Create test reservations
   - Trigger job creation
   - Handle schedule changes

5. **Monitor System Health**
   - Check logs daily
   - Review error patterns
   - Optimize as needed

---

This master index provides a complete roadmap to understanding and maintaining the property management automation system. All documentation is current as of July 11, 2025.