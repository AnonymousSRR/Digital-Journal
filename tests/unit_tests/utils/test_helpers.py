"""
Unit tests for helper utility functions
"""
import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from tests.utils.helpers import (
    generate_random_user_data,
    generate_random_journal_data,
    take_screenshot_on_failure,
    wait_for_element_with_retry,
    verify_element_text,
    verify_element_attribute,
    scroll_to_element,
    wait_for_page_load,
    get_test_data,
    log_test_step,
    verify_url_contains,
    verify_page_title_contains
)


class TestGenerateRandomUserData:
    """Test cases for generate_random_user_data function"""
    
    def test_generate_random_user_data_structure(self):
        """Test that generated user data has correct structure"""
        user_data = generate_random_user_data()
        
        self.assertIsInstance(user_data, dict)
        self.assertIn('first_name', user_data)
        self.assertIn('last_name', user_data)
        self.assertIn('email', user_data)
        self.assertIn('password', user_data)
    
    def test_generate_random_user_data_values(self):
        """Test that generated user data has valid values"""
        user_data = generate_random_user_data()
        
        # Check first_name
        self.assertIsInstance(user_data['first_name'], str)
        self.assertTrue(user_data['first_name'].startswith('random'))
        self.assertTrue(len(user_data['first_name']) > 6)
        
        # Check last_name
        self.assertIsInstance(user_data['last_name'], str)
        self.assertTrue(user_data['last_name'].startswith('lastrandom'))
        self.assertTrue(len(user_data['last_name']) > 10)
        
        # Check email
        self.assertIsInstance(user_data['email'], str)
        self.assertTrue(user_data['email'].startswith('random'))
        self.assertTrue(user_data['email'].endswith('@gmail.com'))
        
        # Check password
        self.assertIsInstance(user_data['password'], str)
        self.assertEqual(user_data['password'], 'TestPassword123!')
    
    def test_generate_random_user_data_uniqueness(self):
        """Test that multiple calls generate different data"""
        user_data1 = generate_random_user_data()
        user_data2 = generate_random_user_data()
        
        # Should be different due to random number
        self.assertNotEqual(user_data1['first_name'], user_data2['first_name'])
        self.assertNotEqual(user_data1['last_name'], user_data2['last_name'])
        self.assertNotEqual(user_data1['email'], user_data2['email'])


class TestGenerateRandomJournalData:
    """Test cases for generate_random_journal_data function"""
    
    def test_generate_random_journal_data_structure(self):
        """Test that generated journal data has correct structure"""
        journal_data = generate_random_journal_data()
        
        self.assertIsInstance(journal_data, dict)
        self.assertIn('title', journal_data)
        self.assertIn('answer', journal_data)
    
    def test_generate_random_journal_data_values(self):
        """Test that generated journal data has valid values"""
        journal_data = generate_random_journal_data()
        
        # Check title
        self.assertIsInstance(journal_data['title'], str)
        self.assertTrue(journal_data['title'].startswith('Automated Journal Entry'))
        self.assertTrue(len(journal_data['title']) > 20)
        
        # Check answer
        self.assertIsInstance(journal_data['answer'], str)
        self.assertEqual(journal_data['answer'], 'This is a random automated answer for testing purposes.')
    
    def test_generate_random_journal_data_uniqueness(self):
        """Test that multiple calls generate different data"""
        journal_data1 = generate_random_journal_data()
        journal_data2 = generate_random_journal_data()
        
        # Should be different due to random number
        self.assertNotEqual(journal_data1['title'], journal_data2['title'])


class TestTakeScreenshotOnFailure:
    """Test cases for take_screenshot_on_failure function"""
    
    @patch('tests.utils.helpers.TestConfig.TAKE_SCREENSHOT_ON_FAILURE', True)
    @patch('tests.utils.helpers.TestConfig.SCREENSHOT_DIR', '/tmp/screenshots')
    @patch('os.makedirs')
    @patch('os.path.join')
    def test_take_screenshot_on_failure_enabled(self, mock_join, mock_makedirs):
        """Test screenshot taking when enabled"""
        mock_driver = Mock()
        mock_driver.save_screenshot = Mock()
        mock_join.return_value = '/tmp/screenshots/failure_test_123.png'
        
        result = take_screenshot_on_failure(mock_driver, 'test')
        
        mock_makedirs.assert_called_once_with('/tmp/screenshots', exist_ok=True)
        mock_driver.save_screenshot.assert_called_once_with('/tmp/screenshots/failure_test_123.png')
        self.assertEqual(result, '/tmp/screenshots/failure_test_123.png')
    
    @patch('tests.utils.helpers.TestConfig.TAKE_SCREENSHOT_ON_FAILURE', False)
    def test_take_screenshot_on_failure_disabled(self):
        """Test screenshot taking when disabled"""
        mock_driver = Mock()
        
        result = take_screenshot_on_failure(mock_driver, 'test')
        
        self.assertIsNone(result)
        mock_driver.save_screenshot.assert_not_called()


class TestWaitForElementWithRetry:
    """Test cases for wait_for_element_with_retry function"""
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    @patch('time.sleep')
    def test_wait_for_element_with_retry_success_first_attempt(self, mock_sleep):
        """Test successful element finding on first attempt"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = wait_for_element_with_retry(mock_driver, ('id', 'test'))
        
        self.assertEqual(result, mock_element)
        mock_sleep.assert_not_called()
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    @patch('time.sleep')
    def test_wait_for_element_with_retry_success_second_attempt(self, mock_sleep):
        """Test successful element finding on second attempt"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait = Mock()
        mock_wait.until.side_effect = [Exception(), mock_element]
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = wait_for_element_with_retry(mock_driver, ('id', 'test'))
        
        self.assertEqual(result, mock_element)
        mock_sleep.assert_called_once_with(1)
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    @patch('time.sleep')
    def test_wait_for_element_with_retry_failure(self, mock_sleep):
        """Test element finding failure after all attempts"""
        mock_driver = Mock()
        mock_wait = Mock()
        mock_wait.until.side_effect = Exception()
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = wait_for_element_with_retry(mock_driver, ('id', 'test'))
        
        self.assertIsNone(result)
        # Should sleep twice (for 3 attempts total)
        self.assertEqual(mock_sleep.call_count, 2)


class TestVerifyElementText:
    """Test cases for verify_element_text function"""
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    def test_verify_element_text_success(self):
        """Test successful text verification"""
        mock_driver = Mock()
        mock_wait = Mock()
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = verify_element_text(mock_driver, ('id', 'test'), 'expected text')
        
        self.assertTrue(result)
        mock_wait.until.assert_called_once()
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    def test_verify_element_text_failure(self):
        """Test failed text verification"""
        mock_driver = Mock()
        mock_wait = Mock()
        mock_wait.until.side_effect = Exception()
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = verify_element_text(mock_driver, ('id', 'test'), 'expected text')
        
        self.assertFalse(result)


class TestVerifyElementAttribute:
    """Test cases for verify_element_attribute function"""
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    def test_verify_element_attribute_success(self):
        """Test successful attribute verification"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.get_attribute.return_value = 'test-class'
        mock_driver.find_element.return_value = mock_element
        mock_wait = Mock()
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = verify_element_attribute(mock_driver, ('id', 'test'), 'class', 'test')
        
        self.assertTrue(result)
        mock_wait.until.assert_called_once()
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    def test_verify_element_attribute_failure(self):
        """Test failed attribute verification"""
        mock_driver = Mock()
        mock_wait = Mock()
        mock_wait.until.side_effect = Exception()
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            result = verify_element_attribute(mock_driver, ('id', 'test'), 'class', 'test')
        
        self.assertFalse(result)


class TestScrollToElement:
    """Test cases for scroll_to_element function"""
    
    @patch('tests.utils.helpers.TestConfig.IMPLICIT_WAIT', 10)
    @patch('time.sleep')
    def test_scroll_to_element(self, mock_sleep):
        """Test scrolling to element"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            scroll_to_element(mock_driver, ('id', 'test'))
        
        mock_driver.execute_script.assert_called_once_with("arguments[0].scrollIntoView(true);", mock_element)
        mock_sleep.assert_called_once_with(0.5)


class TestWaitForPageLoad:
    """Test cases for wait_for_page_load function"""
    
    @patch('tests.utils.helpers.TestConfig.PAGE_LOAD_TIMEOUT', 30)
    def test_wait_for_page_load(self):
        """Test waiting for page load"""
        mock_driver = Mock()
        mock_driver.execute_script.return_value = "complete"
        mock_wait = Mock()
        
        with patch('tests.utils.helpers.WebDriverWait', return_value=mock_wait):
            wait_for_page_load(mock_driver)
        
        mock_wait.until.assert_called_once()


class TestGetTestData:
    """Test cases for get_test_data function"""
    
    @patch('tests.utils.helpers.TestConfig.TEST_USER_EMAIL', 'test@example.com')
    @patch('tests.utils.helpers.TestConfig.TEST_USER_PASSWORD', 'testpass123')
    @patch('tests.utils.helpers.TestConfig.TEST_USER_FIRST_NAME', 'John')
    @patch('tests.utils.helpers.TestConfig.TEST_USER_LAST_NAME', 'Doe')
    def test_get_test_data_valid_user(self):
        """Test getting valid user test data"""
        result = get_test_data('valid_user')
        
        expected = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        self.assertEqual(result, expected)
    
    def test_get_test_data_invalid_user(self):
        """Test getting invalid user test data"""
        result = get_test_data('invalid_user')
        
        expected = {
            'email': 'invalid@example.com',
            'password': 'wrongpassword',
            'first_name': 'Invalid',
            'last_name': 'User'
        }
        self.assertEqual(result, expected)
    
    def test_get_test_data_unknown_type(self):
        """Test getting unknown test data type"""
        result = get_test_data('unknown_type')
        
        self.assertEqual(result, {})


class TestLogTestStep:
    """Test cases for log_test_step function"""
    
    @patch('builtins.print')
    def test_log_test_step(self, mock_print):
        """Test logging test step"""
        log_test_step('Test step description')
        
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn('STEP:', call_args)
        self.assertIn('Test step description', call_args)


class TestVerifyUrlContains:
    """Test cases for verify_url_contains function"""
    
    def test_verify_url_contains_success(self):
        """Test successful URL verification"""
        mock_driver = Mock()
        mock_driver.current_url = 'https://example.com/test-page'
        
        result = verify_url_contains(mock_driver, 'test-page')
        
        self.assertTrue(result)
    
    def test_verify_url_contains_failure(self):
        """Test failed URL verification"""
        mock_driver = Mock()
        mock_driver.current_url = 'https://example.com/other-page'
        
        result = verify_url_contains(mock_driver, 'test-page')
        
        self.assertFalse(result)


class TestVerifyPageTitleContains:
    """Test cases for verify_page_title_contains function"""
    
    def test_verify_page_title_contains_success(self):
        """Test successful page title verification"""
        mock_driver = Mock()
        mock_driver.title = 'Test Page - Example Site'
        
        result = verify_page_title_contains(mock_driver, 'Test Page')
        
        self.assertTrue(result)
    
    def test_verify_page_title_contains_failure(self):
        """Test failed page title verification"""
        mock_driver = Mock()
        mock_driver.title = 'Other Page - Example Site'
        
        result = verify_page_title_contains(mock_driver, 'Test Page')
        
        self.assertFalse(result) 