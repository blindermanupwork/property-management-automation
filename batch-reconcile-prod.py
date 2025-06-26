#!/usr/bin/env python3
"""
Batch reconciliation script for production HCP jobs.
Processes all reservations without Service Job IDs in manageable chunks.
"""

import subprocess
import time
import sys
from datetime import datetime

def run_batch(batch_num, batch_size=200):
    """Run a single batch of reconciliation"""
    print(f"\n{'='*60}")
    print(f"BATCH {batch_num} - Processing {batch_size} records")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # Calculate offset
    offset = (batch_num - 1) * batch_size
    
    # Run the reconciliation with pagination
    cmd = [
        'python3',
        '/home/opc/automation/src/automation/scripts/hcp/reconcile-jobs.py',
        '--env', 'prod',
        '--execute',
        '--limit', str(batch_size)
    ]
    
    try:
        # Run with a timeout of 5 minutes per batch
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Extract summary from output
        output_lines = result.stdout.strip().split('\n')
        summary_started = False
        for line in output_lines:
            if 'RECONCILIATION SUMMARY' in line:
                summary_started = True
            if summary_started:
                print(line)
        
        # Check if we found any matches
        matched = 0
        unmatched = 0
        for line in output_lines:
            if 'Matched:' in line and 'Unmatched:' not in line:
                matched = int(line.split('Matched:')[1].strip())
            elif 'Unmatched:' in line:
                unmatched = int(line.split('Unmatched:')[1].strip())
        
        return matched, unmatched
        
    except subprocess.TimeoutExpired:
        print(f"⚠️ Batch {batch_num} timed out after 5 minutes")
        return 0, batch_size
    except Exception as e:
        print(f"❌ Error in batch {batch_num}: {e}")
        return 0, batch_size

def main():
    print("🚀 Starting batch reconciliation for PRODUCTION environment")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # We know there are about 1381 reservations to process
    total_reservations = 1381
    batch_size = 200
    num_batches = (total_reservations + batch_size - 1) // batch_size
    
    print(f"📊 Total reservations to process: ~{total_reservations}")
    print(f"📦 Batch size: {batch_size}")
    print(f"🔢 Number of batches: {num_batches}")
    
    total_matched = 0
    total_unmatched = 0
    
    for batch_num in range(1, num_batches + 1):
        matched, unmatched = run_batch(batch_num, batch_size)
        total_matched += matched
        total_unmatched += unmatched
        
        # Small delay between batches to avoid overwhelming the API
        if batch_num < num_batches:
            print(f"\n⏳ Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✅ Total matched: {total_matched}")
    print(f"❌ Total unmatched: {total_unmatched}")
    print(f"📊 Total processed: {total_matched + total_unmatched}")
    print(f"🎯 Match rate: {(total_matched / (total_matched + total_unmatched) * 100):.1f}%")

if __name__ == "__main__":
    main()