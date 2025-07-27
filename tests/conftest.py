"""
Pytest configuration and fixtures for Journal App Automation Testing
"""

import pytest
import os
from .utils.driver_manager import DriverManager
from .pages.auth_page import AuthPage
from .pages.home_page import HomePage
from .pages.theme_selector_page import ThemeSelectorPage
from .pages.answer_prompt_page import AnswerPromptPage
from .pages.my_journals_page import MyJournalsPage
from .config.settings import TestConfig


@pytest.fixture(scope="function")
def driver():
    """
    WebDriver fixture that provides a fresh driver instance for each test
    
    Yields:
        webdriver: WebDriver instance
    """
    driver_manager = DriverManager()
    driver = driver_manager.get_driver()
    
    # Set window size
    driver.set_window_size(TestConfig.WINDOW_WIDTH, TestConfig.WINDOW_HEIGHT)
    
    yield driver
    
    # Cleanup after test
    if driver:
        driver.quit()


@pytest.fixture(scope="function")
def auth_page(driver):
    """
    Authentication page fixture
    
    Args:
        driver: WebDriver instance from driver fixture
        
    Yields:
        AuthPage: Authentication page object
    """
    auth_page = AuthPage(driver)
    yield auth_page


@pytest.fixture(scope="function")
def home_page(driver):
    """
    Home page fixture
    
    Args:
        driver: WebDriver instance from driver fixture
        
    Yields:
        HomePage: Home page object
    """
    home_page = HomePage(driver)
    yield home_page


@pytest.fixture(scope="function")
def theme_selector_page(driver):
    """
    Theme selector page fixture
    
    Args:
        driver: WebDriver instance from driver fixture
        
    Yields:
        ThemeSelectorPage: Theme selector page object
    """
    theme_selector_page = ThemeSelectorPage(driver)
    yield theme_selector_page


@pytest.fixture(scope="function")
def answer_prompt_page(driver):
    """
    Answer prompt page fixture
    
    Args:
        driver: WebDriver instance from driver fixture
        
    Yields:
        AnswerPromptPage: Answer prompt page object
    """
    answer_prompt_page = AnswerPromptPage(driver)
    yield answer_prompt_page


@pytest.fixture(scope="function")
def my_journals_page(driver):
    """
    My Journals page fixture
    
    Args:
        driver: WebDriver instance from driver fixture
        
    Yields:
        MyJournalsPage: My Journals page object
    """
    my_journals_page = MyJournalsPage(driver)
    yield my_journals_page


@pytest.fixture(scope="function")
def driver_manager():
    """
    Driver manager fixture for custom driver configuration
    
    Yields:
        DriverManager: Driver manager instance
    """
    driver_manager = DriverManager()
    yield driver_manager


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom options"""
    # Create necessary directories
    os.makedirs(TestConfig.SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(TestConfig.REPORT_DIR, exist_ok=True)


def pytest_runtest_setup(item):
    """Setup before each test"""
    # Any setup logic can be added here
    pass


def pytest_runtest_teardown(item, nextitem):
    """Teardown after each test"""
    # Any cleanup logic can be added here
    pass


# Custom markers
pytest_marks = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "smoke: marks tests as smoke tests",
    "regression: marks tests as regression tests",
    "ui: marks tests as UI tests",
    "auth: marks tests as authentication tests",
    "signup: marks tests as signup tests",
    "signin: marks tests as signin tests",
    "home: marks tests as home page tests",
    "theme: marks tests as theme selector tests",
    "journal: marks tests as journal creation tests",
    "my_journals: marks tests as My Journals page tests",
]


def pytest_configure(config):
    """Register custom markers"""
    for marker in pytest_marks:
        config.addinivalue_line("markers", marker) 