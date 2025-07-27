# Journal App Automation Tests

This directory contains the automation test suite for the Journal App. The tests have been moved from the separate "Journal-App-Automation" folder into the main project structure.

## Directory Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Pytest configuration and fixtures
├── test_journal_app.py          # Main test file with all test cases
├── run_tests.py                 # Test runner script
├── generate_report.py           # Custom report generator
├── setup.py                     # Test setup configuration
├── requirements_automation.txt  # Automation-specific dependencies
├── config/
│   ├── __init__.py
│   └── settings.py              # Test configuration settings
├── pages/
│   ├── __init__.py
│   ├── base_page.py             # Base page object class
│   ├── auth_page.py             # Authentication page object
│   ├── home_page.py             # Home page object
│   ├── theme_selector_page.py   # Theme selector page object
│   ├── answer_prompt_page.py    # Answer prompt page object
│   └── my_journals_page.py      # My journals page object
├── utils/
│   ├── __init__.py
│   ├── driver_manager.py        # WebDriver management
│   └── helpers.py               # Helper utilities
├── reports/                     # Generated test reports
└── screenshots/                 # Screenshots on test failures
```

## Running Tests

### Prerequisites

1. Install the automation dependencies:
   ```bash
   pip install -r tests/requirements_automation.txt
   ```

2. Make sure the Django development server is running:
   ```bash
   python manage.py runserver
   ```

### Running All Tests

```bash
# From the project root directory
python tests/run_tests.py all
```

### Running Specific Test Categories

```bash
# Authentication tests only
python tests/run_tests.py auth

# Smoke tests only
python tests/run_tests.py smoke
```

### Running with Different Browsers

```bash
# Chrome (default)
python tests/run_tests.py all chrome

# Firefox
python tests/run_tests.py all firefox

# Edge
python tests/run_tests.py all edge
```

### Running in Headless Mode

```bash
python tests/run_tests.py all chrome headless
```

### Using Pytest Directly

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_journal_app.py -v

# Run tests with specific markers
python -m pytest tests/ -m auth -v
python -m pytest tests/ -m smoke -v
```

## Test Categories

- **auth**: Authentication-related tests
- **smoke**: Critical functionality tests
- **home**: Home page tests
- **theme**: Theme selection tests
- **journal**: Journal creation tests
- **my_journals**: My journals page tests

## Configuration

Test configuration is managed in `tests/config/settings.py`. Key settings include:

- `BASE_URL`: The base URL for the application
- `BROWSER`: Default browser (chrome, firefox, edge)
- `HEADLESS`: Whether to run in headless mode
- `IMPLICIT_WAIT`: Default wait time for elements
- `WINDOW_WIDTH` and `WINDOW_HEIGHT`: Browser window dimensions

## Reports and Screenshots

- HTML reports are generated in the `tests/reports/` directory
- Screenshots on test failures are saved in the `tests/screenshots/` directory
- Reports include metadata about browser, test type, and execution time

## Troubleshooting

1. **WebDriver Issues**: Make sure you have the appropriate browser installed and the webdriver-manager package is installed.

2. **Import Errors**: If you encounter import errors, make sure you're running the tests from the project root directory.

3. **Server Not Running**: Ensure the Django development server is running on the configured URL before running tests.

4. **Browser Compatibility**: Some tests may behave differently across browsers. Chrome is the recommended browser for testing.

## Notes

- The existing `authentication/tests.py` file remains unchanged and contains Django unit tests
- This automation test suite is separate from the Django unit tests and focuses on end-to-end testing
- All import paths have been updated to work with the new folder structure 