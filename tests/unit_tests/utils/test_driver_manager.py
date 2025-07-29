"""
Unit tests for DriverManager class
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from tests.utils.driver_manager import DriverManager


class TestDriverManager:
    """Test cases for DriverManager class"""
    
    def setUp(self):
        """Set up test data"""
        self.driver_manager = DriverManager()
    
    def test_initialization_default_values(self):
        """Test DriverManager initialization with default values"""
        manager = DriverManager()
        
        self.assertIsNone(manager.driver)
        # Default values should be set from TestConfig
        self.assertIsNotNone(manager.browser)
        self.assertIsNotNone(manager.headless)
    
    def test_initialization_custom_values(self):
        """Test DriverManager initialization with custom values"""
        manager = DriverManager(browser='firefox', headless=True)
        
        self.assertEqual(manager.browser, 'firefox')
        self.assertTrue(manager.headless)
        self.assertIsNone(manager.driver)
    
    @patch('tests.utils.driver_manager.TestConfig.BROWSER', 'chrome')
    @patch('tests.utils.driver_manager.TestConfig.HEADLESS', False)
    def test_get_driver_chrome(self):
        """Test getting Chrome driver"""
        with patch.object(self.driver_manager, '_get_chrome_driver') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            result = self.driver_manager.get_driver()
            
            self.assertEqual(result, mock_driver)
            mock_chrome.assert_called_once()
    
    @patch('tests.utils.driver_manager.TestConfig.BROWSER', 'firefox')
    @patch('tests.utils.driver_manager.TestConfig.HEADLESS', False)
    def test_get_driver_firefox(self):
        """Test getting Firefox driver"""
        with patch.object(self.driver_manager, '_get_firefox_driver') as mock_firefox:
            mock_driver = Mock()
            mock_firefox.return_value = mock_driver
            
            result = self.driver_manager.get_driver()
            
            self.assertEqual(result, mock_driver)
            mock_firefox.assert_called_once()
    
    @patch('tests.utils.driver_manager.TestConfig.BROWSER', 'edge')
    @patch('tests.utils.driver_manager.TestConfig.HEADLESS', False)
    def test_get_driver_edge(self):
        """Test getting Edge driver"""
        with patch.object(self.driver_manager, '_get_edge_driver') as mock_edge:
            mock_driver = Mock()
            mock_edge.return_value = mock_driver
            
            result = self.driver_manager.get_driver()
            
            self.assertEqual(result, mock_driver)
            mock_edge.assert_called_once()
    
    def test_get_driver_unsupported_browser(self):
        """Test getting driver for unsupported browser"""
        self.driver_manager.browser = 'unsupported'
        
        with self.assertRaises(ValueError) as context:
            self.driver_manager.get_driver()
        
        self.assertIn('Unsupported browser', str(context.exception))
    
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_WIDTH', 1920)
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_HEIGHT', 1080)
    @patch('tests.utils.driver_manager.TestConfig.IMPLICIT_WAIT', 10)
    @patch('tests.utils.driver_manager.TestConfig.PAGE_LOAD_TIMEOUT', 30)
    @patch('tests.utils.driver_manager.ChromeDriverManager')
    @patch('tests.utils.driver_manager.ChromeService')
    @patch('tests.utils.driver_manager.webdriver.Chrome')
    def test_get_chrome_driver_success(self, mock_chrome_driver, mock_service, mock_manager):
        """Test successful Chrome driver creation"""
        # Mock the driver manager
        mock_manager_instance = Mock()
        mock_manager_instance.install.return_value = '/path/to/chromedriver'
        mock_manager.return_value = mock_manager_instance
        
        # Mock the service
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # Mock the driver
        mock_driver_instance = Mock()
        mock_chrome_driver.return_value = mock_driver_instance
        
        # Mock os.path.exists to return True
        with patch('os.path.exists', return_value=True):
            with patch('os.chmod'):
                result = self.driver_manager._get_chrome_driver()
        
        self.assertEqual(result, mock_driver_instance)
        mock_chrome_driver.assert_called_once_with(
            service=mock_service_instance,
            options=mock_chrome_driver.call_args[1]['options']
        )
    
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_WIDTH', 1920)
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_HEIGHT', 1080)
    @patch('tests.utils.driver_manager.TestConfig.IMPLICIT_WAIT', 10)
    @patch('tests.utils.driver_manager.TestConfig.PAGE_LOAD_TIMEOUT', 30)
    @patch('tests.utils.driver_manager.ChromeDriverManager')
    def test_get_chrome_driver_headless(self, mock_manager):
        """Test Chrome driver creation in headless mode"""
        self.driver_manager.headless = True
        
        # Mock the driver manager
        mock_manager_instance = Mock()
        mock_manager_instance.install.return_value = '/path/to/chromedriver'
        mock_manager.return_value = mock_manager_instance
        
        with patch('tests.utils.driver_manager.ChromeService'):
            with patch('tests.utils.driver_manager.webdriver.Chrome') as mock_chrome:
                with patch('os.path.exists', return_value=True):
                    with patch('os.chmod'):
                        self.driver_manager._get_chrome_driver()
        
        # Check that headless argument was added
        chrome_options = mock_chrome.call_args[1]['options']
        self.assertIn('--headless', chrome_options.arguments)
    
    @patch('tests.utils.driver_manager.ChromeDriverManager')
    def test_get_chrome_driver_file_not_found(self, mock_manager):
        """Test Chrome driver creation when file not found"""
        # Mock the driver manager to return invalid path
        mock_manager_instance = Mock()
        mock_manager_instance.install.return_value = '/invalid/path/chromedriver'
        mock_manager.return_value = mock_manager_instance
        
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError) as context:
                self.driver_manager._get_chrome_driver()
            
            self.assertIn('ChromeDriver not found', str(context.exception))
    
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_WIDTH', 1920)
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_HEIGHT', 1080)
    @patch('tests.utils.driver_manager.TestConfig.IMPLICIT_WAIT', 10)
    @patch('tests.utils.driver_manager.TestConfig.PAGE_LOAD_TIMEOUT', 30)
    @patch('tests.utils.driver_manager.GeckoDriverManager')
    @patch('tests.utils.driver_manager.FirefoxService')
    @patch('tests.utils.driver_manager.webdriver.Firefox')
    def test_get_firefox_driver_success(self, mock_firefox_driver, mock_service, mock_manager):
        """Test successful Firefox driver creation"""
        # Mock the driver manager
        mock_manager_instance = Mock()
        mock_manager_instance.install.return_value = '/path/to/geckodriver'
        mock_manager.return_value = mock_manager_instance
        
        # Mock the service
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # Mock the driver
        mock_driver_instance = Mock()
        mock_firefox_driver.return_value = mock_driver_instance
        
        result = self.driver_manager._get_firefox_driver()
        
        self.assertEqual(result, mock_driver_instance)
        mock_firefox_driver.assert_called_once_with(
            service=mock_service_instance,
            options=mock_firefox_driver.call_args[1]['options']
        )
    
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_WIDTH', 1920)
    @patch('tests.utils.driver_manager.TestConfig.WINDOW_HEIGHT', 1080)
    @patch('tests.utils.driver_manager.TestConfig.IMPLICIT_WAIT', 10)
    @patch('tests.utils.driver_manager.TestConfig.PAGE_LOAD_TIMEOUT', 30)
    @patch('tests.utils.driver_manager.EdgeChromiumDriverManager')
    @patch('tests.utils.driver_manager.EdgeService')
    @patch('tests.utils.driver_manager.webdriver.Edge')
    def test_get_edge_driver_success(self, mock_edge_driver, mock_service, mock_manager):
        """Test successful Edge driver creation"""
        # Mock the driver manager
        mock_manager_instance = Mock()
        mock_manager_instance.install.return_value = '/path/to/msedgedriver'
        mock_manager.return_value = mock_manager_instance
        
        # Mock the service
        mock_service_instance = Mock()
        mock_service.return_value = mock_service_instance
        
        # Mock the driver
        mock_driver_instance = Mock()
        mock_edge_driver.return_value = mock_driver_instance
        
        result = self.driver_manager._get_edge_driver()
        
        self.assertEqual(result, mock_driver_instance)
        mock_edge_driver.assert_called_once_with(
            service=mock_service_instance,
            options=mock_edge_driver.call_args[1]['options']
        )
    
    @patch('tests.utils.driver_manager.ChromeDriverManager')
    def test_get_chrome_driver_exception_handling(self, mock_manager):
        """Test Chrome driver creation exception handling"""
        # Mock the driver manager to raise an exception
        mock_manager_instance = Mock()
        mock_manager_instance.install.side_effect = Exception("Driver installation failed")
        mock_manager.return_value = mock_manager_instance
        
        with patch('builtins.print') as mock_print:
            with self.assertRaises(Exception):
                self.driver_manager._get_chrome_driver()
            
            # Check that error was printed
            mock_print.assert_called()
            self.assertIn('Error creating Chrome driver', mock_print.call_args[0][0])
    
    def test_chrome_options_configuration(self):
        """Test Chrome options configuration"""
        with patch('tests.utils.driver_manager.ChromeOptions') as mock_options:
            mock_options_instance = Mock()
            mock_options.return_value = mock_options_instance
            
            with patch('tests.utils.driver_manager.ChromeDriverManager'):
                with patch('tests.utils.driver_manager.ChromeService'):
                    with patch('tests.utils.driver_manager.webdriver.Chrome'):
                        with patch('os.path.exists', return_value=True):
                            with patch('os.chmod'):
                                self.driver_manager._get_chrome_driver()
            
            # Check that options were configured
            mock_options_instance.add_argument.assert_called()
            calls = mock_options_instance.add_argument.call_args_list
            
            # Check for specific arguments
            argument_values = [call[0][0] for call in calls]
            self.assertIn('--no-sandbox', argument_values)
            self.assertIn('--disable-dev-shm-usage', argument_values)
            self.assertIn('--disable-gpu', argument_values)
    
    def test_firefox_options_configuration(self):
        """Test Firefox options configuration"""
        with patch('tests.utils.driver_manager.FirefoxOptions') as mock_options:
            mock_options_instance = Mock()
            mock_options.return_value = mock_options_instance
            
            with patch('tests.utils.driver_manager.GeckoDriverManager'):
                with patch('tests.utils.driver_manager.FirefoxService'):
                    with patch('tests.utils.driver_manager.webdriver.Firefox'):
                        self.driver_manager._get_firefox_driver()
            
            # Check that options were configured
            mock_options_instance.add_argument.assert_called()
    
    def test_edge_options_configuration(self):
        """Test Edge options configuration"""
        with patch('tests.utils.driver_manager.EdgeOptions') as mock_options:
            mock_options_instance = Mock()
            mock_options.return_value = mock_options_instance
            
            with patch('tests.utils.driver_manager.EdgeChromiumDriverManager'):
                with patch('tests.utils.driver_manager.EdgeService'):
                    with patch('tests.utils.driver_manager.webdriver.Edge'):
                        self.driver_manager._get_edge_driver()
            
            # Check that options were configured
            mock_options_instance.add_argument.assert_called()
    
    @patch('tests.utils.driver_manager.TestConfig.IMPLICIT_WAIT', 10)
    @patch('tests.utils.driver_manager.TestConfig.PAGE_LOAD_TIMEOUT', 30)
    def test_driver_timeout_configuration(self):
        """Test driver timeout configuration"""
        with patch('tests.utils.driver_manager.ChromeDriverManager'):
            with patch('tests.utils.driver_manager.ChromeService'):
                with patch('tests.utils.driver_manager.webdriver.Chrome') as mock_chrome:
                    with patch('os.path.exists', return_value=True):
                        with patch('os.chmod'):
                            mock_driver_instance = Mock()
                            mock_chrome.return_value = mock_driver_instance
                            
                            self.driver_manager._get_chrome_driver()
            
            # Check that timeouts were set
            mock_driver_instance.implicitly_wait.assert_called_once_with(10)
            mock_driver_instance.set_page_load_timeout.assert_called_once_with(30) 