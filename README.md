# Property Management Automation

Automated property management system for vacation rentals - CSV processing, calendar sync, and service job creation.

## 🚀 Features

- **Gmail Integration**: Downloads CSV reports from iTrip
- **Evolve Scraper**: Extracts data from Evolve vacation rental portal  
- **CSV Processor**: Syncs CSV data to Airtable reservations database
- **ICS Calendar Sync**: Processes calendar feeds for booking data
- **HousecallPro Integration**: Creates service jobs based on reservations
- **Airtable Agent**: AI-powered interface for Airtable operations
- **Webhook System**: Handles external integrations

## 📋 Prerequisites

- Oracle Linux (or similar RHEL-based system)
- Python 3.8+
- Node.js 16+
- Git and GitHub CLI

## 🔧 Setup

### 1. Clone Repository
```bash
git clone https://github.com/blindermanupwork/property-management-automation.git
cd property-management-automation
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
npm install
```

### 3. Configure Credentials

#### Main Environment
```bash
cp .env.example .env
nano .env  # Fill in your credentials
```

#### Development Environment  
```bash
cp environments/dev/.env.example environments/dev/.env
nano environments/dev/.env  # Fill in development credentials
```

#### Production Environment
```bash
cp environments/prod/.env.example environments/prod/.env  
nano environments/prod/.env  # Fill in production credentials
```

### 4. Required Credentials

#### Airtable
- **API Key**: Get from https://airtable.com/developers/web/api/introduction
- **Base ID**: Found in your Airtable base URL
- **Table Name**: Usually "Reservations"

#### Gmail (for CSV downloads)
- **credentials.json**: Download from Google Cloud Console → APIs & Services → Credentials
- Copy `scripts/gmail/credentials.json.example` to `scripts/gmail/credentials.json`
- Fill in your actual Google OAuth credentials

#### HousecallPro (optional)
- **API Key**: Get from HousecallPro developer portal
- **Company ID**: Your HousecallPro company identifier

#### OpenAI (for AI agent)
- **API Key**: Get from https://platform.openai.com/api-keys

## 🏃 Usage

### Development
```bash
./run_dev.sh      # Run in development mode
```

### Production  
```bash
./run_prod.sh     # Run in production mode
```

### Deployment
```bash
# Work on dev branch
git checkout dev
# Make changes...
git add . && git commit -m "New feature"
git push origin dev

# Deploy to production
./deploy_to_prod.sh
```

### Monitoring
```bash
./monitor.sh      # Check system health
```

## 📁 Directory Structure

```
automation/
├── environments/          # Environment-specific configs
│   ├── dev/              # Development environment
│   └── prod/             # Production environment
├── scripts/              # Individual automation scripts
│   ├── CSVtoAirtable/    # CSV processing
│   ├── gmail/            # Gmail integration
│   ├── evolve/           # Evolve scraping
│   ├── icsAirtableSync/  # Calendar sync
│   └── webhook/          # Webhook handlers
├── logs/                 # Application logs
├── CSV_process/          # Incoming CSV files
├── CSV_done/             # Processed CSV files
└── backups/              # Automated backups
```

## 🔄 Automation Schedule

- **Main automation**: Daily at 6 AM
- **Health monitoring**: Every 30 minutes  
- **Backups**: Weekly on Sundays at 2 AM
- **Log cleanup**: Daily at 1 AM

## 🚨 Monitoring & Alerts

The system includes comprehensive monitoring:

- **Health checks**: `./monitor.sh`
- **Error detection**: Automatically scans logs
- **Disk space monitoring**: Alerts when >85% full
- **Process monitoring**: Ensures automation is running

## 🔒 Security

- All credentials stored in `.env` files (never committed)
- Separate development and production environments
- Automated backups with retention policies
- Comprehensive logging for audit trails

## 🐛 Troubleshooting

1. **Check system status**: `./monitor.sh`
2. **View recent logs**: `tail -f logs/health_check.log`
3. **Check alerts**: `cat logs/alerts.log`
4. **Restart automation**: `./run_prod.sh`

## 📝 Development Workflow

1. Work on `dev` branch for all changes
2. Test thoroughly in development environment
3. Use `./deploy_to_prod.sh` to deploy to production
4. Production runs on `main` branch

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch from `dev`
3. Make your changes
4. Test in development environment
5. Submit a pull request to `dev` branch

---

*Generated with [Claude Code](https://claude.ai/code)*