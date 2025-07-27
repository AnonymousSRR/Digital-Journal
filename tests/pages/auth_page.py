"""
Authentication Page Object Model for Journal App
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class AuthPage(BasePage):
    """Page object for the authentication page"""
    
    # Page elements - Header
    HEADING = (By.CSS_SELECTOR, "h1.navbar-brand")
    
    # Tab elements
    SIGNIN_TAB = (By.ID, "signin-tab")
    SIGNUP_TAB = (By.ID, "signup-tab")
    
    # SignIn form elements
    SIGNIN_FORM = (By.ID, "signin-form")
    USERNAME_INPUT = (By.ID, "username-input")
    PASSWORD_INPUT = (By.ID, "password-input")
    SIGNIN_BUTTON = (By.ID, "signin-button")
    
    # SignUp form elements
    SIGNUP_FORM = (By.ID, "signup-form")
    FIRST_NAME_INPUT = (By.ID, "first-name-input")
    LAST_NAME_INPUT = (By.ID, "last-name-input")
    EMAIL_INPUT = (By.ID, "email-input")
    PASSWORD1_INPUT = (By.ID, "password1-input")
    PASSWORD2_INPUT = (By.ID, "password2-input")
    SIGNUP_BUTTON = (By.ID, "signup-button")
    
    # Auth container
    AUTH_CONTAINER = (By.CLASS_NAME, "auth-container")
    AUTH_CARD = (By.CLASS_NAME, "auth-card")
    
    def __init__(self, driver):
        """
        Initialize AuthPage
        
        Args:
            driver: WebDriver instance
        """
        super().__init__(driver)
    
    def navigate_to_auth_page(self):
        """Navigate to the authentication page"""
        self.navigate_to(f"{self.driver.current_url}")
        self.wait_for_page_load()
    
    def get_page_heading(self):
        """
        Get the page heading text
        
        Returns:
            str: Page heading text
        """
        return self.get_element_text(self.HEADING)
    
    def is_auth_container_present(self):
        """
        Check if authentication container is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.AUTH_CONTAINER)
    
    def is_auth_card_present(self):
        """
        Check if authentication card is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.AUTH_CARD)
    
    # Tab functionality
    def click_signin_tab(self):
        """Click on the SignIn tab"""
        self.click_element(self.SIGNIN_TAB)
    
    def click_signup_tab(self):
        """Click on the SignUp tab"""
        self.click_element(self.SIGNUP_TAB)
    
    def is_signin_tab_active(self):
        """
        Check if SignIn tab is active
        
        Returns:
            bool: True if active, False otherwise
        """
        element = self.find_element(self.SIGNIN_TAB)
        return "active" in element.get_attribute("class")
    
    def is_signup_tab_active(self):
        """
        Check if SignUp tab is active
        
        Returns:
            bool: True if active, False otherwise
        """
        element = self.find_element(self.SIGNUP_TAB)
        return "active" in element.get_attribute("class")
    
    # SignIn form functionality
    def is_signin_form_present(self):
        """
        Check if SignIn form is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.SIGNIN_FORM)
    
    def is_signin_form_visible(self):
        """
        Check if SignIn form is visible
        
        Returns:
            bool: True if visible, False otherwise
        """
        return self.is_element_visible(self.SIGNIN_FORM)
    
    def is_username_field_present(self):
        """
        Check if username field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.USERNAME_INPUT)
    
    def is_password_field_present(self):
        """
        Check if password field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.PASSWORD_INPUT)
    
    def is_signin_button_present(self):
        """
        Check if SignIn button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.SIGNIN_BUTTON)
    
    def get_username_placeholder(self):
        """
        Get username field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.USERNAME_INPUT)
        return element.get_attribute("placeholder")
    
    def get_password_placeholder(self):
        """
        Get password field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.PASSWORD_INPUT)
        return element.get_attribute("placeholder")
    
    def enter_username(self, username):
        """
        Enter username in the username field
        
        Args:
            username (str): Username to enter
        """
        self.send_keys_to_element(self.USERNAME_INPUT, username)
    
    def enter_password(self, password):
        """
        Enter password in the password field
        
        Args:
            password (str): Password to enter
        """
        self.send_keys_to_element(self.PASSWORD_INPUT, password)
    
    def click_signin_button(self):
        """Click the SignIn button"""
        self.click_element(self.SIGNIN_BUTTON)
    
    def signin(self, username, password):
        """
        Complete SignIn process
        
        Args:
            username (str): Username/email
            password (str): Password
        """
        self.enter_username(username)
        self.enter_password(password)
        self.click_signin_button()
    
    # SignUp form functionality
    def is_signup_form_present(self):
        """
        Check if SignUp form is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.SIGNUP_FORM)
    
    def is_signup_form_visible(self):
        """
        Check if SignUp form is visible
        
        Returns:
            bool: True if visible, False otherwise
        """
        return self.is_element_visible(self.SIGNUP_FORM)
    
    def is_first_name_field_present(self):
        """
        Check if first name field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.FIRST_NAME_INPUT)
    
    def is_last_name_field_present(self):
        """
        Check if last name field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.LAST_NAME_INPUT)
    
    def is_email_field_present(self):
        """
        Check if email field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.EMAIL_INPUT)
    
    def is_password1_field_present(self):
        """
        Check if password field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.PASSWORD1_INPUT)
    
    def is_password2_field_present(self):
        """
        Check if confirm password field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.PASSWORD2_INPUT)
    
    def is_signup_button_present(self):
        """
        Check if SignUp button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.SIGNUP_BUTTON)
    
    def get_first_name_placeholder(self):
        """
        Get first name field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.FIRST_NAME_INPUT)
        return element.get_attribute("placeholder")
    
    def get_last_name_placeholder(self):
        """
        Get last name field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.LAST_NAME_INPUT)
        return element.get_attribute("placeholder")
    
    def get_email_placeholder(self):
        """
        Get email field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.EMAIL_INPUT)
        return element.get_attribute("placeholder")
    
    def get_password1_placeholder(self):
        """
        Get password field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.PASSWORD1_INPUT)
        return element.get_attribute("placeholder")
    
    def get_password2_placeholder(self):
        """
        Get confirm password field placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.PASSWORD2_INPUT)
        return element.get_attribute("placeholder")
    
    def enter_first_name(self, first_name):
        """
        Enter first name in the first name field
        
        Args:
            first_name (str): First name to enter
        """
        self.send_keys_to_element(self.FIRST_NAME_INPUT, first_name)
    
    def enter_last_name(self, last_name):
        """
        Enter last name in the last name field
        
        Args:
            last_name (str): Last name to enter
        """
        self.send_keys_to_element(self.LAST_NAME_INPUT, last_name)
    
    def enter_email(self, email):
        """
        Enter email in the email field
        
        Args:
            email (str): Email to enter
        """
        self.send_keys_to_element(self.EMAIL_INPUT, email)
    
    def enter_password1(self, password):
        """
        Enter password in the password field
        
        Args:
            password (str): Password to enter
        """
        self.send_keys_to_element(self.PASSWORD1_INPUT, password)
    
    def enter_password2(self, password):
        """
        Enter password in the confirm password field
        
        Args:
            password (str): Password to enter
        """
        self.send_keys_to_element(self.PASSWORD2_INPUT, password)
    
    def click_signup_button(self):
        """Click the SignUp button"""
        self.click_element(self.SIGNUP_BUTTON)
    
    def signup(self, first_name, last_name, email, password):
        """
        Complete SignUp process
        
        Args:
            first_name (str): First name
            last_name (str): Last name
            email (str): Email address
            password (str): Password
        """
        self.enter_first_name(first_name)
        self.enter_last_name(last_name)
        self.enter_email(email)
        self.enter_password1(password)
        self.enter_password2(password)
        self.click_signup_button() 