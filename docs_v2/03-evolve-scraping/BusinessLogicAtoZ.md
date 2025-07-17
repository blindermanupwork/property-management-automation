# Evolve Portal Scraping - Complete Business Logic Documentation

## Overview
This document provides a comprehensive business-level description of automated web scraping for the Evolve property management portal, including browser automation, data extraction workflows, file processing, and environment management.

## Core Business Purpose

The Evolve scraping system automatically extracts property availability and reservation data from the Evolve portal web interface to supplement other data sources and ensure comprehensive property management coverage.

## Business Workflows

### 1. Environment Setup and Execution

#### **Critical Environment Configuration**
**ENVIRONMENT Variable**: Must be set BEFORE Python execution
```bash
# Correct way to run
ENVIRONMENT=production python3 evolveScrape.py --headless --sequential
```

**Business Logic**:
1. **Environment Validation**:
   - Check ENVIRONMENT variable at startup
   - Fail immediately if not set to 'development' or 'production'
   - Cannot be changed after Python starts due to Config singleton

2. **Output Directory Determination**:
   ```python
   if ENVIRONMENT == 'production':
       output_dir = 'CSV_process_production/'
   elif ENVIRONMENT == 'development':
       output_dir = 'CSV_process_development/'
   else:
       raise ValueError("Invalid environment")
   ```

### 2. Browser Automation Setup

#### **Chrome WebDriver Configuration**
**Business Requirements**:
- Must use Google Chrome browser
- Headless mode required for server execution
- Sequential processing to avoid Chrome conflicts

**Chrome Options**:
```python
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-web-security')
chrome_options.add_argument('--disable-features=VizDisplayCompositor')

# Set download directory
prefs = {
    "download.default_directory": "/tmp/evolve_downloads",
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
```

### 3. Portal Authentication

#### **Login Workflow**
**UI Fields Used**:
- **Username Field**: CSS selector `input[name="username"]` or `#username`
- **Password Field**: CSS selector `input[name="password"]` or `#password`
- **Login Button**: CSS selector `input[type="submit"]` or `.login-button`

**Business Logic**:
1. **Navigation to Login Page**:
   ```python
   def navigate_to_login():
       driver.get("https://evolve.com/owner/login")
       wait_for_element("input[name='username']", timeout=30)
   ```

2. **Credential Input**:
   ```python
   def enter_credentials():
       username_field = driver.find_element(By.NAME, "username")
       password_field = driver.find_element(By.NAME, "password")
       
       username_field.clear()
       username_field.send_keys(os.getenv('EVOLVE_USERNAME'))
       
       password_field.clear()
       password_field.send_keys(os.getenv('EVOLVE_PASSWORD'))
   ```

3. **Login Validation**:
   ```python
   def validate_login():
       # Wait for dashboard or property list
       try:
           WebDriverWait(driver, 30).until(
               EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
           )
           return True
       except TimeoutException:
           return False
   ```

### 4. Data Export Process

#### **Two-Tab Export Strategy**
**Tab 1: Property Availability**
- **Purpose**: Current and future availability calendar
- **Navigation Path**: Properties → Calendar View → Export
- **File Format**: Availability CSV with date ranges

**Tab 2: Reservation Data**
- **Purpose**: Current and historical reservations
- **Navigation Path**: Reports → Reservations → Export
- **File Format**: Reservation CSV with guest details

#### **Sequential Export Logic**
**Business Rules**:
1. **Must Process in Order**: Tab 1 then Tab 2
2. **Clean State**: Clear browser between tabs
3. **Validate Each**: Check file download before proceeding

```python
def export_data_sequential():
    try:
        # Export Tab 1 (Availability)
        success_tab1 = export_availability_data()
        if not success_tab1:
            raise Exception("Tab 1 export failed")
            
        # Clear browser state
        clear_browser_cache()
        
        # Export Tab 2 (Reservations)
        success_tab2 = export_reservation_data()
        if not success_tab2:
            raise Exception("Tab 2 export failed")
            
        return True
    except Exception as e:
        log.error(f"Sequential export failed: {e}")
        return False
```

### 5. UI Element Interaction

#### **Export Button Workflow**
**Tab 1 Export Process**:
1. **Navigate to Calendar**: Click "Calendar" in main menu
2. **Select Date Range**: Choose export period (usually current month + next 2 months)
3. **Click Export Button**: CSS selector `.export-btn` or button containing "Export"
4. **Select Format**: Choose CSV format
5. **Confirm Download**: Click final download button

**Tab 2 Export Process**:
1. **Navigate to Reports**: Click "Reports" in main menu
2. **Select Reservations**: Click "Reservations" submenu
3. **Set Date Filter**: Choose date range for reservations
4. **Click Export Button**: Similar to Tab 1 process
5. **Download CSV**: Wait for file generation

#### **Dynamic Element Handling**
**Business Logic**:
```python
def click_with_retry(selector, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            element.click()
            return True
        except (TimeoutException, ElementClickInterceptedException):
            if attempt == max_attempts - 1:
                # Try JavaScript click as fallback
                driver.execute_script(
                    f"document.querySelector('{selector}').click();"
                )
            time.sleep(2)
    return False
```

### 6. File Download Management

#### **Download Directory Management**
**Business Rules**:
1. **Temporary Storage**: All downloads go to `/tmp/evolve_downloads/`
2. **Clean Before Run**: Delete all existing files
3. **Monitor Downloads**: Poll for file completion
4. **Validate Files**: Check size and format

```python
def setup_download_directory():
    download_dir = "/tmp/evolve_downloads"
    
    # Clean existing files
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    
    # Create fresh directory
    os.makedirs(download_dir, exist_ok=True)
    return download_dir

def wait_for_download(filename_pattern, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        files = glob.glob(f"/tmp/evolve_downloads/{filename_pattern}")
        if files:
            # Check file is complete (not growing)
            filepath = files[0]
            initial_size = os.path.getsize(filepath)
            time.sleep(2)
            final_size = os.path.getsize(filepath)
            
            if initial_size == final_size and final_size > 0:
                return filepath
        time.sleep(1)
    return None
```

### 7. File Processing and Movement

#### **Post-Download Processing**
**Business Logic**:
1. **File Validation**:
   ```python
   def validate_csv_file(filepath):
       try:
           df = pd.read_csv(filepath)
           if len(df) == 0:
               raise ValueError("Empty CSV file")
           
           # Check for expected columns
           required_columns = ['property', 'date', 'status']  # Tab 1
           # or ['guest', 'checkin', 'checkout']  # Tab 2
           
           missing_cols = [col for col in required_columns if col not in df.columns]
           if missing_cols:
               log.warning(f"Missing columns: {missing_cols}")
           
           return True
       except Exception as e:
           log.error(f"CSV validation failed: {e}")
           return False
   ```

2. **File Naming and Movement**:
   ```python
   def move_to_processing_folder(source_file, environment):
       timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
       filename = os.path.basename(source_file)
       
       # Add timestamp prefix
       new_filename = f"{timestamp}_{filename}"
       
       # Determine destination
       dest_folder = f"CSV_process_{environment}"
       dest_path = os.path.join(dest_folder, new_filename)
       
       # Move file
       shutil.move(source_file, dest_path)
       log.info(f"Moved {filename} to {dest_path}")
       
       return dest_path
   ```

### 8. Error Handling and Recovery

#### **Retry Logic Implementation**
**Business Rules**:
1. **3-Attempt Maximum**: For each major operation
2. **Exponential Backoff**: 5, 10, 20 second delays
3. **Clean State**: Reset browser between attempts
4. **Screenshot on Error**: Capture UI state for debugging

```python
def execute_with_retry(operation_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = operation_func()
            return result
        except Exception as e:
            log.error(f"Attempt {attempt + 1} failed: {e}")
            
            # Take screenshot for debugging
            screenshot_path = f"/tmp/evolve_error_{attempt}_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff
            delay = 5 * (2 ** attempt)
            time.sleep(delay)
            
            # Reset browser state
            refresh_browser_session()
```

#### **Browser State Management**
```python
def refresh_browser_session():
    try:
        # Clear cookies and cache
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        
        # Navigate back to login
        driver.get("https://evolve.com/owner/login")
        
        # Re-authenticate
        login_success = perform_login()
        if not login_success:
            raise Exception("Re-authentication failed")
            
    except Exception as e:
        log.error(f"Browser refresh failed: {e}")
        # Force browser restart
        restart_browser()
```

### 9. Integration with Automation System

#### **Automation Controller Integration**
**Trigger**: Called by automation controller every 4 hours
**Configuration**: Uses environment-specific settings

**Integration Points**:
1. **Called from**: `src/automation/controller.py`
2. **Success Indicator**: Files moved to `CSV_process_[environment]/`
3. **Follow-up**: CSV processor automatically processes files
4. **Logging**: All activity logged to `evolve_scraping.log`

#### **Command Line Interface**
**Required Flags**:
- `--headless`: Must use for server execution
- `--sequential`: Must use to avoid Chrome conflicts

**Example Usage**:
```bash
# Production execution
ENVIRONMENT=production python3 evolveScrape.py --headless --sequential

# Development testing
ENVIRONMENT=development python3 evolveScrape.py --headless --sequential
```

### 10. Data Quality and Validation

#### **Export Completeness Checks**
**Business Rules**:
1. **Both Files Required**: Tab 1 AND Tab 2 must succeed
2. **Minimum Rows**: Each file must have > 0 data rows
3. **Column Validation**: Expected columns present
4. **Date Range**: Data covers expected time period

```python
def validate_export_completeness(tab1_file, tab2_file):
    issues = []
    
    # Check Tab 1 (Availability)
    if not os.path.exists(tab1_file):
        issues.append("Tab 1 file missing")
    else:
        df1 = pd.read_csv(tab1_file)
        if len(df1) == 0:
            issues.append("Tab 1 file empty")
    
    # Check Tab 2 (Reservations)
    if not os.path.exists(tab2_file):
        issues.append("Tab 2 file missing")
    else:
        df2 = pd.read_csv(tab2_file)
        if len(df2) == 0:
            issues.append("Tab 2 file empty")
    
    if issues:
        raise ValueError(f"Export validation failed: {', '.join(issues)}")
    
    return True
```

## Environment Configuration

### Development Environment
- **Output Directory**: `CSV_process_development/`
- **Log File**: `evolve_scraping_development.log`
- **Test Mode**: Limited property scope
- **Debug Screenshots**: Enabled

### Production Environment
- **Output Directory**: `CSV_process_production/`
- **Log File**: `evolve_scraping_production.log`
- **Full Scope**: All properties processed
- **Optimized Performance**: Minimal logging

## Critical Business Rules

### Pre-Execution Rules
1. **Environment Variable**: Must be set before Python starts
2. **Chrome Installation**: Required on system
3. **Credentials**: EVOLVE_USERNAME and EVOLVE_PASSWORD in environment
4. **Directory Access**: Write access to CSV_process folders

### Execution Rules
1. **Sequential Processing**: Never run multiple instances
2. **Headless Mode**: Required for server deployment
3. **Timeout Limits**: 10-minute maximum runtime
4. **Clean Exit**: Always logout and close browser

### Post-Processing Rules
1. **File Movement**: All files must move to processing folder
2. **Cleanup**: Remove temporary downloads
3. **Validation**: Both exports must succeed
4. **Handoff**: CSV processor takes over automatically

---

**Document Version**: 1.0.0
**Last Updated**: July 11, 2025
**Scope**: Complete Evolve scraping business logic
**Primary Code**: `/src/automation/scripts/evolve/evolveScrape.py`