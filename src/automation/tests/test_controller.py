#!/usr/bin/env python3
"""
Test suite for automation.controller module

Tests the AutomationController class functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import requests

from automation.controller import AutomationController
from automation.config import Config


class TestAutomationController:
    """Test cases for AutomationController class"""
    
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table'
    })
    def test_controller_initialization(self):
        """Test controller initialization with environment variables"""
        Config._env_loaded = False  # Force reload
        controller = AutomationController()
        
        assert controller.airtable_api_key == 'test_api_key'
        assert controller.base_id == 'test_base_id'
        assert controller.automation_table == 'test_table'
    
    def test_controller_missing_api_key(self):
        """Test controller raises error when API key is missing"""
        with patch.dict('os.environ', {}, clear=True):
            Config._env_loaded = False
            with pytest.raises(ValueError, match="AIRTABLE_API_KEY environment variable not set"):
                AutomationController()
    
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table'
    })
    def test_get_headers(self):
        """Test API headers generation"""
        Config._env_loaded = False
        controller = AutomationController()
        headers = controller.get_headers()
        
        expected = {
            "Authorization": "Bearer test_api_key",
            "Content-Type": "application/json"
        }
        assert headers == expected
    
    @patch('requests.get')
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table',
        'AUTOMATION_ACTIVE_FIELD': 'Active'
    })
    def test_check_automation_status_active(self, mock_get):
        """Test checking automation status when automation is active"""
        Config._env_loaded = False
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "fields": {
                        "Active": True
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        controller = AutomationController()
        result = controller.check_automation_status("Test Automation")
        
        assert result is True
        mock_get.assert_called_once()
    
    @patch('requests.get')
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table',
        'AUTOMATION_ACTIVE_FIELD': 'Active'
    })
    def test_check_automation_status_inactive(self, mock_get):
        """Test checking automation status when automation is inactive"""
        Config._env_loaded = False
        
        # Mock successful API response with inactive automation
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "fields": {
                        "Active": False
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        controller = AutomationController()
        result = controller.check_automation_status("Test Automation")
        
        assert result is False
    
    @patch('requests.get')
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table'
    })
    def test_check_automation_status_not_found(self, mock_get):
        """Test checking automation status when automation is not found"""
        Config._env_loaded = False
        
        # Mock API response with no records
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"records": []}
        mock_get.return_value = mock_response
        
        controller = AutomationController()
        result = controller.check_automation_status("Non-existent Automation")
        
        assert result is False
    
    @patch('requests.get')
    @patch('requests.patch')
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table',
        'AUTOMATION_ACTIVE_FIELD': 'Active',
        'AUTOMATION_LAST_RAN_FIELD': 'Last Ran',
        'AUTOMATION_SYNC_DETAILS_FIELD': 'Sync Details'
    })
    def test_run_automation_success(self, mock_patch, mock_get):
        """Test successful automation run"""
        Config._env_loaded = False
        
        # Mock status check (active)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "records": [
                {
                    "id": "rec123",
                    "fields": {"Active": True}
                }
            ]
        }
        mock_get.return_value = mock_get_response
        
        # Mock update request
        mock_patch_response = MagicMock()
        mock_patch_response.status_code = 200
        mock_patch.return_value = mock_patch_response
        
        # Mock automation function
        mock_automation = MagicMock()
        mock_automation.return_value = {"success": True, "message": "Test completed"}
        
        controller = AutomationController()
        result = controller.run_automation("Test Automation", mock_automation)
        
        assert result is True
        mock_automation.assert_called_once()
        mock_patch.assert_called_once()
    
    @patch('requests.get')
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table',
        'AUTOMATION_ACTIVE_FIELD': 'Active'
    })
    def test_run_automation_inactive(self, mock_get):
        """Test automation run when automation is inactive"""
        Config._env_loaded = False
        
        # Mock status check (inactive)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "fields": {"Active": False}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Mock automation function (should not be called)
        mock_automation = MagicMock()
        
        controller = AutomationController()
        result = controller.run_automation("Test Automation", mock_automation)
        
        assert result is False
        mock_automation.assert_not_called()
    
    @patch('requests.get')
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id',
        'AUTOMATION_TABLE_NAME': 'test_table',
        'AUTOMATION_NAME_FIELD': 'Name',
        'AUTOMATION_ACTIVE_FIELD': 'Active',
        'AUTOMATION_LAST_RAN_FIELD': 'Last Ran',
        'AUTOMATION_SYNC_DETAILS_FIELD': 'Sync Details'
    })
    def test_list_automations(self, mock_get):
        """Test listing all automations"""
        Config._env_loaded = False
        
        # Mock API response with multiple automations
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "fields": {
                        "Name": "Test Automation 1",
                        "Active": True,
                        "Last Ran": "2024-01-01",
                        "Sync Details": "Success"
                    }
                },
                {
                    "fields": {
                        "Name": "Test Automation 2", 
                        "Active": False,
                        "Last Ran": "Never",
                        "Sync Details": "No details"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        controller = AutomationController()
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            controller.list_automations()
            
            # Verify that automation details were printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            automation_lines = [line for line in print_calls if 'Test Automation' in line]
            assert len(automation_lines) == 2


class TestControllerIntegration:
    """Integration tests for AutomationController"""
    
    @patch.dict('os.environ', {
        'AIRTABLE_API_KEY': 'test_api_key',
        'PROD_AIRTABLE_BASE_ID': 'test_base_id', 
        'AUTOMATION_TABLE_NAME': 'test_table'
    })
    def test_controller_uses_config_correctly(self):
        """Test that controller correctly uses Config class methods"""
        Config._env_loaded = False
        controller = AutomationController()
        
        # Test that controller got values from Config methods
        assert controller.airtable_api_key == Config.get_airtable_api_key()
        assert controller.base_id == Config.get_airtable_base_id()
        assert controller.automation_table == Config.get_automation_table_name()


if __name__ == "__main__":
    pytest.main([__file__])