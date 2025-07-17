# Automation Controller - Complete Business Logic Documentation

## Overview
This document provides comprehensive business-level description of the Automation Controller system, including orchestration logic, environment management, configuration handling, and workflow coordination for the property management automation platform.

## Core Business Purpose

The Automation Controller serves as the central orchestrator for all property management automation workflows. It manages environment separation, coordinates component execution, handles error recovery, and maintains comprehensive status tracking while ensuring complete isolation between development and production operations.

## Business Workflows

### 1. Central Orchestration Engine

#### **AutomationController Class Implementation**
**Business Logic for Workflow Coordination**:
```python
class AutomationController:
    """Central orchestrator for all automation workflows"""
    
    def __init__(self, config):
        """Initialize controller with environment-specific configuration"""
        self.config = config
        self.airtable = config.get_airtable()
        self.automation_table = self.airtable.table('Automation')
        self.logger = self._setup_logging()
        
        # Define automation execution map
        self.AUTOMATION_MAP = {
            'itrip-csv-gmail': self._run_itrip_gmail,
            'evolve': self._run_evolve_scraping,
            'csv-files': self._run_csv_processing,
            'ics-calendar': self._run_ics_sync,
            'add-service-jobs': self._run_hcp_job_creation,
            'sync-service-jobs': self._run_hcp_sync,
            'update-service-lines': self._run_service_line_updates,
            'job-reconciliation': self._run_job_reconciliation
        }
    
    def run_automation(self, automation_name, function):
        """Core orchestration wrapper with comprehensive status tracking"""
        
        # Check if automation is active in Airtable
        if not self.get_automation_status(automation_name):
            return {
                'success': True,
                'message': f'{automation_name} is disabled in Airtable',
                'skipped': True
            }
        
        # Execute automation with comprehensive error handling
        start_time = time.time()
        try:
            self.logger.info(f"🏃 Starting {automation_name}")
            
            # Update Airtable with "Running" status
            self._update_automation_status(automation_name, 'Running', 'Execution started')
            
            # Execute the automation function
            result = function()
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Determine final status based on result
            if result.get('success', False):
                status = 'Completed'
                message = result.get('message', 'Execution completed successfully')
                statistics = result.get('statistics', '')
            else:
                status = 'Failed'
                message = result.get('error', 'Execution failed')
                statistics = ''
            
            # Update Airtable with final status
            self._update_automation_status(
                automation_name, 
                status, 
                message, 
                statistics, 
                execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = f"Error: {str(e)}"
            
            # Log detailed error information
            self.logger.error(f"❌ {automation_name} failed: {error_message}")
            self.logger.error(traceback.format_exc())
            
            # Update Airtable with failure status
            self._update_automation_status(
                automation_name, 
                'Failed', 
                error_message, 
                '', 
                execution_time
            )
            
            return {
                'success': False,
                'error': error_message,
                'execution_time': execution_time
            }
```

#### **Automation Status Management**
**Business Logic for Airtable-Driven Control**:
```python
def get_automation_status(self, automation_name):
    """Check if automation is active in Airtable"""
    try:
        # Query automation status from Airtable
        records = self.automation_table.all(
            formula=f"{{Automation}} = '{automation_name}'"
        )
        
        if not records:
            # Default to active if not found (backward compatibility)
            self.logger.warning(f"No status record found for {automation_name}, defaulting to active")
            return True
        
        record = records[0]
        is_active = record['fields'].get('Active', True)
        
        if not is_active:
            self.logger.info(f"⏸️ {automation_name} is disabled in Airtable")
        
        return is_active
        
    except Exception as e:
        self.logger.error(f"Error checking automation status: {e}")
        # Default to active on error to prevent automation shutdown
        return True

def _update_automation_status(self, automation_name, status, message, statistics='', execution_time=None):
    """Update automation status in Airtable with comprehensive details"""
    try:
        # Find existing record or create new one
        records = self.automation_table.all(
            formula=f"{{Automation}} = '{automation_name}'"
        )
        
        update_fields = {
            'Status': status,
            'Message': message,
            'Last Updated': datetime.now().isoformat()
        }
        
        # Add optional fields if provided
        if statistics:
            update_fields['Statistics'] = statistics
        if execution_time:
            update_fields['Duration (seconds)'] = round(execution_time, 2)
        
        if records:
            # Update existing record
            record_id = records[0]['id']
            self.automation_table.update(record_id, update_fields)
        else:
            # Create new record
            update_fields['Automation'] = automation_name
            update_fields['Active'] = True  # Default new automations to active
            self.automation_table.create(update_fields)
        
        self.logger.info(f"📊 Updated {automation_name} status: {status}")
        
    except Exception as e:
        self.logger.error(f"Failed to update automation status: {e}")
        # Don't raise exception - status update failure shouldn't stop automation
```

### 2. Environment-Specific Execution Runners

#### **Development Environment Runner**
**Business Logic for Development Execution**:
```python
def main():
    """Development automation runner with safety checks and enhanced logging"""
    
    # Environment safety validation
    current_hostname = socket.gethostname().lower()
    if 'prod' in current_hostname and '--force' not in sys.argv:
        print("⚠️ WARNING: This appears to be a production-like system!")
        print("This script is for DEVELOPMENT environment only.")
        print("Use --force to override this check.")
        sys.exit(1)
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Development Automation Runner')
    parser.add_argument('--list', action='store_true', help='List all automations and their status')
    parser.add_argument('--run', type=str, help='Run specific automation')
    parser.add_argument('--dry-run', action='store_true', help='Show what would run without executing')
    parser.add_argument('--force', action='store_true', help='Force execution despite warnings')
    
    args = parser.parse_args()
    
    # Load development configuration
    try:
        from src.automation.config_dev import DevConfig
        config = DevConfig()
        
        # Validate configuration
        validation_result = config.validate()
        if not validation_result['valid']:
            print("❌ Configuration validation failed:")
            for error in validation_result['errors']:
                print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to load development configuration: {e}")
        sys.exit(1)
    
    # Set up logging for development
    log_file = config.get_log_file_path('automation_dev')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)  # Also log to console in dev
        ]
    )
    
    # Initialize automation controller
    controller = AutomationController(config)
    
    # Handle command-line operations
    if args.list:
        controller.list_automations()
        return
    
    if args.run:
        if args.dry_run:
            print(f"🔍 DRY RUN: Would execute automation '{args.run}'")
            return
        controller.run_specific(args.run)
        return
    
    # Run full automation suite
    if args.dry_run:
        print("🔍 DRY RUN: Would execute full automation suite")
        controller.list_automations()
        return
    
    print("🚀 Starting DEVELOPMENT automation suite...")
    controller.run_all()
```

#### **Production Environment Runner**
**Business Logic for Production Execution**:
```python
def main():
    """Production automation runner with production-optimized settings"""
    
    # Production environment safety validation
    current_hostname = socket.gethostname().lower()
    if 'dev' in current_hostname and '--force' not in sys.argv:
        print("⚠️ WARNING: This appears to be a development-like system!")
        print("This script is for PRODUCTION environment only.")
        print("Use --force to override this check.")
        sys.exit(1)
    
    # Load production configuration
    try:
        from src.automation.config_prod import ProdConfig
        config = ProdConfig()
        
        # Enhanced validation for production
        validation_result = config.validate()
        if not validation_result['valid']:
            print("❌ PRODUCTION configuration validation failed:")
            for error in validation_result['errors']:
                print(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to load PRODUCTION configuration: {e}")
        sys.exit(1)
    
    # Production-optimized logging (file only, no console spam)
    log_file = config.get_log_file_path('automation_prod')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file)]
    )
    
    # Initialize automation controller
    controller = AutomationController(config)
    
    # Production runs full suite by default (no interactive options)
    print("🚀 Starting PRODUCTION automation suite...")
    controller.run_all()
```

### 3. Multi-Layer Configuration Management

#### **Base Configuration Architecture**
**Business Logic for Cross-Platform Configuration**:
```python
class ConfigBase:
    """Base configuration class with intelligent project root discovery"""
    
    def __init__(self):
        """Initialize configuration with automatic environment detection"""
        
        # Discover project root intelligently
        self.project_root = self._find_project_root()
        
        # Load environment variables hierarchically
        self._load_environment_variables()
        
        # Set up timezone handling
        self.arizona_tz = pytz.timezone('America/Phoenix')
        self.logging_tz = pytz.timezone('US/Pacific')  # PST for logs
        
        # Initialize path management
        self._setup_paths()
    
    def _find_project_root(self):
        """Intelligent project root discovery"""
        current_dir = Path(__file__).parent
        
        # Look for project indicators
        indicators = ['setup.py', 'VERSION', 'CLAUDE.md', '.git']
        
        while current_dir != current_dir.parent:
            for indicator in indicators:
                if (current_dir / indicator).exists():
                    return current_dir
            current_dir = current_dir.parent
        
        # Fallback to current directory
        return Path.cwd()
    
    def _load_environment_variables(self):
        """Hierarchical environment variable loading"""
        # Load main .env file
        main_env = self.project_root / '.env'
        if main_env.exists():
            load_dotenv(main_env)
        
        # Load environment-specific .env file
        env_name = os.getenv('ENVIRONMENT', 'development')
        env_specific = self.project_root / f'config/environments/{env_name}/.env'
        if env_specific.exists():
            load_dotenv(env_specific, override=True)
        
        # Store environment name for reference
        self.environment = env_name
    
    def _setup_paths(self):
        """Configure environment-specific paths"""
        self.src_dir = self.project_root / 'src'
        self.automation_dir = self.src_dir / 'automation'
        self.scripts_dir = self.automation_dir / 'scripts'
        self.logs_dir = self.automation_dir / 'logs'
        
        # Ensure critical directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_csv_process_directory(self):
        """Get environment-specific CSV processing directory"""
        env_suffix = '_development' if self.environment == 'development' else '_production'
        return self.scripts_dir / f'CSV_process{env_suffix}'
    
    def get_csv_done_directory(self):
        """Get environment-specific CSV completion directory"""
        env_suffix = '_development' if self.environment == 'development' else '_production'
        return self.scripts_dir / f'CSV_done{env_suffix}'
    
    def get_log_file_path(self, log_name):
        """Generate timestamped log file path"""
        timestamp = datetime.now().strftime('%Y-%m-%d')
        return self.logs_dir / f'{log_name}_{timestamp}.log'
```

#### **Environment-Specific Configuration Classes**
**Business Logic for Development vs Production Settings**:
```python
class DevConfig(ConfigBase):
    """Development environment configuration"""
    
    def __init__(self):
        super().__init__()
        
        # Development-specific Airtable settings
        self.airtable_base_id = 'app67yWFv0hKdl6jM'  # Development base
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY_DEV')
        
        # Development HCP settings
        self.hcp_token = os.getenv('HCP_TOKEN_DEV')
        self.hcp_webhook_secret = os.getenv('HCP_WEBHOOK_SECRET_DEV')
        
        # Development-specific behavior
        self.debug_mode = True
        self.strict_validation = False  # More lenient for development
        self.enable_console_logging = True
    
    def validate(self):
        """Validate development configuration"""
        errors = []
        
        if not self.airtable_api_key or not self.airtable_api_key.startswith('pat'):
            errors.append("Development Airtable API key missing or invalid format")
        
        if self.airtable_base_id != 'app67yWFv0hKdl6jM':
            errors.append("Development Airtable base ID incorrect")
        
        if not self.hcp_token:
            errors.append("Development HCP token missing")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'environment': 'development'
        }

class ProdConfig(ConfigBase):
    """Production environment configuration"""
    
    def __init__(self):
        super().__init__()
        
        # Production-specific Airtable settings
        self.airtable_base_id = 'appZzebEIqCU5R9ER'  # Production base
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY_PROD')
        
        # Production HCP settings
        self.hcp_token = os.getenv('HCP_TOKEN_PROD')
        self.hcp_webhook_secret = os.getenv('HCP_WEBHOOK_SECRET_PROD')
        
        # Production-specific behavior
        self.debug_mode = False
        self.strict_validation = True  # Strict validation for production
        self.enable_console_logging = False  # File logging only
    
    def validate(self):
        """Enhanced validation for production environment"""
        errors = []
        
        if not self.airtable_api_key or not self.airtable_api_key.startswith('pat'):
            errors.append("Production Airtable API key missing or invalid format")
        
        if self.airtable_base_id != 'appZzebEIqCU5R9ER':
            errors.append("Production Airtable base ID incorrect")
        
        if not self.hcp_token:
            errors.append("Production HCP token missing")
        
        # Additional production-specific validations
        if len(self.airtable_api_key or '') < 50:
            errors.append("Production Airtable API key appears too short")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'environment': 'production'
        }
```

### 4. Component Execution and Workflow Orchestration

#### **Sequential Automation Execution**
**Business Logic for Ordered Component Processing**:
```python
def run_all(self):
    """Execute complete automation suite in proper dependency order"""
    
    self.logger.info("🚀 Starting complete automation suite")
    
    # Define execution sequence with dependencies
    automation_sequence = [
        ('itrip-csv-gmail', 'Email processing - Download iTrip CSV attachments'),
        ('evolve', 'Property data - Scrape Evolve property information'),
        ('csv-files', 'Data import - Process CSV files to Airtable'),
        ('ics-calendar', 'Calendar sync - Update ICS feed data'),
        ('add-service-jobs', 'Job creation - Create HousecallPro service jobs'),
        ('sync-service-jobs', 'Job sync - Synchronize HCP job statuses'),
        ('update-service-lines', 'Service updates - Update service descriptions'),
        ('job-reconciliation', 'Post-processing - Match orphaned jobs')
    ]
    
    # Track overall suite execution
    suite_start_time = time.time()
    total_success = True
    execution_summary = []
    
    for automation_name, description in automation_sequence:
        self.logger.info(f"📋 {description}")
        
        try:
            # Execute automation component
            result = self.run_automation(automation_name, self.AUTOMATION_MAP[automation_name])
            
            # Track result for summary
            execution_summary.append({
                'automation': automation_name,
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'skipped': result.get('skipped', False),
                'execution_time': result.get('execution_time', 0)
            })
            
            if not result.get('success', False) and not result.get('skipped', False):
                total_success = False
                self.logger.warning(f"⚠️ {automation_name} failed but continuing suite execution")
        
        except Exception as e:
            total_success = False
            self.logger.error(f"❌ Critical error in {automation_name}: {e}")
            execution_summary.append({
                'automation': automation_name,
                'success': False,
                'message': f"Critical error: {str(e)}",
                'skipped': False,
                'execution_time': 0
            })
    
    # Calculate total execution time
    total_execution_time = time.time() - suite_start_time
    
    # Generate execution summary
    self._log_execution_summary(execution_summary, total_execution_time, total_success)
    
    return {
        'success': total_success,
        'execution_summary': execution_summary,
        'total_execution_time': total_execution_time
    }

def _log_execution_summary(self, execution_summary, total_time, overall_success):
    """Generate comprehensive execution summary"""
    
    self.logger.info("=" * 60)
    self.logger.info("🎯 AUTOMATION SUITE EXECUTION SUMMARY")
    self.logger.info("=" * 60)
    
    successful_count = sum(1 for item in execution_summary if item['success'])
    failed_count = sum(1 for item in execution_summary if not item['success'] and not item['skipped'])
    skipped_count = sum(1 for item in execution_summary if item['skipped'])
    
    self.logger.info(f"📊 Results: {successful_count} successful, {failed_count} failed, {skipped_count} skipped")
    self.logger.info(f"⏱️ Total execution time: {total_time:.2f} seconds")
    self.logger.info(f"🎯 Overall status: {'SUCCESS' if overall_success else 'PARTIAL FAILURE'}")
    
    # Detail each automation result
    for item in execution_summary:
        status_icon = "✅" if item['success'] else "⏸️" if item['skipped'] else "❌"
        self.logger.info(f"{status_icon} {item['automation']}: {item['message']}")
    
    self.logger.info("=" * 60)
```

#### **Individual Component Execution**
**Business Logic for Component-Specific Processing**:
```python
def _run_csv_processing(self):
    """Execute CSV processing with environment isolation"""
    script_path = self.config.scripts_dir / 'CSVtoAirtable/csvProcess.py'
    
    # Set environment variables for subprocess
    env = os.environ.copy()
    env['ENVIRONMENT'] = self.config.environment
    
    try:
        # Execute CSV processing script
        result = subprocess.run(
            ['python3', str(script_path)],
            capture_output=True,
            text=True,
            env=env,
            timeout=300  # 5-minute timeout
        )
        
        if result.returncode == 0:
            # Parse statistics from output
            statistics = self._extract_csv_statistics(result.stdout)
            return {
                'success': True,
                'message': 'CSV processing completed successfully',
                'statistics': statistics
            }
        else:
            return {
                'success': False,
                'error': f'CSV processing failed: {result.stderr}',
                'output': result.stdout
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'CSV processing timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error executing CSV processing: {str(e)}'
        }

def _extract_csv_statistics(self, output):
    """Extract meaningful statistics from CSV processing output"""
    statistics = []
    
    # Look for specific patterns in output
    if 'Total files processed:' in output:
        match = re.search(r'Total files processed: (\d+)', output)
        if match:
            statistics.append(f"Files processed: {match.group(1)}")
    
    if 'Reservations created:' in output:
        match = re.search(r'Reservations created: (\d+)', output)
        if match:
            statistics.append(f"Reservations created: {match.group(1)}")
    
    if 'Duplicates found:' in output:
        match = re.search(r'Duplicates found: (\d+)', output)
        if match:
            statistics.append(f"Duplicates found: {match.group(1)}")
    
    return ', '.join(statistics) if statistics else 'Processing completed'
```

## Critical Business Rules

### Automation Control Rules
1. **Airtable-Driven Control**: All automations respect active/inactive status in Airtable
2. **Graceful Degradation**: Individual automation failures don't stop entire suite
3. **Status Persistence**: All execution results stored in Airtable for audit trail
4. **Environment Safety**: Cross-environment execution prevented by hostname validation

### Environment Separation Rules
1. **Complete Isolation**: Dev and prod environments have separate credentials, bases, and data
2. **Configuration Validation**: Environment-specific validation prevents misconfiguration
3. **Safety Checks**: Hostname-based warnings prevent accidental cross-environment execution
4. **Independent Logging**: Separate log files prevent cross-environment contamination

### Execution Order Rules
1. **Sequential Dependencies**: Automations execute in dependency order
2. **Error Isolation**: Component failures don't cascade to other components
3. **Status Tracking**: Real-time status updates during execution
4. **Timeout Management**: Individual components have timeout protection

### Configuration Management Rules
1. **Hierarchical Loading**: Main .env files override by environment-specific files
2. **Validation Required**: All configurations must pass validation before execution
3. **Path Management**: Cross-platform path handling using pathlib
4. **Credential Isolation**: Complete separation of dev/prod API keys and secrets

## Error Handling Patterns

### Controller-Level Errors
- **Configuration failures** trigger immediate exit with validation details
- **Component timeouts** logged with specific timeout duration
- **Status update failures** logged but don't stop automation execution
- **Critical system errors** captured with full stack traces

### Component-Level Errors
- **Process failures** captured with return codes and error output
- **Timeout errors** handled with graceful termination and cleanup
- **Partial failures** (like ICS sync) reported with detailed error breakdown
- **Resource errors** handled with appropriate fallback behavior

### Recovery Patterns
- **Status tracking** allows manual retry of failed automations
- **Component isolation** prevents cascading failures
- **Detailed logging** enables post-mortem analysis
- **Graceful degradation** maintains system availability

---

**Document Version**: 1.0.0
**Last Updated**: July 12, 2025
**Scope**: Complete Automation Controller business logic
**Primary Code**: Controller orchestration and environment management systems