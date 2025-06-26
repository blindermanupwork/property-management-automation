#!/usr/bin/env python3
"""
Evolve CSV Exporter Script
─────────────────────────
This script automates the process of:
  1. Logging in to the Evolve partner portal at
     https://partner.evolve.com/s/booking/Booking__c/Recent?tabset-feb43=3c3e0
  2. Applying a 'Check-Out' / 'Next 60 days' filter to the booking list
  3. Exporting the filtered booking data as a CSV file
  4. Saving the downloaded CSV into a specified local folder with timestamp

Usage:
    python evolveScrape.py --headless

Dependencies:
    pip install selenium webdriver-manager python-dotenv

Make sure to set EVOLVE_USER and EVOLVE_PASS in a .env file.
"""
# Change these imports at the top
import os
import sys
import time
import pathlib
import argparse
import logging
from datetime import datetime, timedelta, timezone  # Import timezone for PST
import pytz  # For PST timezone
import pandas as pd
import concurrent.futures  # For running browser instances concurrently

# Selenium web driver imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Import the automation config
script_dir = pathlib.Path(__file__).parent.absolute()
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from src.automation.config_wrapper import Config

# ────────────────────────── Configuration ──────────────────────────
# Use Config class for environment variables and paths

# Tab 2 CSV filtering configuration
TAB2_FILTER_MONTHS_PAST = Config.get_fetch_months_before()
TAB2_FILTER_MONTHS_FUTURE = 3  # Keep check-ins up to 3 months ahead
TAB2_FILTER_ENABLED = True     # Set to False to disable filtering
USER = Config.get_evolve_username()
PWD  = Config.get_evolve_password()
if not USER or not PWD:
    sys.exit("Error: Add EVOLVE_USERNAME / EVOLVE_PASSWORD to a .env file before running.")

# URL of the Evolve bookings page with the correct tab parameter
URL = (
    "https://partner.evolve.com/s/booking/Booking__c/Recent"
    "?tabset-feb43=3c3e0"
)
URL_TAB2 = "https://partner.evolve.com/s/booking/Booking__c/Recent?tabset-feb43=2"

# Maximum time to wait for page elements to load (in seconds)
WAIT = 30
# Delay between clicks to allow UI to update (in seconds)
DELAY = 0.5

# Directory to store downloaded CSV files - use CSV_process from Config
DOWNLOAD_DIR = Config.get_csv_process_dir()
# Create the directory if it doesn't exist
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Configure Python logging to display timestamp and message level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Debug logging
print(f"DEBUG: DOWNLOAD_DIR set to: {DOWNLOAD_DIR}")
print(f"DEBUG: Directory exists: {DOWNLOAD_DIR.exists()}")


def filter_tab2_csv(csv_path):
    """
    Filter the Tab 2 CSV file to only include rows where check-in date 
    is between TAB2_FILTER_MONTHS_PAST months ago and TAB2_FILTER_MONTHS_FUTURE months from now.
    
    Returns the path to the filtered CSV file.
    """
    if not TAB2_FILTER_ENABLED:
        log.info("Tab 2 filtering disabled, returning original CSV")
        return csv_path
        
    log.info(f"Filtering Tab 2 CSV to checkins between {TAB2_FILTER_MONTHS_PAST} months ago and {TAB2_FILTER_MONTHS_FUTURE} months ahead")
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        # Keep track of original row count
        original_count = len(df)
        
        # Check if 'Check-In' column exists (adjust name if needed)
        checkin_col = None
        for col in df.columns:
            if 'check-in' in col.lower() or 'checkin' in col.lower():
                checkin_col = col
                break
                
        if not checkin_col:
            log.warning("No Check-In column found in CSV, skipping filter")
            return csv_path
            
        # Convert the Check-In column to datetime
        df[checkin_col] = pd.to_datetime(df[checkin_col], errors='coerce')
        
        # Calculate date ranges in MST (timezone-naive for pandas comparison)
        mst = pytz.timezone('America/Phoenix')
        today = datetime.now(mst).replace(tzinfo=None)  # Remove timezone for pandas comparison
        past_date = today - timedelta(days=30 * TAB2_FILTER_MONTHS_PAST)
        future_date = today + timedelta(days=30 * TAB2_FILTER_MONTHS_FUTURE)
        
        # Filter the dataframe
        filtered_df = df[(df[checkin_col] >= past_date) & (df[checkin_col] <= future_date)]
        
        # Create filtered file path
        filtered_path = csv_path.with_suffix('.filtered.csv')
        
        # Save filtered data
        filtered_df.to_csv(filtered_path, index=False)
        
        log.info(f"Tab 2 CSV filtered: {original_count} rows -> {len(filtered_df)} rows")
        
        # Delete the original file
        os.remove(csv_path)
        
        return filtered_path
        
    except Exception as e:
        log.error(f"Error filtering Tab 2 CSV: {e}")
        return csv_path


def make_driver(headless: bool) -> webdriver.Chrome:
    """
    Initialize and return a Chrome WebDriver with desired options,
    including setting the download directory and headless mode.
    """
    opts = Options()
    
    # Remove user data directory to avoid conflicts
    # opts.add_argument(f"--user-data-dir={user_data_dir}")
    
    # If --headless flag passed, run without GUI
    if headless:
        opts.add_argument("--headless=new")
    # Speed up load and avoid sandbox issues
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    
    # Force browser to use Pacific timezone (so it thinks today is May 28)
    opts.add_argument("--lang=en-US")
    
    # Additional options to prevent conflicts
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-plugins")
    opts.add_argument("--disable-images")
    
    # Configure Chrome to automatically download files without prompt
    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": str(DOWNLOAD_DIR),
        "profile.default_content_settings.popups": 0,
    }
    opts.add_experimental_option("prefs", prefs)

    # Use webdriver-manager to install and manage ChromeDriver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    
    # Override timezone to Pacific Time using Chrome DevTools
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/Los_Angeles"})
    
    # Implicit wait for element presence
    driver.implicitly_wait(5)
    return driver


# New function for the second browser flow (simpler, no filtering needed)
def second_tab_export(headless: bool):
    """
    Open a second browser instance, login to Evolve, navigate to the second tab,
    export those bookings, and filter the CSV based on check-in dates.
    """
    driver = None
    try:
        log.info("Starting second browser for Tab 2 export...")
        driver = make_driver(headless)
        
        # 1) Go straight to Tab 2
        driver.get(URL_TAB2)
        try:
            form = WebDriverWait(driver, WAIT).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            log.info("Tab 2: Login page detected, submitting credentials...")
            inputs = form.find_elements(By.TAG_NAME, "input")[:2]
            inputs[0].send_keys(USER)
            inputs[1].send_keys(PWD)
            form.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        except TimeoutException:
            log.info("Tab 2: Already logged in, skipping.")
        
        # 2) Wait for the bookings page
        WebDriverWait(driver, WAIT).until(
            EC.url_contains("/s/booking/Booking__c/Recent")
        )
        time.sleep(2)
        log.info("Tab 2: Bookings page loaded ✔")
        
        # 3) Debug logging - what's on the page?
        log.info(f"Tab 2: Current URL: {driver.current_url}")
        log.info(f"Tab 2: Page title: {driver.title}")
        
        # 3) Find all "Export" buttons in the small-screen panel and click the last one
        log.info("Tab 2: Locating all Export buttons…")
        export_btns = driver.find_elements(
            By.CSS_SELECTOR,
            "div.slds-text-align_right.slds-show_small button.slds-button_neutral"
        )
        # filter by exact visible text
        export_btns = [b for b in export_btns if b.text.strip().lower() == "export"]
        
        if not export_btns:
            log.warning("Tab 2: No Export buttons found; aborting.")
            return
        
        btn = export_btns[-1]   # pick the bottom-of-table one
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        btn.click()
        log.info("Tab 2: Bottom-table Export clicked ⬇️")
        
        # 4) Wait for the CSV, filter it, and rename it
        log.info(f"Tab 2: Waiting for CSV download in {DOWNLOAD_DIR}")
        before = set(DOWNLOAD_DIR.glob("*.csv"))
        log.info(f"Tab 2: Existing CSV files: {[f.name for f in before]}")
        
        deadline = time.time() + 60
        while time.time() < deadline:
            now = set(DOWNLOAD_DIR.glob("*.csv"))
            new = now - before
            if new:
                orig = new.pop()
                log.info(f"Tab 2: Found new CSV: {orig.name}, size: {orig.stat().st_size} bytes")
                
                # Apply filtering before renaming
                if TAB2_FILTER_ENABLED:
                    filtered_path = filter_tab2_csv(orig)
                    orig = filtered_path
                
                # Generate timestamp in MST and rename
                mst = pytz.timezone('America/Phoenix')
                ts = datetime.now(mst).strftime("%m-%d-%Y--%H-%M-%S") 
                new_name = DOWNLOAD_DIR / f"{ts}_tab2.csv"
                orig.rename(new_name)
                log.info(f"Tab 2: Processing complete → {new_name.name}")
                return
            time.sleep(1)
        log.warning("Tab 2: CSV did not appear within 60 seconds.")
        
    except Exception as e:
        log.error(f"Tab 2 export error: {e}")
    finally:
        if driver:
            driver.quit()


def main_tab1(headless: bool):
    """Run the original flow for tab 1 (with filtering)"""
    driver = None
    try:
        # Create and configure the WebDriver
        driver = make_driver(headless)
        # Perform login sequence
        login(driver)
        # Apply booking filters
        apply_filter(driver)
        # Export the filtered CSV
        click_export(driver)
    except Exception as e:
        log.error(f"Tab 1 export error: {e}")
    finally:
        # Ensure browser closes even on error
        if driver:
            driver.quit()


# ──────────────────────────── Helper Functions ───────────────────────────
def wait_click(driver, by, selector):
    """
    Wait until the element located by (by, selector) is clickable,
    scroll into view, click it, and log the action.
    """
    element = WebDriverWait(driver, WAIT).until(
        EC.element_to_be_clickable((by, selector))
    )
    # Ensure element is visible in viewport
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    # Click via JavaScript to avoid intercept issues
    driver.execute_script("arguments[0].click();", element)
    log.info(f"Clicked element: {selector}")
    return element


def log_result_count(driver, context: str):
    """
    Read the booking result count text (e.g., '25 RESULT(S)')
    from the top-right panel and log it with the provided context.
    """
    try:
        elem = driver.find_element(
            By.CSS_SELECTOR,
            "div.slds-text-heading_small.slds-text-align_right.slds-p-vertical_small"
        )
        count_text = elem.text.strip()
        log.info(f"{context} result count: {count_text}")
    except NoSuchElementException:
        log.warning(f"{context} result count element not found")


# ──────────────────────────── Main Flow Steps ───────────────────────────
def login(driver: webdriver.Chrome):
    """
    Navigate to the Evolve bookings page and perform login if prompted.
    Wait until redirected back to the bookings page.
    """
    driver.get(URL)
    try:
        # Wait for the login form to appear (if not already authenticated)
        form = WebDriverWait(driver, WAIT).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        log.info("Login page detected, submitting credentials...")
        # Grab the first two input fields: email and password
        inputs = form.find_elements(By.TAG_NAME, "input")[:2]
        inputs[0].send_keys(USER)
        inputs[1].send_keys(PWD)
        # Submit the form
        form.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    except TimeoutException:
        # If form didn't appear, assume user is already logged in
        log.info("Login form not detected; continuing as authenticated user.")

    # Wait until URL confirms we're on the Recent bookings page
    WebDriverWait(driver, WAIT).until(
        EC.url_contains("/s/booking/Booking__c/Recent")
    )
    # Extra pause to allow page elements to fully render
    time.sleep(2)
    log.info("Logged in and bookings page loaded ✔")
    # Log initial count of bookings visible
    log_result_count(driver, "Initial")


def apply_filter(driver: webdriver.Chrome):
    """
    Apply the 'Check-In' field filter and select 'Next 60 days',
    then log the result count before and after filtering.
    """
    # Wait for the table header to confirm bookings list is present
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "th[data-label='Guest Name'] div.slds-grid > div.slds-grow"
        ))
    )
    log.info("Bookings table detected; preparing to filter.")
    log_result_count(driver, "Before filter")

    # Open the filter popover
    time.sleep(DELAY)
    wait_click(
        driver,
        By.XPATH,
        "//button[contains(@class,'slds-button_brand') and normalize-space()='Filter This List']"
    )

    # Select 'Check-In' field in the first dropdown
    time.sleep(DELAY)
    field_select = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//select[contains(@class,'slds-select') and option[text()='Check-Out']]"
        ))
    )
    Select(field_select).select_by_visible_text("Check-Out")
    log.info("Filter field set to: Check-Out")
    
    # Check what date the browser thinks it is
    browser_date = driver.execute_script("return new Date().toLocaleDateString('en-US');")
    browser_timezone = driver.execute_script("return Intl.DateTimeFormat().resolvedOptions().timeZone;")
    log.info(f"Browser thinks today is: {browser_date} (timezone: {browser_timezone})")

    # Select 'Next 60 days' in the second dropdown
    time.sleep(DELAY)
    range_select = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//select[contains(@class,'slds-select') and option[text()='Next 60 days']]"
        ))
    )
    Select(range_select).select_by_visible_text("Next 60 days")
    log.info("Filter range set to: Next 60 days")

    # Apply the configured filter
    time.sleep(DELAY)
    wait_click(
        driver,
        By.XPATH,
        "//button[contains(@class,'slds-button_brand') and normalize-space()='Apply Filter']"
    )
    log.info("Filter applied 🔍")
    # Pause to let the new filtered results render
    time.sleep(2)
    log_result_count(driver, "After filter")


def click_export(driver: webdriver.Chrome):
    """
    Locate and click the 'Export' button in the control panel,
    then wait for the CSV file to appear in DOWNLOAD_DIR.
    Rename the file with a timestamp in format MM-DD-YYYY--HH-MM-SS.csv
    """
    log.info("Locating Export button…")
    time.sleep(DELAY)
    # The export and print buttons share a container; locate that container
    container = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "div.slds-text-align_right.slds-show_small"
        ))
    )
    # Iterate buttons within the container to find 'Export'
    buttons = container.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if btn.text.strip().lower() == "export":
            # Scroll and click
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn
            )
            btn.click()
            log.info("Export clicked ⬇️")
            break
    else:
        log.warning("Export button not found; aborting CSV download.")
        return

    # Capture pre-download files to detect new CSV
    before = set(DOWNLOAD_DIR.glob("*.csv"))
    deadline = time.time() + 60
    while time.time() < deadline:
        now = set(DOWNLOAD_DIR.glob("*.csv"))
        new = now - before
        if new:
            # Get the original downloaded file
            orig_file = new.pop()
            
            # Generate timestamp in MST format MM-DD-YYYY--HH-MM-SS
            mst = pytz.timezone('America/Phoenix')
            timestamp = datetime.now(mst).strftime("%m-%d-%Y--%H-%M-%S")
            
            # Create new filename with timestamp
            new_filename = f"{timestamp}.csv"
            new_file = DOWNLOAD_DIR / new_filename
            
            # Rename the file
            orig_file.rename(new_file)
            
            log.info(f"Download complete and renamed → {new_filename}")
            return
        time.sleep(1)
    log.warning("CSV did not appear in folder within 60 seconds.")


def cleanup_old_evolve_csvs():
    """
    Remove old Evolve CSV files from the download directory before generating new ones.
    This prevents duplicate processing when multiple Evolve exports accumulate.
    """
    log.info("Cleaning up old Evolve CSV files...")
    
    # Pattern to match Evolve CSV files (timestamp format: MM-DD-YYYY--HH-MM-SS.csv)
    # and Tab2 files (timestamp_tab2.csv)
    evolve_pattern = "[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]--[0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.csv"
    
    removed_count = 0
    for csv_file in DOWNLOAD_DIR.glob(evolve_pattern):
        try:
            csv_file.unlink()
            removed_count += 1
            log.info(f"Removed old Evolve CSV: {csv_file.name}")
        except Exception as e:
            log.error(f"Error removing {csv_file.name}: {e}")
    
    if removed_count > 0:
        log.info(f"Cleaned up {removed_count} old Evolve CSV file(s)")
    else:
        log.info("No old Evolve CSV files found to clean up")

def main():
    """
    Parse CLI arguments, initialize the WebDriver, and execute the
    login → filter → export sequence before quitting the browser.
    """
    parser = argparse.ArgumentParser(description="Evolve booking CSV exporter.")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode (no GUI)."
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run tab exports sequentially instead of concurrently."
    )
    args = parser.parse_args()

    # Clean up old Evolve CSV files before generating new ones
    cleanup_old_evolve_csvs()

    if args.sequential:
        # Run sequentially
        log.info("Running exports sequentially...")
        try:
            main_tab1(args.headless)
            log.info("Tab 1 export complete")
            time.sleep(2)  # Small delay between runs
            second_tab_export(args.headless)
            log.info("Tab 2 export complete")
        except Exception as e:
            log.error(f"Error in sequential export: {e}")
    else:
        # Run concurrently (default)
        log.info("Running exports concurrently...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            tab1_future = executor.submit(main_tab1, args.headless)
            tab2_future = executor.submit(second_tab_export, args.headless)
            
            # Wait for both to complete
            concurrent.futures.wait([tab1_future, tab2_future])
            
            # Check for any exceptions
            for future in [tab1_future, tab2_future]:
                try:
                    future.result()
                except Exception as e:
                    log.error(f"Error in one of the browser processes: {e}")


if __name__ == "__main__":
    main()