#!/usr/bin/env python3
"""
CSV File Processing with File Locking
Prevents multiple automation runs from processing the same file
"""

import os
import fcntl
import time
import logging
from pathlib import Path
from contextlib import contextmanager

class CSVFileLock:
    """File-based locking for CSV processing"""
    
    def __init__(self, csv_file_path):
        self.csv_file_path = Path(csv_file_path)
        self.lock_file_path = self.csv_file_path.with_suffix('.lock')
        self.lock_file = None
    
    def acquire(self, timeout=30):
        """
        Acquire a lock on the CSV file.
        Returns True if lock acquired, False if timeout.
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Create lock file if it doesn't exist
                self.lock_file = open(self.lock_file_path, 'w')
                
                # Try to acquire exclusive lock (non-blocking)
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # Write process info to lock file
                self.lock_file.write(f"PID: {os.getpid()}\n")
                self.lock_file.write(f"Time: {time.ctime()}\n")
                self.lock_file.write(f"File: {self.csv_file_path}\n")
                self.lock_file.flush()
                
                logging.info(f"Acquired lock for {self.csv_file_path}")
                return True
                
            except IOError:
                # Lock is held by another process
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
                
                # Check if lock file is stale (older than 5 minutes)
                if self.lock_file_path.exists():
                    lock_age = time.time() - self.lock_file_path.stat().st_mtime
                    if lock_age > 300:  # 5 minutes
                        logging.warning(f"Removing stale lock file: {self.lock_file_path}")
                        try:
                            self.lock_file_path.unlink()
                        except:
                            pass
                
                # Wait before retrying
                time.sleep(0.5)
        
        logging.error(f"Failed to acquire lock for {self.csv_file_path} after {timeout}s")
        return False
    
    def release(self):
        """Release the lock on the CSV file"""
        if self.lock_file:
            try:
                # Release the lock
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                
                # Remove lock file
                if self.lock_file_path.exists():
                    self.lock_file_path.unlink()
                
                logging.info(f"Released lock for {self.csv_file_path}")
            except Exception as e:
                logging.error(f"Error releasing lock: {e}")
            finally:
                self.lock_file = None

@contextmanager
def csv_file_lock(csv_file_path):
    """Context manager for CSV file locking"""
    lock = CSVFileLock(csv_file_path)
    acquired = lock.acquire()
    
    if not acquired:
        raise RuntimeError(f"Could not acquire lock for {csv_file_path}")
    
    try:
        yield
    finally:
        lock.release()

def process_csv_files_with_locking(csv_directory):
    """
    Process CSV files with file locking to prevent concurrent processing.
    This wraps the existing CSV processing logic with proper locking.
    """
    csv_files = list(Path(csv_directory).glob("*.csv"))
    
    for csv_file in csv_files:
        # Skip if already being processed (has .processing marker)
        processing_marker = csv_file.with_suffix('.processing')
        if processing_marker.exists():
            logging.info(f"Skipping {csv_file} - already being processed")
            continue
        
        try:
            # Acquire lock before processing
            with csv_file_lock(csv_file):
                # Create processing marker
                processing_marker.touch()
                
                try:
                    # Call the actual CSV processing function
                    logging.info(f"Processing {csv_file} with lock held")
                    process_single_csv_file(csv_file)
                    
                    # Move to done directory after successful processing
                    move_to_done_directory(csv_file)
                    
                finally:
                    # Remove processing marker
                    if processing_marker.exists():
                        processing_marker.unlink()
                        
        except RuntimeError as e:
            logging.warning(f"Could not process {csv_file}: {e}")
            continue
        except Exception as e:
            logging.error(f"Error processing {csv_file}: {e}")
            # Remove processing marker on error
            if processing_marker.exists():
                processing_marker.unlink()

def cleanup_stale_locks(csv_directory, max_age_minutes=10):
    """Remove stale lock and processing files"""
    current_time = time.time()
    max_age_seconds = max_age_minutes * 60
    
    # Clean up stale .lock files
    for lock_file in Path(csv_directory).glob("*.lock"):
        file_age = current_time - lock_file.stat().st_mtime
        if file_age > max_age_seconds:
            logging.warning(f"Removing stale lock file: {lock_file}")
            try:
                lock_file.unlink()
            except:
                pass
    
    # Clean up stale .processing files
    for processing_file in Path(csv_directory).glob("*.processing"):
        file_age = current_time - processing_file.stat().st_mtime
        if file_age > max_age_seconds:
            logging.warning(f"Removing stale processing file: {processing_file}")
            try:
                processing_file.unlink()
            except:
                pass

# Integration example:
"""
# In the main csvProcess.py file, wrap the processing logic:

from csv_file_locking import process_csv_files_with_locking, cleanup_stale_locks

def main():
    # Clean up any stale locks first
    cleanup_stale_locks(Config.get_csv_process_dir())
    
    # Process files with locking
    process_csv_files_with_locking(Config.get_csv_process_dir())
"""