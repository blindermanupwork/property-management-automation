#!/usr/bin/env python3
"""
Airtable Change Detection and Reporting for Story-Based Testing
Monitors Airtable dev base before/after each scenario to detect and report changes.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


@dataclass
class AirtableRecord:
    """Represents an Airtable record for comparison"""
    record_id: str
    fields: Dict[str, Any]
    created_time: Optional[str] = None
    
    def __post_init__(self):
        # Normalize fields for comparison
        self.normalized_fields = self._normalize_fields(self.fields)
    
    def _normalize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field values for consistent comparison"""
        normalized = {}
        for key, value in fields.items():
            if value is None or value == "":
                continue  # Skip empty values
            elif isinstance(value, str):
                normalized[key] = value.strip()
            elif isinstance(value, list):
                # Sort lists for consistent comparison
                normalized[key] = sorted([str(v) for v in value if v])
            else:
                normalized[key] = value
        return normalized
    
    def get_key_fields(self) -> Dict[str, Any]:
        """Get key fields for record identification"""
        key_fields = {}
        important_fields = [
            'Reservation UID', 'Property Name', 'Guest Name', 
            'Check-in Date', 'Check-out Date', 'Status', 'Entry Type'
        ]
        
        for field in important_fields:
            if field in self.normalized_fields:
                key_fields[field] = self.normalized_fields[field]
        
        return key_fields


@dataclass 
class ChangeReport:
    """Represents a change in Airtable records"""
    change_type: str  # 'added', 'removed', 'modified'
    record_id: str
    before: Optional[AirtableRecord] = None
    after: Optional[AirtableRecord] = None
    field_changes: Optional[Dict[str, tuple]] = None  # field_name -> (old_value, new_value)
    
    def __str__(self) -> str:
        if self.change_type == 'added':
            key_fields = self.after.get_key_fields() if self.after else {}
            return f"➕ ADDED: {self.record_id} - {key_fields.get('Guest Name', 'Unknown')} at {key_fields.get('Property Name', 'Unknown')}"
        
        elif self.change_type == 'removed':
            key_fields = self.before.get_key_fields() if self.before else {}
            return f"➖ REMOVED: {self.record_id} - {key_fields.get('Guest Name', 'Unknown')} at {key_fields.get('Property Name', 'Unknown')}"
        
        elif self.change_type == 'modified':
            key_fields = self.after.get_key_fields() if self.after else {}
            changes_summary = []
            if self.field_changes:
                for field, (old, new) in self.field_changes.items():
                    changes_summary.append(f"{field}: '{old}' → '{new}'")
            
            changes_str = ", ".join(changes_summary[:3])  # Show first 3 changes
            if len(changes_summary) > 3:
                changes_str += f" (+{len(changes_summary)-3} more)"
                
            return f"🔄 MODIFIED: {self.record_id} - {key_fields.get('Guest Name', 'Unknown')} - {changes_str}"
        
        return f"❓ UNKNOWN CHANGE: {self.record_id}"


class AirtableMonitor:
    """
    Monitors Airtable dev base for changes during story-based testing.
    """
    
    def __init__(self):
        self.snapshots_dir = Path(__file__).parent / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # Mock data for development - replace with actual Airtable integration
        self.use_mock_data = True
        
    def capture_snapshot(self, snapshot_name: str) -> Dict[str, Any]:
        """Capture current state of Airtable dev base"""
        timestamp = datetime.now().isoformat()
        
        if self.use_mock_data:
            # Mock Airtable data for testing
            snapshot_data = self._generate_mock_airtable_data(snapshot_name)
        else:
            # TODO: Integrate with actual Airtable MCP when available
            snapshot_data = self._fetch_airtable_data_via_mcp()
        
        # Save snapshot to file
        snapshot_file = self.snapshots_dir / f"{snapshot_name}_{timestamp.replace(':', '-')}.json"
        
        with open(snapshot_file, 'w') as f:
            json.dump({
                'snapshot_name': snapshot_name,
                'timestamp': timestamp,
                'data': snapshot_data
            }, f, indent=2)
        
        print(f"📸 Captured snapshot: {snapshot_name} ({len(snapshot_data.get('records', []))} records)")
        return snapshot_data
    
    def _generate_mock_airtable_data(self, snapshot_name: str) -> Dict[str, Any]:
        """Generate mock Airtable data based on scenario context"""
        
        # Simulate different states based on chapter
        if "baseline" in snapshot_name:
            # Empty state
            return {"records": []}
        
        elif "initial" in snapshot_name:
            # Initial bookings created
            return {
                "records": [
                    {
                        "id": "rec_itrip_001",
                        "fields": {
                            "Reservation UID": "itrip_sameday_test_001",
                            "Property Name": "Boris Test House",
                            "Guest Name": "John Smith", 
                            "Check-in Date": "2025-06-05",
                            "Check-out Date": "2025-06-07",
                            "Status": "New",
                            "Entry Type": "Turnover",
                            "Same Day Turnover": True  # iTrip precedence
                        },
                        "createdTime": "2025-06-09T10:30:00Z"
                    },
                    {
                        "id": "rec_evolve_001", 
                        "fields": {
                            "Reservation UID": "evolve_overlap_test_001",
                            "Property Name": "Boris Test House",
                            "Guest Name": "Alice Wilson",
                            "Check-in Date": "2025-06-06", 
                            "Check-out Date": "2025-06-08",
                            "Status": "New",
                            "Entry Type": "Turnover",
                            "Overlapping": True  # Detected overlap with iTrip
                        },
                        "createdTime": "2025-06-09T10:31:00Z"
                    },
                    {
                        "id": "rec_tab2_001",
                        "fields": {
                            "Reservation UID": "123001",
                            "Property Name": "Boris Test Villa #202",  # Matched via listing number
                            "Guest Name": "Mike Brown",
                            "Check-in Date": "2025-06-09",
                            "Check-out Date": "2025-06-11", 
                            "Status": "New",
                            "Entry Type": "Turnover"
                        },
                        "createdTime": "2025-06-09T10:32:00Z"
                    },
                    {
                        "id": "rec_ics_001",
                        "fields": {
                            "Reservation UID": "boris_ics_block_test_001@test.com",
                            "Property Name": "Boris Test Condo",
                            "Guest Name": "Maintenance Block",
                            "Check-in Date": "2025-06-10",
                            "Check-out Date": "2025-06-12",
                            "Status": "New", 
                            "Entry Type": "Block"  # Classified as Block, not Turnover
                        },
                        "createdTime": "2025-06-09T10:33:00Z"
                    }
                ]
            }
        
        elif "stress" in snapshot_name or "date_changes" in snapshot_name:
            # Modified dates with same-day turnover
            return {
                "records": [
                    {
                        "id": "rec_itrip_001_old",
                        "fields": {
                            "Reservation UID": "itrip_sameday_test_001",
                            "Property Name": "Boris Test House",
                            "Guest Name": "John Smith",
                            "Check-in Date": "2025-06-05", 
                            "Check-out Date": "2025-06-07",
                            "Status": "Old",  # Marked as old
                            "Entry Type": "Turnover"
                        },
                        "createdTime": "2025-06-09T10:30:00Z"
                    },
                    {
                        "id": "rec_itrip_001_new",
                        "fields": {
                            "Reservation UID": "itrip_sameday_test_001", 
                            "Property Name": "Boris Test House",
                            "Guest Name": "John Smith",
                            "Check-in Date": "2025-06-08",  # Modified dates
                            "Check-out Date": "2025-06-10", 
                            "Status": "Modified",  # New modified record
                            "Entry Type": "Turnover",
                            "Same Day Turnover": False  # Flag changed
                        },
                        "createdTime": "2025-06-09T11:30:00Z"
                    },
                    {
                        "id": "rec_evolve_002",
                        "fields": {
                            "Reservation UID": "evolve_turnover_test_001",
                            "Property Name": "Boris Test House", 
                            "Guest Name": "Alice Wilson",
                            "Check-in Date": "2025-06-07",
                            "Check-out Date": "2025-06-09",  # Same-day checkout 
                            "Status": "New",
                            "Entry Type": "Turnover",
                            "Same Day Turnover": True  # Real same-day detected
                        },
                        "createdTime": "2025-06-09T11:31:00Z"
                    },
                    {
                        "id": "rec_tab2_002", 
                        "fields": {
                            "Reservation UID": "123002",
                            "Property Name": "Boris Test House",
                            "Guest Name": "Mike Brown", 
                            "Check-in Date": "2025-06-09",  # Same-day checkin
                            "Check-out Date": "2025-06-11",
                            "Status": "New",
                            "Entry Type": "Turnover", 
                            "Same Day Turnover": True  # Cross-platform same-day
                        },
                        "createdTime": "2025-06-09T11:32:00Z"
                    },
                    {
                        "id": "rec_ics_002",
                        "fields": {
                            "Reservation UID": "boris_ics_adjacent_test_001@test.com",
                            "Property Name": "Boris Test Condo",
                            "Guest Name": "Tom Wilson",
                            "Check-in Date": "2025-06-11",  # Adjacent to Tab2 checkout
                            "Check-out Date": "2025-06-12",
                            "Status": "New",
                            "Entry Type": "Turnover",
                            "Overlapping": False  # Adjacent, NOT overlapping
                        },
                        "createdTime": "2025-06-09T11:33:00Z"
                    }
                ]
            }
        
        elif "edge" in snapshot_name or "cancellation" in snapshot_name:
            # Edge cases and cancellations
            return {
                "records": [
                    {
                        "id": "rec_itrip_003",
                        "fields": {
                            "Reservation UID": "itrip_sameday_test_001",
                            "Property Name": "Boris Test House", 
                            "Guest Name": "Smith Family Vacation",  # Guest override test
                            "Check-in Date": "2025-06-08",
                            "Check-out Date": "2025-06-10",
                            "Status": "Modified",
                            "Entry Type": "Turnover",
                            "Guest Override": True  # Override rule triggered
                        },
                        "createdTime": "2025-06-09T12:30:00Z"
                    },
                    # Note: Evolve record missing (cancelled/removed)
                    {
                        "id": "rec_tab2_003",
                        "fields": {
                            "Reservation UID": "123003",
                            "Property Name": "Boris Test House",
                            "Guest Name": "Mike Brown",
                            "Check-in Date": "2025-06-09",
                            "Check-out Date": "2025-06-25",  # 16 nights
                            "Status": "New", 
                            "Entry Type": "Turnover",
                            "Long Term Guest": True  # 16 days ≥ 14 threshold
                        },
                        "createdTime": "2025-06-09T12:31:00Z"
                    },
                    {
                        "id": "rec_ics_error",
                        "fields": {
                            "Error": "Property matching failed for 'Nonexistent Property #999'",
                            "Status": "Error",
                            "Entry Type": "Error"
                        },
                        "createdTime": "2025-06-09T12:32:00Z"
                    }
                ]
            }
        
        # Default empty state
        return {"records": []}
    
    def _fetch_airtable_data_via_mcp(self) -> Dict[str, Any]:
        """Fetch actual Airtable data via MCP (placeholder for future implementation)"""
        # TODO: Implement actual Airtable MCP integration
        # This would use the airtable-dev MCP server to fetch current records
        return {"records": []}
    
    def compare_snapshots(self, before_file: str, after_file: str) -> List[ChangeReport]:
        """Compare two snapshots and return list of changes"""
        
        # Load snapshots
        before_data = self._load_snapshot(before_file)
        after_data = self._load_snapshot(after_file)
        
        if not before_data or not after_data:
            return []
        
        # Convert to records
        before_records = {
            rec['id']: AirtableRecord(rec['id'], rec['fields'], rec.get('createdTime'))
            for rec in before_data.get('records', [])
        }
        
        after_records = {
            rec['id']: AirtableRecord(rec['id'], rec['fields'], rec.get('createdTime'))
            for rec in after_data.get('records', [])
        }
        
        changes = []
        
        # Find added records
        for record_id in after_records:
            if record_id not in before_records:
                changes.append(ChangeReport(
                    change_type='added',
                    record_id=record_id,
                    after=after_records[record_id]
                ))
        
        # Find removed records
        for record_id in before_records:
            if record_id not in after_records:
                changes.append(ChangeReport(
                    change_type='removed', 
                    record_id=record_id,
                    before=before_records[record_id]
                ))
        
        # Find modified records
        for record_id in before_records:
            if record_id in after_records:
                before_rec = before_records[record_id]
                after_rec = after_records[record_id]
                
                # Compare normalized fields
                if before_rec.normalized_fields != after_rec.normalized_fields:
                    field_changes = {}
                    
                    # Find specific field changes
                    all_fields = set(before_rec.normalized_fields.keys()) | set(after_rec.normalized_fields.keys())
                    
                    for field in all_fields:
                        old_value = before_rec.normalized_fields.get(field)
                        new_value = after_rec.normalized_fields.get(field)
                        
                        if old_value != new_value:
                            field_changes[field] = (old_value, new_value)
                    
                    if field_changes:
                        changes.append(ChangeReport(
                            change_type='modified',
                            record_id=record_id,
                            before=before_rec,
                            after=after_rec,
                            field_changes=field_changes
                        ))
        
        return changes
    
    def _load_snapshot(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load snapshot data from file"""
        snapshot_file = self.snapshots_dir / filename
        
        if not snapshot_file.exists():
            print(f"❌ Snapshot file not found: {snapshot_file}")
            return None
        
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
                return data.get('data', {})
        except Exception as e:
            print(f"❌ Failed to load snapshot {filename}: {e}")
            return None
    
    def generate_change_report(self, changes: List[ChangeReport], chapter: str) -> str:
        """Generate a formatted change report"""
        if not changes:
            return f"📊 **No changes detected for {chapter}**\n"
        
        report = []
        report.append(f"📊 **Change Report for {chapter}**")
        report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🔢 Total Changes: {len(changes)}")
        report.append("")
        
        # Group changes by type
        added = [c for c in changes if c.change_type == 'added']
        removed = [c for c in changes if c.change_type == 'removed'] 
        modified = [c for c in changes if c.change_type == 'modified']
        
        if added:
            report.append(f"➕ **Added Records ({len(added)}):**")
            for change in added:
                report.append(f"   {change}")
            report.append("")
        
        if removed:
            report.append(f"➖ **Removed Records ({len(removed)}):**")
            for change in removed:
                report.append(f"   {change}")
            report.append("")
        
        if modified:
            report.append(f"🔄 **Modified Records ({len(modified)}):**")
            for change in modified:
                report.append(f"   {change}")
            report.append("")
        
        return "\n".join(report)
    
    def list_snapshots(self) -> List[str]:
        """List available snapshot files"""
        snapshots = []
        for file in self.snapshots_dir.glob("*.json"):
            snapshots.append(file.name)
        return sorted(snapshots)
    
    def cleanup_old_snapshots(self, keep_last: int = 10):
        """Clean up old snapshot files, keeping only the most recent"""
        snapshots = self.list_snapshots()
        
        if len(snapshots) > keep_last:
            to_delete = snapshots[:-keep_last]
            for filename in to_delete:
                try:
                    (self.snapshots_dir / filename).unlink()
                    print(f"🗑️  Deleted old snapshot: {filename}")
                except Exception as e:
                    print(f"❌ Failed to delete snapshot {filename}: {e}")


def main():
    """Test the Airtable monitor functionality"""
    monitor = AirtableMonitor()
    
    # Capture test snapshots
    print("Testing Airtable Monitor...")
    
    baseline_data = monitor.capture_snapshot("test_baseline")
    initial_data = monitor.capture_snapshot("test_initial_bookings")
    
    # Compare snapshots
    snapshots = monitor.list_snapshots()
    if len(snapshots) >= 2:
        changes = monitor.compare_snapshots(snapshots[-2], snapshots[-1])
        report = monitor.generate_change_report(changes, "Test Comparison")
        print("\n" + report)
    
    print(f"\n📂 Available snapshots: {len(snapshots)}")
    for snapshot in snapshots[-5:]:  # Show last 5
        print(f"   📸 {snapshot}")


if __name__ == "__main__":
    main()