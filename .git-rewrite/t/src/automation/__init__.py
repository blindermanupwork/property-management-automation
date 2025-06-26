"""
Property Management Automation Suite
====================================

A comprehensive automation system for vacation rental property management,
featuring CSV processing, calendar sync, and service job creation.

Version: 1.2.0
"""

__version__ = "1.2.0"
__author__ = "Property Management Automation Team"
__email__ = "automation@example.com"

# Import main classes for easy access
from .config_wrapper import Config
from .controller import AutomationController

__all__ = ["Config", "AutomationController", "__version__"]