#!/usr/bin/env python3
"""
Comprehensive system cleanup script for automation server
Cleans up old logs, temporary files, chrome profiles, and archives
"""

import os
import shutil
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

class SystemCleaner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.freed_space = 0
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def get_size_mb(self, path):
        """Get size of file/directory in MB"""
        if os.path.isfile(path):
            return os.path.getsize(path) / (1024 * 1024)
        elif os.path.isdir(path):
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except:
                        pass
            return total / (1024 * 1024)
        return 0
        
    def remove_item(self, path):
        """Remove file or directory"""
        size_mb = self.get_size_mb(path)
        
        if self.dry_run:
            self.log(f"[DRY RUN] Would remove: {path} ({size_mb:.2f} MB)")
        else:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                self.log(f"Removed: {path} ({size_mb:.2f} MB)")
            except Exception as e:
                self.log(f"Error removing {path}: {e}")
                return 0
                
        self.freed_space += size_mb
        return size_mb
        
    def clean_chrome_profiles(self, days_old=1):
        """Clean old Chrome profile directories"""
        self.log("=== Cleaning Chrome Profiles ===")
        
        chrome_dirs = Path("/tmp").glob("chrome-profile-*")
        cutoff_time = time.time() - (days_old * 86400)
        removed_count = 0
        
        for chrome_dir in chrome_dirs:
            try:
                if chrome_dir.stat().st_mtime < cutoff_time:
                    self.remove_item(str(chrome_dir))
                    removed_count += 1
            except Exception as e:
                self.log(f"Error checking {chrome_dir}: {e}")
                
        self.log(f"Removed {removed_count} Chrome profiles older than {days_old} days")
        
    def clean_old_csv_files(self, days_old=30):
        """Clean old CSV files from done directories"""
        self.log("=== Cleaning Old CSV Files ===")
        
        base_path = Path("/home/opc/automation/src/automation/scripts")
        csv_dirs = ["CSV_done_production", "CSV_done_development"]
        cutoff_time = time.time() - (days_old * 86400)
        removed_count = 0
        
        for csv_dir in csv_dirs:
            dir_path = base_path / csv_dir
            if not dir_path.exists():
                continue
                
            for csv_file in dir_path.glob("*.csv"):
                try:
                    if csv_file.stat().st_mtime < cutoff_time:
                        self.remove_item(str(csv_file))
                        removed_count += 1
                except Exception as e:
                    self.log(f"Error checking {csv_file}: {e}")
                    
        self.log(f"Removed {removed_count} CSV files older than {days_old} days")
        
    def clean_old_logs(self, days_old=30):
        """Clean old log files"""
        self.log("=== Cleaning Old Log Files ===")
        
        log_dir = Path("/home/opc/automation/src/automation/logs")
        cutoff_time = time.time() - (days_old * 86400)
        removed_count = 0
        
        # Archive logs older than specified days
        archive_patterns = ["*_archive_*.log", "*.log.gz", "*.log.[0-9]"]
        
        for pattern in archive_patterns:
            for log_file in log_dir.glob(pattern):
                try:
                    if log_file.stat().st_mtime < cutoff_time:
                        self.remove_item(str(log_file))
                        removed_count += 1
                except Exception as e:
                    self.log(f"Error checking {log_file}: {e}")
                    
        self.log(f"Removed {removed_count} old log files")
        
    def clean_export_archives(self, days_old=60):
        """Clean old export archives"""
        self.log("=== Cleaning Export Archives ===")
        
        export_dir = Path("/home/opc/automation/export/archive")
        if not export_dir.exists():
            return
            
        cutoff_time = time.time() - (days_old * 86400)
        removed_count = 0
        
        # Clean customer job archives
        for subdir in ["customer_jobs", "customer_jobs_by_property"]:
            dir_path = export_dir / subdir
            if dir_path.exists():
                for file in dir_path.glob("*.json"):
                    try:
                        if file.stat().st_mtime < cutoff_time:
                            self.remove_item(str(file))
                            removed_count += 1
                    except Exception as e:
                        self.log(f"Error checking {file}: {e}")
                        
        # Clean dated archive directories
        for item in export_dir.glob("20*_archive*"):
            if item.is_dir():
                try:
                    if item.stat().st_mtime < cutoff_time:
                        self.remove_item(str(item))
                        removed_count += 1
                except Exception as e:
                    self.log(f"Error checking {item}: {e}")
                    
        self.log(f"Removed {removed_count} export archive items")
        
    def clean_npm_cache(self):
        """Clean npm cache"""
        self.log("=== Cleaning NPM Cache ===")
        
        if not self.dry_run:
            try:
                result = subprocess.run(["npm", "cache", "clean", "--force"], 
                                      capture_output=True, text=True)
                self.log("NPM cache cleaned")
            except Exception as e:
                self.log(f"Error cleaning npm cache: {e}")
        else:
            self.log("[DRY RUN] Would clean npm cache")
            
    def clean_pip_cache(self):
        """Clean pip cache"""
        self.log("=== Cleaning Pip Cache ===")
        
        cache_dir = Path.home() / ".cache" / "pip"
        if cache_dir.exists():
            size_mb = self.get_size_mb(str(cache_dir))
            if not self.dry_run:
                try:
                    subprocess.run(["pip", "cache", "purge"], 
                                 capture_output=True, text=True)
                    self.log(f"Pip cache cleaned ({size_mb:.2f} MB)")
                    self.freed_space += size_mb
                except Exception as e:
                    self.log(f"Error cleaning pip cache: {e}")
            else:
                self.log(f"[DRY RUN] Would clean pip cache ({size_mb:.2f} MB)")
                
    def clean_browser_cache(self):
        """Clean browser caches"""
        self.log("=== Cleaning Browser Caches ===")
        
        cache_dirs = [
            Path.home() / ".cache" / "google-chrome",
            Path.home() / ".cache" / "chromium",
            Path.home() / ".cache" / "selenium"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                self.remove_item(str(cache_dir))
                
    def rotate_large_logs(self):
        """Force rotation of large log files"""
        self.log("=== Rotating Large Logs ===")
        
        if not self.dry_run:
            try:
                # Force logrotate for our custom config
                subprocess.run(["sudo", "logrotate", "-f", 
                              "/etc/logrotate.d/automation"], 
                              capture_output=True, text=True)
                self.log("Forced log rotation completed")
            except Exception as e:
                self.log(f"Error rotating logs: {e}")
        else:
            self.log("[DRY RUN] Would force log rotation")
            
    def show_disk_usage(self):
        """Show current disk usage"""
        self.log("=== Current Disk Usage ===")
        
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            self.log(line)
            
    def run_full_cleanup(self):
        """Run all cleanup tasks"""
        self.log("Starting comprehensive system cleanup...")
        
        # Show initial disk usage
        self.show_disk_usage()
        
        # Run cleanup tasks
        self.clean_chrome_profiles(days_old=1)
        self.clean_old_csv_files(days_old=30)
        self.clean_old_logs(days_old=30)
        self.clean_export_archives(days_old=60)
        self.clean_npm_cache()
        self.clean_pip_cache()
        self.clean_browser_cache()
        self.rotate_large_logs()
        
        # Summary
        self.log(f"\n=== Cleanup Summary ===")
        self.log(f"Total space freed: {self.freed_space:.2f} MB")
        
        # Show final disk usage
        self.show_disk_usage()

def main():
    parser = argparse.ArgumentParser(description='System cleanup script')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be cleaned without removing')
    parser.add_argument('--chrome-days', type=int, default=1,
                       help='Days to keep Chrome profiles (default: 1)')
    parser.add_argument('--csv-days', type=int, default=30,
                       help='Days to keep CSV files (default: 30)')
    parser.add_argument('--log-days', type=int, default=30,
                       help='Days to keep old logs (default: 30)')
    parser.add_argument('--export-days', type=int, default=60,
                       help='Days to keep export archives (default: 60)')
    
    args = parser.parse_args()
    
    cleaner = SystemCleaner(dry_run=args.dry_run)
    
    if args.chrome_days or args.csv_days or args.log_days or args.export_days:
        # Run specific cleanups with custom days
        if args.chrome_days:
            cleaner.clean_chrome_profiles(args.chrome_days)
        if args.csv_days:
            cleaner.clean_old_csv_files(args.csv_days)
        if args.log_days:
            cleaner.clean_old_logs(args.log_days)
        if args.export_days:
            cleaner.clean_export_archives(args.export_days)
    else:
        # Run full cleanup with defaults
        cleaner.run_full_cleanup()

if __name__ == "__main__":
    main()