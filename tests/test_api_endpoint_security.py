"""
Tests for toggle_quick_add_preference API endpoint security and validation
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json


User = get_user_model()


class ToggleQuickAddPreferenceSecurityTestCase(TestCase):
    """Test security aspects of the toggle_quick_add_preference endpoint"""
    
    def setUp(self):
        """Create test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.url = reverse('toggle_quick_add_preference')
    
    def test_requires_authentication(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.post(
            self.url,
            data=json.dumps({'enabled': True}),
            content_type='application/json'
        )
        # Should redirect to login or return 302
        self.assertIn(response.status_code, [302, 403])
    
    def test_requires_post_method(self):
        """Test that non-POST methods are rejected"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.put(
            self.url,
            data=json.dumps({'enabled': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 405)
    
    def test_validates_content_type(self):
        """Test that non-JSON content type is rejected"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            self.url,
            data='enabled=true',
            content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Content-Type', data['error'])
    
    def test_validates_enabled_parameter_present(self):
        """Test that missing 'enabled' parameter is rejected"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('enabled', data['error'])
    
    def test_validates_enabled_parameter_type(self):
        """Test that non-boolean 'enabled' parameter is rejected"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Test with string
        response = self.client.post(
            self.url,
            data=json.dumps({'enabled': 'true'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('boolean', data['error'])
        
        # Test with number
        response = self.client.post(
            self.url,
            data=json.dumps({'enabled': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('boolean', data['error'])
    
    def test_handles_invalid_json(self):
        """Test that malformed JSON is rejected"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            self.url,
            data='{"enabled": invalid}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('JSON', data['error'])
    
    def test_successful_enable(self):
        """Test successful enabling of Quick Add preference"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            self.url,
            data=json.dumps({'enabled': True}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.show_quick_add_fab)
    
    def test_successful_disable(self):
        """Test successful disabling of Quick Add preference"""
        self.client.login(email='test@example.com', password='testpass123')
        self.user.show_quick_add_fab = True
        self.user.save()
        
        response = self.client.post(
            self.url,
            data=json.dumps({'enabled': False}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertFalse(self.user.show_quick_add_fab)
    
    def test_does_not_leak_sensitive_info_on_error(self):
        """Test that error messages don't leak sensitive information"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Test with various invalid inputs
        test_cases = [
            {},
            {'enabled': 'true'},
            {'enabled': 1},
        ]
        
        for test_input in test_cases:
            response = self.client.post(
                self.url,
                data=json.dumps(test_input),
                content_type='application/json'
            )
            data = response.json()
            self.assertFalse(data['success'])
            # Error message should be generic, not expose internal details
            self.assertNotIn('Traceback', data['error'])
            self.assertNotIn('Exception', data['error'])
