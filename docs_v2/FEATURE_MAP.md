# Feature Map - Property Management Automation System
**Version**: 2.2.8
**Last Updated**: July 11, 2025

## 🗺️ Complete System Feature Map

This map provides navigation to all documented features in the property management automation system. Each feature contains standardized documentation including business logic, system flows, and examples.

---

## 🏗️ System Foundation

### [00. System Overview](./00-system-overview/)
- **Purpose**: High-level understanding of the entire system
- **Key Topics**: Architecture, data flow, integration points
- **Start Here**: If you're new to the system

---

## 📥 Data Ingestion Features

### [01. CSV Processing](./01-csv-processing/)
- **Purpose**: Process reservation CSVs from iTrip and Evolve via CloudMailin
- **Key Components**: Email parsing, CSV parsing, UID generation, Airtable sync
- **Input**: Email attachments → **Output**: Airtable records

### [02. ICS Feed Sync](./02-ics-feed-sync/)
- **Purpose**: Synchronize calendar feeds from Airbnb, VRBO, Booking.com, etc.
- **Key Components**: Concurrent processing, UID generation, feed status management
- **Input**: ICS URLs → **Output**: Reservation records

### [03. Evolve Portal Scraping](./03-evolve-scraping/)
- **Purpose**: Extract property data from Evolve portal using Selenium
- **Key Components**: Web automation, owner block detection, CSV export
- **Input**: Portal credentials → **Output**: CSV files for processing

---

## 🔌 Integration Features

### [04. HousecallPro Integration](./04-housecallpro-integration/)
- **Purpose**: Create and manage service jobs in HousecallPro
- **Key Components**: Job creation, schedule sync, job reconciliation (optimized), webhook handling, status updates
- **Input**: Airtable reservations → **Output**: HCP jobs with schedules

### [05. Airtable Integration](./05-airtable-integration/)
- **Purpose**: Central database for all property management data
- **Key Components**: Table schemas, field mappings, formula fields, relationships
- **Input**: Multiple sources → **Output**: Unified data store

### [06. MCP Servers](./06-mcp-servers/)
- **Purpose**: AI-powered analysis and operations via Model Context Protocol
- **Subfeatures**:
  - [HCP MCP](./06-mcp-servers/hcp-mcp/) - HousecallPro analysis tools
  - [Airtable MCP](./06-mcp-servers/airtable-mcp/) - Database operations
- **Key Components**: Search tools, analysis functions, CRUD operations

### [07. API Server](./07-api-server/)
- **Purpose**: REST API for job creation, schedule updates, and system operations
- **Key Components**: Express server, authentication, rate limiting, error handling
- **Endpoints**: `/api/dev/*`, `/api/prod/*`

---

## 📋 Business Logic Features

### [08. Schedule Management](./08-schedule-management/)
- **Purpose**: Calculate service times and manage appointment scheduling
- **Key Components**: Time calculation, same-day turnover, long-term guests, custom times
- **Business Rules**: 10:15 AM default, 10:00 AM same-day, 14+ day detection

### [09. Duplicate Detection](./09-duplicate-detection/)
- **Purpose**: Prevent duplicate reservations using UID generation
- **Key Components**: UID patterns, history preservation, cleanup procedures
- **Pattern**: `{source}_{property}_{checkin}_{checkout}_{lastname}`

### [10. Service Line Management](./10-service-line-management/)
- **Purpose**: Build descriptive service names with custom instructions
- **Key Components**: Custom instructions, owner arrival, long-term guest flags
- **Max Length**: 255 characters with smart truncation

### [11. Customer & Property Management](./11-customer-property-management/)
- **Purpose**: Manage property configurations and customer relationships
- **Key Components**: Multi-property support, HCP customer mapping, owner overrides
- **Relationships**: Properties → Customers → Jobs

---

## 🔄 Processing Features

### [12. Webhook Processing](./12-webhook-processing/)
- **Purpose**: Handle incoming webhooks from CloudMailin and HousecallPro
- **Key Components**: Signature verification, queue processing, async handling
- **Endpoints**: `/webhooks/csv-email`, `/webhooks/hcp`, `/webhooks/hcp-dev`

### [13. Automation Controller](./13-automation-controller/)
- **Purpose**: Orchestrate all automated processes
- **Key Components**: Cron scheduling, automation tracking, error handling
- **Schedule**: Every 4 hours (prod on hour, dev at :10)

---

## 🛠️ System Features

### [14. Environment Management](./14-environment-management/)
- **Purpose**: Maintain complete separation between dev and prod
- **Key Components**: Config files, credentials, file paths, API endpoints
- **Bases**: Dev `app67yWFv0hKdl6jM`, Prod `appZzebEIqCU5R9ER`

### [15. Error Handling](./15-error-handling/)
- **Purpose**: Graceful error recovery and retry logic
- **Key Components**: Retry strategies, error logging, recovery procedures
- **Strategies**: Exponential backoff, queue overflow, graceful degradation

### [16. Notification System](./16-notification-system/)
- **Purpose**: Send alerts and updates via multiple channels
- **Key Components**: Email notifications, webhook alerts, sync messages
- **Formats**: Standardized timestamps, status indicators

---

## 📊 Analytics Features

### [17. Reporting & Analytics](./17-reporting-analytics/)
- **Purpose**: Business intelligence and performance metrics
- **Key Components**: Revenue analysis, job statistics, performance tracking
- **Tools**: MCP analysis functions, Airtable views

### [18. Monitoring & Health](./18-monitoring-health/)
- **Purpose**: System health checks and performance monitoring
- **Key Components**: Health endpoints, log analysis, resource monitoring
- **Endpoints**: `/health`, systemd status, log rotation

---

## 🧭 Navigation Tips

### For New Users
1. Start with [System Overview](./00-system-overview/)
2. Read the feature most relevant to your task
3. Check BusinessLogicAtoZ.md for specific rules
4. Review SYSTEM_LOGICAL_FLOW.md for visual understanding

### For Developers
1. Each feature has standardized documentation
2. Flow diagrams use Mermaid syntax
3. Examples are tested and working
4. Version history tracks all changes

### For Operators
1. Focus on operational features (12-16)
2. Check troubleshooting in each feature
3. Monitor health checks regularly
4. Review error handling procedures

---

## 📚 Documentation Standards

Each feature folder contains:
- **README.md** - Feature overview and quick start
- **BusinessLogicAtoZ.md** - All rules alphabetically organized
- **SYSTEM_LOGICAL_FLOW.md** - Visual flow diagrams
- **version-history.md** - Change tracking
- **flows/** - Additional diagram files
- **examples/** - Working code examples

---

**Questions?** Start with the [System Overview](./00-system-overview/) or dive into any specific feature.