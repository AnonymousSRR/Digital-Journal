"""
Unit tests for authentication views custom functions
"""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import Http404
from unittest.mock import Mock, patch, MagicMock
from authentication.views import (
    generate_theme_prompt,
    my_journals_view,
    delete_journal_entry,
    toggle_bookmark,
    theme_selector_view,
    answer_prompt_view,
    SignUpView,
    SignInView,
    AuthenticationView,
    logout_view
)
from authentication.models import CustomUser, Theme, JournalEntry
from authentication.forms import CustomUserCreationForm, CustomAuthenticationForm

User = get_user_model()


class TestGenerateThemePrompt:
    """Test cases for generate_theme_prompt custom function"""
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_success(self, mock_post):
        """Test custom generate_theme_prompt function with successful API call"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'generations': [{'text': 'How have you grown as a leader recently?'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = generate_theme_prompt('Leadership', 'Leadership themes')
        
        self.assertEqual(result, 'How have you grown as a leader recently?')
        mock_post.assert_called_once()
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_api_error(self, mock_post):
        """Test custom generate_theme_prompt function with API error"""
        # Mock API error
        mock_post.side_effect = Exception("API Error")
        
        result = generate_theme_prompt('Leadership', 'Leadership themes')
        
        # Should return fallback prompt
        self.assertIn('Leadership', result.lower())
        self.assertIn('impacted', result.lower())
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_response_cleaning(self, mock_post):
        """Test custom response cleaning in generate_theme_prompt"""
        # Mock response with quotes
        mock_response = Mock()
        mock_response.json.return_value = {
            'generations': [{'text': '"How have you grown as a leader recently?"'}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = generate_theme_prompt('Leadership', 'Leadership themes')
        
        # Quotes should be removed
        self.assertEqual(result, 'How have you grown as a leader recently?')
    
    @patch('authentication.views.requests.post')
    def test_generate_theme_prompt_with_fallback(self, mock_post):
        """Test custom fallback logic in generate_theme_prompt"""
        # Mock API error
        mock_post.side_effect = Exception("API Error")
        
        result = generate_theme_prompt('Team Management', 'Team management themes')
        
        # Should return fallback prompt
        self.assertIn('team management', result.lower())
        self.assertIn('impacted', result.lower())


class TestToggleBookmark(TestCase):
    """Test cases for toggle_bookmark view"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='Test theme description'
        )
        self.journal_entry = JournalEntry.objects.create(
            user=self.user,
            title='Test Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='Test answer',
            bookmarked=False
        )
    
    def test_toggle_bookmark_add_bookmark(self):
        """Test adding a bookmark to an entry"""
        request = self.factory.post(f'/home/toggle-bookmark/{self.journal_entry.id}/')
        request.user = self.user
        
        response = toggle_bookmark(request, self.journal_entry.id)
        
        # Refresh the entry from database
        self.journal_entry.refresh_from_db()
        self.assertTrue(self.journal_entry.bookmarked)
        self.assertEqual(response.status_code, 302)  # Redirect response
    
    def test_toggle_bookmark_remove_bookmark(self):
        """Test removing a bookmark from an entry"""
        # First add a bookmark
        self.journal_entry.bookmarked = True
        self.journal_entry.save()
        
        request = self.factory.post(f'/home/toggle-bookmark/{self.journal_entry.id}/')
        request.user = self.user
        
        response = toggle_bookmark(request, self.journal_entry.id)
        
        # Refresh the entry from database
        self.journal_entry.refresh_from_db()
        self.assertFalse(self.journal_entry.bookmarked)
        self.assertEqual(response.status_code, 302)  # Redirect response
    
    def test_toggle_bookmark_ajax_request(self):
        """Test toggle bookmark with AJAX request"""
        request = self.factory.post(
            f'/home/toggle-bookmark/{self.journal_entry.id}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        request.user = self.user
        
        response = toggle_bookmark(request, self.journal_entry.id)
        
        # Should return JSON response
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertTrue(response.json()['success'])
        self.assertTrue(response.json()['bookmarked'])
    
    def test_toggle_bookmark_unauthorized_user(self):
        """Test toggle bookmark with unauthorized user"""
        other_user = CustomUser.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Doe'
        )
        
        request = self.factory.post(f'/home/toggle-bookmark/{self.journal_entry.id}/')
        request.user = other_user
        
        # Should raise 404 for unauthorized access
        with self.assertRaises(Http404):
            toggle_bookmark(request, self.journal_entry.id)
    
    def test_toggle_bookmark_invalid_entry_id(self):
        """Test toggle bookmark with invalid entry ID"""
        request = self.factory.post('/home/toggle-bookmark/99999/')
        request.user = self.user
        
        # Should raise 404 for non-existent entry
        with self.assertRaises(Http404):
            toggle_bookmark(request, 99999)
    
    def test_toggle_bookmark_get_request(self):
        """Test toggle bookmark with GET request (should redirect)"""
        request = self.factory.get(f'/home/toggle-bookmark/{self.journal_entry.id}/')
        request.user = self.user
        
        response = toggle_bookmark(request, self.journal_entry.id)
        
        # Should redirect for GET requests
        self.assertEqual(response.status_code, 302)


class TestMyJournalsView(TestCase):
    """Test cases for my_journals_view with bookmark functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='Test theme description'
        )
        
        # Create bookmarked entry
        self.bookmarked_entry = JournalEntry.objects.create(
            user=self.user,
            title='Bookmarked Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='Test answer',
            bookmarked=True
        )
        
        # Create regular entry
        self.regular_entry = JournalEntry.objects.create(
            user=self.user,
            title='Regular Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='Test answer',
            bookmarked=False
        )
    
    def test_my_journals_view_bookmarked_first(self):
        """Test that bookmarked entries appear first"""
        request = self.factory.get('/home/my-journals/')
        request.user = self.user
        
        response = my_journals_view(request)
        
        self.assertEqual(response.status_code, 200)
        
        # Get the journal entries from context
        journal_entries = response.context['journal_entries']
        
        # First entry should be bookmarked
        self.assertEqual(journal_entries[0], self.bookmarked_entry)
        self.assertTrue(journal_entries[0].bookmarked)
        
        # Second entry should be regular
        self.assertEqual(journal_entries[1], self.regular_entry)
        self.assertFalse(journal_entries[1].bookmarked)


class TestAuthenticationView(TestCase):
    """Test cases for AuthenticationView custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_authentication_view_get_signin_tab(self):
        """Test custom get_form_class method with signin tab"""
        request = self.factory.get('/auth/?tab=signin')
        view = AuthenticationView()
        view.request = request
        
        form_class = view.get_form_class()
        
        self.assertEqual(form_class, CustomAuthenticationForm)
    
    def test_authentication_view_get_signup_tab(self):
        """Test custom get_form_class method with signup tab"""
        request = self.factory.get('/auth/?tab=signup')
        view = AuthenticationView()
        view.request = request
        
        form_class = view.get_form_class()
        
        self.assertEqual(form_class, CustomUserCreationForm)
    
    def test_get_active_tab_from_get(self):
        """Test custom _get_active_tab method from GET request"""
        request = self.factory.get('/auth/?tab=signup')
        view = AuthenticationView()
        view.request = request
        
        active_tab = view._get_active_tab()
        
        self.assertEqual(active_tab, 'signup')
    
    def test_get_active_tab_default(self):
        """Test custom _get_active_tab method default value"""
        request = self.factory.get('/auth/')
        view = AuthenticationView()
        view.request = request
        
        active_tab = view._get_active_tab()
        
        self.assertEqual(active_tab, 'signin')


class TestSignInView(TestCase):
    """Test cases for SignInView custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_signin_view_get_context_data(self):
        """Test custom get_context_data method"""
        request = self.factory.get('/signin/')
        view = SignInView()
        view.request = request
        
        context = view.get_context_data()
        
        self.assertIn('active_tab', context)
        self.assertEqual(context['active_tab'], 'signin') 