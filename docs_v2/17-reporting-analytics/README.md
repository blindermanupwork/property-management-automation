# Reporting & Analytics

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Status:** Active  
**Owner:** Automation System

## Overview

The reporting and analytics system provides comprehensive business intelligence across all automation components. It tracks operational metrics, generates performance reports, and enables data-driven decision making for property management operations.

## Key Components

### 1. **Operational Metrics Collection**
- Real-time performance tracking
- Success/failure rate monitoring
- Processing time analytics
- Resource utilization metrics

### 2. **HCP Analytics Tools**
- Revenue analysis by customer and property
- Service item usage tracking (towels, linens)
- Job statistics and monthly trends
- Laundry service pattern detection

### 3. **Automation Performance Reports**
- Daily/weekly/monthly summaries
- Component health monitoring
- Error rate analysis
- Processing volume trends

### 4. **Business Intelligence Dashboards**
- Airtable dashboard views
- Real-time status monitoring
- Historical trend analysis
- Predictive insights

### 5. **Data Export Capabilities**
- CSV export for external analysis
- API endpoints for reporting tools
- Automated report generation
- Custom query support

## Business Value

### **Operational Efficiency**
- Identifies bottlenecks in processing
- Tracks automation reliability
- Monitors system performance

### **Revenue Optimization**
- Analyzes service profitability
- Tracks customer lifetime value
- Identifies growth opportunities

### **Resource Management**
- Monitors supply usage patterns
- Optimizes inventory levels
- Predicts future needs

### **Quality Assurance**
- Tracks error rates and patterns
- Identifies data quality issues
- Monitors compliance metrics

## Technical Implementation

### **Data Collection Points**
- Controller execution metrics
- API response times
- Database query performance
- External service availability

### **Analysis Tools**
- HCP MCP bulletproof analytics
- Airtable aggregation formulas
- Custom Python analysis scripts
- JavaScript data processing

### **Report Generation**
- Automated daily summaries
- On-demand analytics queries
- Scheduled report delivery
- Real-time dashboards

## Integration Points

### **Data Sources**
- Airtable operational data
- HousecallPro job metrics
- CSV processing statistics
- ICS sync performance

### **Output Channels**
- Console summaries
- Log file analytics
- Airtable dashboards
- Export files

## Configuration

### **Metrics Collection**
- Configurable sampling rates
- Adjustable retention periods
- Custom metric definitions
- Performance thresholds

### **Report Settings**
- Schedule configuration
- Format preferences
- Distribution lists
- Alert thresholds

## Security & Privacy

### **Data Protection**
- PII anonymization
- Secure storage
- Access controls
- Audit logging

### **Compliance**
- Data retention policies
- Privacy regulations
- Security standards
- Audit requirements

## Related Documentation

- [HCP MCP Analytics Tools](/docs_v2/06-mcp-servers/hcp-mcp/BusinessLogicAtoZ.md) - Bulletproof analysis
- [Notification System](/docs_v2/16-notification-system/) - Alert delivery
- [Monitoring & Health Checks](/docs_v2/18-monitoring-health-checks/) - System monitoring
- [API Server](/docs_v2/07-api-server/) - Data access endpoints

## Quick Start Examples

### View Automation Performance
```python
# Check recent automation runs
controller.get_all_automations_status()
```

### Analyze Revenue by Customer
```javascript
// Using HCP MCP
analyze_customer_revenue()
```

### Generate Monthly Report
```python
# Export monthly statistics
python3 src/automation/scripts/data-exports/export-monthly-stats.py
```

### Check Processing Trends
```sql
-- Airtable formula for weekly trends
DATETIME_DIFF(NOW(), {Last Ran Time}, 'days') <= 7
```

## Version Requirements

- **Python**: 3.8+
- **Node.js**: 18+
- **Airtable**: Pro plan (for dashboards)
- **HCP API**: v2 (for analytics)

---

*The reporting and analytics system transforms raw operational data into actionable business intelligence, enabling data-driven property management decisions.*