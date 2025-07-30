"""
Unit tests for CustomUser model custom methods
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from authentication.models import CustomUser

User = get_user_model()


class TestCustomUserMethods(TestCase):
    """Test cases for CustomUser custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        full_name = self.user.get_full_name()
        
        assert full_name == 'John Doe'
    
    def test_get_full_name_with_empty_last_name(self):
        """Test get_full_name method with empty last name"""
        self.user.last_name = ''
        self.user.save()
        
        full_name = self.user.get_full_name()
        
        assert full_name == 'John'
    
    def test_get_full_name_with_empty_first_name(self):
        """Test get_full_name method with empty first name"""
        self.user.first_name = ''
        self.user.save()
        
        full_name = self.user.get_full_name()
        
        assert full_name == 'Doe'
    
    def test_get_full_name_with_both_empty(self):
        """Test get_full_name method with both names empty"""
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        
        full_name = self.user.get_full_name()
        
        assert full_name == ''
    
    def test_get_full_name_with_whitespace(self):
        """Test get_full_name method with whitespace in names"""
        self.user.first_name = '  John  '
        self.user.last_name = '  Doe  '
        self.user.save()
        
        full_name = self.user.get_full_name()
        
        # The .strip() method removes leading and trailing whitespace
        assert full_name == 'John     Doe'
    
    def test_get_short_name(self):
        """Test get_short_name method"""
        short_name = self.user.get_short_name()
        
        assert short_name == 'John'
    
    def test_get_short_name_with_empty_first_name(self):
        """Test get_short_name method with empty first name"""
        self.user.first_name = ''
        self.user.save()
        
        short_name = self.user.get_short_name()
        
        assert short_name == ''
    
    def test_get_short_name_with_whitespace(self):
        """Test get_short_name method with whitespace in first name"""
        self.user.first_name = '  John  '
        self.user.save()
        
        short_name = self.user.get_short_name()
        
        # The method returns the first_name as-is, including whitespace
        assert short_name == '  John  '
    
    def test_str_representation(self):
        """Test __str__ method"""
        str_repr = str(self.user)
        
        assert str_repr == 'John Doe (test@example.com)'
    
    def test_str_representation_with_empty_names(self):
        """Test __str__ method with empty names"""
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        
        str_repr = str(self.user)
        
        # The __str__ method includes a space between first and last name
        assert str_repr == '  (test@example.com)'
    
    def test_clean_email_normalization(self):
        """Test clean method normalizes email"""
        self.user.email = 'TEST@EXAMPLE.COM'
        self.user.clean()
        
        assert self.user.email == 'test@example.com'
    
    def test_clean_email_already_normalized(self):
        """Test clean method with already normalized email"""
        original_email = self.user.email
        self.user.clean()
        
        assert self.user.email == original_email
    
    def test_clean_email_with_whitespace(self):
        """Test clean method with whitespace in email"""
        self.user.email = '  test@example.com  '
        self.user.clean()
        
        assert self.user.email == 'test@example.com'
    
    def test_clean_without_email(self):
        """Test clean method without email"""
        self.user.email = ''
        self.user.clean()
        
        assert self.user.email == ''
    
    def test_save_calls_clean(self):
        """Test save method calls clean"""
        self.user.email = 'UPPERCASE@EXAMPLE.COM'
        self.user.save()
        
        # Email should be normalized after save
        self.user.refresh_from_db()
        assert self.user.email == 'uppercase@example.com'
    
    def test_save_preserves_other_fields(self):
        """Test save method preserves other fields"""
        original_first_name = self.user.first_name
        original_last_name = self.user.last_name
        original_password = self.user.password
        
        self.user.save()
        
        # Other fields should remain unchanged
        self.user.refresh_from_db()
        assert self.user.first_name == original_first_name
        assert self.user.last_name == original_last_name
        assert self.user.password == original_password
    
    def test_clean_calls_parent_clean(self):
        """Test clean method calls parent clean method"""
        # This test verifies that the parent clean method is called
        # We can't easily test the parent method directly, but we can verify
        # that our custom clean method works alongside it
        self.user.email = 'TEST@EXAMPLE.COM'
        self.user.clean()
        
        assert self.user.email == 'test@example.com'
    
    def test_user_creation_with_manager(self):
        """Test user creation through manager calls clean"""
        user = CustomUser.objects.create_user(
            email='NEWUSER@EXAMPLE.COM',
            password='testpass123',
            first_name='New',
            last_name='User'
        )
        
        # Email should be normalized after creation
        assert user.email == 'newuser@example.com'
    
    def test_superuser_creation_with_manager(self):
        """Test superuser creation through manager calls clean"""
        superuser = CustomUser.objects.create_superuser(
            email='ADMIN@EXAMPLE.COM',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        # Email should be normalized after creation
        assert superuser.email == 'admin@example.com' 