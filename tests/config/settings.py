"""
Configuration settings for Journal App Automation Testing
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TestConfig:
    """Test configuration class"""
    
    # Base URL for the application
    BASE_URL = "http://127.0.0.1:8000/login/"
    
    # Browser configuration
    BROWSER = os.getenv("BROWSER", "chrome").lower()
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    
    # Window size
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1920"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "1080"))
    
    # Screenshot settings
    SCREENSHOT_DIR = "screenshots"
    TAKE_SCREENSHOT_ON_FAILURE = True
    
    # Test data
    TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
    TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")
    TEST_USER_FIRST_NAME = os.getenv("TEST_USER_FIRST_NAME", "Test")
    TEST_USER_LAST_NAME = os.getenv("TEST_USER_LAST_NAME", "User")
    
    # Report settings
    REPORT_DIR = "reports"
    HTML_REPORT = True
    ALLURE_REPORT = True 