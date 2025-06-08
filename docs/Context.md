# /home/opc/automation/docs/

## Purpose
This directory contains comprehensive documentation for the property management automation system, including API documentation, installation guides, testing procedures, and system architecture information. It serves as the central knowledge base for understanding and working with the system.

## Key Subdirectories and What They Do

### **Core Documentation**
- `INSTALLATION.md` - Complete system installation and setup guide
- `COMPREHENSIVE_TESTING_CHECKLIST.md` - Testing procedures and validation steps
- `AIRSCRIPTS_MIGRATION_GUIDE.md` - Migration guide for legacy Airscripts system
- `HOUSECALLPRO_MCP_PLAN.md` - HousecallPro MCP server implementation plan

### **API Documentation**
- `housecallpro-api/` - Complete HousecallPro API documentation
  - `customers/` - Customer management API endpoints
  - `employees/` - Employee management API endpoints  
  - `jobs/` - Job management API endpoints
  - `job-types/` - Job type configuration
  - `schemas/` - API schema definitions

### **System Audit and Analysis**
- `audit/` - Comprehensive system analysis and auditing documentation
  - `COMPREHENSIVE_CODEBASE_AUDIT.md` - Complete codebase analysis
  - `BusinessLogicAtoZ.md` - Business logic documentation
  - `Airtable-HousecallPro-Map.md` - Data mapping between systems
  - `BugReport.md` - Known issues and bug tracking
  - `Deletables.md` - Obsolete code identification
  - `FlowChart.mmd` - System flow diagrams

### **Integration Guides**
- `housecallpromcp.md` - HousecallPro MCP integration documentation

## How to Use the Code

### **Getting Started with Documentation**

#### **New User Setup**
```bash
# 1. Read installation guide first
cat docs/INSTALLATION.md

# 2. Follow comprehensive testing checklist
cat docs/COMPREHENSIVE_TESTING_CHECKLIST.md

# 3. Review system architecture
cat docs/audit/COMPREHENSIVE_CODEBASE_AUDIT.md
```

#### **API Development**
```bash
# Study HousecallPro API patterns
ls docs/housecallpro-api/

# Customer API examples
cat docs/housecallpro-api/customers/01-get-customers.md
cat docs/housecallpro-api/customers/02-create-customer.md

# Job management examples  
cat docs/housecallpro-api/jobs/07-get-jobs.md
cat docs/housecallpro-api/jobs/08-create-job.md
```

### **Understanding System Architecture**

#### **Business Logic Flow**
```bash
# Comprehensive business logic overview
cat docs/audit/BusinessLogicAtoZ.md

# Data mapping between systems
cat docs/audit/Airtable-HousecallPro-Map.md

# System flow visualization
cat docs/audit/FlowChart.mmd  # Mermaid diagram format
```

#### **Migration and Upgrades**
```bash
# Legacy Airscripts migration
cat docs/AIRSCRIPTS_MIGRATION_GUIDE.md

# MCP server implementation
cat docs/HOUSECALLPRO_MCP_PLAN.md
```

## Dependencies and Requirements

### **Documentation Tools**
- **Markdown Viewers**: Any markdown-compatible editor or viewer
- **Mermaid Diagrams**: For viewing `.mmd` flowcharts
- **API Testing Tools**: Postman, curl, or similar for API documentation testing

### **Reference Materials**
- HousecallPro API documentation (external)
- Airtable API documentation (external)
- Property management system knowledge
- OAuth2 and REST API concepts

## Common Workflows and Operations

### **Documentation Maintenance Workflow**

#### **Adding New API Documentation**
```bash
# 1. Create new API endpoint documentation
mkdir -p docs/housecallpro-api/[category]/
cat > docs/housecallpro-api/[category]/[number]-[name].md << 'EOF'
# API Endpoint: [Method] [Endpoint]

## Description
[What this endpoint does]

## Request
```http
[METHOD] [URL]
[Headers]
[Body if applicable]
```

## Response
```json
[Example response]
```

## Example Usage
[Code examples]
EOF
```

#### **Updating System Documentation**
```bash
# 1. Update codebase audit after major changes
# Edit docs/audit/COMPREHENSIVE_CODEBASE_AUDIT.md

# 2. Update business logic documentation
# Edit docs/audit/BusinessLogicAtoZ.md  

# 3. Update data mapping after schema changes
# Edit docs/audit/Airtable-HousecallPro-Map.md
```

### **Testing Documentation Workflow**
```bash
# 1. Follow testing checklist for new features
cat docs/COMPREHENSIVE_TESTING_CHECKLIST.md

# 2. Update checklist with new test scenarios
# Add new test cases to COMPREHENSIVE_TESTING_CHECKLIST.md

# 3. Document any new bugs or issues
# Add entries to docs/audit/BugReport.md
```

### **API Documentation Usage**

#### **Customer Management**
```bash
# Study customer API patterns
cat docs/housecallpro-api/customers/01-get-customers.md
cat docs/housecallpro-api/customers/03-get-customer.md
cat docs/housecallpro-api/customers/04-update-customer.md

# Address management
cat docs/housecallpro-api/customers/05-get-customer-address.md
cat docs/housecallpro-api/customers/06-create-customer-address.md
```

#### **Job Management**
```bash
# Job CRUD operations
cat docs/housecallpro-api/jobs/03-get-job.md
cat docs/housecallpro-api/jobs/07-get-jobs.md
cat docs/housecallpro-api/jobs/08-create-job.md

# Line item management
cat docs/housecallpro-api/jobs/04-get-job-line-items.md
cat docs/housecallpro-api/jobs/05-add-job-line-item.md
cat docs/housecallpro-api/jobs/06-bulk-update-line-items.md
```

## Key Documentation Features

### **Comprehensive API Coverage**
- **Complete Endpoints**: Documentation for all HousecallPro API endpoints used
- **Request/Response Examples**: Real-world examples with actual data structures
- **Error Handling**: Common error scenarios and resolutions
- **Authentication**: OAuth2 and API key authentication patterns

### **System Architecture Documentation**
- **Business Logic**: Complete A-Z business process documentation
- **Data Flow**: Visual representation of data movement through the system
- **Integration Points**: How different systems connect and communicate
- **Environment Separation**: How dev/prod environments are isolated

### **Operational Guides**
- **Installation**: Step-by-step setup instructions
- **Testing**: Comprehensive testing procedures and checklists
- **Troubleshooting**: Common issues and resolution steps
- **Migration**: Guidance for system upgrades and migrations

### **Audit and Maintenance**
- **Codebase Analysis**: Comprehensive code audit and review
- **Bug Tracking**: Known issues and their status
- **Cleanup Identification**: Obsolete code and deletion candidates
- **System Health**: Overall system status and recommendations

## Documentation Standards

### **Markdown Format**
All documentation follows standard Markdown formatting:
```markdown
# Main Heading
## Section Heading  
### Subsection Heading

**Bold text** for emphasis
*Italic text* for terms
`code snippets` for inline code

```language
code blocks with syntax highlighting
```

- Bullet points for lists
1. Numbered lists for procedures
```

### **API Documentation Format**
```markdown
# API Endpoint: [METHOD] [ENDPOINT]

## Description
Brief description of what the endpoint does

## Request
```http
[METHOD] [URL]
Authorization: Bearer [token]
Content-Type: application/json

{
  "request": "body"
}
```

## Response
```json
{
  "response": "example"
}
```

## Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1    | string | Yes    | Description |

## Example Usage
```bash
curl -X [METHOD] \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data":"example"}' \
  "https://api.example.com/endpoint"
```
```

### **System Documentation Standards**
- **Clear Headings**: Use descriptive, hierarchical headings
- **Code Examples**: Include working code examples where applicable
- **Cross-References**: Link to related documentation
- **Update Dates**: Include last updated information
- **Contact Information**: Include maintainer information

## Maintenance and Updates

### **Regular Documentation Review**
```bash
# Monthly review checklist
# 1. Check for outdated API documentation
# 2. Update system architecture diagrams
# 3. Review and update testing procedures
# 4. Update installation guides with any new requirements
# 5. Check links and references for accuracy
```

### **Documentation Validation**
```bash
# Validate markdown syntax
markdownlint docs/**/*.md

# Check for broken links
markdown-link-check docs/**/*.md

# Spell check documentation
aspell check docs/[filename].md
```

### **Version Control Integration**
- All documentation is version controlled with the codebase
- Documentation changes reviewed as part of code review process
- Documentation updates required for all new features
- Automated checks for documentation completeness