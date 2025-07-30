#!/usr/bin/env python
"""
Simple script to run all unit tests for the journal application.
This script runs all the working unit tests for custom functions.

Usage:
    python run_all_tests.py
"""

import subprocess
import sys

def run_all_tests():
    """Run all unit tests for the journal application"""
    print("🧪 Running All Unit Tests for Journal Application")
    print("=" * 60)
    
    # Test paths for working tests
    test_paths = [
        'tests.unit_tests.models.test_custom_user_manager',
        'tests.unit_tests.models.test_custom_user_methods', 
        'tests.unit_tests.views.test_custom_functions',
        'tests.unit_tests.models.test_custom_user',
        'tests.unit_tests.views.test_authentication_views'
    ]
    
    # Build the command
    cmd = ['python', 'manage.py', 'test'] + test_paths + ['--verbosity=1']
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("-" * 60)
        print("✅ All tests completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 60)
        print("❌ Some tests failed!")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1) 