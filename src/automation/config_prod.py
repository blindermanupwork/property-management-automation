#!/usr/bin/env python3
"""
Production Configuration for Property Management Automation System
"""

from typing import List
from .config_base import ConfigBase

class ProdConfig(ConfigBase):
    """Production environment configuration"""
    
    def __init__(self):
        """Initialize production configuration"""
        super().__init__('production')
        
    def get_airtable_api_key(self) -> str:
        """Get Airtable API key for production"""
        return self.get('PROD_AIRTABLE_API_KEY', '')
        
    def get_airtable_base_id(self) -> str:
        """Get Airtable base ID for production"""
        return self.get('PROD_AIRTABLE_BASE_ID', '')
        
    def get_airtable_table_name(self, table_type: str) -> str:
        """Get Airtable table name for production environment
        
        Args:
            table_type: Type of table (e.g., 'reservations', 'automation_control')
            
        Returns:
            Table name for the production environment
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
        """Validate production configuration. Returns list of errors."""
        errors = []
        
        # Required environment variables for production
        required_vars = [
            'PROD_AIRTABLE_API_KEY',
            'PROD_AIRTABLE_BASE_ID',
        ]
        
        for var in required_vars:
            value = self.get(var)
            if not value or value.strip() == '':
                errors.append(f"Missing or empty required environment variable: {var}")
                
        # Validate Airtable API key format
        api_key = self.get_airtable_api_key()
        if api_key:
            if not api_key.startswith('pat'):
                errors.append("PROD_AIRTABLE_API_KEY should start with 'pat'")
            if len(api_key) < 20:
                errors.append("PROD_AIRTABLE_API_KEY appears to be too short")
        else:
            errors.append("PROD_AIRTABLE_API_KEY is required for production environment")
            
        # Validate Airtable base ID format  
        base_id = self.get_airtable_base_id()
        if base_id:
            if not base_id.startswith('app'):
                errors.append("PROD_AIRTABLE_BASE_ID should start with 'app'")
            if len(base_id) != 17:
                errors.append("PROD_AIRTABLE_BASE_ID should be 17 characters long")
        else:
            errors.append("PROD_AIRTABLE_BASE_ID is required for production environment")
            
        return errors
        
    @property
    def is_production(self) -> bool:
        """Check if this is production environment"""
        return True
        
    @property
    def environment_name(self) -> str:
        """Get human-readable environment name"""
        return "Production"
        
    def __repr__(self) -> str:
        """String representation"""
        return f"<ProdConfig: {self.root_dir}>"