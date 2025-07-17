# Customer & Property Management - Complete System Logical Flow

## Overview
This document describes the complete operational flow of the Customer & Property Management system, from property data ingestion through customer relationship management, owner detection algorithms, service assignments, and HousecallPro integration.

## Primary Data Flow

### 1. Property Data Ingestion and Consolidation

#### Multi-Source Data Reception
Property information arrives from multiple sources with different priorities:
- Manual administrative updates receive highest priority treatment
- Evolve scraping provides automated property listing synchronization
- CSV imports from email processing supply bulk reservation data
- ICS calendar feeds contribute booking and availability information
- System defaults provide fallback values for missing information

#### Data Source Priority Resolution
System processes conflicting property information using priority hierarchy:
- Manual entries override all automated sources
- Evolve scraping data supersedes CSV and ICS information
- CSV import data takes precedence over calendar feeds
- ICS feed data used when no higher priority source available
- System defaults applied only when no other source provides data

#### Property Record Consolidation
Each property field receives value from highest priority available source:
- Field-by-field evaluation determines best available data
- Source tracking maintains audit trail for each field value
- Last updated timestamps recorded for change detection
- Conflict resolution logs created for administrative review
- Consolidated record stored as authoritative property state

### 2. Customer Relationship Establishment

#### Property-Customer Link Creation
System establishes relationships between properties and service customers:
- Properties link to customer records through Airtable record references
- Customer records contain actual HousecallPro customer identifiers
- Validation confirms customer record completeness before proceeding
- Missing customer assignments trigger manual review workflows
- Invalid customer links prevent job creation until resolved

#### HCP Customer ID Resolution Process
Multi-step validation ensures proper customer identification:
- Property record provides linked customer record reference
- Customer record lookup retrieves full customer information
- HCP Customer ID extracted from validated customer record
- Customer name and contact information collected for service context
- Validation failures logged with specific resolution requirements

#### Customer Data Validation
System validates customer information completeness:
- HCP Customer ID presence confirmed before job creation
- Customer contact information verified for communication needs
- Service preferences and special requirements identified
- Billing information status checked for invoicing readiness
- Customer account status verified for active service eligibility

### 3. Owner Detection and Classification

#### Reservation Context Analysis
System analyzes reservation patterns to identify owner activities:
- Checkout date and property identification extracted from reservation
- Property schedule queried for future bookings and blocks
- Entry type classification separates reservations from owner blocks
- Date proximity calculations determine owner arrival probability
- Status filtering excludes cancelled or inactive entries

#### Block Detection Algorithm Execution
Owner arrival detection follows strict proximity rules:
- All blocks at same property after checkout date identified
- Block check-in dates compared to guest checkout timing
- Blocks starting within 24 hours classified as owner arrivals
- Blocks beyond 24-hour window excluded from owner detection
- First qualifying block determines owner arrival status

#### Owner Arrival Flag Setting
System sets appropriate flags based on detection results:
- Owner Arriving field updated in Airtable reservation record
- Flag triggers special service line generation for cleaners
- Service scheduling adjustments applied for owner preparation
- Communication templates selected based on owner arrival status
- Historical owner pattern tracking updated for future reference

### 4. Property-Based Service Assignment

#### Service Type Determination
System assigns appropriate service types based on context:
- Reservation entry type influences initial service assignment
- Property characteristics affect service complexity requirements
- Guest vs owner occupancy determines service focus areas
- Seasonal factors influence cleaning intensity and scope
- Historical service patterns guide standard service selection

#### Service Template Mapping
Property configuration determines HCP job template selection:
- Turnover services use property's Turnover Job Template ID
- Return Laundry services use dedicated laundry template configuration
- Inspection services use inspection-specific template settings
- Template validation confirms availability before job creation
- Missing templates trigger service configuration error workflows

#### Service Name Generation with Property Context
Descriptive service names combine multiple contextual elements:
- Base service type forms foundation of service description
- Owner arrival detection adds OWNER ARRIVING prefix when applicable
- Next guest information appends arrival date for turnover context
- Same-day turnover scenarios receive SAME DAY priority prefix
- Property-specific requirements influence service name customization

### 5. HCP Address Validation and Management

#### Address Configuration Verification
System validates HCP address settings before job creation:
- Property record must contain valid HCP Address ID
- Address existence verified through HCP API lookup
- Address-customer relationship confirmed through HCP validation
- Address details compared to property information for consistency
- Missing or invalid addresses prevent job creation until resolved

#### Address-Customer Relationship Validation
System confirms proper address assignments in HCP:
- Retrieved address customer ID compared to expected customer
- Mismatched customer assignments trigger relationship review
- Address accessibility verified through API permissions
- Service location details validated for cleaner dispatch
- Address changes propagated to dependent service records

#### Property Location Consistency Checking
System validates address consistency across platforms:
- Property name components compared to HCP address details
- Address components checked for reasonable property name matches
- Significant discrepancies flagged for administrative review
- Confidence scores assigned based on matching criteria
- Low confidence matches require manual verification

### 6. Service Template Configuration Management

#### Template Availability Validation
System confirms required templates exist for service creation:
- Service type determines which template field to check
- Property record queried for appropriate template ID
- Template existence verified in HCP before job creation
- Missing templates prevent service assignment until configured
- Template validation errors logged with specific resolution steps

#### Template-Service Type Mapping
Business logic maps service types to appropriate templates:
- Standard turnovers use Turnover Job Template configuration
- Return laundry services use dedicated laundry template
- Inspection services use inspection-specific template settings
- Deep cleaning and initial services default to turnover template
- Custom service types require explicit template assignment

#### Template Configuration Error Handling
System manages template configuration issues gracefully:
- Missing templates trigger administrative notification workflows
- Invalid template IDs prevent job creation with clear error messages
- Template access permission issues escalated to HCP admin
- Template configuration guidance provided for property setup
- Fallback procedures used when possible to maintain service delivery

### 7. Data Quality and Validation Processing

#### Property Data Completeness Checking
System validates essential property information before processing:
- Property name presence confirmed for identification purposes
- Customer assignment verified for service delivery context
- HCP Address ID validated for physical service location
- Service template availability checked for job creation capability
- Status field verified for active service eligibility

#### Critical Field Change Detection
System monitors important property field modifications:
- Customer assignment changes affect billing and service delivery
- Address ID changes impact service location and dispatcher routing
- Template changes influence service configuration and pricing
- Status changes affect service eligibility and scheduling
- Name changes require communication update and record synchronization

#### Data Integration Conflict Resolution
System handles conflicting information from multiple sources:
- Priority-based field assignment resolves most conflicts automatically
- Manual review triggered for critical field conflicts
- Audit trails maintained for all data source changes
- Administrative alerts generated for significant conflicts
- Historical data preserved for conflict resolution reference

### 8. Error Recovery and Validation Workflows

#### Property Validation Failure Handling
System manages property configuration errors systematically:
- Missing customer assignments trigger property setup workflows
- Invalid HCP relationships prevent job creation with clear guidance
- Template configuration errors provide specific resolution instructions
- Address validation failures require HCP administrator intervention
- Status conflicts require property manager review and resolution

#### Owner Detection Error Management
System handles owner detection algorithm failures gracefully:
- Missing checkout dates result in conservative no-owner assumptions
- Property ID resolution failures skip owner analysis entirely
- Date parsing errors use safe fallback values
- Block query failures default to standard service procedures
- Detection algorithm errors logged for pattern analysis

#### Service Assignment Error Recovery
System provides fallback procedures for service assignment failures:
- Template lookup failures prevent job creation with clear error messages
- Service type mapping errors use conservative default assignments
- Name generation failures use minimal safe service descriptions
- HCP API failures trigger retry procedures with exponential backoff
- Critical errors escalated to administrative review workflows

## State Management Flow

### Property States
- **New**: Recently added property awaiting configuration
- **Configuring**: Property setup in progress with incomplete information
- **Active**: Fully configured property eligible for service scheduling
- **Inactive**: Temporarily disabled property not receiving services
- **Archived**: Historical property no longer in service rotation

### Customer Relationship States
- **Unlinked**: Property not assigned to any customer
- **Linking**: Customer assignment in progress
- **Linked**: Property successfully assigned to validated customer
- **Invalid**: Customer relationship configuration contains errors
- **Updating**: Customer information modification in progress

### Owner Detection States
- **Analyzing**: Examining reservation context for owner patterns
- **Detected**: Owner arrival identified and validated
- **Not Detected**: No owner arrival found within detection window
- **Error**: Detection algorithm encountered processing errors
- **Manual Override**: Administrative override of automatic detection

## Performance Optimization Flow

### Property Data Caching
- Property records cached for rapid lookup during job creation
- Customer relationship information stored for immediate access
- Template configurations cached to reduce HCP API calls
- Address validation results cached for consistent performance
- Property change detection optimized through incremental updates

### Owner Detection Efficiency
- Block queries optimized using indexed property and date fields
- Detection algorithm skips analysis when checkout date missing
- Property schedule analysis limited to relevant time windows
- Result caching reduces redundant detection calculations
- Historical pattern analysis improves detection accuracy

### Service Assignment Optimization
- Template mapping performed through efficient lookup tables
- Service name generation uses pre-computed property context
- HCP API calls minimized through intelligent batching
- Validation procedures optimized for common success scenarios
- Error handling streamlined for rapid failure recovery

## Integration Points and Dependencies

### Upstream Data Sources
- **Evolve Scraper**: Property listing and characteristic information
- **CSV Processor**: Reservation and guest booking data
- **ICS Processor**: Calendar and availability information
- **Manual Entry**: Administrative updates and corrections

### Downstream Service Impacts
- **Job Creation**: Property validation enables HCP job creation
- **Service Scheduling**: Owner detection influences service timing
- **Service Delivery**: Property characteristics affect service requirements
- **Communication**: Customer relationships determine notification recipients

### Cross-System Synchronization
- **Airtable Updates**: Property changes propagated to reservation records
- **HCP Synchronization**: Customer and address changes reflected in job creation
- **Cache Invalidation**: Property updates trigger cache refresh procedures
- **Audit Logging**: All property changes tracked for compliance and troubleshooting

## Monitoring and Quality Assurance

### Property Data Quality Metrics
- Completeness rates tracked for essential property fields
- Customer assignment success rates monitored for relationship management
- Template configuration coverage measured for service delivery readiness
- Address validation success rates tracked for location accuracy
- Data source priority compliance monitored for consistency

### Owner Detection Accuracy Tracking
- Detection algorithm success rates measured against manual verification
- False positive rates tracked for algorithm refinement
- Detection timing accuracy monitored for service schedule optimization
- Block classification accuracy validated through outcome analysis
- Historical pattern accuracy improves future detection confidence

### Service Assignment Quality Monitoring
- Template mapping success rates tracked for configuration completeness
- Service name generation accuracy validated through cleaner feedback
- HCP integration success rates monitored for platform reliability
- Error recovery effectiveness measured through resolution time tracking
- Customer satisfaction correlation analyzed for service quality improvement

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Primary Code**: Property relationship management and validation systems
**Related**: BusinessLogicAtoZ.md, mermaid-flows.md