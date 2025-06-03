#!/usr/bin/env python3
"""
Config Wrapper
Automatically selects the correct config class based on ENVIRONMENT variable
This allows existing scripts to continue working without major modifications
"""

import os
from .config_dev import DevConfig
from .config_prod import ProdConfig

def get_config():
    """Get the appropriate config based on ENVIRONMENT variable
    
    Returns:
        DevConfig or ProdConfig instance
    """
    environment = os.environ.get('ENVIRONMENT', 'development').lower()
    
    if environment == 'production':
        return ProdConfig()
    else:
        return DevConfig()

# Create a singleton instance that scripts can import
Config = get_config()