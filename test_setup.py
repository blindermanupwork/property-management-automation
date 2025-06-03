#!/usr/bin/env python3
"""
Quick Setup Test Script
=======================

Verifies that the automation system is properly configured and portable.
Run this script to validate your setup before deploying.
"""

import sys
import os
from pathlib import Path


def test_imports():
    """Test that all required imports work"""
    print("🔍 Testing imports...")
    
    tests = [
        ("automation.config_wrapper", "Config"),
        ("automation.controller", "AutomationController"), 
        ("automation.scripts.run_automation", "AutomationRunner"),
    ]
    
    for module, class_name in tests:
        try:
            mod = __import__(module, fromlist=[class_name])
            cls = getattr(mod, class_name)
            print(f"  ✅ {module}.{class_name}")
        except ImportError as e:
            print(f"  ❌ {module}.{class_name}: {e}")
            return False
        except AttributeError as e:
            print(f"  ❌ {module}.{class_name}: {e}")
            return False
    
    return True


def test_config():
    """Test configuration system"""
    print("\n🔧 Testing configuration...")
    
    try:
        from automation.config_wrapper import Config
        
        # Test project root discovery
        root = Config.get_project_root()
        print(f"  ✅ Project root: {root}")
        
        # Test path methods
        paths = [
            ("Scripts directory", Config.get_scripts_dir()),
            ("Logs directory", Config.get_logs_dir()),
            ("CSV process directory", Config.get_csv_process_dir()),
            ("CSV done directory", Config.get_csv_done_dir()),
        ]
        
        for name, path in paths:
            if isinstance(path, Path):
                print(f"  ✅ {name}: {path}")
            else:
                print(f"  ❌ {name}: Not a Path object")
                return False
        
        # Test environment methods
        env_methods = [
            ("Automation table name", Config.get_automation_table_name()),
            ("Automation active field", Config.get_automation_active_field()),
            ("Automation name field", Config.get_automation_name_field()),
        ]
        
        for name, value in env_methods:
            if isinstance(value, str):
                print(f"  ✅ {name}: '{value}'")
            else:
                print(f"  ❌ {name}: Not a string")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False


def test_controller():
    """Test controller initialization"""
    print("\n🎮 Testing controller...")
    
    try:
        # Set minimal required environment
        os.environ.setdefault('AIRTABLE_API_KEY', 'test_key')
        os.environ.setdefault('PROD_AIRTABLE_BASE_ID', 'test_base')
        os.environ.setdefault('AUTOMATION_TABLE_NAME', 'test_table')
        
        from automation.controller import AutomationController
        from automation.config_wrapper import Config
        
        # Reset config to pick up test environment
        Config._env_loaded = False
        
        controller = AutomationController()
        print(f"  ✅ Controller initialized")
        print(f"  ✅ API Key: {'*' * len(controller.airtable_api_key)}")
        print(f"  ✅ Base ID: {controller.base_id}")
        print(f"  ✅ Table: {controller.automation_table}")
        
        # Test headers
        headers = controller.get_headers()
        if 'Authorization' in headers and 'Content-Type' in headers:
            print(f"  ✅ Headers generated correctly")
        else:
            print(f"  ❌ Headers missing required fields")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Controller test failed: {e}")
        return False


def test_scripts():
    """Test script imports"""
    print("\n📜 Testing scripts...")
    
    try:
        from automation.scripts.run_automation import AutomationRunner, main
        
        print(f"  ✅ AutomationRunner imported")
        print(f"  ✅ main function imported")
        
        # Test runner initialization
        runner = AutomationRunner()
        print(f"  ✅ AutomationRunner instantiated")
        print(f"  ✅ Scripts directory: {runner.scripts_dir}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Scripts test failed: {e}")
        return False


def test_portability():
    """Test cross-platform portability"""
    print("\n🌍 Testing portability...")
    
    try:
        from automation.config_wrapper import Config
        
        # Test that we can change working directory and still work
        original_cwd = os.getcwd()
        
        try:
            # Change to temp directory
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                print(f"  ✅ Changed to temp directory: {temp_dir}")
                
                # Should still be able to find project root
                from automation.config_wrapper import find_project_root
                root = find_project_root()
                print(f"  ✅ Found project root from temp dir: {root}")
                
                # Should still be able to import
                from automation.controller import AutomationController
                print(f"  ✅ Can still import from temp directory")
                
        finally:
            os.chdir(original_cwd)
        
        print(f"  ✅ Portability test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Portability test failed: {e}")
        return False


def test_package_structure():
    """Test package structure"""
    print("\n📦 Testing package structure...")
    
    try:
        from automation.config_wrapper import Config
        
        project_root = Config.get_project_root()
        
        # Check expected files and directories
        expected_items = [
            ("src/automation/__init__.py", "Package init file"),
            ("src/automation/config_wrapper.py", "Config wrapper module"),
            ("src/automation/controller.py", "Controller module"),
            ("src/automation/scripts/__init__.py", "Scripts package init"),
            ("setup.py", "Setup script"),
            ("pyproject.toml", "Modern Python config"),
        ]
        
        for path_str, description in expected_items:
            path = project_root / path_str
            if path.exists():
                print(f"  ✅ {description}: {path_str}")
            else:
                print(f"  ⚠️  {description}: {path_str} (missing)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Package structure test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Automation System Setup Test")
    print("=" * 35)
    
    # Add src to path
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
    
    tests = [
        test_imports,
        test_config,
        test_controller,
        test_scripts,
        test_portability,
        test_package_structure,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your automation system is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)