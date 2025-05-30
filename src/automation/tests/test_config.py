#!/usr/bin/env python3
"""
Test suite for automation.config module

Tests configuration management, path resolution, and portability features.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from automation.config import Config


class TestConfig:
    """Test cases for Config class"""
    
    def test_project_root_discovery(self):
        """Test that project root is discovered correctly"""
        root = Config.find_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        # Check that at least one marker file exists
        marker_files = ['.env', 'VERSION', 'README.md', 'requirements.txt']
        assert any((root / marker).exists() for marker in marker_files)
    
    def test_directory_structure(self):
        """Test that all expected directories are accessible"""
        # Test core directories
        assert Config.get_scripts_dir().exists()
        assert Config.get_logs_dir().exists()
        
        # Test CSV directories (should be created if they don't exist)
        csv_process = Config.get_csv_process_dir()
        csv_done = Config.get_csv_done_dir()
        assert isinstance(csv_process, Path)
        assert isinstance(csv_done, Path)
    
    def test_path_portability(self):
        """Test that all paths are platform-agnostic"""
        paths = [
            Config.get_project_root(),
            Config.get_scripts_dir(),
            Config.get_logs_dir(),
            Config.get_csv_process_dir(),
            Config.get_csv_done_dir(),
            Config.get_backups_dir(),
            Config.get_itripcsv_downloads_dir()
        ]
        
        for path in paths:
            assert isinstance(path, Path)
            # Ensure paths use forward slashes internally (pathlib handles OS conversion)
            assert not '\\' in str(path)
    
    def test_environment_loading(self):
        """Test environment variable loading"""
        # Test with mock environment
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            Config._env_loaded = False  # Reset to force reload
            value = Config.get_env('TEST_VAR', 'default')
            assert value == 'test_value'
    
    def test_env_type_conversion(self):
        """Test environment variable type conversion"""
        with patch.dict(os.environ, {
            'BOOL_TRUE': 'true',
            'BOOL_FALSE': 'false', 
            'INT_VAL': '42'
        }):
            Config._env_loaded = False
            
            assert Config.get_env_bool('BOOL_TRUE') is True
            assert Config.get_env_bool('BOOL_FALSE') is False
            assert Config.get_env_bool('MISSING_BOOL', True) is True
            
            assert Config.get_env_int('INT_VAL') == 42
            assert Config.get_env_int('MISSING_INT', 10) == 10
    
    def test_airtable_configuration(self):
        """Test Airtable configuration methods"""
        # Test that methods return strings (may be empty if not configured)
        api_key = Config.get_airtable_api_key()
        base_id = Config.get_airtable_base_id()
        table_name = Config.get_automation_table_name()
        
        assert isinstance(api_key, str)
        assert isinstance(base_id, str)
        assert isinstance(table_name, str)
    
    def test_field_configuration(self):
        """Test Airtable field configuration methods"""
        fields = [
            Config.get_automation_name_field(),
            Config.get_automation_active_field(),
            Config.get_automation_last_ran_field(),
            Config.get_automation_sync_details_field()
        ]
        
        for field in fields:
            assert isinstance(field, str)
            assert len(field) > 0  # Should have default values
    
    def test_sys_path_management(self):
        """Test sys.path management"""
        import sys
        original_path = sys.path.copy()
        
        try:
            Config.add_project_to_path()
            # Check that project root is in sys.path
            project_root_str = str(Config.get_project_root())
            assert project_root_str in sys.path
        finally:
            # Restore original path
            sys.path[:] = original_path
    
    def test_directory_creation(self):
        """Test automatic directory creation"""
        # This should not raise any exceptions
        Config.ensure_directories()
        
        # Check that CSV directories exist after ensure_directories
        assert Config.get_csv_process_dir().exists()
        assert Config.get_csv_done_dir().exists()
        assert Config.get_logs_dir().exists()
    
    def test_missing_environment_validation(self):
        """Test environment validation for missing required keys"""
        with patch.dict(os.environ, {}, clear=True):
            Config._env_loaded = False
            
            missing = Config.validate_required_env([
                'REQUIRED_KEY_1',
                'REQUIRED_KEY_2'
            ])
            
            assert 'REQUIRED_KEY_1' in missing
            assert 'REQUIRED_KEY_2' in missing


class TestConfigIntegration:
    """Integration tests for Config class"""
    
    def test_import_from_scripts(self):
        """Test that Config can be imported from various script locations"""
        # This simulates how scripts import the config
        import sys
        from pathlib import Path
        
        # Simulate being in scripts/CSVtoAirtable/
        script_path = Config.get_scripts_dir() / "CSVtoAirtable"
        
        # Add the src directory to path (as scripts do)
        Config.add_project_to_path()
        
        # Should be able to import
        try:
            from automation.config import Config as ImportedConfig
            assert ImportedConfig is not None
        except ImportError:
            pytest.fail("Could not import Config from script location")
    
    def test_cross_platform_paths(self):
        """Test that paths work across platforms"""
        paths = [
            Config.get_project_root() / "test_file.txt",
            Config.get_scripts_dir() / "subdir" / "script.py",
            Config.get_logs_dir() / "test.log"
        ]
        
        for path in paths:
            # Should be able to create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)
            assert path.parent.exists()
    
    def test_config_singleton_behavior(self):
        """Test that Config behaves as a singleton"""
        # Multiple calls should return same project root
        root1 = Config.get_project_root()
        root2 = Config.get_project_root()
        assert root1 == root2
        
        # Environment should only be loaded once
        Config._env_loaded = False
        Config.get_env('TEST')
        first_load = Config._env_loaded
        
        Config.get_env('TEST2')
        second_load = Config._env_loaded
        
        assert first_load == second_load == True


if __name__ == "__main__":
    pytest.main([__file__])