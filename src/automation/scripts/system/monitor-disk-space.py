#!/usr/bin/env python3
"""
Monitor disk space usage and send alerts when thresholds are exceeded
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

class DiskSpaceMonitor:
    def __init__(self):
        self.warning_threshold = 85  # percent
        self.critical_threshold = 90  # percent
        self.log_file = Path("/home/opc/automation/src/automation/logs/disk_monitor.log")
        
    def log(self, level, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Print to console
        print(log_entry.strip())
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
            
    def get_disk_usage(self):
        """Get disk usage statistics"""
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        
        usage_data = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                filesystem = parts[0]
                size = parts[1]
                used = parts[2]
                available = parts[3]
                percent = int(parts[4].rstrip('%'))
                mount = parts[5]
                
                usage_data.append({
                    'filesystem': filesystem,
                    'size': size,
                    'used': used,
                    'available': available,
                    'percent': percent,
                    'mount': mount
                })
                
        return usage_data
        
    def get_largest_directories(self, path='/', depth=2, count=10):
        """Get largest directories"""
        cmd = f"du -h --max-depth={depth} {path} 2>/dev/null | sort -hr | head -{count}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        directories = []
        for line in result.stdout.strip().split('\n'):
            if line:
                size, path = line.split('\t')
                directories.append({'size': size, 'path': path})
                
        return directories
        
    def get_large_files(self, path='/', size_mb=100, count=20):
        """Find files larger than specified size"""
        cmd = f"find {path} -type f -size +{size_mb}M -exec ls -lh {{}} \\; 2>/dev/null | sort -k5 -hr | head -{count}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 9:
                    size = parts[4]
                    filename = ' '.join(parts[8:])
                    files.append({'size': size, 'path': filename})
                    
        return files
        
    def get_old_logs(self, days=30):
        """Find old log files"""
        log_dirs = [
            "/home/opc/automation/src/automation/logs",
            "/var/log",
            "/tmp"
        ]
        
        old_files = []
        for log_dir in log_dirs:
            cmd = f"find {log_dir} -name '*.log*' -mtime +{days} -type f 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            for filepath in result.stdout.strip().split('\n'):
                if filepath:
                    try:
                        size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                        old_files.append({
                            'path': filepath,
                            'size_mb': round(size, 2)
                        })
                    except:
                        pass
                        
        return sorted(old_files, key=lambda x: x['size_mb'], reverse=True)
        
    def analyze_chrome_profiles(self):
        """Analyze Chrome profile usage"""
        cmd = "find /tmp -name 'chrome-profile-*' -type d 2>/dev/null | wc -l"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        count = int(result.stdout.strip())
        
        cmd = "du -sh /tmp/chrome-profile-* 2>/dev/null | awk '{sum += $1} END {print sum}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        total_mb = result.stdout.strip() or "0"
        
        return {'count': count, 'total_mb': total_mb}
        
    def generate_report(self):
        """Generate comprehensive disk usage report"""
        self.log("INFO", "Starting disk space analysis...")
        
        # Get disk usage
        disk_usage = self.get_disk_usage()
        
        # Check root filesystem
        root_fs = next((d for d in disk_usage if d['mount'] == '/'), None)
        if root_fs:
            if root_fs['percent'] >= self.critical_threshold:
                self.log("CRITICAL", f"Root filesystem at {root_fs['percent']}% capacity!")
            elif root_fs['percent'] >= self.warning_threshold:
                self.log("WARNING", f"Root filesystem at {root_fs['percent']}% capacity")
            else:
                self.log("INFO", f"Root filesystem at {root_fs['percent']}% capacity")
                
        # Report on all filesystems
        self.log("INFO", "=== Filesystem Usage ===")
        for fs in disk_usage:
            self.log("INFO", f"{fs['mount']}: {fs['used']}/{fs['size']} ({fs['percent']}%)")
            
        # Largest directories
        self.log("INFO", "\n=== Largest Directories ===")
        large_dirs = self.get_largest_directories('/home/opc', depth=3, count=15)
        for dir_info in large_dirs[:10]:
            self.log("INFO", f"{dir_info['size']}\t{dir_info['path']}")
            
        # Large files
        self.log("INFO", "\n=== Large Files (>100MB) ===")
        large_files = self.get_large_files('/home/opc', size_mb=100)
        for file_info in large_files[:10]:
            self.log("INFO", f"{file_info['size']}\t{file_info['path']}")
            
        # Chrome profiles
        chrome_info = self.analyze_chrome_profiles()
        self.log("INFO", f"\n=== Chrome Profiles ===")
        self.log("INFO", f"Count: {chrome_info['count']} profiles")
        self.log("INFO", f"Total size: ~{chrome_info['total_mb']} MB")
        
        # Old logs
        self.log("INFO", "\n=== Old Log Files (>30 days) ===")
        old_logs = self.get_old_logs(30)
        total_old_size = sum(f['size_mb'] for f in old_logs)
        self.log("INFO", f"Found {len(old_logs)} old log files totaling {total_old_size:.2f} MB")
        for log_info in old_logs[:5]:
            self.log("INFO", f"{log_info['size_mb']:.2f} MB\t{log_info['path']}")
            
        # Recommendations
        self.log("INFO", "\n=== Cleanup Recommendations ===")
        if chrome_info['count'] > 50:
            self.log("INFO", f"- Run Chrome profile cleanup (would free ~{chrome_info['total_mb']} MB)")
        if total_old_size > 100:
            self.log("INFO", f"- Clean old log files (would free {total_old_size:.2f} MB)")
        if root_fs and root_fs['percent'] > 85:
            self.log("INFO", "- Consider running full system cleanup")
            self.log("INFO", "- Review and clean export archives")
            
        return {
            'disk_usage': disk_usage,
            'large_dirs': large_dirs[:10],
            'large_files': large_files[:10],
            'chrome_profiles': chrome_info,
            'old_logs_size': total_old_size
        }

def main():
    monitor = DiskSpaceMonitor()
    report = monitor.generate_report()
    
    # Return non-zero exit code if critical
    root_fs = next((d for d in report['disk_usage'] if d['mount'] == '/'), None)
    if root_fs and root_fs['percent'] >= monitor.critical_threshold:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())