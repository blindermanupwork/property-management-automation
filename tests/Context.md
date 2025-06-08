# /home/opc/automation/tests/

## Purpose
This directory contains comprehensive test suites for the property management automation system, including unit tests, integration tests, end-to-end scenarios, and specialized business logic validation. The tests provide confidence in system reliability and catch regressions during development.

## Key Files and What They Do

### **Comprehensive Test Suites**
- `comprehensive-e2e-test.py` - End-to-end testing across the entire system
- `comprehensive-scenario-tests.py` - Real-world scenario testing with sample data
- `boris-dev-comprehensive-tests.py` - Development environment specific comprehensive tests
- `dev-comprehensive-tests.cjs` - Node.js based development tests

### **Business Logic Tests**
- `critical-business-logic-tests.py` - Tests for core business operations
- `happy-path-business-logic-tests.py` - Positive test cases for standard workflows
- `ics-processing-edge-case-tests.py` - Edge case testing for ICS calendar processing

### **Dynamic Testing**
- `dynamic-test-generator.py` - Generates test cases based on current system state

## How to Use the Code

### **Running Test Suites**

#### **Complete Test Suite**
```bash
# Run all Python tests
python3 -m pytest tests/ -v

# Run tests with coverage reporting
python3 -m pytest tests/ --cov=automation --cov-report=html

# Run specific test file
python3 -m pytest tests/comprehensive-e2e-test.py -v

# Run with detailed output
python3 -m pytest tests/ -v -s
```

#### **Individual Test Execution**
```bash
# Run comprehensive end-to-end tests
cd tests/
python3 comprehensive-e2e-test.py

# Run business logic tests
python3 critical-business-logic-tests.py
python3 happy-path-business-logic-tests.py

# Run ICS processing edge cases
python3 ics-processing-edge-case-tests.py

# Run development-specific tests
python3 boris-dev-comprehensive-tests.py
```

#### **Node.js Tests**
```bash
# Run Node.js based tests
cd tests/
node dev-comprehensive-tests.cjs
```

### **Test Development Patterns**

#### **Basic Test Structure**
```python
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.automation.config_wrapper import Config
from src.automation.controller import AutomationController

class TestAutomationComponent:
    def setup_method(self):
        """Setup before each test method"""
        self.config = Config
        self.controller = AutomationController(self.config)
    
    def test_basic_functionality(self):
        """Test basic component functionality"""
        result = self.controller.get_automation_status("test_automation")
        assert isinstance(result, bool)
    
    def test_error_handling(self):
        """Test error conditions"""
        with pytest.raises(ValueError):
            self.controller.invalid_operation()
```

#### **End-to-End Test Pattern**
```python
def test_complete_workflow():
    """Test complete data processing workflow"""
    # 1. Setup test data
    test_csv_file = create_test_csv()
    
    # 2. Process through system
    result = process_csv_file(test_csv_file)
    
    # 3. Verify results
    assert result['status'] == 'success'
    assert result['records_processed'] > 0
    
    # 4. Cleanup
    cleanup_test_data()
```

### **Test Configuration**

#### **Environment-Specific Testing**
```python
# Test development environment
from src.automation.config_dev import DevConfig
dev_config = DevConfig()
dev_controller = AutomationController(dev_config)

# Test production environment (use with caution)
from src.automation.config_prod import ProdConfig
prod_config = ProdConfig()
# Note: Production tests should use test data only
```

## Dependencies and Requirements

### **Testing Framework Dependencies**
- `pytest` - Primary testing framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `requests-mock` - HTTP request mocking

### **System Testing Dependencies**
- All main automation dependencies
- Test data files and fixtures
- Mock API servers for integration testing
- Temporary file system access

### **Installation**
```bash
# Install testing dependencies
pip3 install pytest pytest-cov pytest-mock requests-mock

# Install development dependencies
pip3 install -e ".[dev]"

# Or install all requirements
pip3 install -r requirements.txt
```

## Common Workflows and Operations

### **Development Testing Workflow**
```bash
# 1. Run quick unit tests during development
python3 -m pytest tests/ -k "not slow" -v

# 2. Run full test suite before commits
python3 -m pytest tests/ -v

# 3. Generate coverage report
python3 -m pytest tests/ --cov=automation --cov-report=html
open htmlcov/index.html  # View coverage report

# 4. Run specific test categories
python3 -m pytest tests/ -k "business_logic" -v
python3 -m pytest tests/ -k "integration" -v
```

### **Continuous Integration Workflow**
```bash
# CI pipeline test commands
python3 -m pytest tests/ --cov=automation --cov-fail-under=80
python3 -m pytest tests/ --junitxml=test-results.xml
python3 -m pytest tests/ --cov=automation --cov-report=xml
```

### **Debug and Troubleshooting Workflow**
```bash
# Run tests with debug output
python3 -m pytest tests/ -v -s --tb=long

# Run single test with pdb debugger
python3 -m pytest tests/test_specific.py::test_function -v -s --pdb

# Run tests with logging output
python3 -m pytest tests/ -v -s --log-cli-level=DEBUG
```

## Key Test Categories

### **Unit Tests**
Located within individual test files, testing isolated components:
- Configuration system validation
- Controller functionality
- Utility functions
- Data processing logic

### **Integration Tests**
Testing interaction between components:
- Airtable API integration
- HousecallPro API integration
- File system operations
- Email processing workflows

### **End-to-End Tests**
Complete workflow testing:
- CSV download → processing → Airtable sync
- Evolve scraping → data transformation → storage
- ICS processing → calendar updates
- Service job creation → HousecallPro sync

### **Business Logic Tests**
Critical business rule validation:
- Reservation data processing
- Customer matching algorithms
- Service scheduling logic
- Data deduplication rules

### **Edge Case Tests**
Boundary condition and error scenario testing:
- Malformed CSV files
- Network connectivity issues
- API rate limiting
- Invalid data formats

## Test Data Management

### **Test Data Patterns**
```python
# Create test CSV data
def create_test_csv():
    test_data = [
        {
            'Property Name': 'Test Property',
            'Reservation UID': 'TEST_UID_001',
            'Guest Name': 'Test Guest',
            'Check-in': '2025-06-10',
            'Check-out': '2025-06-12'
        }
    ]
    return generate_csv_file(test_data)

# Mock API responses
@pytest.fixture
def mock_airtable_response():
    return {
        'records': [
            {
                'id': 'rec123',
                'fields': {
                    'Property Name': 'Test Property',
                    'Status': 'Active'
                }
            }
        ]
    }
```

### **Test Environment Setup**
```python
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup clean test environment for each test"""
    # Create temporary directories
    test_dirs = create_test_directories()
    
    # Setup test configuration
    setup_test_config()
    
    yield test_dirs
    
    # Cleanup after test
    cleanup_test_directories(test_dirs)
```

## Specialized Test Suites

### **Boris Development Tests**
`boris-dev-comprehensive-tests.py` - Specialized tests for development environment:
- Development-specific configuration testing
- Dev Airtable base integration
- Local file system testing
- Development API endpoint testing

### **ICS Processing Edge Cases**
`ics-processing-edge-case-tests.py` - Specialized calendar processing tests:
- Malformed ICS files
- Timezone edge cases
- Recurring event processing
- Calendar format variations

### **Dynamic Test Generation**
`dynamic-test-generator.py` - Generates tests based on current system state:
- Property-specific test cases
- Customer data variations
- Current reservation scenarios
- Live system state testing

## Best Practices

### **Test Writing Guidelines**
```python
# 1. Descriptive test names
def test_csv_processor_handles_missing_property_name():
    """Test that CSV processor gracefully handles missing property names"""
    pass

# 2. Arrange-Act-Assert pattern
def test_reservation_creation():
    # Arrange
    reservation_data = create_test_reservation()
    
    # Act
    result = process_reservation(reservation_data)
    
    # Assert
    assert result['status'] == 'created'
    assert 'id' in result

# 3. Proper cleanup
def test_file_processing():
    test_file = create_temp_file()
    try:
        result = process_file(test_file)
        assert result is not None
    finally:
        os.remove(test_file)
```

### **Mocking Best Practices**
```python
# Mock external API calls
@patch('requests.get')
def test_api_integration(mock_get):
    mock_get.return_value.json.return_value = {'status': 'success'}
    
    result = call_external_api()
    assert result['status'] == 'success'
    mock_get.assert_called_once()

# Mock file system operations
@patch('pathlib.Path.exists')
def test_file_handling(mock_exists):
    mock_exists.return_value = True
    
    result = check_file_exists('test.csv')
    assert result is True
```

### **Test Organization**
- **One test file per module** being tested
- **Group related tests** in test classes
- **Use descriptive test names** that explain what is being tested
- **Include both positive and negative test cases**
- **Test edge cases and error conditions**

## Performance Testing

### **Load Testing Patterns**
```python
def test_csv_processing_performance():
    """Test CSV processing with large files"""
    large_csv = create_large_test_csv(rows=10000)
    
    start_time = time.time()
    result = process_csv(large_csv)
    processing_time = time.time() - start_time
    
    assert processing_time < 30  # Should complete within 30 seconds
    assert result['status'] == 'success'
```

### **Memory Usage Testing**
```python
import psutil
import os

def test_memory_usage():
    """Test that processing doesn't consume excessive memory"""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    process_large_dataset()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Should not increase memory by more than 100MB
    assert memory_increase < 100 * 1024 * 1024
```

## Troubleshooting Tests

### **Common Test Issues**
```bash
# Tests failing due to missing dependencies
pip3 install -r requirements.txt

# Tests failing due to configuration issues
python3 test_setup.py

# Tests failing due to permission issues
chmod 755 tests/
chmod 644 tests/*.py

# Tests failing due to import issues
export PYTHONPATH=/home/opc/automation:$PYTHONPATH
```

### **Debug Commands**
```bash
# Run tests with verbose output
python3 -m pytest tests/ -v -s

# Run specific test with debugging
python3 -m pytest tests/test_file.py::test_function -v -s --pdb

# Generate detailed test report
python3 -m pytest tests/ --html=test-report.html --self-contained-html
```