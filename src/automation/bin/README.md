# Operational Scripts (bin/)

This directory contains all shell scripts for system operations, deployment, and maintenance.

## 📁 Scripts Overview

### **🔄 Deployment Scripts**
- **`deploy_to_prod.sh`** - Complete Git-based production deployment workflow
  ```bash
  ./bin/deploy_to_prod.sh
  ```
  - Tests in development environment first
  - Creates backup before deployment  
  - Merges dev branch to main
  - Switches to production environment
  - Updates dependencies
  - Verifies deployment health

- **`deploy.sh`** - Manual production deployment with safety checks
  ```bash
  ./bin/deploy.sh
  ```
  - Creates backup before deployment
  - Runs tests in development environment
  - Deploys to production with dependency updates
  - Verifies deployment success

### **💾 Backup & Maintenance**
- **`backup.sh`** - Comprehensive system backup
  ```bash
  ./bin/backup.sh
  ```
  - Creates full system backup (excludes logs, node_modules)
  - Creates data-only backup (CSV files, configs, credentials)
  - Automatic retention policy (14 full, 30 data backups)
  - Integrity verification
  - Size reporting

### **📊 Monitoring & Health**
- **`monitor.sh`** - Production health monitoring
  ```bash
  ./bin/monitor.sh
  ```
  - Checks for recent automation runs
  - Scans logs for errors
  - Monitors disk space usage
  - Detects stuck CSV files
  - Comprehensive health reporting
  - Alert system integration

### **⏰ Scheduling & Automation**  
- **`setup_cron.sh`** - Automated task scheduling
  ```bash
  ./bin/setup_cron.sh
  ```
  - Sets up daily automation runs (6 AM)
  - Health monitoring every 30 minutes
  - Weekly backups (Sundays 2 AM)
  - Automatic log cleanup (daily 1 AM)
  - Preserves existing crontab entries

## 🔧 Usage Examples

### Development Workflow
```bash
# Test changes locally
python run_anywhere.py --test

# Deploy to production
./bin/deploy_to_prod.sh
```

### Production Operations
```bash
# Manual deployment
./bin/deploy.sh

# Check system health
./bin/monitor.sh

# Create backup
./bin/backup.sh

# Setup automation scheduling
./bin/setup_cron.sh
```

### Maintenance
```bash
# View backup status
ls -la backups/

# Check recent logs
tail -f logs/*.log

# Monitor disk usage
df -h
```

## ⚠️ Important Notes

### **File Paths**
All scripts use absolute paths and are location-independent. They automatically detect the project root directory.

### **Environment Detection**
Scripts automatically source the correct environment configuration:
- Development: `config/environments/dev/.env`
- Production: `config/environments/prod/.env`

### **Safety Features**
- All deployment scripts run tests before deploying
- Automatic backups before any changes
- Rollback capabilities with stored backups
- Health verification after deployment

### **Logging**
All scripts log to `logs/` directory with timestamps and detailed operation tracking.

## 🔒 Security

- No credentials stored in scripts
- Environment-specific configuration isolation
- Backup integrity verification
- Secure deployment workflows

---

*These scripts provide a complete operational framework for the automation system.*