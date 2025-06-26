#!/usr/bin/env python3
"""
Robust batch reconciliation runner that processes reservations in small batches
and can resume from where it left off if interrupted.
"""

import subprocess
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# State file to track progress
STATE_FILE = Path("/home/opc/automation/.reconciliation_state.json")

def load_state():
    """Load the current reconciliation state"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_processed_batch': 0,
        'total_matched': 0,
        'total_unmatched': 0,
        'started_at': datetime.now().isoformat()
    }

def save_state(state):
    """Save the current reconciliation state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def run_single_batch(batch_size=50, offset=0):
    """Run a single batch with specific offset"""
    print(f"\n🔄 Processing batch with offset {offset} (size: {batch_size})")
    
    cmd = [
        'python3',
        '/home/opc/automation/src/automation/scripts/hcp/reconcile-jobs.py',
        '--env', 'prod',
        '--execute',
        '--limit', str(batch_size),
        '--offset', str(offset)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Parse results from output
        matched = 0
        unmatched = 0
        
        for line in result.stdout.split('\n'):
            if 'Matched:' in line and 'Unmatched:' not in line:
                try:
                    matched = int(line.split('Matched:')[1].strip())
                except:
                    pass
            elif 'Unmatched:' in line:
                try:
                    unmatched = int(line.split('Unmatched:')[1].strip())
                except:
                    pass
        
        print(f"✅ Batch complete: {matched} matched, {unmatched} unmatched")
        return matched, unmatched, True
        
    except subprocess.TimeoutExpired:
        print(f"⚠️ Batch timed out after 60 seconds")
        return 0, batch_size, False
    except Exception as e:
        print(f"❌ Batch error: {e}")
        return 0, batch_size, False

def main():
    print("🚀 Starting robust batch reconciliation")
    print("📊 This will process all production reservations in small batches")
    print("💾 Progress is saved and can be resumed if interrupted")
    
    # Load previous state
    state = load_state()
    
    if state['last_processed_batch'] > 0:
        print(f"\n📌 Resuming from batch {state['last_processed_batch'] + 1}")
        print(f"   Previous progress: {state['total_matched']} matched, {state['total_unmatched']} unmatched")
    
    # Process configuration
    batch_size = 50  # Small batches to avoid timeouts
    total_estimated = 1400  # Approximate number of reservations
    
    current_offset = state['last_processed_batch'] * batch_size
    batch_num = state['last_processed_batch'] + 1
    
    try:
        while current_offset < total_estimated:
            print(f"\n{'='*60}")
            print(f"BATCH {batch_num} - Offset: {current_offset}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            matched, unmatched, success = run_single_batch(batch_size, current_offset)
            
            # Update state
            state['total_matched'] += matched
            state['total_unmatched'] += unmatched
            state['last_processed_batch'] = batch_num - 1
            save_state(state)
            
            # Check if we've processed everything
            if matched + unmatched == 0:
                print("\n✅ No more records to process!")
                break
            
            current_offset += batch_size
            batch_num += 1
            
            # Small delay between batches
            if current_offset < total_estimated:
                print("⏳ Waiting 2 seconds before next batch...")
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Reconciliation interrupted by user")
        print(f"💾 Progress saved. Run again to resume from batch {batch_num}")
        
    # Final summary
    print(f"\n{'='*60}")
    print("RECONCILIATION SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total matched: {state['total_matched']}")
    print(f"❌ Total unmatched: {state['total_unmatched']}")
    print(f"📊 Total processed: {state['total_matched'] + state['total_unmatched']}")
    
    if state['total_matched'] + state['total_unmatched'] > 0:
        match_rate = (state['total_matched'] / (state['total_matched'] + state['total_unmatched']) * 100)
        print(f"🎯 Match rate: {match_rate:.1f}%")
    
    # Clean up state file if completed
    if current_offset >= total_estimated or (matched + unmatched == 0):
        STATE_FILE.unlink(missing_ok=True)
        print("\n🏁 Reconciliation completed!")
    else:
        print(f"\n💾 Progress saved. Run again to continue from batch {batch_num}")

if __name__ == "__main__":
    main()