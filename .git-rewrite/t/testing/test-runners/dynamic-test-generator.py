#!/usr/bin/env python3
"""
Dynamic Test Data Generator for Property Management Automation
Creates realistic fake reservations from Evolve, iTrip, and ICS sources
Supports new, modified, and removed scenarios with intelligent data generation
"""

import csv
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pytz

# Add project root to path
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config

@dataclass
class GuestProfile:
    """Guest profile for generating realistic data"""
    first_name: str
    last_name: str
    email: str
    phone: str
    preferences: Dict[str, str]

@dataclass
class PropertyProfile:
    """Property profile for consistent test data"""
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str
    max_guests: int

@dataclass
class Reservation:
    """Unified reservation data structure"""
    uid: str
    property_name: str
    property_address: str
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in: datetime
    check_out: datetime
    source: str  # 'evolve', 'itrip', 'ics'
    status: str  # 'new', 'modified', 'removed'
    custom_instructions: Optional[str] = None
    next_guest_date: Optional[datetime] = None
    booking_id: Optional[str] = None

class DynamicTestGenerator:
    """Smart test data generator for all reservation sources"""
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.config = Config
        self.arizona_tz = pytz.timezone('America/Phoenix')
        
        # Boris test customer data
        self.boris_customer = {
            'name': 'Boris Blinderman Test Dev',
            'email': 'boris.test.dev@hcp_dev_testing.com',
            'phone': '555-123-4567',
            'hcp_id': 'cus_7fab445b03d34da19250755b48130eba'
        }
        
        # Test property profiles
        self.test_properties = [
            PropertyProfile(
                name="Boris Test Villa",
                address="123 Test Dev Street",
                city="Phoenix",
                state="AZ", 
                zip_code="85001",
                property_type="Villa",
                max_guests=8
            ),
            PropertyProfile(
                name="Boris Test Condo",
                address="456 Test Dev Avenue",
                city="Scottsdale",
                state="AZ",
                zip_code="85257",
                property_type="Condo",
                max_guests=4
            ),
            PropertyProfile(
                name="Boris Test House",
                address="789 Test Dev Boulevard",
                city="Tempe",
                state="AZ",
                zip_code="85281",
                property_type="House",
                max_guests=6
            )
        ]
        
        # Guest profiles for variety
        self.guest_profiles = [
            GuestProfile("John", "Smith", "john.smith@example.com", "555-111-2222", {"cleaning": "extra"}),
            GuestProfile("Sarah", "Johnson", "sarah.j@example.com", "555-333-4444", {"towels": "extra"}),
            GuestProfile("Mike", "Wilson", "m.wilson@example.com", "555-555-6666", {"checkout": "late"}),
            GuestProfile("Lisa", "Brown", "lisa.brown@example.com", "555-777-8888", {"checkin": "early"}),
            GuestProfile("David", "Garcia", "d.garcia@example.com", "555-999-0000", {"pets": "allowed"}),
        ]
        
        # Custom instruction templates
        self.custom_instructions = [
            "Extra deep cleaning required",
            "Guest requesting additional towels",
            "Late checkout - extra time needed",
            "Pet-friendly cleaning needed",
            "Special occasion - extra care",
            "Long-term guest - thorough clean",
            "Same-day turnover - priority clean",
            "Heavy usage - detailed cleaning",
        ]
        
        # Reservation UID tracking for modifications/removals
        self.existing_uids = {}
        
    def generate_date_range(self, days_from_now: int = 0, duration_days: int = None) -> Tuple[datetime, datetime]:
        """Generate realistic check-in/check-out dates"""
        base_date = datetime.now(self.arizona_tz) + timedelta(days=days_from_now)
        
        if duration_days is None:
            # Realistic stay durations with weights
            duration_weights = {
                2: 0.2,   # Weekend stays
                3: 0.15,  # Long weekends
                4: 0.1,   # Short stays
                7: 0.25,  # Week stays
                14: 0.15, # Two weeks (long-term threshold)
                21: 0.1,  # Three weeks (long-term)
                30: 0.05  # Month stays (long-term)
            }
            duration_days = random.choices(
                list(duration_weights.keys()),
                weights=list(duration_weights.values())
            )[0]
        
        check_in = base_date.replace(hour=16, minute=0, second=0, microsecond=0)
        check_out = check_in + timedelta(days=duration_days)
        check_out = check_out.replace(hour=11, minute=0, second=0, microsecond=0)
        
        return check_in, check_out
    
    def generate_next_guest_date(self, check_out: datetime) -> Optional[datetime]:
        """Generate realistic next guest arrival date"""
        if random.random() < 0.3:  # 30% chance of no next guest
            return None
        
        # Next guest typically arrives 1-5 days after checkout
        days_gap = random.randint(1, 5)
        next_date = check_out + timedelta(days=days_gap)
        return next_date.replace(hour=16, minute=0, second=0, microsecond=0)
    
    def generate_reservation_uid(self, source: str) -> str:
        """Generate realistic reservation UID based on source"""
        if source == 'evolve':
            return f"EV-{random.randint(100000, 999999)}"
        elif source == 'itrip':
            return f"IT-{uuid.uuid4().hex[:8].upper()}"
        else:  # ics
            return str(uuid.uuid4())
    
    def create_reservation(self, 
                         source: str, 
                         status: str = 'new', 
                         base_reservation: Optional[Reservation] = None,
                         custom_params: Optional[Dict] = None) -> Reservation:
        """Create a single reservation with specified parameters"""
        
        # Use base reservation for modifications, or create new
        if base_reservation and status in ['modified', 'removed']:
            reservation = base_reservation
            if status == 'modified':
                # Modify some aspects of the reservation
                if random.random() < 0.4:  # 40% chance to modify dates
                    new_check_in, new_check_out = self.generate_date_range(
                        days_from_now=random.randint(-5, 15)
                    )
                    reservation.check_in = new_check_in
                    reservation.check_out = new_check_out
                
                if random.random() < 0.3:  # 30% chance to modify guest
                    guest = random.choice(self.guest_profiles)
                    reservation.guest_name = f"{guest.first_name} {guest.last_name}"
                    reservation.guest_email = guest.email
                    reservation.guest_phone = guest.phone
                
                if random.random() < 0.5:  # 50% chance to add/modify custom instructions
                    reservation.custom_instructions = random.choice(self.custom_instructions)
        else:
            # Create new reservation
            property_profile = random.choice(self.test_properties)
            guest_profile = random.choice(self.guest_profiles)
            
            # Apply custom parameters if provided
            if custom_params:
                if 'days_from_now' in custom_params:
                    check_in, check_out = self.generate_date_range(
                        days_from_now=custom_params['days_from_now'],
                        duration_days=custom_params.get('duration_days')
                    )
                else:
                    check_in, check_out = self.generate_date_range()
                
                if 'property_index' in custom_params:
                    property_profile = self.test_properties[custom_params['property_index']]
                
                if 'guest_index' in custom_params:
                    guest_profile = self.guest_profiles[custom_params['guest_index']]
            else:
                check_in, check_out = self.generate_date_range(
                    days_from_now=random.randint(-10, 30)
                )
            
            reservation = Reservation(
                uid=self.generate_reservation_uid(source),
                property_name=property_profile.name,
                property_address=f"{property_profile.address}, {property_profile.city}, {property_profile.state} {property_profile.zip_code}",
                guest_name=f"{guest_profile.first_name} {guest_profile.last_name}",
                guest_email=guest_profile.email,
                guest_phone=guest_profile.phone,
                check_in=check_in,
                check_out=check_out,
                source=source,
                status=status,
                custom_instructions=random.choice(self.custom_instructions) if random.random() < 0.4 else None,
                next_guest_date=self.generate_next_guest_date(check_out),
                booking_id=f"{source.upper()}-{random.randint(10000, 99999)}"
            )
        
        reservation.status = status
        return reservation
    
    def generate_evolve_csv(self, reservations: List[Reservation], filename: str = None) -> str:
        """Generate Evolve-format CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evolve_test_data_{timestamp}.csv"
        
        csv_dir = self.config.get_csv_process_dir()
        filepath = csv_dir / filename
        
        # Evolve CSV format (no "Property Name" header - this identifies it as Evolve)
        headers = [
            "Confirmation Number", "Guest First Name", "Guest Last Name", 
            "Guest Email", "Guest Phone", "Property Address", "Check-in Date", 
            "Check-out Date", "Status", "Special Requests"
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for reservation in reservations:
                if reservation.source == 'evolve':
                    first_name, last_name = reservation.guest_name.split(' ', 1)
                    
                    # Evolve status mapping
                    status_map = {'new': 'Confirmed', 'modified': 'Modified', 'removed': 'Cancelled'}
                    evolve_status = status_map.get(reservation.status, 'Confirmed')
                    
                    writer.writerow([
                        reservation.booking_id,
                        first_name,
                        last_name,
                        reservation.guest_email,
                        reservation.guest_phone,
                        reservation.property_address,
                        reservation.check_in.strftime("%Y-%m-%d"),
                        reservation.check_out.strftime("%Y-%m-%d"),
                        evolve_status,
                        reservation.custom_instructions or ""
                    ])
        
        return str(filepath)
    
    def generate_itrip_csv(self, reservations: List[Reservation], filename: str = None) -> str:
        """Generate iTrip-format CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iTrip_Report_{timestamp}.csv"
        
        csv_dir = self.config.get_csv_process_dir()
        filepath = csv_dir / filename
        
        # iTrip CSV format (includes "Property Name" header - this identifies it as iTrip)
        headers = [
            "Reservation ID", "Property Name", "Property Address", "Guest Name", 
            "Guest Email", "Guest Phone", "Check-in Date", "Check-out Date", 
            "Reservation Status", "Next Guest Date", "Custom Instructions"
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for reservation in reservations:
                if reservation.source == 'itrip':
                    # iTrip status mapping
                    status_map = {'new': 'Active', 'modified': 'Modified', 'removed': 'Cancelled'}
                    itrip_status = status_map.get(reservation.status, 'Active')
                    
                    next_guest_str = ""
                    if reservation.next_guest_date:
                        next_guest_str = reservation.next_guest_date.strftime("%Y-%m-%d")
                    
                    writer.writerow([
                        reservation.uid,
                        reservation.property_name,
                        reservation.property_address,
                        reservation.guest_name,
                        reservation.guest_email,
                        reservation.guest_phone,
                        reservation.check_in.strftime("%Y-%m-%d"),
                        reservation.check_out.strftime("%Y-%m-%d"),
                        itrip_status,
                        next_guest_str,
                        reservation.custom_instructions or ""
                    ])
        
        return str(filepath)
    
    def generate_ics_feed(self, reservations: List[Reservation], filename: str = None) -> str:
        """Generate ICS calendar feed file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"boris_test_calendar_{timestamp}.ics"
        
        # For now, create a simple ICS representation
        # In real implementation, this would be a proper ICS calendar format
        ics_dir = Path("/tmp/test_ics_feeds")
        ics_dir.mkdir(exist_ok=True)
        filepath = ics_dir / filename
        
        ics_content = []
        ics_content.append("BEGIN:VCALENDAR")
        ics_content.append("VERSION:2.0")
        ics_content.append("PRODID:-//Test Generator//Boris Test Calendar//EN")
        
        for reservation in reservations:
            if reservation.source == 'ics':
                ics_content.extend([
                    "BEGIN:VEVENT",
                    f"UID:{reservation.uid}",
                    f"DTSTART:{reservation.check_in.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND:{reservation.check_out.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{reservation.guest_name} - {reservation.property_name}",
                    f"DESCRIPTION:Guest: {reservation.guest_name}\\nEmail: {reservation.guest_email}\\nPhone: {reservation.guest_phone}",
                    f"LOCATION:{reservation.property_address}",
                    f"STATUS:{'CANCELLED' if reservation.status == 'removed' else 'CONFIRMED'}",
                    "END:VEVENT"
                ])
        
        ics_content.append("END:VCALENDAR")
        
        with open(filepath, 'w', encoding='utf-8') as icsfile:
            icsfile.write('\n'.join(ics_content))
        
        return str(filepath)
    
    def generate_test_scenario(self, scenario_name: str, count: int = 10) -> Dict[str, List[str]]:
        """Generate specific test scenarios"""
        
        scenarios = {
            'mixed_sources': self._generate_mixed_sources_scenario,
            'long_term_guests': self._generate_long_term_scenario,
            'same_day_turnovers': self._generate_same_day_turnover_scenario,
            'modifications_sequence': self._generate_modification_sequence_scenario,
            'edge_cases': self._generate_edge_cases_scenario,
            'custom_instructions_variety': self._generate_custom_instructions_scenario,
        }
        
        if scenario_name not in scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        return scenarios[scenario_name](count)
    
    def _generate_mixed_sources_scenario(self, count: int) -> Dict[str, List[str]]:
        """Generate reservations from all sources with various statuses"""
        reservations = []
        files_created = []
        
        # Distribute across sources
        sources = ['evolve', 'itrip', 'ics']
        statuses = ['new', 'modified', 'removed']
        
        for i in range(count):
            source = sources[i % len(sources)]
            status = statuses[i % len(statuses)]
            
            reservation = self.create_reservation(source, status)
            reservations.append(reservation)
        
        # Group by source and create files
        for source in sources:
            source_reservations = [r for r in reservations if r.source == source]
            if source_reservations:
                if source == 'evolve':
                    file_path = self.generate_evolve_csv(source_reservations)
                elif source == 'itrip':
                    file_path = self.generate_itrip_csv(source_reservations)
                else:
                    file_path = self.generate_ics_feed(source_reservations)
                files_created.append(file_path)
        
        return {
            'scenario': 'mixed_sources',
            'files_created': files_created,
            'reservations_count': len(reservations)
        }
    
    def _generate_long_term_scenario(self, count: int) -> Dict[str, List[str]]:
        """Generate long-term guest scenarios (≥14 days)"""
        reservations = []
        
        for i in range(count):
            source = random.choice(['evolve', 'itrip', 'ics'])
            
            # Force long-term stays
            custom_params = {
                'days_from_now': random.randint(0, 30),
                'duration_days': random.choice([14, 21, 30, 45, 60])  # All long-term
            }
            
            reservation = self.create_reservation(source, 'new', custom_params=custom_params)
            reservation.custom_instructions = "Long-term guest - deep cleaning required"
            reservations.append(reservation)
        
        files_created = []
        
        # Create files by source
        for source in ['evolve', 'itrip', 'ics']:
            source_reservations = [r for r in reservations if r.source == source]
            if source_reservations:
                if source == 'evolve':
                    file_path = self.generate_evolve_csv(source_reservations, f"evolve_long_term_test.csv")
                elif source == 'itrip':
                    file_path = self.generate_itrip_csv(source_reservations, f"itrip_long_term_test.csv")
                else:
                    file_path = self.generate_ics_feed(source_reservations, f"ics_long_term_test.ics")
                files_created.append(file_path)
        
        return {
            'scenario': 'long_term_guests',
            'files_created': files_created,
            'reservations_count': len(reservations)
        }
    
    def _generate_same_day_turnover_scenario(self, count: int) -> Dict[str, List[str]]:
        """Generate same-day turnover scenarios"""
        reservations = []
        
        base_date = datetime.now(self.arizona_tz) + timedelta(days=7)
        
        for i in range(count):
            # Create checkout and checkin on same day
            checkout_time = base_date.replace(hour=11, minute=0)
            checkin_time = base_date.replace(hour=16, minute=0)
            
            # Guest checking out
            checkout_reservation = self.create_reservation(
                'itrip', 'new',
                custom_params={
                    'days_from_now': 6,  # So checkout is tomorrow
                    'duration_days': 3
                }
            )
            checkout_reservation.check_out = checkout_time
            checkout_reservation.custom_instructions = "Same-day turnover - priority cleaning"
            checkout_reservation.next_guest_date = checkin_time
            
            # Guest checking in same day
            checkin_reservation = self.create_reservation(
                'evolve', 'new',
                custom_params={
                    'property_index': 0  # Same property
                }
            )
            checkin_reservation.check_in = checkin_time
            checkin_reservation.check_out = checkin_time + timedelta(days=3)
            
            reservations.extend([checkout_reservation, checkin_reservation])
            base_date += timedelta(days=1)  # Next day for next pair
        
        files_created = []
        
        # Create separate files for each source
        evolve_reservations = [r for r in reservations if r.source == 'evolve']
        itrip_reservations = [r for r in reservations if r.source == 'itrip']
        
        if evolve_reservations:
            file_path = self.generate_evolve_csv(evolve_reservations, "evolve_same_day_turnover.csv")
            files_created.append(file_path)
        
        if itrip_reservations:
            file_path = self.generate_itrip_csv(itrip_reservations, "itrip_same_day_turnover.csv")
            files_created.append(file_path)
        
        return {
            'scenario': 'same_day_turnovers',
            'files_created': files_created,
            'reservations_count': len(reservations)
        }
    
    def _generate_modification_sequence_scenario(self, count: int) -> Dict[str, List[str]]:
        """Generate sequence: new → modified → removed"""
        files_created = []
        
        # Create initial reservations
        base_reservations = []
        for i in range(count):
            source = random.choice(['evolve', 'itrip'])
            reservation = self.create_reservation(source, 'new')
            base_reservations.append(reservation)
        
        # Create files for each stage
        stages = ['new', 'modified', 'removed']
        
        for stage in stages:
            stage_reservations = []
            
            for base_reservation in base_reservations:
                if stage == 'new':
                    modified_reservation = base_reservation
                else:
                    modified_reservation = self.create_reservation(
                        base_reservation.source, 
                        stage, 
                        base_reservation=base_reservation
                    )
                stage_reservations.append(modified_reservation)
            
            # Create files for this stage
            for source in ['evolve', 'itrip']:
                source_reservations = [r for r in stage_reservations if r.source == source]
                if source_reservations:
                    if source == 'evolve':
                        file_path = self.generate_evolve_csv(
                            source_reservations, 
                            f"evolve_modification_sequence_{stage}.csv"
                        )
                    else:
                        file_path = self.generate_itrip_csv(
                            source_reservations, 
                            f"itrip_modification_sequence_{stage}.csv"
                        )
                    files_created.append(file_path)
        
        return {
            'scenario': 'modifications_sequence',
            'files_created': files_created,
            'reservations_count': len(base_reservations) * 3  # 3 stages
        }
    
    def _generate_edge_cases_scenario(self, count: int) -> Dict[str, List[str]]:
        """Generate edge cases and error scenarios"""
        reservations = []
        
        edge_cases = [
            # Very short stays
            {'duration_days': 1, 'custom_instructions': 'One night only - quick turnover'},
            # Very long stays  
            {'duration_days': 90, 'custom_instructions': 'Extended stay - monthly cleaning'},
            # Past dates (late entries)
            {'days_from_now': -5, 'custom_instructions': 'Late entry - already departed'},
            # Far future dates
            {'days_from_now': 180, 'custom_instructions': 'Advance booking - special prep'},
            # Same day check-in/out
            {'duration_days': 0, 'custom_instructions': 'Day use only - light cleaning'},
        ]
        
        for i in range(count):
            edge_case = edge_cases[i % len(edge_cases)]
            source = random.choice(['evolve', 'itrip', 'ics'])
            
            reservation = self.create_reservation(source, 'new', custom_params=edge_case)
            reservation.custom_instructions = edge_case['custom_instructions']
            reservations.append(reservation)
        
        files_created = []
        
        # Create files by source
        for source in ['evolve', 'itrip', 'ics']:
            source_reservations = [r for r in reservations if r.source == source]
            if source_reservations:
                if source == 'evolve':
                    file_path = self.generate_evolve_csv(source_reservations, "evolve_edge_cases.csv")
                elif source == 'itrip':
                    file_path = self.generate_itrip_csv(source_reservations, "itrip_edge_cases.csv")
                else:
                    file_path = self.generate_ics_feed(source_reservations, "ics_edge_cases.ics")
                files_created.append(file_path)
        
        return {
            'scenario': 'edge_cases',
            'files_created': files_created,
            'reservations_count': len(reservations)
        }
    
    def _generate_custom_instructions_scenario(self, count: int) -> Dict[str, List[str]]:
        """Generate variety of custom instructions scenarios"""
        reservations = []
        
        # Test various custom instruction scenarios
        instruction_scenarios = [
            "Extra towels needed - guest requested 12 towels",
            "Pet-friendly cleaning required - hypoallergenic products only",
            "Late checkout approved - guest leaving at 3 PM, clean after",
            "VIP guest - white glove service and fresh flowers",
            "Damage reported - inspect and document before next guest",
            "Special occasion - anniversary setup requested",
            "Medical needs - ensure all surfaces sanitized",
            "Extended family - extra bedding and high chair needed",
            "Business guest - ensure WiFi and workspace ready",
            "Repeat guest - knows property well, standard service",
            "A" * 250,  # Test truncation - over 200 char limit
            "Unicode test: café, naïve, résumé, piñata 🎉🏠🧹",  # Unicode chars
        ]
        
        for i in range(count):
            source = random.choice(['evolve', 'itrip'])
            reservation = self.create_reservation(source, 'new')
            reservation.custom_instructions = instruction_scenarios[i % len(instruction_scenarios)]
            reservations.append(reservation)
        
        files_created = []
        
        # Create files by source
        for source in ['evolve', 'itrip']:
            source_reservations = [r for r in reservations if r.source == source]
            if source_reservations:
                if source == 'evolve':
                    file_path = self.generate_evolve_csv(source_reservations, "evolve_custom_instructions.csv")
                else:
                    file_path = self.generate_itrip_csv(source_reservations, "itrip_custom_instructions.csv")
                files_created.append(file_path)
        
        return {
            'scenario': 'custom_instructions_variety',
            'files_created': files_created,
            'reservations_count': len(reservations)
        }
    
    def cleanup_test_files(self) -> int:
        """Clean up generated test files"""
        csv_dir = self.config.get_csv_process_dir()
        ics_dir = Path("/tmp/test_ics_feeds")
        
        files_removed = 0
        
        # Remove test CSV files
        for pattern in ["*test*.csv", "*boris*.csv", "*modification*.csv", "*edge*.csv", "*long_term*.csv", "*same_day*.csv", "*custom*.csv"]:
            for file_path in csv_dir.glob(pattern):
                file_path.unlink()
                files_removed += 1
        
        # Remove test ICS files
        if ics_dir.exists():
            for file_path in ics_dir.glob("*.ics"):
                file_path.unlink()
                files_removed += 1
        
        return files_removed

def main():
    """CLI interface for the test generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic Test Data Generator')
    parser.add_argument('--scenario', choices=[
        'mixed_sources', 'long_term_guests', 'same_day_turnovers', 
        'modifications_sequence', 'edge_cases', 'custom_instructions_variety'
    ], help='Test scenario to generate')
    parser.add_argument('--count', type=int, default=10, help='Number of reservations to generate')
    parser.add_argument('--environment', choices=['development', 'production'], default='development')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test files')
    parser.add_argument('--all-scenarios', action='store_true', help='Generate all test scenarios')
    
    args = parser.parse_args()
    
    generator = DynamicTestGenerator(args.environment)
    
    if args.cleanup:
        removed_count = generator.cleanup_test_files()
        print(f"🧹 Cleaned up {removed_count} test files")
        return
    
    if args.all_scenarios:
        scenarios = [
            'mixed_sources', 'long_term_guests', 'same_day_turnovers', 
            'modifications_sequence', 'edge_cases', 'custom_instructions_variety'
        ]
        
        print(f"🚀 Generating all test scenarios for {args.environment} environment...")
        
        total_files = 0
        total_reservations = 0
        
        for scenario in scenarios:
            print(f"\n📝 Generating scenario: {scenario}")
            result = generator.generate_test_scenario(scenario, args.count)
            
            print(f"   Files created: {len(result['files_created'])}")
            print(f"   Reservations: {result['reservations_count']}")
            
            for file_path in result['files_created']:
                print(f"   📄 {file_path}")
            
            total_files += len(result['files_created'])
            total_reservations += result['reservations_count']
        
        print(f"\n🎉 All scenarios generated!")
        print(f"   Total files: {total_files}")
        print(f"   Total reservations: {total_reservations}")
        
    elif args.scenario:
        print(f"🚀 Generating {args.scenario} scenario for {args.environment} environment...")
        result = generator.generate_test_scenario(args.scenario, args.count)
        
        print(f"✅ Generated {result['reservations_count']} reservations")
        print(f"📁 Files created:")
        for file_path in result['files_created']:
            print(f"   📄 {file_path}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()