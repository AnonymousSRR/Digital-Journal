"""
Base Page Object Model class for Journal App Automation Testing
"""

import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ..config.settings import TestConfig


class BasePage:
    """Base page class with common methods for all page objects"""
    
    def __init__(self, driver):
        """
        Initialize BasePage
        
        Args:
            driver: WebDriver instance
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, TestConfig.IMPLICIT_WAIT)
        self.actions = ActionChains(driver)
    
    def navigate_to(self, url):
        """
        Navigate to a specific URL
        
        Args:
            url (str): URL to navigate to
        """
        self.driver.get(url)
    
    def get_page_title(self):
        """
        Get the page title
        
        Returns:
            str: Page title
        """
        return self.driver.title
    
    def get_current_url(self):
        """
        Get the current URL
        
        Returns:
            str: Current URL
        """
        return self.driver.current_url
    
    def find_element(self, locator, timeout=None):
        """
        Find a single element with explicit wait
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
            
        Returns:
            WebElement: Found element
        """
        wait_time = timeout or TestConfig.IMPLICIT_WAIT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.presence_of_element_located(locator))
    
    def find_elements(self, locator, timeout=None):
        """
        Find multiple elements with explicit wait
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
            
        Returns:
            list: List of found elements
        """
        wait_time = timeout or TestConfig.IMPLICIT_WAIT
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.presence_of_all_elements_located(locator))
    
    def click_element(self, locator, timeout=None):
        """
        Click on an element with explicit wait
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
        """
        element = self.find_element(locator, timeout)
        self.wait.until(EC.element_to_be_clickable(locator))
        element.click()
    
    def send_keys_to_element(self, locator, text, timeout=None):
        """
        Send keys to an element with explicit wait
        
        Args:
            locator (tuple): Element locator (By, value)
            text (str): Text to send
            timeout (int): Timeout in seconds
        """
        element = self.find_element(locator, timeout)
        element.clear()
        element.send_keys(text)
    
    def get_element_text(self, locator, timeout=None):
        """
        Get text from an element
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
            
        Returns:
            str: Element text
        """
        element = self.find_element(locator, timeout)
        return element.text
    
    def is_element_present(self, locator, timeout=None):
        """
        Check if element is present
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
            
        Returns:
            bool: True if element is present, False otherwise
        """
        try:
            self.find_element(locator, timeout)
            return True
        except (TimeoutException, NoSuchElementException):
            return False
    
    def is_element_visible(self, locator, timeout=None):
        """
        Check if element is visible
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
            
        Returns:
            bool: True if element is visible, False otherwise
        """
        try:
            wait_time = timeout or TestConfig.IMPLICIT_WAIT
            wait = WebDriverWait(self.driver, wait_time)
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except (TimeoutException, NoSuchElementException):
            return False
    
    def wait_for_element_visible(self, locator, timeout=None):
        """
        Wait for element to be visible
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Timeout in seconds
        """
        wait_time = timeout or TestConfig.IMPLICIT_WAIT
        wait = WebDriverWait(self.driver, wait_time)
        wait.until(EC.visibility_of_element_located(locator))
    
    def take_screenshot(self, filename=None):
        """
        Take a screenshot
        
        Args:
            filename (str): Screenshot filename
            
        Returns:
            str: Path to screenshot file
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(TestConfig.SCREENSHOT_DIR, exist_ok=True)
        
        filepath = os.path.join(TestConfig.SCREENSHOT_DIR, filename)
        self.driver.save_screenshot(filepath)
        return filepath
    
    def scroll_to_element(self, locator):
        """
        Scroll to an element
        
        Args:
            locator (tuple): Element locator (By, value)
        """
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Small delay for smooth scrolling
    
    def wait_for_page_load(self, timeout=None):
        """
        Wait for page to load completely
        
        Args:
            timeout (int): Timeout in seconds
        """
        wait_time = timeout or TestConfig.PAGE_LOAD_TIMEOUT
        wait = WebDriverWait(self.driver, wait_time)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") 