#!/usr/bin/env python3
"""
Unit Test Runner for Journal App
"""

import sys
import os
import subprocess
from datetime import datetime

def run_unit_tests(test_category=None, verbose=False, coverage=False):
    """
    Run unit tests for the Journal App
    
    Args:
        test_category (str): Specific test category to run (models, forms, views, utils, config)
        verbose (bool): Run tests in verbose mode
        coverage (bool): Generate coverage report
    """
    
    # Set up the command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if test_category:
        cmd.append(f"tests/unit_tests/{test_category}/")
    else:
        cmd.append("tests/unit_tests/")
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage if requested
    if coverage:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coverage_file = f"tests/reports/coverage_{timestamp}.html"
        cmd.extend([
            "--cov=authentication",
            "--cov=config", 
            "--cov=tests.utils",
            "--cov-report=html:" + coverage_file,
            "--cov-report=term-missing"
        ])
    
    # Add HTML report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"tests/reports/unit_test_report_{timestamp}.html"
    cmd.extend(["--html", report_file, "--self-contained-html"])
    
    # Add metadata
    cmd.extend(["--metadata", "TestType", "unit"])
    cmd.extend(["--metadata", "Category", test_category or "all"])
    cmd.extend(["--metadata", "Timestamp", timestamp])
    
    print(f"Running unit tests with command: {' '.join(cmd)}")
    print(f"Test Category: {test_category or 'all'}")
    print(f"Verbose: {verbose}")
    print(f"Coverage: {coverage}")
    print("-" * 80)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=True)
        print("-" * 80)
        print("✅ All unit tests passed successfully!")
        print(f"📊 HTML report generated: {report_file}")
        if coverage:
            print(f"📈 Coverage report generated: {coverage_file}")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 80)
        print(f"❌ Unit tests failed with exit code: {e.returncode}")
        return False

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) < 2:
        print("Usage: python run_unit_tests.py <test_category> [options]")
        print("\nTest Categories:")
        print("  all     - Run all unit tests (default)")
        print("  models  - Run model tests only")
        print("  forms   - Run form tests only")
        print("  views   - Run view tests only")
        print("  utils   - Run utility tests only")
        print("  config  - Run configuration tests only")
        print("\nOptions:")
        print("  verbose - Run in verbose mode")
        print("  coverage - Generate coverage report")
        print("\nExamples:")
        print("  python run_unit_tests.py all")
        print("  python run_unit_tests.py models verbose")
        print("  python run_unit_tests.py views coverage")
        print("  python run_unit_tests.py all verbose coverage")
        return
    
    test_category = sys.argv[1]
    verbose = "verbose" in sys.argv
    coverage = "coverage" in sys.argv
    
    # Validate test category
    valid_categories = ["all", "models", "forms", "views", "utils", "config"]
    if test_category not in valid_categories:
        print(f"❌ Invalid test category: {test_category}")
        print(f"Valid categories: {', '.join(valid_categories)}")
        return
    
    # Set category to None for "all" to run all tests
    if test_category == "all":
        test_category = None
    
    # Run the tests
    success = run_unit_tests(test_category, verbose, coverage)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 