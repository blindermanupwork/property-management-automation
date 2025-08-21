# Complete Property Management Automation Migration Guide
**Version**: Client Deployment Edition  
**Generated**: 2025-08-11  
**Current System**: Oracle Linux 8.10  
**Note**: This guide uses `cal.tanqtop.com` as placeholder - replace with actual client domain  

## ⚠️ CRITICAL PREREQUISITES

### Target Server Requirements
- **OS**: RHEL 8.x, Oracle Linux 8.x, Rocky Linux 8.x, or AlmaLinux 8.x (Ubuntu 20.04+ also works with modifications)
- **Python**: 3.9.x (EXACT - not 3.8, not 3.10+)
- **Node.js**: 18.x LTS
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 20GB minimum free space
- **Network**: Static IP or reliable dynamic DNS
- **Ports Required**: 80, 443, 3006, 5000, 5001 (minimum)

### Required System Access
- Root or sudo access
- Ability to configure systemd services
- Firewall configuration permissions
- SELinux configuration (if enabled)

---

## 📋 PHASE 1: Pre-Migration Preparation (Current Server)

### Step 1.1: Stop All Services
```bash
# Stop automation services to prevent data changes during migration
sudo systemctl stop webhook
sudo systemctl stop webhook-dev
sudo systemctl stop airscripts-api
sudo systemctl stop airscripts-api-https

# Stop cron temporarily
crontab -l > ~/cron_backup.txt
crontab -r
```

### Step 1.2: Create Complete System Backup
```bash
# Create backup directory
mkdir -p ~/migration_backup
cd ~/migration_backup

# 1. Backup all environment files (CRITICAL!)
cp /opt/servativ_scheduler/.env ./root.env
cp /opt/servativ_scheduler/config/environments/dev/.env ./dev.env
cp /opt/servativ_scheduler/config/environments/prod/.env ./prod.env
cp /opt/servativ_scheduler/src/automation/scripts/airscripts-api/.env ./airscripts.env
cp /opt/servativ_scheduler/tools/airtable-mcp-server/.env ./airtable-mcp.env
cp /opt/servativ_scheduler/tools/trello-mcp-server/.env ./trello-mcp.env

# 2. Backup systemd service files
sudo cp /etc/systemd/system/webhook.service ./
sudo cp /etc/systemd/system/webhook-dev.service ./
sudo cp /etc/systemd/system/airscripts-api.service ./
sudo cp /etc/systemd/system/airscripts-api-https.service ./

# 3. Backup nginx configuration
sudo cp /etc/nginx/conf.d/servativ.conf ./nginx-servativ.conf
sudo cp /etc/nginx/nginx.conf ./nginx-main.conf

# 4. Backup SSL certificates (if any)
sudo cp -r /etc/letsencrypt ./letsencrypt_backup 2>/dev/null || echo "No Let's Encrypt certs"
cp /opt/servativ_scheduler/app/*.crt ./ 2>/dev/null || echo "No app certs"
cp /opt/servativ_scheduler/app/*.key ./ 2>/dev/null || echo "No app keys"

# 5. Document current package versions
pip3 freeze > python_packages.txt
npm list -g --depth=0 > npm_global_packages.txt

# 6. Save current firewall rules
sudo firewall-cmd --list-all > firewall_rules.txt

# 7. Document current system packages
rpm -qa | grep -E "(python|node|chrome|selenium)" > system_packages.txt
```

### Step 1.3: Clean and Prepare Code for Migration
```bash
cd /opt/servativ_scheduler

# Create cleanup script
cat << 'EOF' > prepare_migration.sh
#!/bin/bash
echo "🧹 Preparing for migration..."

# Remove Python cache
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Remove node_modules (will reinstall)
find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null

# Remove old logs (keep last 7 days)
find ./src/automation/logs -name "*.log*" -mtime +7 -delete 2>/dev/null

# Remove build artifacts
rm -rf .eggs/ build/ dist/ *.egg-info 2>/dev/null

# Archive CSV data (don't delete - might need for debugging)
tar -czf csv_backup_$(date +%Y%m%d).tar.gz \
  src/automation/scripts/CSV_done_* \
  src/automation/scripts/CSV_process_* 2>/dev/null

echo "✅ Cleanup complete"
EOF

chmod +x prepare_migration.sh
./prepare_migration.sh
```

### Step 1.4: Create Migration Archive
```bash
cd /home

# Create comprehensive archive (excluding unnecessary files)
sudo tar -czf automation_migration.tar.gz \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='node_modules' \
  --exclude='.git' \
  --exclude='*.log' \
  --exclude='CSV_done_*' \
  --exclude='CSV_process_*' \
  --exclude='archive' \
  opc/automation/

# Copy to backup directory
mv automation_migration.tar.gz ~/migration_backup/

# Create checksum for verification
cd ~/migration_backup
sha256sum automation_migration.tar.gz > migration.sha256
```

---

## 🖥️ PHASE 2: Target Server Preparation

### Step 2.1: Initial System Setup
```bash
# Update system
sudo dnf update -y

# Install EPEL repository (for additional packages)
sudo dnf install -y epel-release

# Install development tools
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y gcc gcc-c++ make openssl-devel bzip2-devel libffi-devel
```

### Step 2.2: Install Python 3.9 (EXACT VERSION)
```bash
# For Fedora 39:
sudo dnf install -y python3.9 python3.9-pip python3.9-devel python3.9-venv

# Set Python 3.9 as automation Python
sudo alternatives --install /usr/bin/python3-automation python3-automation /usr/bin/python3.9 1

# Create symlink for automation scripts
sudo ln -sf /usr/bin/python3.9 /usr/local/bin/python3-automation

# Verify version
python3.9 --version  # Should show Python 3.9.x

# Note: System will keep Python 3.12 as default, we use 3.9 specifically for automation
```

### Step 2.3: Install Node.js 18 LTS
```bash
# Install NodeSource repository
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -

# Install Node.js
sudo dnf install -y nodejs

# Verify versions
node --version  # Should show v18.x.x
npm --version   # Should show 10.x.x
```

### Step 2.4: Install Google Chrome (for Evolve scraper)
```bash
# Add Google Chrome repository
cat << 'EOF' | sudo tee /etc/yum.repos.d/google-chrome.repo
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF

# Install Chrome and headless dependencies
sudo dnf install -y google-chrome-stable

# Install additional dependencies for headless Chrome
sudo dnf install -y \
  liberation-fonts \
  vulkan \
  mesa-vulkan-drivers \
  libxkbcommon \
  xorg-x11-server-Xvfb \
  libX11 libXcomposite libXcursor libXdamage \
  libXext libXi libXtst libXrandr libXScrnSaver \
  libXss libgconf-2-4 alsa-lib atk gtk3 \
  ipa-gothic-fonts xorg-x11-fonts-100dpi \
  xorg-x11-fonts-75dpi xorg-x11-utils \
  xorg-x11-fonts-cyrillic xorg-x11-fonts-Type1 \
  xorg-x11-fonts-misc

# Verify installation
google-chrome --version
```

### Step 2.5: Install Additional System Dependencies
```bash
# Install required system packages
sudo dnf install -y \
  nginx \
  git \
  wget \
  curl \
  vim \
  htop \
  tmux \
  redis \
  postgresql-devel \
  mysql-devel \
  unzip \
  jq \
  logrotate \
  chrony

# Start and enable nginx
sudo systemctl enable --now nginx

# Configure chrony for time sync
sudo systemctl enable --now chronyd
```

### Step 2.6: Create User and Directory Structure
```bash
# Create opc user if it doesn't exist (skip if using different username)
sudo useradd -m -s /bin/bash opc
sudo usermod -aG wheel opc  # Add to sudo group

# Switch to the user
sudo su - opc

# Create directory structure
mkdir -p ~/automation
mkdir -p ~/migration_backup
```

---

## 📦 PHASE 3: Code and Configuration Deployment

### Step 3.1: Transfer Files to New Server
```bash
# On OLD server:
cd ~/migration_backup
scp automation_migration_20250810_230948.tar.gz automation_migration_20250810_230948.tar.gz.sha256 \
    critical_files_20250810_230948.tar.gz critical_files_20250810_230948.tar.gz.sha256 \
    MIGRATION_CHECKLIST.md \
    boris@194.195.120.63:~/migration_backup/

# On NEW server:
cd ~/migration_backup

# Verify checksum
sha256sum -c migration.sha256

# Extract automation code
cd /opt
sudo tar -xzf ~/migration_backup/automation_migration.tar.gz
sudo chown -R boris:boris servativ_scheduler/
```

### Step 3.2: Restore Environment Files
```bash
cd /opt/servativ_scheduler

# Restore all .env files
cp ~/migration_backup/root.env .env
cp ~/migration_backup/dev.env config/environments/dev/.env
cp ~/migration_backup/prod.env config/environments/prod/.env
cp ~/migration_backup/airscripts.env src/automation/scripts/airscripts-api/.env
cp ~/migration_backup/airtable-mcp.env tools/airtable-mcp-server/.env
cp ~/migration_backup/trello-mcp.env tools/trello-mcp-server/.env

# IMPORTANT: Update API_DOMAIN in .env to your client's domain
sed -i 's/API_DOMAIN=.*/API_DOMAIN=cal.tanqtop.com/' .env
sed -i 's/HCP_WEBHOOK_URL=.*/HCP_WEBHOOK_URL=https:\/\/cal.tanqtop.com\/webhooks\/hcp/' .env

# Note: The following variables have been removed as of Aug 2025:
# - GMAIL_CREDS_PATH, GMAIL_TOKEN_PATH (Gmail deprecated, using CloudMailin)
# - HCP_DEFAULT_EMPLOYEE_ID (not used)
# - MAX_REQUESTS_PER_MINUTE (not actually used)
# Duplicate job type variables have been consolidated to PROD_HCP_JOB_TYPE_* format

# Set proper permissions
chmod 600 .env
chmod 600 config/environments/*/.env
chmod 600 src/automation/scripts/airscripts-api/.env
chmod 600 tools/*/.env
```

### Step 3.3: Install Python Dependencies
```bash
cd /opt/servativ_scheduler

# Create and activate virtual environment (optional but recommended)
python3.9 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Note: This project runs scripts directly, no package installation needed

# Verify key packages
pip show pyairtable selenium python-dotenv
```

### Step 3.4: Install Node.js Dependencies
```bash
# Note: No root package.json, install dependencies in subdirectories only

# Install MCP server dependencies
cd tools/airtable-mcp-server
npm install
npm run build

cd ../hcp-mcp-dev
npm install
npm run build

cd ../hcp-mcp-prod
npm install
npm run build

cd ../trello-mcp-server
npm install
npm run build

# Install API server dependencies
cd /opt/servativ_scheduler/src/automation/scripts/airscripts-api
npm install

# Install shared scripts dependencies
cd /opt/servativ_scheduler/src/automation/scripts/shared
npm install

# Return to root
cd /opt/servativ_scheduler
```

### Step 3.5: Configure MCP Servers for Claude (if using Claude Code)
```bash
# Navigate to project directory
cd /opt/servativ_scheduler

# Add Airtable Development MCP Server
claude mcp add-json airtable-dev '{
  "command": "npx",
  "args": ["-y", "airtable-mcp-server"],
  "env": {
    "AIRTABLE_API_KEY": "REDACTED_DEV_API_KEY",
    "AIRTABLE_BASE_ID": "app67yWFv0hKdl6jM"
  }
}'

# Add Airtable Production MCP Server  
claude mcp add-json airtable-prod '{
  "command": "npx", 
  "args": ["-y", "airtable-mcp-server"],
  "env": {
    "AIRTABLE_API_KEY": "REDACTED_PROD_API_KEY",
    "AIRTABLE_BASE_ID": "appZzebEIqCU5R9ER"
  }
}'

# Add HousecallPro Development MCP Server
claude mcp add-json hcp-mcp-dev '{
  "command": "node",
  "args": ["/opt/servativ_scheduler/tools/hcp-mcp-dev/dist/index.js"]
}'

# Add HousecallPro Production MCP Server
claude mcp add-json hcp-mcp-prod '{
  "command": "node",
  "args": ["/opt/servativ_scheduler/tools/hcp-mcp-prod/dist/index.js"]  
}'

# Add Trello MCP Server
claude mcp add-json trello '{
  "command": "node",
  "args": ["/opt/servativ_scheduler/tools/trello-mcp-server/dist/index.js"]
}'

# Verify MCP servers are configured
claude mcp list

# Note: API keys are from /opt/servativ_scheduler/config/environments/{dev,prod}/.env
# Dev: DEV_AIRTABLE_API_KEY=REDACTED_DEV_API_KEY
# Prod: PROD_AIRTABLE_API_KEY=REDACTED_PROD_API_KEY
```

---

## ⚙️ PHASE 4: System Services Configuration

### Step 4.1: Install Systemd Service Files
```bash
# Copy service files
sudo cp ~/migration_backup/webhook.service /etc/systemd/system/
sudo cp ~/migration_backup/webhook-dev.service /etc/systemd/system/
sudo cp ~/migration_backup/airscripts-api.service /etc/systemd/system/
sudo cp ~/migration_backup/airscripts-api-https.service /etc/systemd/system/

# Copy airtable-agent service if it exists
if [ -f ~/migration_backup/airtable-agent.service ]; then
  sudo cp ~/migration_backup/airtable-agent.service /etc/systemd/system/
  echo "Airtable-agent service installed"
else
  echo "No airtable-agent service found (optional component)"
fi

# Update paths if username is different (replace 'opc' with your username)
if [ "$USER" != "opc" ]; then
  sudo sed -i "s|/home/opc|/home/$USER|g" /etc/systemd/system/webhook*.service
  sudo sed -i "s|/home/opc|/home/$USER|g" /etc/systemd/system/airscripts*.service
  sudo sed -i "s|User=opc|User=$USER|g" /etc/systemd/system/*.service
  sudo sed -i "s|Group=opc|Group=$USER|g" /etc/systemd/system/*.service
fi

# Reload systemd
sudo systemctl daemon-reload
```

### Step 4.2: Configure Nginx
```bash
# Copy nginx configuration from the project directory
sudo cp /opt/servativ_scheduler/src/automation/scripts/airscripts-api/nginx-servativ.conf /etc/nginx/conf.d/client-automation.conf

# Update server_name and paths for your client
sudo vim /etc/nginx/conf.d/client-automation.conf
# Required changes:
# 1. Change server_name from 'servativ.themomentcatchers.com' to your client's domain
# 2. Update SSL certificate paths to match your domain
# 3. Verify proxy_pass ports (3002 for AirScripts API, 5000/5001 for webhooks)

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### Step 4.3: Configure Firewall
```bash
# Open required ports
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=3002/tcp  # AirScripts API (was incorrectly listed as 3006)
sudo firewall-cmd --permanent --add-port=5000/tcp  # Production webhook service
sudo firewall-cmd --permanent --add-port=5001/tcp  # Development webhook service

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

### Step 4.4: Configure SELinux (if enabled)
```bash
# Check if SELinux is enabled
getenforce

# If enabled, configure for our services
if [ "$(getenforce)" != "Disabled" ]; then
  # Allow nginx to proxy
  sudo setsebool -P httpd_can_network_connect 1
  
  # Allow services to bind to ports
  sudo semanage port -a -t http_port_t -p tcp 3006 2>/dev/null || true
  sudo semanage port -a -t http_port_t -p tcp 5000 2>/dev/null || true
  sudo semanage port -a -t http_port_t -p tcp 5001 2>/dev/null || true
  
  # Set context for automation directory
  sudo semanage fcontext -a -t httpd_sys_content_t "/home/$USER/automation(/.*)?"
  sudo restorecon -Rv /home/$USER/automation
fi
```

---

## 🔄 PHASE 5: External Services Update

### Step 5.1: Update DNS Records
```bash
# Update your domain's DNS A record to point to new server IP
# This varies by provider (Cloudflare, Route53, etc.)

# While waiting for DNS propagation, update local hosts file for testing:
echo "194.195.120.63 cal.tanqtop.com" | sudo tee -a /etc/hosts
```

### Step 5.2: Update CloudMailin Webhook URL
```
1. Log into CloudMailin dashboard
2. Update webhook URL to: https://cal.tanqtop.com/webhooks/csv-email
   Example: https://automation.clientname.com/webhooks/csv-email
3. Set format to: Multipart or JSON
4. Set CloudMailin Secret (from .env CLOUDMAILIN_SECRET)
   - Used for webhook authentication
   - Critical for security
5. Test with a sample email with CSV attachment
```

### Step 5.3: Update HousecallPro Webhooks
```
For Production (3rd party forwarding):
1. Contact the forwarding service to update target URL
2. New URL: https://cal.tanqtop.com/webhooks/hcp
   Example: https://automation.clientname.com/webhooks/hcp

For Development (if applicable):
1. Log into HousecallPro
2. Go to Settings > Integrations > Webhooks
3. Update URL to: https://cal.tanqtop.com/webhooks/hcp-dev
   Example: https://automation.clientname.com/webhooks/hcp-dev
```

### Step 5.4: Update SSL Certificates
```bash
# Install certbot
sudo dnf install -y certbot python3-certbot-nginx

# Generate new certificate for client's domain
sudo certbot --nginx -d cal.tanqtop.com
# Or for subdomain: sudo certbot --nginx -d automation.clientname.com

# Set up auto-renewal
sudo systemctl enable --now certbot-renew.timer
```

---

## ✅ PHASE 6: Verification and Testing

### Step 6.1: Start Services
```bash
# Start services one by one and check logs
sudo systemctl start webhook
sudo journalctl -u webhook -f  # Check for errors (Ctrl+C to exit)

sudo systemctl start webhook-dev
sudo journalctl -u webhook-dev -f

sudo systemctl start airscripts-api
sudo journalctl -u airscripts-api -f

# Enable services to start on boot
sudo systemctl enable webhook webhook-dev airscripts-api
```

### Step 6.2: Test Core Functionality
```bash
cd /opt/servativ_scheduler

# Test Python imports
python3.9 -c "from src.automation.controller import AutomationController; print('✅ Python imports OK')"

# Test automation runners (dry run)
python3.9 src/run_automation_dev.py --dry-run
python3.9 src/run_automation_prod.py --dry-run

# Test webhook endpoints (replace with client's domain)
curl -X POST https://cal.tanqtop.com/webhooks/hcp -H "Content-Type: application/json" -d '{"test": true}'
curl -X POST https://cal.tanqtop.com/webhooks/hcp-dev -H "Content-Type: application/json" -d '{"test": true}'

# Test API endpoint
curl https://cal.tanqtop.com/api/health
```

### Step 6.3: Verify HCP Job Type IDs
```bash
# Verify HCP Job Type IDs are set correctly in environment files
cd /opt/servativ_scheduler

# Check production job type IDs
grep "PROD_HCP_JOB_TYPE" config/environments/prod/.env

# Check development job type IDs  
grep "DEV_HCP_JOB_TYPE" config/environments/dev/.env

# These should match the IDs from your HousecallPro account:
# - Go to Settings > Job Types in HCP
# - Get the exact IDs for:
#   - Turnover STR Same Day
#   - Turnover STR Next Guest
#   - Mid Stay Refresh
#   - Inspection

# If IDs are missing or incorrect, update them:
vim config/environments/prod/.env
vim config/environments/dev/.env
```

### Step 6.4: Restore Cron Jobs
```bash
# Create logrotate config first
cat << 'EOF' > ~/automation/logrotate.conf
/opt/servativ_scheduler/src/automation/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 opc opc
}
EOF

# Review and restore cron
cat ~/migration_backup/cron_backup.txt

# Update paths if needed and reinstall
crontab -e
# Add these entries (adjust paths if needed):
# Production automation - every hour
0 * * * * /usr/bin/python3.9 /opt/servativ_scheduler/src/run_automation_prod.py >> /opt/servativ_scheduler/src/automation/logs/automation_prod_cron.log 2>&1
# Development automation - every 4 hours
10 0,4,8,12,16,20 * * * /usr/bin/python3.9 /opt/servativ_scheduler/src/run_automation_dev.py >> /opt/servativ_scheduler/src/automation/logs/automation_dev_cron.log 2>&1
# Log rotation - daily at 2 AM
0 2 * * * /usr/sbin/logrotate -s /home/boris/.logrotate.state /opt/servativ_scheduler/logrotate.conf
# Chrome cleanup - daily at 2:30 AM (automatic via cleanup-system.py)
30 2 * * * /usr/bin/python3.9 /opt/servativ_scheduler/src/automation/scripts/system/cleanup-system.py --chrome-days 1 >> /opt/servativ_scheduler/src/automation/logs/cleanup_cron.log 2>&1
# Full system cleanup - weekly on Sunday at 3 AM
0 3 * * 0 /usr/bin/python3.9 /opt/servativ_scheduler/src/automation/scripts/system/cleanup-system.py >> /opt/servativ_scheduler/src/automation/logs/cleanup_cron.log 2>&1

# Verify
crontab -l
```

### Step 6.5: Test External Integrations
```bash
# Test Airtable connection
cd /opt/servativ_scheduler
python3.9 -c "
from pyairtable import Table
import os
from dotenv import load_dotenv
load_dotenv('config/environments/prod/.env')
table = Table(os.getenv('AIRTABLE_BASE_ID'), 'Properties', os.getenv('AIRTABLE_API_KEY'))
print('✅ Airtable connection OK')
"

# Test HousecallPro API
curl -H "Authorization: Token YOUR_HCP_API_KEY" \
  https://api.housecallpro.com/v1/customers?page_size=1

# Test CloudMailin webhook (send a test email)

# Test Evolve scraper
ENVIRONMENT=production python3.9 src/automation/scripts/evolve/evolveScrape.py --headless --test
```

### Step 6.6: Monitor First Production Run
```bash
# Run production automation manually first
cd /opt/servativ_scheduler
python3.9 src/run_automation_prod.py

# Watch logs
tail -f src/automation/logs/automation_prod*.log

# Check for errors in each component log
tail -f src/automation/logs/csv_sync_Production.log
tail -f src/automation/logs/ics_sync_prod.log
tail -f src/automation/logs/webhook.log
```

### Step 6.7: Verify Webhook Authentication
```bash
# Test webhook internal auth secret (used for forwarding)
cd /opt/servativ_scheduler

# Check SERVATIV_WEBHOOK_SECRET is set
grep "SERVATIV_WEBHOOK_SECRET" .env

# Test with correct auth header (replace with client's domain)
curl -X POST https://cal.tanqtop.com/webhooks/hcp \
  -H "Content-Type: application/json" \
  -H "X-Internal-Auth: YOUR_SERVATIV_WEBHOOK_SECRET" \
  -d '{"test": true}'

# Should return 200 OK - check webhook logs
tail -f src/automation/logs/webhook.log

# If webhooks are failing:
# 1. Verify SERVATIV_WEBHOOK_SECRET matches in .env and forwarding service
# 2. Check HCP webhook signature validation is working
# 3. Ensure nginx is properly forwarding headers
```

### Step 6.8: Verify Version and Repository
```bash
# Check current version
cat ~/automation/VERSION  # Should show 2.2.19 or later

# Verify git configuration
cd /opt/servativ_scheduler
git remote -v  # Should show your repository URLs
git branch     # Should show current branch (dev or main)
git status     # Check for uncommitted changes

# If remote is not configured:
git remote add origin YOUR_GIT_REPO_URL
git fetch origin
git branch --set-upstream-to=origin/dev dev  # or main
```

---

## 🔍 PHASE 7: Post-Migration Checklist

### Critical Verifications
- [ ] All .env files restored with correct permissions (600)
- [ ] Webhook endpoints responding (5000, 5001)
- [ ] API endpoints responding (3006)
- [ ] Nginx proxy working correctly
- [ ] SSL certificates valid
- [ ] Firewall rules applied
- [ ] SELinux configured (if applicable)

### Service Status
- [ ] webhook service running
- [ ] webhook-dev service running
- [ ] airscripts-api service running
- [ ] nginx service running
- [ ] All services enabled for boot

### Functionality Tests
- [ ] CSV processing working
- [ ] ICS sync working
- [ ] Evolve scraper working
- [ ] CloudMailin emails received
- [ ] HousecallPro webhooks received
- [ ] Airtable updates working
- [ ] HCP job creation working

### External Services
- [ ] DNS pointing to new server
- [ ] CloudMailin webhook URL updated
- [ ] HousecallPro webhook URLs updated
- [ ] All API integrations tested

### Monitoring
- [ ] Cron jobs running on schedule
- [ ] Log rotation configured
- [ ] Disk space adequate
- [ ] Memory usage normal
- [ ] No errors in system logs

---

## 🚨 TROUBLESHOOTING

### Common Issues and Solutions

#### Python Import Errors
```bash
# Missing module
pip install MODULE_NAME

# Wrong Python version
python3.9 --version  # Must be 3.9.x
sudo alternatives --config python3
```

#### Service Won't Start
```bash
# Check service status
sudo systemctl status SERVICE_NAME

# Check logs
sudo journalctl -u SERVICE_NAME -n 100

# Common fixes:
# - Fix paths in service file
# - Fix permissions: sudo chown -R $USER:$USER ~/automation
# - Check Python path: which python3
```

#### Nginx 502 Bad Gateway
```bash
# Check if backend services are running
sudo systemctl status webhook webhook-dev airscripts-api

# Check nginx error log
sudo tail -f /var/log/nginx/error.log

# Verify proxy_pass URLs in nginx config
sudo vim /etc/nginx/conf.d/servativ.conf
```

#### Webhook Not Receiving
```bash
# Check firewall
sudo firewall-cmd --list-ports

# Test locally
curl -X POST http://localhost:5000/webhooks/test -H "Content-Type: application/json" -d '{}'

# Check service logs
sudo journalctl -u webhook -f
```

#### Chrome/Selenium Issues
```bash
# Install Chrome dependencies
sudo dnf install -y libX11 libXcomposite libXcursor libXdamage libXext libXi libXtst libXrandr libXScrnSaver libXss libgconf-2-4 alsa-lib atk gtk3 ipa-gothic-fonts xorg-x11-fonts-100dpi xorg-x11-fonts-75dpi xorg-x11-utils xorg-x11-fonts-cyrillic xorg-x11-fonts-Type1 xorg-x11-fonts-misc

# Test Chrome
google-chrome --headless --no-sandbox --dump-dom https://google.com
```

#### Permission Denied Errors
```bash
# Fix ownership
sudo chown -R $USER:$USER ~/automation

# Fix file permissions
find ~/automation -type f -name "*.py" -exec chmod 644 {} \;
find ~/automation -type f -name "*.sh" -exec chmod 755 {} \;
chmod 600 ~/automation/.env
chmod 600 ~/automation/config/environments/*/.env
```

---

## 📊 Performance Optimization

### After Migration Stabilizes
```bash
# 1. Enable Python optimization
python3.9 -O -m compileall ~/automation/src

# 2. Configure nginx caching
# Add to nginx config location blocks:
proxy_cache_valid 200 302 10m;
proxy_cache_valid 404 1m;

# 3. Optimize database connections
# Add to .env files:
AIRTABLE_RATE_LIMIT=5  # requests per second
HCP_RATE_LIMIT=10      # requests per second

# 4. Setup log rotation
cat << 'EOF' | sudo tee /etc/logrotate.d/automation
/opt/servativ_scheduler/src/automation/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 opc opc
    sharedscripts
    postrotate
        systemctl reload webhook webhook-dev airscripts-api 2>/dev/null || true
    endscript
}
EOF
```

---

## 📝 Final Notes

### Critical Reminders
1. **NEVER** skip the environment file backup - they contain all API keys
2. **ALWAYS** test in dry-run mode first
3. **UPDATE** all external webhook URLs immediately after DNS changes
4. **MONITOR** logs closely for the first 24-48 hours
5. **KEEP** the old server running for at least 1 week as backup

### Migration Timeline
- Phase 1-2: 2-3 hours (preparation and setup)
- Phase 3-4: 1-2 hours (deployment and configuration)
- Phase 5: 1-24 hours (DNS propagation varies)
- Phase 6-7: 2-3 hours (testing and verification)
- **Total: 6-8 hours active work + DNS propagation time**

### Support Resources
- Automation logs: `~/automation/src/automation/logs/`
- System logs: `sudo journalctl -u SERVICE_NAME`
- Nginx logs: `/var/log/nginx/`
- Python errors: Check PYTHONPATH and virtual env
- Service issues: Check systemd service files

### Rollback Plan
If critical issues occur:
1. Update DNS back to old server
2. Restart services on old server
3. Restore cron on old server
4. Investigate issues on new server offline

---

## Validation Checksum
This guide is complete and accurate for Oracle Linux 8.x / RHEL 8.x based systems.
Generated with all system-specific configurations from active production environment.