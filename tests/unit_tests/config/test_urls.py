"""
Unit tests for custom view functions
"""
from django.test import TestCase, RequestFactory
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.shortcuts import render
from config.urls import home_view, home_redirect
from authentication.models import CustomUser

User = get_user_model()


class TestHomeView(TestCase):
    """Test cases for custom home_view function"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_home_view_authenticated_user(self):
        """Test custom home_view function for authenticated user"""
        request = self.factory.get('/home/')
        request.user = self.user
        
        response = home_view(request)
        
        self.assertEqual(response.status_code, 200)
        # Check that the view returns a response
        self.assertIsNotNone(response)


class TestHomeRedirect(TestCase):
    """Test cases for custom home_redirect function"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_home_redirect_authenticated_user(self):
        """Test custom home_redirect function for authenticated user"""
        request = self.factory.get('/')
        request.user = self.user
        
        response = home_redirect(request)
        
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertEqual(response.url, '/home/') 