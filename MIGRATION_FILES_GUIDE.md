# Migration Files Location & Usage Guide

## 📁 Where Everything Is Saved

All migration files are in: **`/home/opc/migration_backup/`**

### Main Files Created:
```bash
/home/opc/migration_backup/
├── automation_migration_20250810_230948.tar.gz     # 27MB - Clean code archive
├── automation_migration_20250810_230948.tar.gz.sha256  # Checksum for verification
├── critical_files_20250810_230948.tar.gz           # 71KB - All configs/env/services
├── critical_files_20250810_230948.tar.gz.sha256    # Checksum
├── MIGRATION_CHECKLIST.md                          # Step-by-step checklist
└── critical_files_20250810_230948/                 # Extracted critical files folder
    ├── env_files/          # All .env files
    ├── services/           # Systemd service files
    ├── configs/            # Nginx, CLAUDE.md files
    ├── ssl/                # SSL certificates
    └── system/             # System docs (cron, packages, etc)
```

## 📦 How to Transfer to New Server

### Step 1: On THIS (old) server
```bash
# Go to backup directory
cd /home/opc/migration_backup

# List the files (your timestamps will be different)
ls -lah

# Transfer to new server via SCP
scp automation_migration_*.tar.gz \
    critical_files_*.tar.gz \
    *.sha256 \
    MIGRATION_CHECKLIST.md \
    username@new-server-ip:~/
```

### Step 2: On NEW server
```bash
# Create directories
mkdir -p ~/migration_backup
mkdir -p ~/automation

# Move files to backup directory
mv automation_migration_*.tar.gz critical_files_*.tar.gz *.sha256 MIGRATION_CHECKLIST.md ~/migration_backup/
cd ~/migration_backup

# Verify checksums (IMPORTANT!)
sha256sum -c automation_migration_*.tar.gz.sha256
sha256sum -c critical_files_*.tar.gz.sha256
# Both should say "OK"
```

## 📂 How to Unpack/Extract

### On NEW Server:

#### 1. Extract the main automation code:
```bash
# Go to home directory
cd /home/opc

# Extract automation code (creates automation/ folder)
sudo tar -xzf ~/migration_backup/automation_migration_*.tar.gz

# Fix ownership (replace 'opc' with your username if different)
sudo chown -R opc:opc automation/
```

#### 2. Extract critical files (configs, env, etc):
```bash
cd ~/migration_backup

# Extract critical files
tar -xzf critical_files_*.tar.gz

# Now you have a folder with all configs
ls critical_files_*/
# Shows: env_files/ services/ configs/ ssl/ system/
```

#### 3. Restore environment files:
```bash
cd ~/automation

# Restore root .env
cp ~/migration_backup/critical_files_*/env_files/root.env .env

# Restore environment-specific .env files
cp ~/migration_backup/critical_files_*/env_files/dev.env config/environments/dev/.env
cp ~/migration_backup/critical_files_*/env_files/prod.env config/environments/prod/.env

# Restore service .env files
cp ~/migration_backup/critical_files_*/env_files/airscripts.env src/automation/scripts/airscripts-api/.env
cp ~/migration_backup/critical_files_*/env_files/airtable-mcp.env tools/airtable-mcp-server/.env
cp ~/migration_backup/critical_files_*/env_files/trello-mcp.env tools/trello-mcp-server/.env

# Set correct permissions (IMPORTANT!)
chmod 600 .env
chmod 600 config/environments/*/.env
chmod 600 src/automation/scripts/airscripts-api/.env
chmod 600 tools/*/.env
```

#### 4. Restore systemd services:
```bash
# Copy service files to systemd
sudo cp ~/migration_backup/critical_files_*/services/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload
```

#### 5. Restore nginx config:
```bash
# Copy nginx configuration
sudo cp ~/migration_backup/critical_files_*/configs/nginx-servativ.conf /etc/nginx/conf.d/servativ.conf

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## 🔍 What's in Each Archive

### `automation_migration_*.tar.gz` (27MB)
Contains CLEAN automation code:
- ✅ All Python scripts
- ✅ All source code
- ✅ Package.json files
- ✅ Requirements.txt
- ✅ CLAUDE.md files
- ❌ NO node_modules (will reinstall)
- ❌ NO logs
- ❌ NO cache files
- ❌ NO old CSVs

### `critical_files_*.tar.gz` (71KB)
Contains ALL configuration:
- ✅ All .env files with API keys
- ✅ Systemd service files
- ✅ Nginx configuration
- ✅ SSL certificates backup
- ✅ Cron jobs list
- ✅ Python packages list
- ✅ System configuration

## ✅ Quick Verification

After extracting on new server:
```bash
# Check automation folder exists
ls -la ~/automation/

# Check critical files exist
ls -la ~/automation/.env
ls -la ~/automation/src/run_automation_prod.py
ls -la ~/automation/tools/airtable-mcp-server/

# Check services are installed
ls -la /etc/systemd/system/webhook*.service
```

## 📋 Full Migration Steps

Follow the complete guide at:
`~/migration_backup/MIGRATION_CHECKLIST.md`

Or use the comprehensive guide:
`~/automation/COMPLETE_MIGRATION_GUIDE.md`

## ⚠️ Important Notes

1. **Keep the old server running** until everything is confirmed working
2. **Test everything** on the new server before switching DNS
3. **Update .env files** with new server's domain/IP where needed
4. **Install dependencies** after extracting (npm install, pip install -r requirements.txt)
5. **Don't forget SSL certificates** - you may need to regenerate with certbot

## 🆘 If Something Goes Wrong

1. You still have the old server running (don't shut it down!)
2. All original files are untouched
3. You have checksums to verify file integrity
4. The migration checklist has rollback steps

Remember: The script created backups WITHOUT deleting anything, so your current server is still 100% functional!