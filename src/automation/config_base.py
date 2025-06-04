#!/usr/bin/env python3
"""
Base Configuration Class for Property Management Automation System
Provides shared configuration logic for both dev and prod environments
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

class ConfigBase:
    """Base configuration class with shared logic for all environments"""
    
    def __init__(self, environment: str):
        """Initialize base configuration
        
        Args:
            environment: Either 'development' or 'production'
        """
        self.environment = environment
        self._root_dir = None
        self._config = {}
        self._load_config()
        
    def _find_project_root(self) -> Path:
        """Find project root by looking for setup.py or VERSION file"""
        current_dir = Path.cwd()
        
        # Search up to 5 levels
        for _ in range(5):
            if (current_dir / 'setup.py').exists() or (current_dir / 'VERSION').exists():
                return current_dir
            if current_dir.parent == current_dir:
                break
            current_dir = current_dir.parent
            
        # Fallback
        return Path('/home/opc/automation')
    
    def _load_config(self):
        """Load configuration from .env file"""
        root_dir = self._find_project_root()
        self._root_dir = root_dir
        
        # Load main .env file
        env_file = root_dir / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            
        # Load environment-specific .env file
        # Map full environment names to directory names
        env_dir_map = {
            'development': 'dev',
            'production': 'prod'
        }
        env_dir = env_dir_map.get(self.environment, self.environment)
        env_specific_file = root_dir / 'config' / 'environments' / env_dir / '.env'
        if env_specific_file.exists():
            load_dotenv(env_specific_file, override=True)
            
        # Store all config values
        self._config = dict(os.environ)
        
    @property
    def root_dir(self) -> Path:
        """Get project root directory"""
        if self._root_dir is None:
            self._root_dir = self._find_project_root()
        return self._root_dir
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
        
    def get_path(self, *parts: str) -> Path:
        """Get path relative to project root"""
        return self.root_dir / Path(*parts)
        
    def get_script_path(self, *parts: str) -> Path:
        """Get path relative to scripts directory"""
        return self.get_path('src', 'automation', 'scripts', *parts)
        
    def get_log_path(self, *parts: str) -> Path:
        """Get path relative to logs directory"""
        return self.get_path('src', 'automation', 'logs', *parts)
        
    @property
    def csv_process_dir(self) -> Path:
        """Get CSV processing directory for this environment"""
        return self.get_script_path(f'CSV_process_{self.environment}')
        
    @property
    def csv_done_dir(self) -> Path:
        """Get CSV done directory for this environment"""
        return self.get_script_path(f'CSV_done_{self.environment}')
        
    def get_itripcsv_downloads_dir(self) -> Path:
        """Get iTrip CSV downloads directory (environment-specific)"""
        return self.csv_process_dir
        
    def get_csv_process_dir(self) -> Path:
        """Get CSV processing directory (legacy compatibility method)"""
        return self.csv_process_dir
        
    def get_csv_done_dir(self) -> Path:
        """Get CSV done directory (legacy compatibility method)"""
        return self.csv_done_dir
        
    def get_logs_dir(self) -> Path:
        """Get logs directory"""
        return self.get_log_path()
        
    def get_backups_dir(self) -> Path:
        """Get backups directory"""
        return self.get_path('backups')
        
    # Date filtering configuration methods
    def get_fetch_months_before(self) -> int:
        """Get number of months to look back for reservations"""
        return int(self.get('FETCH_RESERVATIONS_MONTHS_BEFORE', 2))
        
    def get_ignore_blocks_months_away(self) -> int:
        """Get number of months ahead to ignore blocked events"""
        return int(self.get('IGNORE_EVENTS_ENDING_MONTHS_AWAY', 24))
        
    def get_ignore_events_ending_before_today(self) -> bool:
        """Get whether to ignore events ending before today"""
        value = self.get('IGNORE_EVENTS_ENDING_BEFORE_TODAY', 'true')
        return value.lower() in ('true', '1', 'yes', 'on')
        
    # Evolve credentials
    def get_evolve_username(self) -> str:
        """Get Evolve username"""
        return self.get('EVOLVE_USERNAME', '')
        
    def get_evolve_password(self) -> str:
        """Get Evolve password"""
        return self.get('EVOLVE_PASSWORD', '')
        
    def ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = [
            self.csv_process_dir,
            self.csv_done_dir,
            self.get_log_path(),
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    # Timezone handling
    @property
    def timezone(self) -> pytz.timezone:
        """Get timezone for the application"""
        return pytz.timezone('America/Phoenix')
        
    @property
    def log_timezone(self) -> pytz.timezone:
        """Get timezone for logging (PST)"""
        return pytz.timezone('America/Los_Angeles')
        
    def get_current_time(self) -> datetime:
        """Get current time in application timezone"""
        return datetime.now(self.timezone)
        
    def get_log_time(self) -> datetime:
        """Get current time in logging timezone"""
        return datetime.now(self.log_timezone)
        
    # Abstract methods to be implemented by subclasses
    def get_airtable_api_key(self) -> str:
        """Get Airtable API key for this environment"""
        raise NotImplementedError("Subclass must implement get_airtable_api_key")
        
    def get_airtable_base_id(self) -> str:
        """Get Airtable base ID for this environment"""
        raise NotImplementedError("Subclass must implement get_airtable_base_id")
        
    def get_airtable_table_name(self, table_type: str) -> str:
        """Get Airtable table name for this environment"""
        raise NotImplementedError("Subclass must implement get_airtable_table_name")
        
    def validate_config(self) -> List[str]:
        """Validate configuration. Returns list of errors."""
        raise NotImplementedError("Subclass must implement validate_config")