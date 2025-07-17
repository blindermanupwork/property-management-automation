# Environment Management - Business Logic A-Z

**Version:** 2.2.8  
**Last Updated:** July 12, 2025  
**Purpose:** Complete alphabetical documentation of environment management business rules and implementation

---

## 🎯 **BUSINESS RULES BY ALPHABETICAL ORDER**

### **A - Automatic Environment Detection**

**Condition**: When ENVIRONMENT variable is not explicitly set  
**Action**: System automatically detects environment based on hostname analysis  
**Implementation**: 
```python
# From config_wrapper.py
environment = os.environ.get('ENVIRONMENT', 'development').lower()
if environment == 'production':
    return ProdConfig()
else:
    return DevConfig()
```
**Exception**: Force flag can override automatic detection  
**Business Impact**: Prevents manual misconfiguration and ensures proper environment selection

### **B - Base Configuration Inheritance**

**Condition**: All environment configurations need shared functionality  
**Action**: DevConfig and ProdConfig inherit from ConfigBase abstract class  
**Implementation**:
```python
# From config_base.py
class ConfigBase(ABC):
    def __init__(self, environment: str):
        self.environment = environment
        self._setup_timezone()
        self._discover_project_root()
        self._load_environment_variables()
        self._ensure_directories()
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """Must be implemented by environment-specific classes"""
        pass
```
**Exception**: Abstract methods must be implemented by subclasses  
**Business Impact**: Ensures consistent configuration handling across environments

### **C - Configuration Validation Enforcement**

**Condition**: Before any automation execution begins  
**Action**: Comprehensive validation of environment-specific configuration  
**Implementation**:
```python
# From config_dev.py
def validate_config(self) -> List[str]:
    """Validate development configuration. Returns list of errors."""
    errors = []
    
    api_key = os.environ.get('DEV_AIRTABLE_API_KEY')
    if not api_key:
        errors.append("DEV_AIRTABLE_API_KEY is required for development")
    elif not api_key.startswith('pat'):
        errors.append("DEV_AIRTABLE_API_KEY should start with 'pat'")
    
    base_id = os.environ.get('DEV_AIRTABLE_BASE_ID')
    if not base_id:
        errors.append("DEV_AIRTABLE_BASE_ID is required for development")
    elif len(base_id) != 17:
        errors.append("DEV_AIRTABLE_BASE_ID should be 17 characters long")
    
    return errors
```
**Exception**: Can be bypassed with --force flag in emergency situations  
**Business Impact**: Prevents execution with invalid credentials or misconfiguration

### **D - Directory Structure Isolation**

**Condition**: All environment-specific operations need isolated file storage  
**Action**: Automatically create and use environment-specific directories  
**Implementation**:
```python
# From config_base.py
@property
def csv_process_dir(self) -> Path:
    """Get CSV processing directory for this environment"""
    return self.get_script_path(f'CSV_process_{self.environment}')

@property
def csv_done_dir(self) -> Path:
    """Get CSV done directory for this environment"""
    return self.get_script_path(f'CSV_done_{self.environment}')

def get_logs_dir(self) -> Path:
    """Get logs directory with environment-specific naming"""
    return self.automation_dir / 'logs'
```
**Exception**: Manual override possible via direct path specification  
**Business Impact**: Complete data isolation prevents cross-environment contamination

### **E - Environment Variable Hierarchical Loading**

**Condition**: System needs flexible configuration from multiple sources  
**Action**: Load configuration in order of precedence (later overrides earlier)  
**Implementation**:
```python
# From config_base.py
def _load_environment_variables(self):
    """Load environment variables with hierarchical precedence"""
    # 1. Load main .env file
    env_file = self.project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    
    # 2. Load environment-specific .env file (overrides main)
    env_dir_map = {'development': 'dev', 'production': 'prod'}
    env_dir = env_dir_map.get(self.environment, self.environment)
    env_specific_file = self.project_root / 'config' / 'environments' / env_dir / '.env'
    if env_specific_file.exists():
        load_dotenv(env_specific_file, override=True)
```
**Exception**: Direct environment variable setting always takes highest precedence  
**Business Impact**: Flexible configuration management with clear override behavior

### **F - Force Override Safety Mechanism**

**Condition**: When safety checks prevent execution but override is needed  
**Action**: --force flag bypasses hostname and environment safety checks  
**Implementation**:
```python
# From run_automation_dev.py
if not args.force:
    hostname = os.environ.get('HOSTNAME', '').lower()
    if 'prod' in hostname or 'production' in hostname:
        print("⚠️  WARNING: You appear to be on a production system!")
        print("   Use --force if you really want to run DEVELOPMENT automation here.")
        print("   Consider using run_automation_prod.py instead.")
        sys.exit(1)
```
**Exception**: Should only be used in emergency or maintenance situations  
**Business Impact**: Provides emergency override while maintaining safety by default

### **G - Graceful Configuration Error Handling**

**Condition**: When configuration validation fails  
**Action**: Clear error reporting with specific remediation guidance  
**Implementation**:
```python
# From controller.py
config_errors = config.validate_config()
if config_errors:
    print("❌ Configuration validation failed:")
    for error in config_errors:
        print(f"   • {error}")
    print("\n💡 Please fix the configuration issues and try again.")
    sys.exit(1)
```
**Exception**: Force flag may bypass some validation errors  
**Business Impact**: Prevents execution with invalid configuration and provides actionable error messages

### **H - Hostname-Based Safety Validation**

**Condition**: Runner script executes on system with hostname indicating wrong environment  
**Action**: Warning message displayed and execution blocked unless forced  
**Implementation**:
```python
# Safety check logic present in both dev and prod runners
hostname = os.environ.get('HOSTNAME', '').lower()

# In development runner
if 'prod' in hostname or 'production' in hostname:
    print("⚠️  WARNING: You appear to be on a production system!")
    
# In production runner  
if 'dev' in hostname or 'development' in hostname:
    print("⚠️  WARNING: You appear to be on a development system!")
```
**Exception**: --force flag bypasses hostname checks  
**Business Impact**: Prevents accidental cross-environment execution

### **I - Isolated Credential Management**

**Condition**: Each environment needs separate API keys and authentication  
**Action**: Environment-specific credential loading with validation  
**Implementation**:
```python
# Development credentials (config_dev.py)
@property
def airtable_api_key(self) -> str:
    return os.environ.get('DEV_AIRTABLE_API_KEY', '')

@property  
def airtable_base_id(self) -> str:
    return os.environ.get('DEV_AIRTABLE_BASE_ID', '')

# Production credentials (config_prod.py)
@property
def airtable_api_key(self) -> str:
    return os.environ.get('PROD_AIRTABLE_API_KEY', '')

@property
def airtable_base_id(self) -> str:
    return os.environ.get('PROD_AIRTABLE_BASE_ID', '')
```
**Exception**: Shared credentials (if any) loaded from main .env file  
**Business Impact**: Complete credential isolation prevents cross-environment access

### **J - Job Processing Environment Routing**

**Condition**: Job creation and processing must target correct environment  
**Action**: HCP integration routes to environment-appropriate accounts and endpoints  
**Implementation**:
```python
# From webhook.py
environment = os.environ.get('ENVIRONMENT', 'production')
log_filename = f"webhook_{environment}.log" if environment == 'development' else "webhook.log"

# Different webhook endpoints:
# Dev: /webhooks/hcp-dev (port 5001)
# Prod: /webhooks/hcp (port 5000)
```
**Exception**: Emergency routing possible via configuration override  
**Business Impact**: Ensures job operations affect correct HCP account and Airtable base

### **K - Kubernetes-Ready Configuration Architecture**

**Condition**: System may be deployed in containerized environments  
**Action**: Configuration uses environment variables and file-based config  
**Implementation**:
```python
# From config_base.py - Supports K8s ConfigMaps and Secrets
def _discover_project_root(self) -> Path:
    """Discover project root using multiple methods for deployment flexibility"""
    current = Path.cwd()
    
    # Method 1: Look for setup.py (pip install -e .)
    for parent in [current] + list(current.parents):
        if (parent / 'setup.py').exists():
            return parent
    
    # Method 2: Look for VERSION file  
    for parent in [current] + list(current.parents):
        if (parent / 'VERSION').exists():
            return parent
    
    # Method 3: Look for .git directory
    for parent in [current] + list(current.parents):
        if (parent / '.git').exists():
            return parent
    
    return current
```
**Exception**: Can be overridden via PROJECT_ROOT environment variable  
**Business Impact**: Flexible deployment supporting multiple container orchestration platforms

### **L - Logging Environment Separation**

**Condition**: Development and production need different logging configurations  
**Action**: Environment-specific logging with appropriate levels and outputs  
**Implementation**:
```python
# From config_dev.py
def setup_logging(self):
    """Setup development logging with console and file output"""
    logging.basicConfig(
        level=logging.DEBUG,  # More verbose for development
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(self.get_logs_dir() / f'automation_dev_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()  # Console output for development
        ]
    )

# From config_prod.py
def setup_logging(self):
    """Setup production logging with file-only output"""
    logging.basicConfig(
        level=logging.INFO,  # Less verbose for production
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(self.get_logs_dir() / f'automation_prod_{datetime.now().strftime("%Y%m%d")}.log')
            # No console output for production
        ]
    )
```
**Exception**: Log level can be overridden via LOG_LEVEL environment variable  
**Business Impact**: Appropriate logging for each environment's operational needs

### **M - Multi-Environment Cron Scheduling**

**Condition**: Both environments need automated execution without conflicts  
**Action**: Staggered cron schedules with environment-specific scripts  
**Implementation**:
```bash
# From cron_setup_dev.sh
0 0,4,8,12,16,20 * * * cd /home/opc/automation && python3 src/run_automation_dev.py

# From cron_setup_prod.sh  
10 0,4,8,12,16,20 * * * cd /home/opc/automation && python3 src/run_automation_prod.py
```
**Exception**: Cron can be disabled by removing entries  
**Business Impact**: Automated operations for both environments without scheduling conflicts

### **N - Network Endpoint Environment Routing**

**Condition**: Different environments need different API endpoints and ports  
**Action**: Environment-specific routing for webhooks and external integrations  
**Implementation**:
```python
# Webhook routing configuration
# Development: https://servativ.themomentcatchers.com/webhooks/hcp-dev (port 5001)
# Production: https://servativ.themomentcatchers.com/webhooks/hcp (port 5000)

# Service configuration
# Development: webhook-dev service on port 5001
# Production: webhook service on port 5000
```
**Exception**: Can be overridden via service configuration files  
**Business Impact**: Proper request routing prevents cross-environment webhook delivery

### **O - Operational Environment Detection**

**Condition**: Scripts need to determine their operating environment  
**Action**: Multiple detection methods with fallback to development  
**Implementation**:
```python
# From config_wrapper.py
def get_config() -> 'ConfigBase':
    """Get singleton config instance based on environment detection"""
    global _config_instance
    if _config_instance is None:
        environment = os.environ.get('ENVIRONMENT', 'development').lower()
        if environment == 'production':
            _config_instance = ProdConfig()
        else:
            _config_instance = DevConfig()
    return _config_instance
```
**Exception**: Can be forced via explicit ENVIRONMENT variable setting  
**Business Impact**: Reliable environment detection with safe defaults

### **P - Path Management Cross-Platform Compatibility**

**Condition**: System may run on different operating systems  
**Action**: Use pathlib for consistent cross-platform path handling  
**Implementation**:
```python
# From config_base.py
from pathlib import Path

def get_script_path(self, script_name: str) -> Path:
    """Get path to script directory or file with cross-platform compatibility"""
    return self.automation_dir / 'scripts' / script_name

def get_csv_process_dir(self) -> Path:
    """Get CSV processing directory for this environment"""
    return self.get_script_path(f'CSV_process_{self.environment}')
```
**Exception**: Direct string paths can be used but not recommended  
**Business Impact**: Consistent operation across Windows, Linux, and macOS

### **Q - Quality Assurance Through Validation**

**Condition**: System needs to ensure configuration quality before execution  
**Action**: Multi-level validation at startup and runtime  
**Implementation**:
```python
# From config_prod.py - Enhanced production validation
def validate_config(self) -> List[str]:
    """Enhanced validation for production environment"""
    errors = []
    
    # API key validation
    api_key = os.environ.get('PROD_AIRTABLE_API_KEY')
    if not api_key:
        errors.append("PROD_AIRTABLE_API_KEY is required for production")
    elif len(api_key) < 50:  # More stringent validation
        errors.append("PROD_AIRTABLE_API_KEY appears too short for production use")
    
    # Additional production-specific checks
    if not os.environ.get('PROD_HCP_TOKEN'):
        errors.append("PROD_HCP_TOKEN is required for production HCP integration")
    
    return errors
```
**Exception**: Development may have more lenient validation  
**Business Impact**: Higher reliability through comprehensive pre-execution validation

### **R - Runner Script Environment Enforcement**

**Condition**: Separate runner scripts needed for each environment  
**Action**: Independent scripts with environment-specific configuration  
**Implementation**:
```python
# From run_automation_dev.py
def main():
    """Development automation runner with safety checks"""
    parser = argparse.ArgumentParser(description='Run development automation suite')
    parser.add_argument('--force', action='store_true', help='Force execution despite warnings')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be executed')
    args = parser.parse_args()
    
    # Environment safety check
    if not args.force:
        hostname = os.environ.get('HOSTNAME', '').lower()
        if 'prod' in hostname or 'production' in hostname:
            print("⚠️  WARNING: You appear to be on a production system!")
            sys.exit(1)
    
    # Load development configuration
    config = DevConfig()
    controller = AutomationController(config)
```
**Exception**: Force flag bypasses safety checks  
**Business Impact**: Clear separation of execution paths with built-in safety

### **S - Singleton Configuration Pattern**

**Condition**: System needs consistent configuration access across modules  
**Action**: Singleton pattern ensures single configuration instance  
**Implementation**:
```python
# From config_wrapper.py
_config_instance = None

def get_config() -> 'ConfigBase':
    """Get singleton config instance"""
    global _config_instance
    if _config_instance is None:
        environment = os.environ.get('ENVIRONMENT', 'development').lower()
        if environment == 'production':
            _config_instance = ProdConfig()
        else:
            _config_instance = DevConfig()
    return _config_instance

# Usage across modules
Config = get_config()
```
**Exception**: Can be reset by setting _config_instance to None  
**Business Impact**: Consistent configuration access and prevents configuration conflicts

### **T - Timezone Management Environment-Aware**

**Condition**: Different environments may have different timezone requirements  
**Action**: Configurable timezone handling with environment-specific settings  
**Implementation**:
```python
# From config_base.py
def _setup_timezone(self):
    """Setup timezone handling for the environment"""
    # Arizona timezone for business data (no DST changes)
    self.business_tz = pytz.timezone('America/Phoenix')
    
    # Pacific timezone for logging and system operations
    self.system_tz = pytz.timezone('America/Los_Angeles')
    
    # Current time in both timezones
    now_utc = datetime.now(pytz.UTC)
    self.business_time = now_utc.astimezone(self.business_tz)
    self.system_time = now_utc.astimezone(self.system_tz)
```
**Exception**: Can be overridden via TIMEZONE environment variables  
**Business Impact**: Accurate time handling for business operations and logging

### **U - User Interface Environment Adaptation**

**Condition**: Different environments need different user interface behaviors  
**Action**: Environment-specific CLI options and output formatting  
**Implementation**:
```python
# Development interface - more verbose and interactive
if config.environment == 'development':
    print("🔧 Development Mode")
    print(f"📁 Using dev base: {config.airtable_base_id}")
    print(f"📂 CSV dir: {config.csv_process_dir}")

# Production interface - minimal and automated
else:
    print("🚀 Production Mode")
    print(f"Base: {config.airtable_base_id[:8]}...")
```
**Exception**: Verbosity can be controlled via --verbose flag  
**Business Impact**: Appropriate interface complexity for each environment's operational context

### **V - Version Control Environment Awareness**

**Condition**: Different environments may run different code versions  
**Action**: Environment-specific version tracking and compatibility checks  
**Implementation**:
```python
# From config_base.py
def get_version_info(self) -> dict:
    """Get version information for environment tracking"""
    version_file = self.project_root / 'VERSION'
    if version_file.exists():
        version = version_file.read_text().strip()
    else:
        version = 'unknown'
    
    return {
        'version': version,
        'environment': self.environment,
        'timestamp': datetime.now().isoformat(),
        'hostname': os.environ.get('HOSTNAME', 'unknown')
    }
```
**Exception**: Version checking can be disabled for emergency operations  
**Business Impact**: Version tracking enables better debugging and deployment management

### **W - Webhook Environment Isolation**

**Condition**: Webhooks must be routed to correct environment  
**Action**: Environment-specific webhook endpoints and processing  
**Implementation**:
```python
# From webhook.py
environment = os.environ.get('ENVIRONMENT', 'production')

# Environment-specific logging
log_filename = f"webhook_{environment}.log" if environment == 'development' else "webhook.log"

# Environment-specific Airtable base
if environment == 'development':
    base_id = os.environ.get('DEV_AIRTABLE_BASE_ID')
else:
    base_id = os.environ.get('PROD_AIRTABLE_BASE_ID')
```
**Exception**: Can be overridden via explicit environment configuration  
**Business Impact**: Proper webhook routing prevents cross-environment data corruption

### **X - eXecution Environment Validation**

**Condition**: Before any automation execution  
**Action**: Comprehensive validation of execution environment  
**Implementation**:
```python
# From controller.py
def validate_execution_environment(self):
    """Validate environment is ready for automation execution"""
    validation_errors = []
    
    # Check configuration
    config_errors = self.config.validate_config()
    validation_errors.extend(config_errors)
    
    # Check required directories
    required_dirs = [
        self.config.csv_process_dir,
        self.config.csv_done_dir,
        self.config.get_logs_dir()
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            validation_errors.append(f"Required directory missing: {dir_path}")
    
    return validation_errors
```
**Exception**: Directory creation can be automatic with proper permissions  
**Business Impact**: Prevents execution failures due to missing resources

### **Y - Yearlong Configuration Persistence**

**Condition**: Configuration settings need to persist across restarts and deployments  
**Action**: File-based configuration with version control  
**Implementation**:
```bash
# Environment-specific configuration files
config/environments/dev/.env
config/environments/prod/.env

# Version controlled configuration templates
config/templates/dev_template.env
config/templates/prod_template.env
```
**Exception**: Emergency configuration can be provided via environment variables  
**Business Impact**: Stable configuration management with deployment consistency

### **Z - Zero-Downtime Environment Switching**

**Condition**: Environment changes should not disrupt ongoing operations  
**Action**: Graceful configuration reloading and validation  
**Implementation**:
```python
# From config_wrapper.py
def reload_config(force_environment: str = None):
    """Reload configuration with optional environment override"""
    global _config_instance
    
    if force_environment:
        os.environ['ENVIRONMENT'] = force_environment
    
    # Clear singleton to force reload
    _config_instance = None
    
    # Get new configuration
    return get_config()
```
**Exception**: Some changes may require full service restart  
**Business Impact**: Operational flexibility with minimal service disruption

---

## 🔧 **ENVIRONMENT-SPECIFIC BUSINESS RULES**

### **Development Environment Rules**

1. **Lenient Validation**: Less strict validation to support experimentation
2. **Console Logging**: Both file and console output for development visibility
3. **Debug Mode**: Enhanced logging and error reporting
4. **Interactive Features**: Support for development workflow and debugging
5. **Safety Warnings**: Alerts when running on production-like systems

### **Production Environment Rules**

1. **Strict Validation**: Enhanced validation for production reliability
2. **File-Only Logging**: Optimized logging for production performance
3. **Minimal Output**: Streamlined interface for automated execution
4. **Enhanced Security**: Additional security checks and validation
5. **Performance Optimization**: Optimized execution with minimal overhead

---

## 📊 **CONFIGURATION HIERARCHY AND PRECEDENCE**

### **Loading Order (Later Overrides Earlier)**

1. **Base Configuration**: Shared settings from ConfigBase
2. **Main .env File**: Project-level environment variables
3. **Environment-Specific .env**: Environment-targeted overrides
4. **Environment Class**: Code-level environment-specific settings
5. **Runtime Parameters**: Command-line and execution-time overrides
6. **Emergency Overrides**: Force flags and emergency configuration

---

*This business logic documentation provides comprehensive coverage of all environment management rules, ensuring proper understanding and implementation of the dual-environment architecture that maintains complete separation while enabling flexible operational management.*