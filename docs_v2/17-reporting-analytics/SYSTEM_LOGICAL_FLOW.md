# Reporting & Analytics - System Logical Flow

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Text-based operational flow documentation for reporting and analytics system

---

## 🔄 **OPERATIONAL REPORTING FLOWS**

### **1. HCP Job Analysis Flow**

**Trigger**: Request for job statistics or revenue analysis

**Process Flow**:
1. **Cache Validation**
   - Check for cached job files in environment directory
   - Validate JSON structure of each file
   - Count available files for processing
   - Throw error if no valid cache exists

2. **Data Extraction Loop**
   - Open each cache file sequentially
   - Parse JSON with multiple structure fallbacks
   - Extract jobs array from various locations
   - Track file processing count

3. **Job Processing**
   - Iterate through each job in file
   - Extract revenue using fallback strategy
   - Categorize by status and date
   - Build customer statistics map

4. **Aggregation and Ranking**
   - Calculate totals and averages
   - Sort customers by revenue
   - Generate monthly trends
   - Package with quality metrics

**Output**: Comprehensive analysis with execution time and data quality indicators

---

### **2. Service Item Usage Analysis Flow**

**Trigger**: Request to analyze specific items (towels, linens, etc.)

**Process Flow**:
1. **Pattern Compilation**
   - Convert search pattern to regex
   - Set case-insensitive flag
   - Prepare field list for searching

2. **Line Item Scanning**
   - Load cached job files
   - Iterate through job line items
   - Match against pattern in name/description
   - Skip jobs without line items

3. **Usage Calculation**
   - Parse quantity and pricing fields
   - Calculate total cost (quantity × unit cost)
   - Calculate total revenue (quantity × unit price)
   - Track customer-specific usage

4. **Summary Generation**
   - Sum total quantities across all jobs
   - Calculate average price per unit
   - Build usage detail array
   - Include processing metrics

**Output**: Item-specific analysis with customer breakdown and financial metrics

---

### **3. CSV Processing Report Flow**

**Trigger**: Completion of CSV file processing

**Process Flow**:
1. **Result Collection**
   - Gather outcomes by property and source
   - Count new, modified, unchanged records
   - Map property IDs to names

2. **Property Grouping**
   - Iterate through summary by property
   - Format header with source and property name
   - Count outcomes by type
   - Skip empty property results

3. **Summary Calculation**
   - Sum totals across all properties
   - Separate by outcome type
   - Calculate processing statistics

4. **Report Formatting**
   - Add delimiter headers
   - List property-specific details
   - Append summary section
   - Close with delimiter footer

**Output**: Structured report suitable for logging and automation parsing

---

### **4. ICS Feed Sync Reporting Flow**

**Trigger**: Completion of ICS calendar sync

**Process Flow**:
1. **Statistics Initialization**
   - Create counters for each outcome
   - Track feed success/failure
   - Initialize property mapping

2. **Feed Result Processing**
   - Iterate through feed statistics
   - Resolve property names from IDs
   - Accumulate outcome counts
   - Track error conditions

3. **Machine-Readable Output**
   - Generate ICS_SUMMARY line
   - Include all key metrics
   - Format for automation parsing
   - Print to stdout for capture

4. **Human-Readable Report**
   - Format run digest section
   - List per-feed statistics
   - Generate summary totals
   - Log with proper structure

**Output**: Dual-format output for both human review and automation consumption

---

### **5. Customer Revenue Analysis Flow**

**Trigger**: Request for customer financial analysis

**Process Flow**:
1. **Customer Data Structure**
   - Initialize empty customer map
   - Set up statistics tracking
   - Prepare for aggregation

2. **Job Revenue Attribution**
   - Extract customer ID from job
   - Calculate job revenue
   - Increment job count
   - Track by work status

3. **Customer Aggregation**
   - Build customer profile
   - Sum total revenue
   - Count jobs by status
   - Calculate averages

4. **Results Compilation**
   - Convert map to array
   - Calculate average job values
   - Sort by total revenue
   - Return customer array

**Output**: Ranked customer list with comprehensive financial metrics

---

### **6. Monthly Trend Analysis Flow**

**Trigger**: Any analysis including temporal data

**Process Flow**:
1. **Date Extraction**
   - Get created or scheduled date
   - Parse into Date object
   - Extract year and month
   - Format as YYYY-MM

2. **Monthly Accumulation**
   - Initialize month if new
   - Increment job count
   - Add to revenue total
   - Handle invalid dates

3. **Trend Calculation**
   - Convert object to array
   - Sort chronologically
   - Calculate month-over-month
   - Identify patterns

4. **Visualization Prep**
   - Structure for charting
   - Include all metrics
   - Maintain sort order
   - Package for display

**Output**: Time-series data ready for trend visualization

---

### **7. Automation Performance Reporting Flow**

**Trigger**: Completion of automation suite run

**Process Flow**:
1. **Result Collection**
   - Track each automation outcome
   - Record execution times
   - Note any failures
   - Calculate totals

2. **Performance Metrics**
   - Count successful runs
   - Calculate success rate
   - Sum total duration
   - Identify slowest component

3. **Visual Summary**
   - Create header separator
   - List each component status
   - Show success indicators
   - Display timing data

4. **Console Output**
   - Print formatted summary
   - Use emoji indicators
   - Show completion time
   - Include environment info

**Output**: Comprehensive automation run summary with KPIs

---

### **8. Data Quality Tracking Flow**

**Trigger**: Any analysis operation

**Process Flow**:
1. **Metric Initialization**
   - Set file counter to zero
   - Initialize record counter
   - Create error counter
   - Start execution timer

2. **Processing Tracking**
   - Increment for each file
   - Add record counts
   - Log any errors
   - Continue on failure

3. **Quality Calculation**
   - Calculate error rate
   - Determine completeness
   - Check data freshness
   - Assess reliability

4. **Metric Packaging**
   - Create quality object
   - Include all counters
   - Add to results
   - Return with analysis

**Output**: Data quality metrics embedded in all analysis results

---

### **9. Revenue Extraction Flow**

**Trigger**: Need to determine job monetary value

**Process Flow**:
1. **Field Priority Check**
   - Try job.total first
   - Fallback to total_amount
   - Check invoice_total
   - Try amount, price, subtotal

2. **Type Validation**
   - Check if number type
   - Parse string values
   - Validate not NaN
   - Return on first valid

3. **Line Item Summation**
   - Check for line items array
   - Calculate quantity × price
   - Sum all line items
   - Use as last resort

4. **Default Handling**
   - Return zero if no value
   - Never return null/undefined
   - Ensure numeric type
   - Log extraction method

**Output**: Reliable revenue value using best available source

---

### **10. Report Distribution Flow**

**Trigger**: Scheduled or on-demand report generation

**Process Flow**:
1. **Report Type Selection**
   - Identify requested report
   - Load appropriate template
   - Set parameter defaults
   - Validate permissions

2. **Data Collection**
   - Run required analyses
   - Aggregate results
   - Apply filters
   - Format output

3. **Distribution Routing**
   - Check delivery preferences
   - Queue for each channel
   - Track delivery status
   - Handle failures

4. **Confirmation Loop**
   - Verify delivery success
   - Log distribution
   - Update last-sent time
   - Notify requestor

**Output**: Reports delivered to configured destinations with tracking

---

## 🔧 **REPORTING CONFIGURATION PATTERNS**

### **Analysis Defaults**
- **Top Customers**: Limited to 10
- **Monthly Trends**: All available months
- **Error Tolerance**: Continue on individual failures
- **Execution Tracking**: Always enabled

### **Output Formats**
- **Console**: Human-readable with emojis
- **Logs**: Structured with delimiters
- **API**: JSON with metadata
- **Export**: CSV with headers

### **Performance Thresholds**
- **Analysis Timeout**: 30 seconds
- **File Size Limit**: 100MB per cache
- **Memory Limit**: 512MB per analysis
- **Concurrent Files**: 10 maximum

---

*This operational flow documentation provides comprehensive coverage of how reporting and analytics flow through the property management automation system, transforming raw data into actionable intelligence.*