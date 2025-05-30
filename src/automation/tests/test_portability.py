#!/usr/bin/env python3
"""
Test suite for portability and cross-platform compatibility

Tests that the automation system works across different environments and setups.
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from automation.config import Config


class TestPortability:
    """Test portability across different environments"""
    
    def test_package_importability(self):
        """Test that the automation package can be imported from different locations"""
        # Test direct import
        try:
            from automation import Config as ImportedConfig
            from automation import AutomationController
            assert ImportedConfig is not None
            assert AutomationController is not None
        except ImportError as e:
            pytest.fail(f"Could not import automation package: {e}")
    
    def test_script_imports(self):
        """Test that scripts can import the automation package"""
        # Test entry point import
        try:
            from automation.scripts.run_automation import AutomationRunner, main
            assert AutomationRunner is not None
            assert main is not None
        except ImportError as e:
            pytest.fail(f"Could not import automation scripts: {e}")
    
    def test_path_independence(self):
        """Test that the system works regardless of current working directory"""
        original_cwd = os.getcwd()
        
        try:
            # Test from different working directories
            test_dirs = [
                Config.get_project_root(),
                Config.get_scripts_dir(),
                tempfile.gettempdir()
            ]
            
            for test_dir in test_dirs:
                if test_dir.exists():
                    os.chdir(str(test_dir))
                    
                    # Should still be able to find project root
                    project_root = Config.find_project_root()
                    assert project_root.exists()
                    
                    # Should still be able to get paths
                    scripts_dir = Config.get_scripts_dir()
                    assert isinstance(scripts_dir, Path)
        finally:
            os.chdir(original_cwd)
    
    def test_environment_isolation(self):
        """Test that the system works with different environment setups"""
        original_env = os.environ.copy()
        
        try:
            # Test with minimal environment
            os.environ.clear()
            Config._env_loaded = False
            
            # Should still work with defaults
            project_root = Config.get_project_root()
            assert project_root.exists()
            
            # Test with custom environment
            os.environ.update({
                'AUTOMATION_TABLE_NAME': 'CustomTable',
                'AUTOMATION_ACTIVE_FIELD': 'CustomActive'
            })
            Config._env_loaded = False
            
            assert Config.get_automation_table_name() == 'CustomTable'
            assert Config.get_automation_active_field() == 'CustomActive'
            
        finally:
            os.environ.clear()
            os.environ.update(original_env)
            Config._env_loaded = False
    
    def test_cross_platform_paths(self):
        """Test that paths work correctly on different platforms"""
        # Mock different platform scenarios
        test_cases = [
            ('posix', '/'),
            ('nt', '\\')
        ]
        
        for os_name, sep in test_cases:
            with patch('os.name', os_name):
                # Paths should always be Path objects
                paths = [
                    Config.get_project_root(),
                    Config.get_scripts_dir(),
                    Config.get_logs_dir()
                ]
                
                for path in paths:
                    assert isinstance(path, Path)
                    # Path objects handle platform differences internally
                    assert path.is_absolute()
    
    def test_installation_scenarios(self):
        """Test different installation scenarios"""
        # Test development installation (current scenario)
        assert Config.get_project_root().exists()
        
        # Test that required directories can be created
        test_dirs = [
            Config.get_csv_process_dir(),
            Config.get_csv_done_dir(),
            Config.get_logs_dir(),
            Config.get_backups_dir()
        ]
        
        for test_dir in test_dirs:
            # Should be able to create if it doesn't exist
            test_dir.mkdir(parents=True, exist_ok=True)
            assert test_dir.exists()


class TestSystemIntegration:
    """Test system-level integration and compatibility"""
    
    def test_python_version_compatibility(self):
        """Test that the system works with supported Python versions"""
        # Check minimum Python version (3.8+)
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
        
        # Test that required modules can be imported
        required_modules = [
            'pathlib',
            'os',
            'sys', 
            'logging',
            'datetime',
            'json'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                pytest.fail(f"Required module {module} not available")
    
    def test_dependency_compatibility(self):
        """Test that dependencies are properly handled"""
        # Test that automation package can be imported without external deps
        try:
            from automation.config import Config
            # Basic functionality should work without external dependencies
            project_root = Config.get_project_root()
            assert project_root.exists()
        except ImportError as e:
            pytest.fail(f"Basic automation package import failed: {e}")
    
    def test_file_system_compatibility(self):
        """Test file system operations across platforms"""
        # Test file creation and deletion
        test_file = Config.get_logs_dir() / "test_portability.txt"
        
        try:
            # Should be able to create file
            test_file.write_text("test content")
            assert test_file.exists()
            
            # Should be able to read file
            content = test_file.read_text()
            assert content == "test content"
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_subprocess_compatibility(self):
        """Test that subprocess operations work correctly"""
        import subprocess
        
        # Test basic subprocess operation
        try:
            result = subprocess.run([
                sys.executable, '-c', 'print("test")'
            ], capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0
            assert "test" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.fail(f"Subprocess operation failed: {e}")


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_project_markers(self):
        """Test behavior when project marker files are missing"""
        # Create a temporary directory without marker files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Mock __file__ to point to temp directory
            fake_file = temp_path / "fake_script.py"
            fake_file.touch()
            
            with patch('automation.config.Path') as mock_path:
                mock_path.return_value = fake_file
                mock_path.__file__ = str(fake_file)
                
                # Should fall back to reasonable defaults
                try:
                    root = Config.find_project_root()
                    assert isinstance(root, Path)
                except Exception as e:
                    # Should handle gracefully
                    assert "No project root found" in str(e) or root.exists()
    
    def test_permission_errors(self):
        """Test handling of permission errors"""
        # Test with read-only directory (if possible to simulate)
        try:
            # Attempt to create a directory in a restricted location
            restricted_path = Path("/root/test_automation") if os.name == 'posix' else Path("C:\\Windows\\test_automation")
            
            if not restricted_path.exists():
                # This should fail gracefully rather than crash
                try:
                    restricted_path.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    # Expected behavior - should be handled gracefully
                    pass
        except Exception:
            # Any other exception handling should be graceful
            pass
    
    def test_corrupted_environment(self):
        """Test handling of corrupted environment variables"""
        with patch.dict('os.environ', {
            'AIRTABLE_API_KEY': '',  # Empty string
            'AUTOMATION_ACTIVE_FIELD': None,  # None value (shouldn't happen but test anyway)
        }):
            Config._env_loaded = False
            
            # Should handle empty/None values gracefully
            api_key = Config.get_airtable_api_key()
            assert isinstance(api_key, str)  # Should be empty string, not None
            
            active_field = Config.get_automation_active_field()
            assert isinstance(active_field, str)
            assert len(active_field) > 0  # Should use default


if __name__ == "__main__":
    pytest.main([__file__])