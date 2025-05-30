#!/usr/bin/env python3
"""
Universal Automation Runner
===========================

This script can run the automation system from anywhere without installation.
It automatically handles:
- Package path discovery and setup
- Environment configuration
- Dependency verification
- Cross-platform compatibility

Usage:
    python run_anywhere.py              # Run all automations
    python run_anywhere.py --list       # List available automations
    python run_anywhere.py --test       # Run system tests
    python run_anywhere.py --install    # Install package in development mode
    python run_anywhere.py --help       # Show help
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def find_project_root():
    """Find the project root directory from any location"""
    current = Path(__file__).parent.absolute()
    marker_files = ['.env', 'VERSION', 'README.md', 'requirements.txt', 'setup.py']
    
    while current != current.parent:
        if any((current / marker).exists() for marker in marker_files):
            return current
        current = current.parent
    
    # If not found, use the directory containing this script
    return Path(__file__).parent.absolute()


def setup_python_path(project_root):
    """Add the project to Python path for imports"""
    src_dir = project_root / "src"
    project_root_str = str(project_root)
    src_dir_str = str(src_dir)
    
    # Add both project root and src to path if not already present
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    if src_dir.exists() and src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)


def verify_dependencies():
    """Check if required dependencies are available"""
    required_packages = [
        ('requests', 'requests'),
        ('pyairtable', 'pyairtable'),
        ('python-dotenv', 'dotenv'),
        ('pathlib', None)  # Built-in, no install name
    ]
    
    missing = []
    for package_name, import_name in required_packages:
        if import_name is None:
            continue
            
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    return missing


def install_dependencies(missing_packages):
    """Install missing dependencies"""
    if not missing_packages:
        return True
    
    print(f"📦 Installing missing dependencies: {', '.join(missing_packages)}")
    
    try:
        subprocess.run([
            'python3', '-m', 'pip', 'install'
        ] + missing_packages, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_automation_suite():
    """Run the complete automation suite"""
    try:
        from automation.scripts.run_automation import main
        print("🚀 Starting automation suite...")
        main()
        return True
    except Exception as e:
        print(f"❌ Automation suite failed: {e}")
        return False


def list_automations():
    """List all available automations"""
    try:
        from automation.controller import AutomationController
        
        print("📋 Available Automations:")
        print("=" * 30)
        
        controller = AutomationController()
        controller.list_automations()
        return True
    except Exception as e:
        print(f"❌ Failed to list automations: {e}")
        return False


def run_tests():
    """Run the test suite"""
    project_root = find_project_root()
    tests_dir = project_root / "src" / "automation" / "tests"
    
    if not tests_dir.exists():
        print("❌ Tests directory not found")
        return False
    
    try:
        # Try to run with pytest
        result = subprocess.run([
            'python', '-m', 'pytest', str(tests_dir), '-v'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            print(result.stdout)
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("📦 Installing pytest...")
        subprocess.run(['python3', '-m', 'pip', 'install', 'pytest'])
        
        # Retry
        result = subprocess.run([
            'python3', '-m', 'pytest', str(tests_dir), '-v'
        ])
        return result.returncode == 0


def install_package():
    """Install the package in development mode"""
    project_root = find_project_root()
    setup_py = project_root / "setup.py"
    
    if not setup_py.exists():
        print("❌ setup.py not found")
        return False
    
    try:
        print("📦 Installing package in development mode...")
        subprocess.run([
            'python3', '-m', 'pip', 'install', '-e', str(project_root)
        ], check=True)
        print("✅ Package installed successfully!")
        print("You can now run 'run-automation' from anywhere.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False


def show_system_info():
    """Show system information"""
    project_root = find_project_root()
    
    print("🔍 System Information:")
    print("=" * 25)
    print(f"Project Root: {project_root}")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {sys.platform}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    # Check if package is importable
    try:
        setup_python_path(project_root)
        from automation.config import Config
        print("✅ Automation package is importable")
        print(f"Config Project Root: {Config.get_project_root()}")
    except ImportError as e:
        print(f"❌ Automation package not importable: {e}")
    
    # Check dependencies
    missing = verify_dependencies()
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
    else:
        print("✅ All dependencies available")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Universal Automation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_anywhere.py              # Run all automations
  python run_anywhere.py --list       # List available automations  
  python run_anywhere.py --test       # Run system tests
  python run_anywhere.py --install    # Install package for system-wide use
  python run_anywhere.py --info       # Show system information
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all available automations')
    parser.add_argument('--test', action='store_true', 
                       help='Run the test suite')
    parser.add_argument('--install', action='store_true',
                       help='Install package in development mode')
    parser.add_argument('--info', action='store_true',
                       help='Show system information')
    parser.add_argument('--auto-install', action='store_true',
                       help='Automatically install missing dependencies')
    
    args = parser.parse_args()
    
    # Find project root and setup paths
    project_root = find_project_root()
    setup_python_path(project_root)
    
    print(f"🏠 Project Root: {project_root}")
    
    # Show system info if requested
    if args.info:
        show_system_info()
        return
    
    # Check dependencies
    missing_deps = verify_dependencies()
    if missing_deps:
        if args.auto_install:
            if not install_dependencies(missing_deps):
                sys.exit(1)
        else:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            print("Run with --auto-install to install them automatically, or install manually:")
            print(f"pip install {' '.join(missing_deps)}")
            sys.exit(1)
    
    # Handle different modes
    if args.install:
        success = install_package()
    elif args.list:
        success = list_automations()
    elif args.test:
        success = run_tests()
    else:
        success = run_automation_suite()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()