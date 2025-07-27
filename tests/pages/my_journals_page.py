"""
My Journals Page Object Model for Journal App
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class MyJournalsPage(BasePage):
    """Page object for the My Journals page"""
    
    # Page elements
    BACK_BUTTON = (By.CSS_SELECTOR, ".back-button")
    MY_JOURNALS_TITLE = (By.CSS_SELECTOR, ".my-journals-title")
    MY_JOURNALS_CONTAINER = (By.CLASS_NAME, "my-journals-container")
    JOURNALS_GRID = (By.CLASS_NAME, "journals-grid")
    
    # Journal cards
    JOURNAL_CARDS = (By.CSS_SELECTOR, ".journal-card")
    JOURNAL_CARD_HEADER = (By.CLASS_NAME, "journal-card-header")
    JOURNAL_CARD_CONTENT = (By.CLASS_NAME, "journal-card-content")
    JOURNAL_DATE = (By.CLASS_NAME, "journal-date")
    JOURNAL_DETAILS = (By.CLASS_NAME, "journal-detail")
    DETAIL_LABEL = (By.CLASS_NAME, "detail-label")
    DETAIL_VALUE = (By.CLASS_NAME, "detail-value")
    EXPAND_HINT = (By.CLASS_NAME, "expand-hint")
    DELETE_JOURNAL_BTN = (By.CSS_SELECTOR, ".delete-journal-btn")
    
    # No journals section
    NO_JOURNALS = (By.CLASS_NAME, "no-journals")
    NO_JOURNALS_CONTENT = (By.CLASS_NAME, "no-journals-content")
    CREATE_FIRST_BTN = (By.CSS_SELECTOR, ".create-first-btn")
    
    # Journals stats
    JOURNALS_STATS = (By.CLASS_NAME, "journals-stats")
    STATS_TEXT = (By.CLASS_NAME, "stats-text")
    
    # Journal Modal
    JOURNAL_MODAL = (By.ID, "journalModal")
    MODAL_CONTENT = (By.CLASS_NAME, "journal-modal-content")
    MODAL_HEADER = (By.CLASS_NAME, "journal-modal-header")
    MODAL_TITLE = (By.CLASS_NAME, "modal-title")
    MODAL_CLOSE = (By.CSS_SELECTOR, ".modal-close")
    MODAL_BODY = (By.CLASS_NAME, "journal-modal-body")
    
    # Modal journal details
    MODAL_JOURNAL_CARD = (By.CLASS_NAME, "modal-journal-card")
    MODAL_JOURNAL_DATE = (By.ID, "modalDate")
    MODAL_JOURNAL_TITLE = (By.ID, "modalTitle")
    MODAL_JOURNAL_THEME = (By.ID, "modalTheme")
    MODAL_JOURNAL_PROMPT = (By.ID, "modalPrompt")
    MODAL_JOURNAL_ANSWER = (By.ID, "modalAnswer")
    
    # Search functionality (if present in navbar)
    SEARCH_INPUT = (By.CSS_SELECTOR, ".navbar-search-input")
    
    def __init__(self, driver):
        """
        Initialize MyJournalsPage
        
        Args:
            driver: WebDriver instance
        """
        super().__init__(driver)
    
    def get_page_title(self):
        """
        Get the My Journals page title
        
        Returns:
            str: Page title text
        """
        return self.get_element_text(self.MY_JOURNALS_TITLE)
    
    def is_back_button_present(self):
        """
        Check if back button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.BACK_BUTTON)
    
    def is_my_journals_container_present(self):
        """
        Check if My Journals container is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.MY_JOURNALS_CONTAINER)
    
    def is_journals_grid_present(self):
        """
        Check if journals grid is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.JOURNALS_GRID)
    
    def get_journal_cards_count(self):
        """
        Get the number of journal cards present
        
        Returns:
            int: Number of journal cards
        """
        journal_cards = self.find_elements(self.JOURNAL_CARDS)
        return len(journal_cards)
    
    def is_no_journals_section_present(self):
        """
        Check if no journals section is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.NO_JOURNALS)
    
    def is_create_first_button_present(self):
        """
        Check if create first journal button is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.CREATE_FIRST_BTN)
    
    def click_create_first_button(self):
        """Click the create first journal button"""
        self.click_element(self.CREATE_FIRST_BTN)
    
    def is_journals_stats_present(self):
        """
        Check if journals stats section is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.JOURNALS_STATS)
    
    def get_stats_text(self):
        """
        Get the stats text
        
        Returns:
            str: Stats text
        """
        return self.get_element_text(self.STATS_TEXT)
    
    def get_journal_card_by_index(self, index):
        """
        Get a specific journal card by index
        
        Args:
            index (int): Index of the journal card
            
        Returns:
            WebElement: Journal card element
        """
        journal_cards = self.find_elements(self.JOURNAL_CARDS)
        if 0 <= index < len(journal_cards):
            return journal_cards[index]
        return None
    
    def click_journal_card(self, index):
        """
        Click on a specific journal card to open modal
        
        Args:
            index (int): Index of the journal card to click
        """
        journal_card = self.get_journal_card_by_index(index)
        if journal_card:
            journal_card.click()
    
    def get_journal_card_date(self, index):
        """
        Get the date of a specific journal card
        
        Args:
            index (int): Index of the journal card
            
        Returns:
            str: Journal date
        """
        journal_card = self.get_journal_card_by_index(index)
        if journal_card:
            date_element = journal_card.find_element(*self.JOURNAL_DATE)
            return date_element.text
        return None
    
    def get_journal_card_details(self, index):
        """
        Get all details of a specific journal card
        
        Args:
            index (int): Index of the journal card
            
        Returns:
            dict: Dictionary containing journal details
        """
        journal_card = self.get_journal_card_by_index(index)
        if not journal_card:
            return None
        
        details = {}
        detail_elements = journal_card.find_elements(*self.JOURNAL_DETAILS)
        
        for detail in detail_elements:
            label_element = detail.find_element(*self.DETAIL_LABEL)
            value_element = detail.find_element(*self.DETAIL_VALUE)
            label = label_element.text.replace(":", "").strip()
            value = value_element.text.strip()
            details[label] = value
        
        return details
    
    def click_delete_journal_button(self, index):
        """
        Click the delete button on a specific journal card
        
        Args:
            index (int): Index of the journal card
        """
        journal_card = self.get_journal_card_by_index(index)
        if journal_card:
            delete_btn = journal_card.find_element(*self.DELETE_JOURNAL_BTN)
            delete_btn.click()
    
    def is_journal_modal_present(self):
        """
        Check if journal modal is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.JOURNAL_MODAL)
    
    def is_journal_modal_visible(self):
        """
        Check if journal modal is visible
        
        Returns:
            bool: True if visible, False otherwise
        """
        modal = self.find_element(self.JOURNAL_MODAL)
        return modal.is_displayed()
    
    def close_journal_modal(self):
        """Close the journal modal"""
        close_btn = self.find_element(self.MODAL_CLOSE)
        close_btn.click()
    
    def get_modal_journal_date(self):
        """
        Get the journal date from modal
        
        Returns:
            str: Journal date from modal
        """
        return self.get_element_text(self.MODAL_JOURNAL_DATE)
    
    def get_modal_journal_title(self):
        """
        Get the journal title from modal
        
        Returns:
            str: Journal title from modal
        """
        return self.get_element_text(self.MODAL_JOURNAL_TITLE)
    
    def get_modal_journal_theme(self):
        """
        Get the journal theme from modal
        
        Returns:
            str: Journal theme from modal
        """
        return self.get_element_text(self.MODAL_JOURNAL_THEME)
    
    def get_modal_journal_prompt(self):
        """
        Get the journal prompt from modal
        
        Returns:
            str: Journal prompt from modal
        """
        return self.get_element_text(self.MODAL_JOURNAL_PROMPT)
    
    def get_modal_journal_answer(self):
        """
        Get the journal answer from modal
        
        Returns:
            str: Journal answer from modal
        """
        return self.get_element_text(self.MODAL_JOURNAL_ANSWER)
    
    def get_modal_journal_details(self):
        """
        Get all journal details from modal
        
        Returns:
            dict: Dictionary containing modal journal details
        """
        details = {
            "date": self.get_modal_journal_date(),
            "title": self.get_modal_journal_title(),
            "theme": self.get_modal_journal_theme(),
            "prompt": self.get_modal_journal_prompt(),
            "answer": self.get_modal_journal_answer()
        }
        return details
    
    def is_search_input_present(self):
        """
        Check if search input is present
        
        Returns:
            bool: True if present, False otherwise
        """
        return self.is_element_present(self.SEARCH_INPUT)
    
    def enter_search_term(self, search_term):
        """
        Enter search term in search input
        
        Args:
            search_term (str): Search term to enter
        """
        if self.is_search_input_present():
            self.send_keys_to_element(self.SEARCH_INPUT, search_term)
    
    def clear_search_input(self):
        """Clear the search input"""
        if self.is_search_input_present():
            search_input = self.find_element(self.SEARCH_INPUT)
            search_input.clear()
    
    def verify_journal_card_structure(self, index):
        """
        Verify that a journal card has the correct structure
        
        Args:
            index (int): Index of the journal card
            
        Returns:
            bool: True if structure is correct, False otherwise
        """
        journal_card = self.get_journal_card_by_index(index)
        if not journal_card:
            return False
        
        # Check for required elements
        required_elements = [
            self.JOURNAL_DATE,
            self.JOURNAL_DETAILS,
            self.EXPAND_HINT,
            self.DELETE_JOURNAL_BTN
        ]
        
        for element_locator in required_elements:
            try:
                journal_card.find_element(*element_locator)
            except:
                return False
        
        return True
    
    def verify_journal_details_present(self, index):
        """
        Verify that a journal card has all required details
        
        Args:
            index (int): Index of the journal card
            
        Returns:
            bool: True if all details are present, False otherwise
        """
        details = self.get_journal_card_details(index)
        if not details:
            return False
        
        required_details = ["TITLE", "THEME", "PROMPT", "ANSWER"]
        for detail in required_details:
            if detail not in details or not details[detail]:
                return False
        
        return True
    
    def wait_for_my_journals_load(self):
        """Wait for My Journals page to load completely"""
        self.wait_for_element_visible(self.MY_JOURNALS_TITLE)
        self.wait_for_element_visible(self.MY_JOURNALS_CONTAINER)
    
    def wait_for_journal_modal_load(self):
        """Wait for journal modal to load completely"""
        self.wait_for_element_visible(self.JOURNAL_MODAL)
        self.wait_for_element_visible(self.MODAL_CONTENT)
        self.wait_for_element_visible(self.MODAL_JOURNAL_DATE) 