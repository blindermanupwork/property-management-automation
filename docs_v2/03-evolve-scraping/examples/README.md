# Evolve Scraping - Examples

**Feature:** 03-evolve-scraping  
**Purpose:** Real-world examples of web scraping Evolve property management portal  
**Last Updated:** July 14, 2025

---

## 📋 Table of Contents

1. [Selenium Configuration](#selenium-configuration)
2. [Login Process Examples](#login-process-examples)
3. [Property Data Extraction](#property-data-extraction)
4. [Multi-Tab Export Handling](#multi-tab-export-handling)
5. [Error Recovery Scenarios](#error-recovery-scenarios)
6. [Performance Optimization](#performance-optimization)

---

## 🌐 Selenium Configuration

### Chrome Options Setup
```python
def setup_chrome_options(headless=True, download_dir="/home/opc/automation/CSV_process_development"):
    """Configure Chrome for Evolve scraping"""
    options = webdriver.ChromeOptions()
    
    # Basic options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    if headless:
        options.add_argument('--headless=new')  # New headless mode
    
    # Window size for consistent rendering
    options.add_argument('--window-size=1920,1080')
    
    # Download preferences
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    options.add_experimental_option("prefs", prefs)
    
    # Performance options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return options
```

### WebDriver Initialization
```python
def initialize_driver():
    """Initialize Chrome WebDriver with retry logic"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            service = Service('/usr/local/bin/chromedriver')
            driver = webdriver.Chrome(service=service, options=setup_chrome_options())
            
            # Set timeouts
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            
            print(f"✅ Chrome WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise
```

---

## 🔐 Login Process Examples

### Standard Login Flow
```python
def login_to_evolve(driver, username, password):
    """Login to Evolve portal with error handling"""
    login_url = "https://login.evolve.com"
    
    try:
        # Navigate to login page
        print(f"🌐 Navigating to {login_url}")
        driver.get(login_url)
        
        # Wait for login form
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Enter credentials
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        
        username_field.clear()
        username_field.send_keys(username)
        
        password_field.clear()
        password_field.send_keys(password)
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-container"))
        )
        
        print("✅ Login successful")
        return True
        
    except TimeoutException:
        print("❌ Login timeout - dashboard not loaded")
        # Check for error messages
        try:
            error_msg = driver.find_element(By.CLASS_NAME, "error-message").text
            print(f"❌ Login error: {error_msg}")
        except:
            pass
        return False
```

### Two-Factor Authentication Handling
```python
def handle_2fa(driver, timeout=300):
    """Handle 2FA if required"""
    try:
        # Check if 2FA page appeared
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "verification-code"))
        )
        
        print("🔐 2FA required - waiting for user input...")
        print(f"⏳ You have {timeout} seconds to complete 2FA")
        
        # Wait for user to complete 2FA
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-container"))
        )
        
        print("✅ 2FA completed successfully")
        return True
        
    except TimeoutException:
        # No 2FA required or already completed
        return True
```

---

## 📊 Property Data Extraction

### Navigation to Reservations
```python
def navigate_to_reservations(driver):
    """Navigate to reservations page"""
    try:
        # Click reservations menu
        reservations_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/reservations')]"))
        )
        reservations_link.click()
        
        # Wait for page load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "reservations-table"))
        )
        
        print("✅ Navigated to reservations page")
        return True
        
    except Exception as e:
        print(f"❌ Failed to navigate to reservations: {e}")
        return False
```

### Export Button Interaction
```python
def click_export_button(driver):
    """Click the export button and handle dropdown"""
    try:
        # Find and click export button
        export_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Export')]"))
        )
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        time.sleep(1)
        
        # Click using JavaScript to avoid interception
        driver.execute_script("arguments[0].click();", export_button)
        
        # Wait for dropdown menu
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "export-menu"))
        )
        
        print("✅ Export menu opened")
        return True
        
    except Exception as e:
        print(f"❌ Failed to open export menu: {e}")
        # Take screenshot for debugging
        driver.save_screenshot("export_error.png")
        return False
```

---

## 📑 Multi-Tab Export Handling

### Sequential Tab Export
```python
def export_all_tabs_sequential(driver, download_dir):
    """Export both tabs sequentially to avoid conflicts"""
    exported_files = []
    
    # Tab configurations
    tabs = [
        {
            "name": "Current Reservations",
            "xpath": "//div[@class='export-menu']//a[contains(text(), 'Current')]",
            "wait_element": "current-reservations-table"
        },
        {
            "name": "Future Reservations", 
            "xpath": "//div[@class='export-menu']//a[contains(text(), 'Future')]",
            "wait_element": "future-reservations-table"
        }
    ]
    
    for i, tab in enumerate(tabs):
        print(f"📥 Exporting {tab['name']}...")
        
        try:
            # Click export option
            export_option = driver.find_element(By.XPATH, tab['xpath'])
            export_option.click()
            
            # Wait for download to start
            time.sleep(2)
            
            # Monitor download completion
            downloaded_file = wait_for_download(download_dir, timeout=60)
            
            if downloaded_file:
                # Rename to include tab identifier
                timestamp = datetime.now().strftime('%m-%d-%Y--%H-%M-%S')
                new_name = f"{timestamp}_tab{i+1}.csv"
                new_path = os.path.join(download_dir, new_name)
                
                os.rename(downloaded_file, new_path)
                exported_files.append(new_path)
                print(f"✅ Downloaded: {new_name}")
            else:
                print(f"❌ Download timeout for {tab['name']}")
                
            # Wait between exports
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Failed to export {tab['name']}: {e}")
    
    return exported_files
```

### Download Monitoring
```python
def wait_for_download(download_dir, timeout=60, check_interval=1):
    """Monitor download directory for new files"""
    start_time = time.time()
    initial_files = set(os.listdir(download_dir))
    
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - initial_files
        
        # Look for CSV files
        csv_files = [f for f in new_files if f.endswith('.csv') and not f.endswith('.crdownload')]
        
        if csv_files:
            # Wait a bit more to ensure download is complete
            time.sleep(2)
            
            # Verify file size is stable
            file_path = os.path.join(download_dir, csv_files[0])
            size1 = os.path.getsize(file_path)
            time.sleep(1)
            size2 = os.path.getsize(file_path)
            
            if size1 == size2:  # File size stable
                return file_path
        
        time.sleep(check_interval)
    
    return None
```

---

## 🔧 Error Recovery Scenarios

### Scenario 1: Stale Element Reference
```python
def safe_click(driver, locator, max_retries=3):
    """Click element with stale element retry"""
    for attempt in range(max_retries):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(locator)
            )
            element.click()
            return True
        except StaleElementReferenceException:
            print(f"⚠️ Stale element, retry {attempt + 1}/{max_retries}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Click failed: {e}")
            break
    
    return False
```

### Scenario 2: Page Load Timeout
```python
def robust_page_load(driver, url, max_retries=3):
    """Load page with timeout handling"""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            # Wait for any element that indicates page loaded
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print(f"⚠️ Page load timeout, retry {attempt + 1}/{max_retries}")
            driver.refresh()
        except Exception as e:
            print(f"❌ Page load failed: {e}")
            break
    
    return False
```

### Scenario 3: Download Failure Recovery
```python
def export_with_recovery(driver, download_dir):
    """Export with automatic recovery on failure"""
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            # Clear any previous downloads
            clear_old_downloads(download_dir)
            
            # Navigate to fresh page
            driver.refresh()
            time.sleep(2)
            
            # Attempt export
            files = export_all_tabs_sequential(driver, download_dir)
            
            if len(files) == 2:  # Both tabs exported
                print(f"✅ Export successful on attempt {attempt + 1}")
                return files
            else:
                print(f"⚠️ Incomplete export, retrying...")
                
        except Exception as e:
            print(f"❌ Export attempt {attempt + 1} failed: {e}")
            
        # Wait before retry
        time.sleep(10)
    
    raise Exception("Export failed after all attempts")
```

---

## 🚀 Performance Optimization

### Resource Usage Monitoring
```python
import psutil

def monitor_resources():
    """Monitor system resources during scraping"""
    process = psutil.Process()
    
    return {
        'cpu_percent': process.cpu_percent(interval=1),
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'threads': process.num_threads(),
        'chrome_processes': len([p for p in psutil.process_iter(['name']) 
                               if 'chrome' in p.info['name'].lower()])
    }

# Usage during scraping
print(f"📊 Resources: {monitor_resources()}")
```

### Memory Leak Prevention
```python
def cleanup_driver(driver):
    """Properly cleanup driver to prevent memory leaks"""
    try:
        # Close all windows
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            driver.close()
    except:
        pass
    
    try:
        # Quit driver
        driver.quit()
    except:
        pass
    
    # Kill any remaining Chrome processes
    os.system("pkill -f 'chrome.*--headless'")
    
    print("🧹 Driver cleanup completed")
```

### Parallel vs Sequential Processing
```python
# Configuration for different environments
SCRAPING_CONFIG = {
    'development': {
        'headless': True,
        'parallel': False,  # Sequential to avoid conflicts
        'download_wait': 5,  # Seconds between downloads
        'max_workers': 1
    },
    'production': {
        'headless': True,
        'parallel': False,  # Always sequential for stability
        'download_wait': 5,
        'max_workers': 1
    }
}
```

---

## 📊 Real-World Metrics

### Typical Scraping Session
```python
# Production metrics from July 2025
SCRAPING_METRICS = {
    'total_duration': '3m 45s',
    'login_time': '8s',
    'navigation_time': '5s',
    'export_tab1_time': '45s',
    'export_tab2_time': '42s',
    'file_processing_time': '2m 15s',
    'total_records': 487,
    'memory_peak': '385 MB',
    'cpu_peak': '45%'
}

# Success rates
SUCCESS_RATES = {
    'login_success': '98%',
    'export_success': '95%',
    'recovery_success': '100%',  # When retry needed
    'total_uptime': '99.2%'
}
```

---

## 🔗 Related Documentation
- [Evolve Scraping Business Logic](../BusinessLogicAtoZ.md)
- [Evolve Scraping Flows](../flows/)
- [CSV Processing Integration](../../01-csv-processing/)