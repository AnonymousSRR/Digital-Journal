"""
Tests for FAB preference default value change
Phase 3: Add User Preference with Default OFF
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class FABPreferenceDefaultOffTests(TestCase):
    """Test suite to verify FAB is disabled by default for new users"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
    
    def test_new_user_has_fab_disabled(self):
        """Test case 1: New users have FAB disabled by default"""
        # Arrange & Act: Create new user
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Assert: show_quick_add_fab is False
        self.assertFalse(user.show_quick_add_fab)
    
    def test_home_page_respects_fab_preference_disabled(self):
        """Test case 2: Home page respects FAB preference when disabled"""
        # Arrange: User has FAB disabled
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.show_quick_add_fab = False
        user.save()
        
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Load home page
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: FAB and modal are not rendered
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('id="quick-add-btn"', html)
        self.assertNotIn('id="quickAddModal"', html)
    
    def test_home_page_shows_fab_when_enabled(self):
        """Test case 3: Home page shows FAB when user enables it"""
        # Arrange: User has FAB enabled
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.show_quick_add_fab = True
        user.save()
        
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Load home page
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: FAB and modal ARE rendered
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="quick-add-btn"', html)
        self.assertIn('id="quickAddModal"', html)
    
    def test_default_value_in_model_field(self):
        """Test case 4: Model field has correct default value"""
        # Arrange & Act: Get the field definition
        field = CustomUser._meta.get_field('show_quick_add_fab')
        
        # Assert: Default is False
        self.assertFalse(field.default)
    
    def test_multiple_new_users_all_have_fab_disabled(self):
        """Test case 5: Multiple new users all have FAB disabled"""
        # Arrange & Act: Create multiple users
        user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            password='pass123'
        )
        user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            password='pass123'
        )
        user3 = CustomUser.objects.create_user(
            email='user3@example.com',
            password='pass123'
        )
        
        # Assert: All have FAB disabled
        self.assertFalse(user1.show_quick_add_fab)
        self.assertFalse(user2.show_quick_add_fab)
        self.assertFalse(user3.show_quick_add_fab)
    
    def test_user_can_manually_enable_fab(self):
        """Test case 6: User can manually enable FAB"""
        # Arrange: Create user with default FAB disabled
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertFalse(user.show_quick_add_fab)
        
        # Act: Enable FAB
        user.show_quick_add_fab = True
        user.save()
        
        # Assert: FAB is enabled
        user.refresh_from_db()
        self.assertTrue(user.show_quick_add_fab)
    
    def test_user_can_enable_fab_via_api(self):
        """Test case 7: User can enable FAB via API endpoint"""
        # Arrange: User has FAB disabled
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.show_quick_add_fab = False
        user.save()
        
        # Log in the user
        self.client.force_login(user)
        
        # Act: Enable via API
        response = self.client.post('/home/api/preferences/quick-add/', 
            data='{"enabled": true}',
            content_type='application/json'
        )
        
        # Assert: Preference updated
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        user.refresh_from_db()
        self.assertTrue(user.show_quick_add_fab)
    
    def test_user_can_disable_fab_via_api(self):
        """Test case 8: User can disable FAB via API endpoint"""
        # Arrange: User has FAB enabled
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        user.show_quick_add_fab = True
        user.save()
        
        # Log in the user
        self.client.force_login(user)
        
        # Act: Disable via API
        response = self.client.post('/home/api/preferences/quick-add/', 
            data='{"enabled": false}',
            content_type='application/json'
        )
        
        # Assert: Preference updated
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        user.refresh_from_db()
        self.assertFalse(user.show_quick_add_fab)
