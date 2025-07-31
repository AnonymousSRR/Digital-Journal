# Unit Tests for Journal Application

This directory contains comprehensive unit tests for all custom functions in the journal application. These tests focus specifically on functions that were written for this project, not those included by default through Django.

## Test Structure

```
tests/unit_tests/
├── __init__.py
├── README.md
├── run_unit_tests.py
├── views/
│   ├── test_custom_functions.py      # Tests for custom view functions
│   └── test_authentication_views.py  # Existing view tests
├── models/
│   ├── test_custom_user_manager.py   # Tests for CustomUserManager
│   ├── test_custom_user_methods.py   # Tests for CustomUser methods
│   └── test_custom_user.py           # Existing model tests
└── forms/
    ├── test_custom_user_creation_form.py    # Tests for signup form
    └── test_custom_authentication_form.py   # Tests for login form
```

## Test Logs

All test execution logs are stored in the `test_logs/` directory at the project root:

```
test_logs/
├── README.md                          # Documentation for test logs
├── test_log_20250730_231308.txt      # Example log file
├── test_log_20250731_082954.txt      # Latest log file
└── ...                                # Historical logs
```

### Test Log Features
- **Automatic Organization**: All logs are automatically saved to `test_logs/` folder
- **Timestamped Files**: Each log is named with timestamp: `test_log_YYYYMMDD_HHMMSS.txt`
- **Complete Output**: Logs contain both stdout and stderr from test execution
- **Performance Tracking**: Includes execution duration and test statistics
- **Historical Record**: Maintains history of all test runs for debugging

### Managing Test Logs
```bash
# List recent test logs
python list_test_logs.py

# View specific log file
cat test_logs/test_log_20250731_082954.txt

# Clean up old logs (keep last 30 days)
find test_logs/ -name "test_log_*.txt" -mtime +30 -delete
```

## Custom Functions Tested

### Views (`views/test_custom_functions.py`)
- **`generate_theme_prompt(theme_name, theme_description)`**
  - Tests API integration with Cohere
  - Tests fallback behavior when API fails
  - Tests response cleaning and normalization
  - Tests theme-specific examples

- **`AuthenticationView._get_active_tab()`**
  - Tests tab detection from GET parameters
  - Tests tab detection from POST form actions
  - Tests default tab behavior

- **`AuthenticationView._handle_signup()`**
  - Tests successful user creation
  - Tests error handling during user creation
  - Tests success/error message generation

- **`AuthenticationView._handle_signin()`**
  - Tests successful authentication
  - Tests invalid credentials handling
  - Tests login process and message generation

### Models (`models/test_custom_user_manager.py`)
- **`CustomUserManager.create_user()`**
  - Tests user creation with valid data
  - Tests email normalization
  - Tests validation errors
  - Tests optional password handling

- **`CustomUserManager.create_superuser()`**
  - Tests superuser creation
  - Tests required flag validation
  - Tests email normalization

### Models (`models/test_custom_user_methods.py`)
- **`CustomUser.get_full_name()`**
  - Tests full name generation
  - Tests handling of empty names
  - Tests whitespace handling

- **`CustomUser.get_short_name()`**
  - Tests short name generation
  - Tests empty name handling

- **`CustomUser.clean()`**
  - Tests email normalization
  - Tests whitespace handling

- **`CustomUser.save()`**
  - Tests that save calls clean method
  - Tests field preservation

### Forms (`forms/test_custom_user_creation_form.py`)
- **`CustomUserCreationForm.clean_email()`**
  - Tests email validation
  - Tests duplicate email detection
  - Tests email normalization

- **`CustomUserCreationForm.clean()`**
  - Tests password matching validation
  - Tests form-level validation

- **`CustomUserCreationForm.save()`**
  - Tests user creation
  - Tests email normalization
  - Tests commit behavior

### Forms (`forms/test_custom_authentication_form.py`)
- **`CustomAuthenticationForm.clean_username()`**
  - Tests email normalization
  - Tests whitespace handling

- **`CustomAuthenticationForm.confirm_login_allowed()`**
  - Tests active user validation
  - Tests inactive user rejection

## Running the Tests

### Using the Comprehensive Test Runner (Recommended)
```bash
# Run all tests with detailed logging
python run_tests_with_log.py

# This will:
# - Run all 101 unit tests
# - Save detailed log to test_logs/ folder
# - Display real-time progress
# - Show summary with pass/fail counts
```

### Using the Test Runner Script
```bash
# Run all unit tests
python tests/unit_tests/run_unit_tests.py

# Run with verbose output
python tests/unit_tests/run_unit_tests.py --verbose

# Run with coverage report
python tests/unit_tests/run_unit_tests.py --coverage

# Use Django test runner instead of pytest
python tests/unit_tests/run_unit_tests.py --django
```

### Using pytest directly
```bash
# Run all unit tests
python -m pytest tests/unit_tests/

# Run specific test file
python -m pytest tests/unit_tests/views/test_custom_functions.py

# Run with coverage
python -m pytest tests/unit_tests/ --cov=authentication --cov-report=html
```

### Using Django test runner
```bash
# Run all unit tests
python manage.py test tests.unit_tests

# Run specific test module
python manage.py test tests.unit_tests.views.test_custom_functions

# Run with verbose output
python manage.py test tests.unit_tests --verbosity=2
```

## Test Coverage

The unit tests are designed to achieve high coverage of custom functions:

- **API Integration**: Tests for `generate_theme_prompt()` cover successful API calls, error handling, and fallback behavior
- **Form Validation**: Comprehensive tests for custom form validation methods
- **Model Methods**: Tests for all custom model methods and manager functions
- **View Helpers**: Tests for helper methods in view classes
- **Edge Cases**: Tests for error conditions, empty values, and boundary cases

## Test Data

Each test file includes proper setup and teardown methods:
- Test data is created in `setUp()` methods
- Database is cleaned between tests
- Mock objects are used for external dependencies (API calls)
- Real database operations are tested where appropriate

## Best Practices

1. **Isolation**: Each test is independent and doesn't rely on other tests
2. **Mocking**: External dependencies (like API calls) are mocked
3. **Edge Cases**: Tests cover error conditions and boundary cases
4. **Descriptive Names**: Test method names clearly describe what is being tested
5. **Documentation**: Each test includes a docstring explaining its purpose
6. **Logging**: All test runs are logged for debugging and historical tracking

## Adding New Tests

When adding new custom functions to the application:

1. Create a new test file in the appropriate directory
2. Follow the naming convention: `test_<module_name>.py`
3. Use descriptive test method names
4. Include tests for both success and failure cases
5. Mock external dependencies
6. Add the new test file to `run_unit_tests.py`

## Dependencies

The tests require:
- `pytest` for test running
- `pytest-cov` for coverage reporting (optional)
- `unittest.mock` for mocking (included in Python standard library)

Install test dependencies:
```bash
pip install pytest pytest-cov
``` 