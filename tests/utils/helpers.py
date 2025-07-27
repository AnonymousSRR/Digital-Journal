"""
Helper utilities for Journal App Automation Testing
"""

import time
import os
import random
from datetime import datetime
from ..config.settings import TestConfig


def generate_random_user_data():
    """
    Generate random user data for testing
    
    Returns:
        dict: Dictionary containing random user data
    """
    random_number = random.randint(1000, 9999)
    
    user_data = {
        "first_name": f"random{random_number}",
        "last_name": f"lastrandom{random_number}",
        "email": f"random{random_number}@gmail.com",
        "password": "TestPassword123!"
    }
    
    return user_data


def generate_random_journal_data():
    """
    Generate random journal data for testing
    
    Returns:
        dict: Dictionary containing random journal data
    """
    random_number = random.randint(1000, 9999)
    
    journal_data = {
        "title": f"Automated Journal Entry {random_number}",
        "answer": "This is a random automated answer for testing purposes."
    }
    
    return journal_data


def take_screenshot_on_failure(driver, test_name):
    """
    Take a screenshot when a test fails
    
    Args:
        driver: WebDriver instance
        test_name (str): Name of the test that failed
        
    Returns:
        str: Path to the screenshot file
    """
    if TestConfig.TAKE_SCREENSHOT_ON_FAILURE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"failure_{test_name}_{timestamp}.png"
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(TestConfig.SCREENSHOT_DIR, exist_ok=True)
        
        filepath = os.path.join(TestConfig.SCREENSHOT_DIR, filename)
        driver.save_screenshot(filepath)
        return filepath
    return None


def wait_for_element_with_retry(driver, locator, max_attempts=3, delay=1):
    """
    Wait for an element with retry logic
    
    Args:
        driver: WebDriver instance
        locator (tuple): Element locator (By, value)
        max_attempts (int): Maximum number of attempts
        delay (int): Delay between attempts in seconds
        
    Returns:
        WebElement: Found element or None if not found
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    for attempt in range(max_attempts):
        try:
            wait = WebDriverWait(driver, TestConfig.IMPLICIT_WAIT)
            element = wait.until(EC.presence_of_element_located(locator))
            return element
        except TimeoutException:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                return None
    return None


def verify_element_text(driver, locator, expected_text, timeout=None):
    """
    Verify that an element contains the expected text
    
    Args:
        driver: WebDriver instance
        locator (tuple): Element locator (By, value)
        expected_text (str): Expected text
        timeout (int): Timeout in seconds
        
    Returns:
        bool: True if text matches, False otherwise
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    try:
        wait_time = timeout or TestConfig.IMPLICIT_WAIT
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.text_to_be_present_in_element(locator, expected_text))
        return True
    except TimeoutException:
        return False


def verify_element_attribute(driver, locator, attribute, expected_value, timeout=None):
    """
    Verify that an element has the expected attribute value
    
    Args:
        driver: WebDriver instance
        locator (tuple): Element locator (By, value)
        attribute (str): Attribute name
        expected_value (str): Expected attribute value
        timeout (int): Timeout in seconds
        
    Returns:
        bool: True if attribute value matches, False otherwise
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    try:
        wait_time = timeout or TestConfig.IMPLICIT_WAIT
        wait = WebDriverWait(driver, wait_time)
        
        def attribute_contains(driver):
            element = driver.find_element(*locator)
            return expected_value in element.get_attribute(attribute)
        
        wait.until(attribute_contains)
        return True
    except TimeoutException:
        return False


def scroll_to_element(driver, locator):
    """
    Scroll to an element
    
    Args:
        driver: WebDriver instance
        locator (tuple): Element locator (By, value)
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    wait = WebDriverWait(driver, TestConfig.IMPLICIT_WAIT)
    element = wait.until(EC.presence_of_element_located(locator))
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(0.5)  # Small delay for smooth scrolling


def wait_for_page_load(driver, timeout=None):
    """
    Wait for page to load completely
    
    Args:
        driver: WebDriver instance
        timeout (int): Timeout in seconds
    """
    from selenium.webdriver.support.ui import WebDriverWait
    
    wait_time = timeout or TestConfig.PAGE_LOAD_TIMEOUT
    wait = WebDriverWait(driver, wait_time)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")


def get_test_data(test_name):
    """
    Get test data for a specific test
    
    Args:
        test_name (str): Name of the test
        
    Returns:
        dict: Test data dictionary
    """
    test_data = {
        "valid_user": {
            "email": TestConfig.TEST_USER_EMAIL,
            "password": TestConfig.TEST_USER_PASSWORD,
            "first_name": TestConfig.TEST_USER_FIRST_NAME,
            "last_name": TestConfig.TEST_USER_LAST_NAME
        },
        "invalid_user": {
            "email": "invalid@example.com",
            "password": "wrongpassword",
            "first_name": "Invalid",
            "last_name": "User"
        }
    }
    
    return test_data.get(test_name, {})


def log_test_step(step_description):
    """
    Log a test step for better test reporting
    
    Args:
        step_description (str): Description of the test step
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] STEP: {step_description}")


def verify_url_contains(driver, expected_partial_url):
    """
    Verify that the current URL contains the expected partial URL
    
    Args:
        driver: WebDriver instance
        expected_partial_url (str): Expected partial URL
        
    Returns:
        bool: True if URL contains the expected part, False otherwise
    """
    current_url = driver.current_url
    return expected_partial_url in current_url


def verify_page_title_contains(driver, expected_partial_title):
    """
    Verify that the page title contains the expected partial title
    
    Args:
        driver: WebDriver instance
        expected_partial_title (str): Expected partial title
        
    Returns:
        bool: True if title contains the expected part, False otherwise
    """
    page_title = driver.title
    return expected_partial_title in page_title 