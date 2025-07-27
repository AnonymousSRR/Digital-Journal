#!/usr/bin/env python3
"""
Test Runner for Journal App Automation Testing
"""

import sys
import os
import subprocess
from datetime import datetime

def run_tests(test_type="all", browser="chrome", headless=False, report=True):
    """
    Run the automation tests
    
    Args:
        test_type (str): Type of tests to run (all, auth, smoke, etc.)
        browser (str): Browser to use (chrome, firefox, edge)
        headless (bool): Run in headless mode
        report (bool): Generate HTML report
    """
    
    # Set environment variables
    env = os.environ.copy()
    env["BROWSER"] = browser
    env["HEADLESS"] = "true" if headless else "false"
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test selection
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "auth":
        cmd.extend(["-m", "auth"])
    elif test_type == "smoke":
        cmd.extend(["-m", "smoke"])
    else:
        cmd.append(f"tests/test_{test_type}.py")
    
    # Add verbosity
    cmd.append("-v")
    
    # Add HTML report if requested
    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/report_{test_type}_{timestamp}.html"
        cmd.extend(["--html", report_file, "--self-contained-html"])
    
    # Add metadata
    cmd.extend(["--metadata", "Browser", browser])
    cmd.extend(["--metadata", "TestType", test_type])
    cmd.extend(["--metadata", "Headless", str(headless)])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print(f"Environment: BROWSER={browser}, HEADLESS={headless}")
    print("-" * 80)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, env=env, check=True)
        print("-" * 80)
        print("✅ All tests passed successfully!")
        if report:
            print(f"📊 HTML report generated: {report_file}")
        return True
    except subprocess.CalledProcessError as e:
        print("-" * 80)
        print(f"❌ Tests failed with exit code: {e.returncode}")
        return False

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <test_type> [browser] [headless]")
        print("\nTest Types:")
        print("  all     - Run all tests")
        print("  auth    - Run authentication tests only")
        print("  smoke   - Run smoke tests only")
        print("\nBrowsers:")
        print("  chrome  - Use Chrome browser (default)")
        print("  firefox - Use Firefox browser")
        print("  edge    - Use Edge browser")
        print("\nOptions:")
        print("  headless - Run in headless mode")
        print("\nExamples:")
        print("  python run_tests.py all")
        print("  python run_tests.py auth chrome")
        print("  python run_tests.py smoke firefox headless")
        return
    
    test_type = sys.argv[1]
    browser = sys.argv[2] if len(sys.argv) > 2 else "chrome"
    headless = "headless" in sys.argv
    
    # Validate test type
    valid_test_types = ["all", "auth", "smoke"]
    if test_type not in valid_test_types:
        print(f"❌ Invalid test type: {test_type}")
        print(f"Valid test types: {', '.join(valid_test_types)}")
        return
    
    # Validate browser
    valid_browsers = ["chrome", "firefox", "edge"]
    if browser not in valid_browsers:
        print(f"❌ Invalid browser: {browser}")
        print(f"Valid browsers: {', '.join(valid_browsers)}")
        return
    
    # Run the tests
    success = run_tests(test_type, browser, headless)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 