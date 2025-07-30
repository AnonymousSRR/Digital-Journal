#!/usr/bin/env python
"""
Unit Test Runner for Journal Application Custom Functions

This script runs comprehensive unit tests for all custom functions in the application.
It focuses on testing isolated functions that were written specifically for this project,
not those included by default through Django.

Usage:
    python run_unit_tests.py
    python run_unit_tests.py --verbose
    python run_unit_tests.py --coverage
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()


def run_tests_with_pytest(verbose=False, coverage=False):
    """Run unit tests using pytest"""
    cmd = ['python', '-m', 'pytest']
    
    # Add test paths
    test_paths = [
        'tests/unit_tests/views/test_custom_functions.py',
        'tests/unit_tests/models/test_custom_user_manager.py',
        'tests/unit_tests/models/test_custom_user_methods.py',
        'tests/unit_tests/forms/test_custom_user_creation_form.py',
        'tests/unit_tests/forms/test_custom_authentication_form.py',
        'tests/unit_tests/models/test_custom_user.py',  # Existing tests
        'tests/unit_tests/views/test_authentication_views.py',  # Existing tests
    ]
    
    cmd.extend(test_paths)
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend([
            '--cov=authentication',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-fail-under=80'
        ])
    
    # Add pytest options for better output
    cmd.extend([
        '--tb=short',
        '--strict-markers',
        '--disable-warnings'
    ])
    
    print("Running unit tests for custom functions...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("-" * 80)
        print("✅ All unit tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 80)
        print("❌ Some unit tests failed!")
        return False


def run_tests_with_django(verbose=False):
    """Run unit tests using Django's test runner"""
    cmd = ['python', 'manage.py', 'test']
    
    # Add test paths
    test_paths = [
        'tests.unit_tests.views.test_custom_functions',
        'tests.unit_tests.models.test_custom_user_manager',
        'tests.unit_tests.models.test_custom_user_methods',
        'tests.unit_tests.forms.test_custom_user_creation_form',
        'tests.unit_tests.forms.test_custom_authentication_form',
        'tests.unit_tests.models.test_custom_user',
        'tests.unit_tests.views.test_authentication_views',
    ]
    
    cmd.extend(test_paths)
    
    if verbose:
        cmd.append('--verbosity=2')
    
    print("Running unit tests with Django test runner...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("-" * 80)
        print("✅ All unit tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 80)
        print("❌ Some unit tests failed!")
        return False


def main():
    """Main function to run unit tests"""
    parser = argparse.ArgumentParser(
        description='Run unit tests for custom functions in the journal application'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests in verbose mode'
    )
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Run tests with coverage report'
    )
    parser.add_argument(
        '--django',
        action='store_true',
        help='Use Django test runner instead of pytest'
    )
    
    args = parser.parse_args()
    
    print("🧪 Journal Application - Unit Test Runner")
    print("=" * 80)
    print("Testing custom functions (not Django defaults):")
    print("• generate_theme_prompt() - Custom API integration")
    print("• _get_active_tab() - Helper method")
    print("• _handle_signup() - Helper method")
    print("• _handle_signin() - Helper method")
    print("• CustomUserManager methods")
    print("• CustomUser model methods")
    print("• Custom form validation methods")
    print("=" * 80)
    
    if args.django:
        success = run_tests_with_django(verbose=args.verbose)
    else:
        success = run_tests_with_pytest(verbose=args.verbose, coverage=args.coverage)
    
    if success:
        print("\n🎉 Unit test execution completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Unit test execution failed!")
        sys.exit(1)


if __name__ == '__main__':
    main() 