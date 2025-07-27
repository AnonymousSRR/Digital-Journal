"""
Theme Selector Page Object Model for Journal App
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class ThemeSelectorPage(BasePage):
    """Page object for the theme selector page"""
    
    # Page elements
    BACK_BUTTON = (By.CSS_SELECTOR, ".back-button")
    THEME_SELECTOR_TITLE = (By.CSS_SELECTOR, ".theme-selector-title")
    THEME_SELECTOR_CONTAINER = (By.CLASS_NAME, "theme-selector-container")
    THEMES_GRID = (By.CLASS_NAME, "themes-grid")
    THEME_BUTTONS = (By.CSS_SELECTOR, ".theme-button")
    NEXT_BUTTON = (By.ID, "next-button")
    
    # Theme button selectors (for specific themes)
    BUSINESS_IMPACT_BUTTON = (By.CSS_SELECTOR, ".theme-button[data-theme-name='Business Impact']")
    DELIVERY_IMPACT_BUTTON = (By.CSS_SELECTOR, ".theme-button[data-theme-name='Delivery Impact']")
    ORG_IMPACT_BUTTON = (By.CSS_SELECTOR, ".theme-button[data-theme-name='Org Impact']")
    TEAM_IMPACT_BUTTON = (By.CSS_SELECTOR, ".theme-button[data-theme-name='Team Impact']")
    TECHNOLOGY_IMPACT_BUTTON = (By.CSS_SELECTOR, ".theme-button[data-theme-name='Technology Impact']")
    
    def __init__(self, driver):
        """
        Initialize ThemeSelectorPage
        
        Args:
            driver: WebDriver instance
        """
        super().__init__(driver)
    
    def get_page_title(self):
        """
        Get the theme selector page title
        
        Returns:
            str: Page title text
        """
        return self.get_element_text(self.THEME_SELECTOR_TITLE)
    
    def is_back_button_present(self):
        """
        Check if back button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.BACK_BUTTON)
    
    def is_theme_selector_container_present(self):
        """
        Check if theme selector container is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.THEME_SELECTOR_CONTAINER)
    
    def is_themes_grid_present(self):
        """
        Check if themes grid is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.THEMES_GRID)
    
    def get_theme_buttons_count(self):
        """
        Get the number of theme buttons present
        
        Returns:
            int: Number of theme buttons
        """
        theme_buttons = self.find_elements(self.THEME_BUTTONS)
        return len(theme_buttons)
    
    def is_theme_button_present(self, theme_name):
        """
        Check if a specific theme button is present
        
        Args:
            theme_name (str): Name of the theme button
            
        Returns:
            bool: True if present, False otherwise
        """
        theme_button_selector = (By.CSS_SELECTOR, f".theme-button[data-theme-name='{theme_name}']")
        return self.is_element_present(theme_button_selector)
    
    def get_theme_button_text(self, theme_name):
        """
        Get the text of a specific theme button
        
        Args:
            theme_name (str): Name of the theme button
            
        Returns:
            str: Theme button text
        """
        theme_button_selector = (By.CSS_SELECTOR, f".theme-button[data-theme-name='{theme_name}']")
        return self.get_element_text(theme_button_selector)
    
    def click_theme_button(self, theme_name):
        """
        Click on a specific theme button
        
        Args:
            theme_name (str): Name of the theme button to click
        """
        theme_button_selector = (By.CSS_SELECTOR, f".theme-button[data-theme-name='{theme_name}']")
        self.click_element(theme_button_selector)
    
    def is_theme_button_selected(self, theme_name):
        """
        Check if a specific theme button is selected
        
        Args:
            theme_name (str): Name of the theme button
            
        Returns:
            bool: True if selected, False otherwise
        """
        theme_button_selector = (By.CSS_SELECTOR, f".theme-button[data-theme-name='{theme_name}']")
        element = self.find_element(theme_button_selector)
        return "selected" in element.get_attribute("class")
    
    def is_next_button_present(self):
        """
        Check if next button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.NEXT_BUTTON)
    
    def is_next_button_enabled(self):
        """
        Check if next button is enabled
        
        Returns:
            bool: True if enabled, False otherwise
        """
        element = self.find_element(self.NEXT_BUTTON)
        return not element.get_attribute("disabled")
    
    def click_next_button(self):
        """Click the next button"""
        self.click_element(self.NEXT_BUTTON)
    
    def click_back_button(self):
        """Click the back button"""
        self.click_element(self.BACK_BUTTON)
    
    def get_selected_theme_id(self):
        """
        Get the data-theme-id of the selected theme button
        
        Returns:
            str: Selected theme ID or None if no theme is selected
        """
        selected_button = self.find_element((By.CSS_SELECTOR, ".theme-button.selected"))
        if selected_button:
            return selected_button.get_attribute("data-theme-id")
        return None
    
    def verify_all_theme_buttons_present(self):
        """
        Verify that all expected theme buttons are present
        
        Returns:
            bool: True if all theme buttons are present, False otherwise
        """
        expected_themes = [
            "Business Impact",
            "Delivery Impact", 
            "Org Impact",
            "Team Impact",
            "Technology Impact"
        ]
        
        for theme in expected_themes:
            if not self.is_theme_button_present(theme):
                return False
        return True
    
    def wait_for_theme_selector_load(self):
        """Wait for theme selector page to load completely"""
        self.wait_for_element_visible(self.THEME_SELECTOR_TITLE)
        self.wait_for_element_visible(self.THEMES_GRID)
        self.wait_for_element_visible(self.NEXT_BUTTON) 