# Installation Guide

Complete installation guide for the Property Management Automation System.

## 🎯 Overview

This system can be installed in multiple ways depending on your needs:
- **Development Installation**: For local development and testing
- **Production Installation**: For automated production deployment
- **Portable Installation**: Run without system installation
- **Docker Installation**: Containerized deployment

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (any modern distribution)
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Disk Space**: 100MB for application, additional space for logs and CSV files
- **Network**: Internet connection for API calls and email access

### Recommended Requirements
- **Python**: 3.9 or higher
- **Memory**: 2GB RAM or more
- **Disk Space**: 1GB or more for logs and data storage

## 🚀 Quick Installation Methods

### Method 1: Universal Runner (Recommended for Testing)
```bash
# Clone the repository
git clone <your-repository-url>
cd automation

# Run without installation
python run_anywhere.py --test    # Test setup
python run_anywhere.py          # Run automations
```

### Method 2: Package Installation (Recommended for Production)
```bash
# Clone and install
git clone <your-repository-url>
cd automation
pip install -e .

# Run from anywhere
run-automation
```

### Method 3: Docker Installation
```bash
# Build container
docker build -t automation-system .

# Run container
docker run -d --name automation automation-system
```

## 🔧 Detailed Installation Steps

### Step 1: Clone Repository
```bash
git clone <your-repository-url>
cd automation
```

### Step 2: Python Environment Setup

#### Option A: Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv automation-env

# Activate (Linux/macOS)
source automation-env/bin/activate

# Activate (Windows)
automation-env\Scripts\activate
```

#### Option B: Conda Environment
```bash
# Create conda environment
conda create -n automation python=3.9
conda activate automation
```

### Step 3: Install Dependencies

#### Automatic Installation
```bash
# Install with auto-dependency resolution
python run_anywhere.py --auto-install
```

#### Manual Installation
```bash
# Install from requirements file
pip install -r requirements.txt

# Or install individual packages
pip install requests pyairtable python-dotenv pathlib
```

### Step 4: Package Installation

#### Development Installation
```bash
# Install in development mode (recommended for development)
pip install -e .

# Test installation
run-automation --list
```

#### Production Installation
```bash
# Install package
pip install .

# Or install from GitHub directly
pip install git+<your-repository-url>
```

### Step 5: Configuration Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (use your preferred editor)
nano .env
# OR
vim .env
# OR
code .env
```

### Step 6: Verify Installation
```bash
# Run setup test
python test_setup.py

# Test automation system
run-automation --test

# List available automations
run-automation --list
```

## ⚙️ Configuration

### Environment Variables
Create `.env` file in project root:

```bash
# Required Configuration
AIRTABLE_API_KEY=your_api_key_here
PROD_AIRTABLE_BASE_ID=your_base_id_here
AUTOMATION_TABLE_NAME=Automation

# Optional Configuration (defaults provided)
AUTOMATION_NAME_FIELD=Name
AUTOMATION_ACTIVE_FIELD=Active
AUTOMATION_LAST_RAN_FIELD=Last Ran
AUTOMATION_SYNC_DETAILS_FIELD=Sync Details

# Gmail Configuration (for iTrip CSV)
GMAIL_CREDENTIALS_PATH=scripts/gmail/credentials.json

# Evolve Configuration
EVOLVE_USER=your_username
EVOLVE_PASS=your_password

# Logging Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

### Airtable Setup
1. Create Airtable account at https://airtable.com
2. Create a new base or use existing base
3. Create "Automation" table with fields:
   - Name (Single line text)
   - Active (Checkbox)
   - Last Ran (Date & time)
   - Sync Details (Long text)
4. Get API key from https://airtable.com/developers/web/api/introduction
5. Get Base ID from your base URL (starts with "app")

### Gmail Integration Setup
1. Go to Google Cloud Console
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials.json
6. Copy to `scripts/gmail/credentials.json`

## 🐳 Docker Installation

### Build Docker Image
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -e .

# Create required directories
RUN mkdir -p logs CSV_process CSV_done backups

# Run automation
CMD ["run-automation"]
```

### Build and Run
```bash
# Build image
docker build -t automation-system .

# Run with environment file
docker run -d \
  --name automation \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/CSV_process:/app/CSV_process \
  -v $(pwd)/CSV_done:/app/CSV_done \
  automation-system

# Check logs
docker logs automation
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  automation:
    build: .
    container_name: automation-system
    env_file: .env
    volumes:
      - ./logs:/app/logs
      - ./CSV_process:/app/CSV_process
      - ./CSV_done:/app/CSV_done
      - ./backups:/app/backups
    restart: unless-stopped
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## 🔧 Platform-Specific Instructions

### Windows Installation
```cmd
# Install Python from python.org
# Download and extract repository
# Open Command Prompt or PowerShell

cd automation
python -m pip install --upgrade pip
pip install -e .

# Test installation
run-automation.exe --test
```

### macOS Installation
```bash
# Install Python via Homebrew (recommended)
brew install python@3.9

# Or use system Python
cd automation
pip3 install -e .

# Test installation
run-automation --test
```

### Linux Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL/Oracle Linux
sudo yum install python3 python3-pip

# Install automation system
cd automation
pip3 install -e .

# Test installation
run-automation --test
```

## 🚨 Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Linux/macOS - fix permissions
chmod +x run_anywhere.py
sudo chown -R $USER:$USER automation/

# Windows - run as administrator
# Right-click Command Prompt → "Run as administrator"
```

#### Python Not Found
```bash
# Check Python installation
python --version
python3 --version

# Add Python to PATH (Windows)
# Add Python installation directory to system PATH

# Use full path if needed
/usr/bin/python3 run_anywhere.py
```

#### Missing Dependencies
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install missing dependencies
python run_anywhere.py --auto-install

# Or install manually
pip install requests pyairtable python-dotenv
```

#### Import Errors
```bash
# Verify Python path
python run_anywhere.py --info

# Check installation
python test_setup.py

# Reinstall package
pip uninstall automation
pip install -e .
```

#### Network Issues
```bash
# Test network connectivity
ping google.com

# Configure proxy if needed
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# Or in .env file
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

### Getting Help
```bash
# System information
python run_anywhere.py --info

# Detailed test results
python test_setup.py

# Check logs
tail -f logs/automation.log

# Enable debug mode
export AUTOMATION_DEBUG=1
run-automation
```

## ✅ Verification Checklist

After installation, verify these items work:

- [ ] `python test_setup.py` passes all tests
- [ ] `run-automation --list` shows available automations
- [ ] `run-automation --test` runs without errors
- [ ] Configuration file `.env` exists and has required values
- [ ] Required directories are created automatically
- [ ] Can import automation package: `python -c "from automation.config import Config; print('OK')"`
- [ ] Airtable connection works (check logs)
- [ ] Gmail credentials configured (if using iTrip integration)

## 🔄 Updates and Maintenance

### Updating the System
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Test after update
python test_setup.py
```

### Uninstallation
```bash
# Uninstall package
pip uninstall automation

# Remove files (optional)
rm -rf automation/

# Remove virtual environment (if used)
rm -rf automation-env/
```

---

For additional help, see [Troubleshooting Guide](TROUBLESHOOTING.md) or create an issue on GitHub.