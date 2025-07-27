#!/usr/bin/env python3
"""
Custom Test Report Generator for Journal App Automation Testing
"""

import subprocess
import sys
from datetime import datetime

def run_tests_and_generate_report():
    """Run tests and generate a custom report"""
    
    print("🧪 Running Journal App Automation Tests...")
    print("=" * 80)
    
    # Run the tests
    try:
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/test_journal_app.py", 
            "-v"
        ], capture_output=True, text=True, check=True)
        
        # Parse the output to extract test results
        output_lines = result.stdout.split('\n')
        test_results = []
        
        for line in output_lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'ERROR' in line):
                # Extract test name and status
                if 'PASSED' in line:
                    test_name = line.split('::')[-1].split(' PASSED')[0]
                    status = 'PASSED'
                elif 'FAILED' in line:
                    test_name = line.split('::')[-1].split(' FAILED')[0]
                    status = 'FAILED'
                elif 'ERROR' in line:
                    test_name = line.split('::')[-1].split(' ERROR')[0]
                    status = 'ERROR'
                else:
                    continue
                
                test_results.append((test_name, status))
        
        # Generate the report
        generate_test_report(test_results)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}")
        print("Test output:")
        print(e.stdout)
        print(e.stderr)
        return False
    
    return True

def generate_test_report(test_results):
    """Generate and display the test report"""
    
    # Test case descriptions
    test_descriptions = {
        "test_authentication_page_elements": "Verify authentication page elements and form fields",
        "test_authentication_page_url": "Verify correct URL and page title",
        "test_form_field_interactions": "Verify form field interactions and input capabilities",
        "test_user_signup_and_signin": "Test user signup and signin with random credentials",
        "test_home_screen_options": "Verify all home screen options are present after login",
        "test_theme_selection_functionality": "Test theme selection and Next button functionality",
        "test_journal_creation_functionality": "Test complete journal creation workflow",
        "test_my_journals_functionality": "Test My Journals page with journal display, modal, search, and delete",
        "test_user_logout_functionality": "Test user logout and session termination"
    }
    
    print("\n📊 JOURNAL APP AUTOMATION TEST REPORT")
    print("=" * 80)
    print(f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Browser: Chrome")
    print(f"🔗 Test URL: http://127.0.0.1:8000/login/")
    print("=" * 80)
    
    # Header
    print(f"{'Test Case':<40} | {'Test Case Description':<60} | {'Status':<10}")
    print("-" * 120)
    
    # Test results
    total_tests = len(test_results)
    passed_tests = 0
    failed_tests = 0
    
    for test_name, status in test_results:
        description = test_descriptions.get(test_name, "No description available")
        
        # Truncate description if too long
        if len(description) > 58:
            description = description[:55] + "..."
        
        # Format status with emoji
        status_display = "✅ PASSED" if status == "PASSED" else "❌ FAILED" if status == "FAILED" else "⚠️ ERROR"
        
        print(f"{test_name:<40} | {description:<60} | {status_display:<10}")
        
        if status == "PASSED":
            passed_tests += 1
        else:
            failed_tests += 1
    
    print("-" * 120)
    
    # Summary
    print(f"\n📈 TEST SUMMARY")
    print("=" * 40)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    
    if total_tests > 0:
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    else:
        print(f"📊 Success Rate: N/A (no tests found)")
    
    print("\n" + "=" * 80)
    
    if total_tests == 0:
        print("⚠️ No tests were executed. Please check the test configuration.")
    elif failed_tests == 0:
        print("🎉 All tests passed successfully!")
    else:
        print(f"⚠️ {failed_tests} test(s) failed. Please review the failures.")

def main():
    """Main function"""
    success = run_tests_and_generate_report()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 