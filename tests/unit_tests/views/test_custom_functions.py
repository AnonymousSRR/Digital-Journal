"""
Unit tests for custom functions in views module
"""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import Http404, JsonResponse
from django.contrib import messages
from unittest.mock import Mock, patch, MagicMock
from authentication.views import (
    generate_theme_prompt,
    AuthenticationView
)
from authentication.models import CustomUser, Theme, JournalEntry
from authentication.forms import CustomUserCreationForm, CustomAuthenticationForm
import requests

User = get_user_model()


class TestGenerateThemePrompt(TestCase):
    """Test cases for generate_theme_prompt custom function"""
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_success(self, mock_post):
        """Test successful API call to Cohere"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'generations': [{'text': 'How have you grown as a leader recently?'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = generate_theme_prompt('Leadership', 'Leadership themes')
        
        assert result == 'How have you grown as a leader recently?'
        mock_post.assert_called_once()
        
        # Verify API call parameters
        call_args = mock_post.call_args
        assert call_args[1]['headers']['Authorization'] == 'Bearer yyvejL50thRkw70IRXctuFKyrkBwJ0QUBYBt6nEn'
        assert call_args[1]['json']['model'] == 'command'
        assert call_args[1]['json']['max_tokens'] == 100
        assert call_args[1]['json']['temperature'] == 0.7
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_with_quotes(self, mock_post):
        """Test response cleaning when API returns quoted text"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'generations': [{'text': '"How have you grown as a leader recently?"'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = generate_theme_prompt('Leadership', 'Leadership themes')
        
        # Quotes should be removed
        assert result == 'How have you grown as a leader recently?'
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_api_error(self, mock_post):
        """Test fallback behavior when API call fails"""
        mock_post.side_effect = Exception("API Error")
        
        result = generate_theme_prompt('Technology Impact', 'Technology themes')
        
        # Should return fallback prompt from theme examples
        assert 'balance' in result.lower()
        assert 'delivery' in result.lower()
        assert 'technical' in result.lower()
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_unknown_theme(self, mock_post):
        """Test fallback behavior for unknown theme"""
        mock_post.side_effect = Exception("API Error")
        
        result = generate_theme_prompt('Unknown Theme', 'Unknown description')
        
        # Should return generic fallback prompt
        assert 'unknown theme' in result.lower()
        assert 'impacted' in result.lower()
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_requests_exception(self, mock_post):
        """Test handling of requests.RequestException"""
        mock_post.side_effect = Exception("Request failed")
        
        result = generate_theme_prompt('Team Impact', 'Team themes')
        
        # Should return fallback prompt from theme examples
        assert 'leadership style' in result.lower()
        assert 'situation' in result.lower()
        assert 'individual' in result.lower()
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_timeout(self, mock_post):
        """Test handling of timeout errors with retry logic"""
        # Mock timeout exception for all attempts
        mock_post.side_effect = requests.exceptions.Timeout("Read timed out. (read timeout=10)")
        
        result = generate_theme_prompt('Business Impact', 'Business themes')
        
        # Should return fallback prompt after timeout
        assert 'stakeholders' in result.lower()
        assert 'engineering' in result.lower()
        assert 'strategic' in result.lower()
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_retry_success(self, mock_post):
        """Test retry logic with eventual success"""
        # First call fails, second call succeeds
        mock_response = Mock()
        mock_response.json.return_value = {
            'generations': [{'text': 'How have you grown as a leader recently?'}]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_post.side_effect = [
            requests.exceptions.Timeout("Read timed out. (read timeout=10)"),
            mock_response
        ]
        
        result = generate_theme_prompt('Leadership', 'Leadership themes')
        
        assert result == 'How have you grown as a leader recently?'
        assert mock_post.call_count == 2
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_connection_error(self, mock_post):
        """Test handling of connection errors"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = generate_theme_prompt('Org Impact', 'Org themes')
        
        # Should return fallback prompt from theme examples
        assert 'organization' in result.lower()
        assert 'contributed' in result.lower()
        assert 'immediate' in result.lower()
    
    def test_generate_theme_prompt_theme_examples(self):
        """Test that theme examples are properly defined"""
        # Test that all expected themes have examples
        expected_themes = [
            'Technology Impact',
            'Delivery Impact', 
            'Business Impact',
            'Team Impact',
            'Org Impact'
        ]
        
        # This test verifies the function structure without making API calls
        with patch('authentication.views.requests.post') as mock_post:
            mock_post.side_effect = Exception("Test")
            
            for theme in expected_themes:
                result = generate_theme_prompt(theme, f'{theme} description')
                # Check that the result contains keywords from the theme examples
                if theme == 'Technology Impact':
                    assert 'balance' in result.lower() or 'delivery' in result.lower()
                elif theme == 'Delivery Impact':
                    assert 'delivery' in result.lower() or 'quality' in result.lower()
                elif theme == 'Business Impact':
                    assert 'stakeholders' in result.lower() or 'business' in result.lower()
                elif theme == 'Team Impact':
                    assert 'leadership' in result.lower() or 'team' in result.lower()
                elif theme == 'Org Impact':
                    assert 'organization' in result.lower() or 'culture' in result.lower()


class TestAuthenticationViewHelperMethods(TestCase):
    """Test cases for helper methods in AuthenticationView"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.view = AuthenticationView()
        self.view.request = self.factory.get('/')
    
    def test_get_active_tab_from_post_signup(self):
        """Test _get_active_tab method with POST signup action"""
        self.view.request = self.factory.post('/', {'form_action': '/auth/?tab=signup'})
        self.view.request.method = 'POST'
        
        result = self.view._get_active_tab()
        
        assert result == 'signup'
    
    def test_get_active_tab_from_post_signin(self):
        """Test _get_active_tab method with POST signin action"""
        self.view.request = self.factory.post('/', {'form_action': '/auth/'})
        self.view.request.method = 'POST'
        
        result = self.view._get_active_tab()
        
        assert result == 'signin'
    
    def test_get_active_tab_from_get_signup(self):
        """Test _get_active_tab method with GET signup tab"""
        self.view.request = self.factory.get('/?tab=signup')
        
        result = self.view._get_active_tab()
        
        assert result == 'signup'
    
    def test_get_active_tab_from_get_signin(self):
        """Test _get_active_tab method with GET signin tab"""
        self.view.request = self.factory.get('/?tab=signin')
        
        result = self.view._get_active_tab()
        
        assert result == 'signin'
    
    def test_get_active_tab_default(self):
        """Test _get_active_tab method with no tab specified"""
        self.view.request = self.factory.get('/')
        
        result = self.view._get_active_tab()
        
        assert result == 'signin'
    
    @patch('authentication.views.messages.success')
    @patch('authentication.views.messages.error')
    def test_handle_signup_success(self, mock_error, mock_success):
        """Test _handle_signup method with successful user creation"""
        self.view.request = self.factory.post('/')
        
        # Create a mock form with valid data
        form = Mock()
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        form.save.return_value = user
        
        result = self.view._handle_signup(form)
        
        # Verify success message was called
        mock_success.assert_called_once()
        assert 'Account created successfully' in mock_success.call_args[0][1]
        
        # Verify redirect
        assert result.status_code == 302
        assert 'tab=signin' in result.url
    
    @patch('authentication.views.messages.error')
    def test_handle_signup_exception(self, mock_error):
        """Test _handle_signup method with exception during user creation"""
        self.view.request = self.factory.post('/')
        
        # Create a mock form that raises an exception
        form = Mock()
        form.save.side_effect = Exception("Database error")
        # Mock form.errors to be a dictionary-like object
        form.errors = {'__all__': ['Database error']}
        
        result = self.view._handle_signup(form)
        
        # Verify error message was called
        mock_error.assert_called()
        # Should call form_invalid
        assert result is not None
    
    @patch('authentication.views.authenticate')
    @patch('authentication.views.login')
    @patch('authentication.views.messages.success')
    def test_handle_signin_success(self, mock_success, mock_login, mock_authenticate):
        """Test _handle_signin method with successful authentication"""
        self.view.request = self.factory.post('/')
        
        # Create a mock form with valid data
        form = Mock()
        form.cleaned_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
        
        # Create a mock user
        user = Mock()
        user.get_full_name.return_value = 'John Doe'
        mock_authenticate.return_value = user
        
        result = self.view._handle_signin(form)
        
        # Verify authentication was called
        mock_authenticate.assert_called_once_with(
            self.view.request, 
            username='test@example.com', 
            password='testpass123'
        )
        
        # Verify login was called
        mock_login.assert_called_once_with(self.view.request, user)
        
        # Verify success message
        mock_success.assert_called_once()
        assert 'Welcome back' in mock_success.call_args[0][1]
    
    @patch('authentication.views.authenticate')
    @patch('authentication.views.messages.error')
    def test_handle_signin_invalid_credentials(self, mock_error, mock_authenticate):
        """Test _handle_signin method with invalid credentials"""
        self.view.request = self.factory.post('/')
        
        # Create a mock form with valid data
        form = Mock()
        form.cleaned_data = {
            'username': 'test@example.com',
            'password': 'wrongpassword'
        }
        # Mock form.errors to be a dictionary-like object
        form.errors = {'__all__': ['Invalid credentials']}
        
        # Mock authentication failure
        mock_authenticate.return_value = None
        
        result = self.view._handle_signin(form)
        
        # Verify error message was called
        mock_error.assert_called()
        # Should call form_invalid
        assert result is not None
    
    def test_get_context_data_signin_tab(self):
        """Test get_context_data method with signin tab active"""
        self.view.request = self.factory.get('/?tab=signin')
        
        context = self.view.get_context_data()
        
        assert context['active_tab'] == 'signin'
        assert context['signin_form'] is not None
        assert context['signup_form'] is None
    
    def test_get_context_data_signup_tab(self):
        """Test get_context_data method with signup tab active"""
        self.view.request = self.factory.get('/?tab=signup')
        
        context = self.view.get_context_data()
        
        assert context['active_tab'] == 'signup'
        assert context['signin_form'] is None
        assert context['signup_form'] is not None 