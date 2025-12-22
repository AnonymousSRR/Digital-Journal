"""
Tests for FAB user preference functionality
Phase 3: Add User Preference to Disable/Enable FAB
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class FABUserPreferenceTests(TestCase):
    """Test suite to verify user preference for showing/hiding FAB"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
    
    def test_fab_visible_when_preference_enabled(self):
        """Test case 1: FAB visible when preference is enabled"""
        # Arrange: User has FAB preference enabled
        self.user.show_quick_add_fab = True
        self.user.save()
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: FAB is rendered in HTML
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="quick-add-btn"', html)
        self.assertIn('class="fab"', html)
    
    def test_fab_hidden_when_preference_disabled(self):
        """Test case 2: FAB hidden when preference is disabled"""
        # Arrange: User has FAB preference disabled
        self.user.show_quick_add_fab = False
        self.user.save()
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: FAB is NOT rendered in HTML
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn('id="quick-add-btn"', html)
    
    def test_modal_hidden_when_preference_disabled(self):
        """Verify modal is also not rendered when FAB is disabled"""
        # Arrange: User has FAB preference disabled
        self.user.show_quick_add_fab = False
        self.user.save()
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: Modal is NOT rendered in HTML
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn('id="quickAddModal"', html)
    
    def test_default_preference_is_enabled(self):
        """Verify new users have FAB enabled by default"""
        # Arrange: Create a new user
        new_user = CustomUser.objects.create_user(
            email='newuser@example.com',
            password='testpass123',
            first_name='New',
            last_name='User'
        )
        
        # Assert: Default preference is True
        self.assertTrue(new_user.show_quick_add_fab)
    
    def test_preference_persists_across_sessions(self):
        """Verify preference persists across login sessions"""
        # Arrange: User disables FAB
        self.user.show_quick_add_fab = False
        self.user.save()
        
        # Act: Login and check home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        
        # Assert: FAB is still hidden
        html = response.content.decode()
        self.assertNotIn('id="quick-add-btn"', html)
        
        # Act: Logout and login again
        self.client.logout()
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        
        # Assert: FAB is still hidden
        html = response.content.decode()
        self.assertNotIn('id="quick-add-btn"', html)
    
    def test_context_includes_fab_preference(self):
        """Verify home view context includes show_quick_add_fab"""
        # Arrange: User is logged in
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: Context includes preference
        self.assertEqual(response.status_code, 200)
        self.assertIn('show_quick_add_fab', response.context)
        self.assertEqual(response.context['show_quick_add_fab'], self.user.show_quick_add_fab)
