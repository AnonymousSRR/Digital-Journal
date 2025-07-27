"""
Home Page Object Model for Journal App
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class HomePage(BasePage):
    """Page object for the home/dashboard page"""
    
    # Page elements
    APP_TITLE = (By.CSS_SELECTOR, "h1.navbar-brand")  # Digital Journal App title
    WELCOME_MESSAGE = (By.CSS_SELECTOR, ".welcome-message h2")
    HOME_CONTAINER = (By.CLASS_NAME, "home-container")
    CREATE_JOURNAL_BTN = (By.ID, "create-journal-btn")
    MY_JOURNALS_BTN = (By.ID, "my-journals-btn")
    DASHBOARD_BUTTONS = (By.CLASS_NAME, "dashboard-buttons")
    LOGOUT_BTN = (By.ID, "logout-btn")  # Logout button
    
    def __init__(self, driver):
        """
        Initialize HomePage
        
        Args:
            driver: WebDriver instance
        """
        super().__init__(driver)
    
    def get_app_title(self):
        """
        Get the app title text
        
        Returns:
            str: App title text
        """
        return self.get_element_text(self.APP_TITLE)
    
    def get_welcome_message(self):
        """
        Get the welcome message text
        
        Returns:
            str: Welcome message text
        """
        return self.get_element_text(self.WELCOME_MESSAGE)
    
    def is_app_title_present(self):
        """
        Check if app title is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.APP_TITLE)
    
    def is_home_container_present(self):
        """
        Check if home container is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.HOME_CONTAINER)
    
    def is_welcome_message_present(self):
        """
        Check if welcome message is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.WELCOME_MESSAGE)
    
    def is_create_journal_button_present(self):
        """
        Check if create journal button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.CREATE_JOURNAL_BTN)
    
    def is_my_journals_button_present(self):
        """
        Check if my journals button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.MY_JOURNALS_BTN)
    
    def is_logout_button_present(self):
        """
        Check if logout button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.LOGOUT_BTN)
    
    def click_create_journal_button(self):
        """Click the create journal button"""
        self.click_element(self.CREATE_JOURNAL_BTN)
    
    def click_my_journals_button(self):
        """Click the my journals button"""
        self.click_element(self.MY_JOURNALS_BTN)
    
    def click_logout_button(self):
        """Click the logout button"""
        self.click_element(self.LOGOUT_BTN)
    
    def verify_welcome_message_contains_name(self, first_name):
        """
        Verify that welcome message contains the user's first name
        
        Args:
            first_name (str): User's first name
            
        Returns:
            bool: True if welcome message contains the name, False otherwise
        """
        welcome_text = self.get_welcome_message()
        return first_name in welcome_text
    
    def verify_welcome_message_format(self, first_name):
        """
        Verify that welcome message has the correct format
        
        Args:
            first_name (str): User's first name
            
        Returns:
            bool: True if welcome message has correct format, False otherwise
        """
        welcome_text = self.get_welcome_message()
        expected_format = f"Hi {first_name}, what's your plan today?"
        return welcome_text == expected_format
    
    def wait_for_home_page_load(self):
        """Wait for home page to load completely"""
        self.wait_for_element_visible(self.WELCOME_MESSAGE)
        self.wait_for_element_visible(self.DASHBOARD_BUTTONS)
        self.wait_for_element_visible(self.LOGOUT_BTN) 