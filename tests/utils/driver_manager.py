"""
WebDriver Manager for Journal App Automation Testing
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from ..config.settings import TestConfig


class DriverManager:
    """Manages WebDriver instances for different browsers"""
    
    def __init__(self, browser=None, headless=None):
        """
        Initialize DriverManager
        
        Args:
            browser (str): Browser type (chrome, firefox, edge)
            headless (bool): Run browser in headless mode
        """
        self.browser = browser or TestConfig.BROWSER
        self.headless = headless if headless is not None else TestConfig.HEADLESS
        self.driver = None
    
    def get_driver(self):
        """
        Get WebDriver instance based on browser configuration
        
        Returns:
            webdriver: Configured WebDriver instance
        """
        if self.browser == "chrome":
            return self._get_chrome_driver()
        elif self.browser == "firefox":
            return self._get_firefox_driver()
        elif self.browser == "edge":
            return self._get_edge_driver()
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")
    
    def _get_chrome_driver(self):
        """Get Chrome WebDriver instance"""
        chrome_options = ChromeOptions()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument(f"--window-size={TestConfig.WINDOW_WIDTH},{TestConfig.WINDOW_HEIGHT}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        
        try:
            # Create service with automatic driver management
            driver_path = ChromeDriverManager().install()
            
            # Fix for macOS ARM64 issue - ensure we get the correct executable
            if driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                # Remove the incorrect suffix and use the actual chromedriver executable
                driver_path = driver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
            
            # Verify the file exists and is executable
            if not os.path.exists(driver_path):
                raise FileNotFoundError(f"ChromeDriver not found at: {driver_path}")
            
            # Make sure the file is executable
            os.chmod(driver_path, 0o755)
            
            service = ChromeService(driver_path)
            
            # Create driver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Configure timeouts
            driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
            driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
            
            return driver
            
        except Exception as e:
            print(f"Error creating Chrome driver: {e}")
            print("Trying alternative approach...")
            
            # Alternative approach - try without service
            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
                driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
                return driver
            except Exception as e2:
                print(f"Alternative approach also failed: {e2}")
                raise Exception(f"Failed to create Chrome driver: {e}")
    
    def _get_firefox_driver(self):
        """Get Firefox WebDriver instance"""
        firefox_options = FirefoxOptions()
        
        if self.headless:
            firefox_options.add_argument("--headless")
        
        firefox_options.add_argument(f"--width={TestConfig.WINDOW_WIDTH}")
        firefox_options.add_argument(f"--height={TestConfig.WINDOW_HEIGHT}")
        
        # Create service with automatic driver management
        service = FirefoxService(GeckoDriverManager().install())
        
        # Create driver
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        # Configure timeouts
        driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
        driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
        
        return driver
    
    def _get_edge_driver(self):
        """Get Edge WebDriver instance"""
        edge_options = EdgeOptions()
        
        if self.headless:
            edge_options.add_argument("--headless")
        
        edge_options.add_argument(f"--window-size={TestConfig.WINDOW_WIDTH},{TestConfig.WINDOW_HEIGHT}")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        
        # Create service with automatic driver management
        service = EdgeService(EdgeChromiumDriverManager().install())
        
        # Create driver
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # Configure timeouts
        driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
        driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
        
        return driver
    
    def quit_driver(self):
        """Quit the WebDriver instance"""
        if self.driver:
            self.driver.quit()
            self.driver = None 