"""
Unit tests for CustomUserManager methods
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from authentication.models import CustomUser

User = get_user_model()


class TestCustomUserManager(TestCase):
    """Test cases for CustomUserManager custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.manager = User.objects
    
    def test_create_user_success(self):
        """Test successful user creation"""
        user = self.manager.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.email == 'test@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password('testpass123')
    
    def test_create_user_without_email(self):
        """Test user creation without email raises ValueError"""
        with pytest.raises(ValueError, match='The Email field must be set'):
            self.manager.create_user(
                email='',
                password='testpass123',
                first_name='John',
                last_name='Doe'
            )
    
    def test_create_user_without_password(self):
        """Test user creation without password"""
        user = self.manager.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.email == 'test@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        # User should be created but password should not be set
        assert not user.check_password('')
    
    def test_create_user_email_normalization(self):
        """Test email normalization during user creation"""
        user = self.manager.create_user(
            email='TEST@EXAMPLE.COM',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.email == 'test@example.com'
    
    def test_create_user_with_extra_fields(self):
        """Test user creation with extra fields"""
        user = self.manager.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            is_active=False
        )
        
        assert user.email == 'test@example.com'
        assert user.is_active is False
    
    def test_create_superuser_success(self):
        """Test successful superuser creation"""
        superuser = self.manager.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        assert superuser.email == 'admin@example.com'
        assert superuser.first_name == 'Admin'
        assert superuser.last_name == 'User'
        assert superuser.is_active is True
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.check_password('adminpass123')
    
    def test_create_superuser_without_staff_flag(self):
        """Test superuser creation without is_staff=True raises ValueError"""
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            self.manager.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='User',
                is_staff=False
            )
    
    def test_create_superuser_without_superuser_flag(self):
        """Test superuser creation without is_superuser=True raises ValueError"""
        with pytest.raises(ValueError, match='Superuser must have is_superuser=True'):
            self.manager.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                first_name='Admin',
                last_name='User',
                is_superuser=False
            )
    
    def test_create_superuser_with_custom_flags(self):
        """Test superuser creation with custom flags"""
        superuser = self.manager.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_active=False
        )
        
        assert superuser.email == 'admin@example.com'
        assert superuser.is_active is False
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
    
    def test_create_superuser_email_normalization(self):
        """Test email normalization during superuser creation"""
        superuser = self.manager.create_superuser(
            email='ADMIN@EXAMPLE.COM',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        assert superuser.email == 'admin@example.com'
    
    def test_create_superuser_without_password(self):
        """Test superuser creation without password"""
        superuser = self.manager.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User'
        )
        
        assert superuser.email == 'admin@example.com'
        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        # Superuser should be created but password should not be set
        assert not superuser.check_password('') 