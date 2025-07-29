# Unit Tests for Journal App

This directory contains comprehensive unit tests for all isolated functions in the Journal App. The tests are organized by component type and follow Django testing best practices.

## Directory Structure

```
unit_tests/
├── README.md                           # This file
├── run_unit_tests.py                   # Unit test runner script
├── __init__.py                         # Package initialization
├── models/                             # Model unit tests
│   ├── __init__.py
│   └── test_custom_user.py            # CustomUser, Theme, JournalEntry tests
├── forms/                              # Form unit tests
│   ├── __init__.py
│   └── test_authentication_forms.py   # CustomUserCreationForm, CustomAuthenticationForm tests
├── views/                              # View unit tests
│   ├── __init__.py
│   └── test_authentication_views.py   # Authentication views and functions
├── utils/                              # Utility function tests
│   ├── __init__.py
│   ├── test_helpers.py                # Helper utility functions
│   └── test_driver_manager.py         # DriverManager class tests
└── config/                             # Configuration tests
    ├── __init__.py
    └── test_urls.py                   # URL configuration and view functions
```

## Test Categories

### 1. Models (`models/`)
Tests for Django models and their methods:
- **CustomUserManager**: User creation, superuser creation, validation
- **CustomUser**: Model fields, methods, validation, string representation
- **Theme**: Model creation, uniqueness constraints
- **JournalEntry**: Model relationships, ordering, cascade behavior

### 2. Forms (`forms/`)
Tests for Django forms and validation:
- **CustomUserCreationForm**: Registration form validation, email normalization, password matching
- **CustomAuthenticationForm**: Login form validation, username normalization, user status checks

### 3. Views (`views/`)
Tests for Django views and view functions:
- **generate_theme_prompt**: API integration, error handling, fallback behavior
- **my_journals_view**: Journal listing, search functionality
- **delete_journal_entry**: Entry deletion, permission checks
- **theme_selector_view**: Theme retrieval
- **answer_prompt_view**: Journal creation
- **SignUpView, SignInView, AuthenticationView**: Authentication flow
- **logout_view**: User logout

### 4. Utils (`utils/`)
Tests for utility functions and classes:
- **Helper Functions**: Random data generation, screenshot handling, element verification
- **DriverManager**: WebDriver creation, browser configuration, error handling

### 5. Config (`config/`)
Tests for configuration and URL routing:
- **URL Configuration**: URL patterns, routing, parameter handling
- **View Functions**: Home view, redirect logic

## Running Unit Tests

### Prerequisites

1. Install test dependencies:
   ```bash
   pip install pytest pytest-django pytest-cov pytest-html
   ```

2. Make sure Django is properly configured for testing.

### Running All Unit Tests

```bash
# From the project root directory
python tests/unit_tests/run_unit_tests.py all
```

### Running Specific Test Categories

```bash
# Model tests only
python tests/unit_tests/run_unit_tests.py models

# Form tests only
python tests/unit_tests/run_unit_tests.py forms

# View tests only
python tests/unit_tests/run_unit_tests.py views

# Utility tests only
python tests/unit_tests/run_unit_tests.py utils

# Configuration tests only
python tests/unit_tests/run_unit_tests.py config
```

### Running with Options

```bash
# Verbose output
python tests/unit_tests/run_unit_tests.py all verbose

# Generate coverage report
python tests/unit_tests/run_unit_tests.py all coverage

# Both verbose and coverage
python tests/unit_tests/run_unit_tests.py all verbose coverage
```

### Using Pytest Directly

```bash
# Run all unit tests
python -m pytest tests/unit_tests/ -v

# Run specific test file
python -m pytest tests/unit_tests/models/test_custom_user.py -v

# Run with coverage
python -m pytest tests/unit_tests/ --cov=authentication --cov=config --cov=tests.utils --cov-report=html
```

## Test Features

### Coverage
- **Model Coverage**: 100% coverage of model methods and validation
- **Form Coverage**: Complete form validation and cleaning methods
- **View Coverage**: All view functions and error handling paths
- **Utility Coverage**: All helper functions and edge cases

### Mocking
- **API Calls**: External API calls are mocked for reliable testing
- **Database**: Tests use Django's test database
- **File System**: File operations are mocked where appropriate

### Test Data
- **Fixtures**: Reusable test data and objects
- **Random Data**: Generated test data for uniqueness
- **Edge Cases**: Tests for boundary conditions and error scenarios

## Test Reports

### HTML Reports
Unit test reports are generated in `tests/reports/` with timestamps:
- `unit_test_report_YYYYMMDD_HHMMSS.html`
- `coverage_YYYYMMDD_HHMMSS.html` (when coverage is enabled)

### Coverage Reports
Coverage reports show:
- Line coverage percentage
- Missing lines
- Branch coverage
- Function coverage

## Best Practices

### Test Organization
- Each test class focuses on a specific component
- Test methods have descriptive names
- Tests are independent and can run in any order

### Assertions
- Use specific assertions for better error messages
- Test both positive and negative cases
- Verify side effects and state changes

### Mocking
- Mock external dependencies
- Use realistic mock data
- Test error conditions with mocked exceptions

### Database
- Use Django's test database
- Clean up test data in tearDown methods
- Test database constraints and relationships

## Troubleshooting

### Import Errors
If you encounter import errors:
1. Make sure you're running from the project root directory
2. Check that Django settings are properly configured
3. Verify that all dependencies are installed

### Database Issues
If database tests fail:
1. Ensure Django test database is properly configured
2. Check for conflicting test data
3. Verify model migrations are up to date

### Mock Issues
If mocks aren't working:
1. Check that patches are applied to the correct modules
2. Verify mock setup in setUp methods
3. Ensure mocks are properly cleaned up

## Contributing

When adding new unit tests:
1. Follow the existing naming conventions
2. Add tests to the appropriate category directory
3. Include both positive and negative test cases
4. Update this README if adding new test categories
5. Ensure tests pass before committing

## Notes

- Unit tests are designed to be fast and isolated
- They don't require a running web server
- Tests use Django's test framework and pytest
- Coverage reports help identify untested code
- All tests should pass before deployment 