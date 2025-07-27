"""
Answer Prompt Page Object Model for Journal App
"""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class AnswerPromptPage(BasePage):
    """Page object for the answer prompt page"""
    
    # Page elements
    BACK_BUTTON = (By.CSS_SELECTOR, ".back-button")
    ANSWER_PROMPT_TITLE = (By.CSS_SELECTOR, ".answer-prompt-title")
    ANSWER_PROMPT_CONTAINER = (By.CLASS_NAME, "answer-prompt-container")
    PROMPT_SECTION = (By.CLASS_NAME, "prompt-section")
    
    # Theme information
    THEME_INFO = (By.CLASS_NAME, "theme-info")
    THEME_NAME = (By.CLASS_NAME, "theme-name")
    THEME_DESCRIPTION = (By.CLASS_NAME, "theme-description")
    
    # Prompt box
    PROMPT_BOX = (By.CLASS_NAME, "prompt-box")
    PROMPT_LABEL = (By.CLASS_NAME, "prompt-label")
    PROMPT_TEXT = (By.CLASS_NAME, "prompt-text")
    
    # Form elements
    ANSWER_FORM = (By.CLASS_NAME, "answer-form")
    TITLE_INPUT = (By.ID, "title")
    ANSWER_TEXTAREA = (By.ID, "answer")
    SAVE_BUTTON = (By.CSS_SELECTOR, ".save-button")
    
    # Form groups
    FORM_GROUPS = (By.CLASS_NAME, "form-group")
    FORM_LABELS = (By.CLASS_NAME, "form-label")
    
    def __init__(self, driver):
        """
        Initialize AnswerPromptPage
        
        Args:
            driver: WebDriver instance
        """
        super().__init__(driver)
    
    def get_page_title(self):
        """
        Get the answer prompt page title
        
        Returns:
            str: Page title text
        """
        return self.get_element_text(self.ANSWER_PROMPT_TITLE)
    
    def is_back_button_present(self):
        """
        Check if back button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.BACK_BUTTON)
    
    def is_answer_prompt_container_present(self):
        """
        Check if answer prompt container is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.ANSWER_PROMPT_CONTAINER)
    
    def is_prompt_section_present(self):
        """
        Check if prompt section is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.PROMPT_SECTION)
    
    def get_theme_name(self):
        """
        Get the selected theme name
        
        Returns:
            str: Theme name text
        """
        return self.get_element_text(self.THEME_NAME)
    
    def is_theme_info_present(self):
        """
        Check if theme info section is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.THEME_INFO)
    
    def get_prompt_text(self):
        """
        Get the prompt text
        
        Returns:
            str: Prompt text
        """
        return self.get_element_text(self.PROMPT_TEXT)
    
    def is_prompt_box_present(self):
        """
        Check if prompt box is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.PROMPT_BOX)
    
    def is_answer_form_present(self):
        """
        Check if answer form is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.ANSWER_FORM)
    
    def is_title_input_present(self):
        """
        Check if title input field is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.TITLE_INPUT)
    
    def is_answer_textarea_present(self):
        """
        Check if answer textarea is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.ANSWER_TEXTAREA)
    
    def is_save_button_present(self):
        """
        Check if save button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.SAVE_BUTTON)
    
    def get_title_input_placeholder(self):
        """
        Get the title input placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.TITLE_INPUT)
        return element.get_attribute("placeholder")
    
    def get_answer_textarea_placeholder(self):
        """
        Get the answer textarea placeholder text
        
        Returns:
            str: Placeholder text
        """
        element = self.find_element(self.ANSWER_TEXTAREA)
        return element.get_attribute("placeholder")
    
    def enter_journal_title(self, title):
        """
        Enter journal title
        
        Args:
            title (str): Journal title to enter
        """
        self.send_keys_to_element(self.TITLE_INPUT, title)
    
    def enter_journal_answer(self, answer):
        """
        Enter journal answer
        
        Args:
            answer (str): Journal answer to enter
        """
        self.send_keys_to_element(self.ANSWER_TEXTAREA, answer)
    
    def get_entered_title(self):
        """
        Get the currently entered title
        
        Returns:
            str: Entered title text
        """
        element = self.find_element(self.TITLE_INPUT)
        return element.get_attribute("value")
    
    def get_entered_answer(self):
        """
        Get the currently entered answer
        
        Returns:
            str: Entered answer text
        """
        element = self.find_element(self.ANSWER_TEXTAREA)
        return element.get_attribute("value")
    
    def click_save_button(self):
        """Click the save button"""
        self.click_element(self.SAVE_BUTTON)
    
    def click_back_button(self):
        """Click the back button"""
        self.click_element(self.BACK_BUTTON)
    
    def verify_form_labels(self):
        """
        Verify that form labels are present and correct
        
        Returns:
            bool: True if labels are correct, False otherwise
        """
        labels = self.find_elements(self.FORM_LABELS)
        expected_labels = ["Journal Title", "Your Response"]
        
        if len(labels) != len(expected_labels):
            return False
        
        for i, label in enumerate(labels):
            if label.text != expected_labels[i]:
                return False
        
        return True
    
    def verify_placeholders(self):
        """
        Verify that input placeholders are correct
        
        Returns:
            bool: True if placeholders are correct, False otherwise
        """
        title_placeholder = self.get_title_input_placeholder()
        answer_placeholder = self.get_answer_textarea_placeholder()
        
        expected_title_placeholder = "Enter a title for your journal entry..."
        expected_answer_placeholder = "Write your thoughts, reflections, or answers here..."
        
        return (title_placeholder == expected_title_placeholder and 
                answer_placeholder == expected_answer_placeholder)
    
    def fill_journal_form(self, title, answer):
        """
        Fill the journal form with title and answer
        
        Args:
            title (str): Journal title
            answer (str): Journal answer
        """
        self.enter_journal_title(title)
        self.enter_journal_answer(answer)
    
    def wait_for_answer_prompt_load(self):
        """Wait for answer prompt page to load completely"""
        self.wait_for_element_visible(self.ANSWER_PROMPT_TITLE)
        self.wait_for_element_visible(self.PROMPT_SECTION)
        self.wait_for_element_visible(self.ANSWER_FORM)
        self.wait_for_element_visible(self.SAVE_BUTTON) 