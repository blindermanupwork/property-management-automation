#!/usr/bin/env python3
"""
Development Configuration for Property Management Automation System
"""

from typing import List
from .config_base import ConfigBase

class DevConfig(ConfigBase):
    """Development environment configuration"""
    
    def __init__(self):
        """Initialize development configuration"""
        super().__init__('development')
        
    def get_airtable_api_key(self) -> str:
        """Get Airtable API key for development"""
        return self.get('DEV_AIRTABLE_API_KEY', '')
        
    def get_airtable_base_id(self) -> str:
        """Get Airtable base ID for development"""
        return self.get('DEV_AIRTABLE_BASE_ID', '')
        
    def get_airtable_table_name(self, table_type: str) -> str:
        """Get Airtable table name for development environment
        
        Args:
            table_type: Type of table (e.g., 'reservations', 'automation_control')
            
        Returns:
            Table name for the development environment
        """
        table_mappings = {
            'reservations': 'Reservations',
            'automation_control': 'Automation',
            'calendars': 'Calendars',
            'properties': 'Properties',
            'owners': 'Owners',
            'api_logs': 'API Logs',
            'ics_feeds': 'ICS Feeds',
            'ics_cron': 'ICS Cron'
        }
        return table_mappings.get(table_type, table_type)
        
    def validate_config(self) -> List[str]:
        """Validate development configuration. Returns list of errors."""
        errors = []
        
        # Required environment variables for development
        required_vars = [
            'DEV_AIRTABLE_API_KEY',
            'DEV_AIRTABLE_BASE_ID',
        ]
        
        for var in required_vars:
            value = self.get(var)
            if not value or value.strip() == '':
                errors.append(f"Missing or empty required environment variable: {var}")
                
        # Validate Airtable API key format
        api_key = self.get_airtable_api_key()
        if api_key:
            if not api_key.startswith('pat'):
                errors.append("DEV_AIRTABLE_API_KEY should start with 'pat'")
            if len(api_key) < 20:
                errors.append("DEV_AIRTABLE_API_KEY appears to be too short")
        else:
            errors.append("DEV_AIRTABLE_API_KEY is required for development environment")
            
        # Validate Airtable base ID format
        base_id = self.get_airtable_base_id()
        if base_id:
            if not base_id.startswith('app'):
                errors.append("DEV_AIRTABLE_BASE_ID should start with 'app'")
            if len(base_id) != 17:
                errors.append("DEV_AIRTABLE_BASE_ID should be 17 characters long")
        else:
            errors.append("DEV_AIRTABLE_BASE_ID is required for development environment")
            
        return errors
        
    @property
    def is_production(self) -> bool:
        """Check if this is production environment"""
        return False
        
    @property
    def environment_name(self) -> str:
        """Get human-readable environment name"""
        return "Development"
        
    def __repr__(self) -> str:
        """String representation"""
        return f"<DevConfig: {self.root_dir}>"