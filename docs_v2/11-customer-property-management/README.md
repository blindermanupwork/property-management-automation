# Customer & Property Management

## Overview
The Customer & Property Management feature handles the complex relationships between properties, property owners, reservations, and service assignments. It manages property data synchronization from multiple sources, maintains property-to-customer mappings for HousecallPro integration, and handles the intricate business logic of property ownership, blocks, and service scheduling.

## Core Functionality

### Property Data Management
- **Multi-Source Integration**: Handles property data from Evolve scraping, ICS feeds, CSV imports, and manual entries
- **Property Metadata**: Manages property names, addresses, amenities, cleaning requirements, and service specifications
- **Change Detection**: Tracks property information changes and propagates updates across systems
- **Data Validation**: Ensures property data consistency and completeness before processing

### Customer Relationship Management
- **HCP Customer Mapping**: Links Airtable properties to HousecallPro customer and address records
- **Owner vs Guest Management**: Distinguishes between property owners (who receive services) and guests (who stay at properties)
- **Contact Information**: Manages owner contact details, service preferences, and communication channels
- **Service History**: Tracks service patterns, preferences, and special requirements per property

### Property-Based Service Logic
- **Owner Arrival Detection**: Automatically identifies when property owners are returning (triggers special service flags)
- **Block Management**: Handles owner blocks, maintenance blocks, and other non-guest periods
- **Service Type Assignment**: Determines appropriate service types based on property characteristics and usage patterns
- **Scheduling Optimization**: Considers property-specific factors for service timing and resource allocation

## Key Components

### Property Data Sources
1. **Evolve Platform**: Automated scraping of property listings and details
2. **ICS Calendar Feeds**: Property availability and booking information
3. **CSV Imports**: Bulk property data updates and corrections
4. **Manual Entry**: Administrative updates and custom property configurations

### Customer Integration Points
1. **HousecallPro Customers**: Property owners who receive cleaning services
2. **HousecallPro Addresses**: Physical service locations linked to HCP customers
3. **Airtable Properties**: Central property registry with comprehensive metadata
4. **Service Assignments**: Links between properties, customers, and service requirements

### Business Logic Triggers
1. **Owner Return Detection**: Analyzes booking patterns to identify owner arrivals
2. **Property Type Services**: Assigns service types based on property characteristics
3. **Seasonal Adjustments**: Modifies service requirements based on usage patterns
4. **Maintenance Scheduling**: Coordinates property maintenance with service schedules

## Integration Architecture

### Upstream Dependencies
- **Evolve Scraper**: Provides property listing data and availability
- **ICS Processor**: Supplies booking and availability information
- **CSV Processor**: Handles bulk property data imports
- **HCP Integration**: Manages customer and address synchronization

### Downstream Impacts
- **Job Creation**: Property data influences service type and scheduling
- **Service Line Management**: Property characteristics affect service descriptions
- **Schedule Management**: Property-specific requirements influence timing
- **Webhook Processing**: Property changes trigger update cascades

## Current Version
**Version**: 2.2.8
**Status**: Active and maintained
**Environment Support**: Complete dev/prod separation
**Data Volume**: 500+ properties across multiple platforms

## Related Documentation
- **HousecallPro Integration**: For customer/address API details
- **Evolve Scraping**: For property data acquisition
- **ICS Feed Sync**: For booking and availability data
- **API Server**: For property-related endpoints and operations