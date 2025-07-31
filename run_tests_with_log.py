#!/usr/bin/env python
"""
Comprehensive Test Runner with Detailed Logging
This script runs all unit tests and generates a detailed log of each test case with its status.
"""

import subprocess
import sys
import json
import time
import re
import os
from datetime import datetime
from pathlib import Path

def run_tests_with_detailed_logging():
    """Run all tests with detailed logging and status tracking"""
    
    print("🧪 COMPREHENSIVE UNIT TEST RUNNER")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Ensure test_logs directory exists
    test_logs_dir = Path("test_logs")
    test_logs_dir.mkdir(exist_ok=True)
    
    # List all test modules to run
    test_modules = [
        'tests.unit_tests.models.test_custom_user_manager',
        'tests.unit_tests.models.test_custom_user_methods', 
        'tests.unit_tests.views.test_custom_functions',
        'tests.unit_tests.models.test_custom_user',
        'tests.unit_tests.views.test_authentication_views',
        'tests.unit_tests.forms.test_custom_user_creation_form',
        'tests.unit_tests.forms.test_custom_authentication_form',
        'tests.unit_tests.authentication.models.test_time_formatting'
    ]
    
    print("\n📁 Running All Tests...")
    print("-" * 60)
    
    cmd = [
        'python', 'manage.py', 'test'
    ] + test_modules + [
        '--verbosity=2', '--noinput'
    ]
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300  # 5 minute timeout
        )
        end_time = time.time()
        duration = end_time - start_time
        
        # Get the output
        output_lines = result.stdout.split('\n')
        error_lines = result.stderr.split('\n')
        
        # Save the complete output to file in test_logs directory
        log_filename = test_logs_dir / f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        save_complete_log(output_lines, error_lines, log_filename, duration)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📋 TEST EXECUTION SUMMARY")
        print("=" * 80)
        
        print(f"⏱️  Total Duration: {duration:.2f}s")
        print(f"📊 Exit Code: {result.returncode}")
        print(f"✅ Overall Result: {'SUCCESS' if result.returncode == 0 else 'FAILURE'}")
        print(f"💾 Complete log saved to: {log_filename}")
        
        # Show the test output
        print("\n📝 TEST OUTPUT")
        print("=" * 80)
        
        # Show the stderr output which contains the test results
        for line in error_lines:
            if line.strip():
                print(line)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout: Tests took too long to run")
        return False
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        return False

def save_complete_log(output_lines, error_lines, filename, duration):
    """Save complete test log to file"""
    with open(filename, 'w') as f:
        f.write("COMPLETE UNIT TEST LOG\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {duration:.2f}s\n\n")
        
        f.write("STDOUT OUTPUT:\n")
        f.write("-" * 40 + "\n")
        for line in output_lines:
            f.write(f"{line}\n")
        
        f.write("\nSTDERR OUTPUT (TEST RESULTS):\n")
        f.write("-" * 40 + "\n")
        for line in error_lines:
            f.write(f"{line}\n")

if __name__ == '__main__':
    success = run_tests_with_detailed_logging()
    sys.exit(0 if success else 1) 