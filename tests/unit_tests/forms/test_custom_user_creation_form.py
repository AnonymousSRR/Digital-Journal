"""
Unit tests for CustomUserCreationForm custom methods
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from authentication.forms import CustomUserCreationForm
from authentication.models import CustomUser

User = get_user_model()


class TestCustomUserCreationForm(TestCase):
    """Test cases for CustomUserCreationForm custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        }
    
    def test_clean_email_success(self):
        """Test clean_email method with valid email"""
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_email = form.clean_email()
        
        assert cleaned_email == 'test@example.com'
    
    def test_clean_email_normalization(self):
        """Test clean_email method normalizes email"""
        self.form_data['email'] = 'TEST@EXAMPLE.COM'
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_email = form.clean_email()
        
        assert cleaned_email == 'test@example.com'
    
    def test_clean_email_with_whitespace(self):
        """Test clean_email method with whitespace in email"""
        self.form_data['email'] = '  test@example.com  '
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_email = form.clean_email()
        
        assert cleaned_email == 'test@example.com'
    
    def test_clean_email_duplicate(self):
        """Test clean_email method with duplicate email"""
        # Create a user with the same email
        CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Existing',
            last_name='User'
        )
        
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to duplicate email
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'already exists' in str(form.errors['email'])
    
    def test_clean_email_case_insensitive_duplicate(self):
        """Test clean_email method with case-insensitive duplicate email"""
        # Create a user with uppercase email
        CustomUser.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='testpass123',
            first_name='Existing',
            last_name='User'
        )
        
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to duplicate email (case-insensitive)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'already exists' in str(form.errors['email'])
    
    def test_clean_email_empty(self):
        """Test clean_email method with empty email"""
        self.form_data['email'] = ''
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to empty email
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_clean_success(self):
        """Test clean method with valid data"""
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_data = form.cleaned_data
        
        assert cleaned_data['password1'] == 'testpass123'
        assert cleaned_data['password2'] == 'testpass123'
    
    def test_clean_password_mismatch(self):
        """Test clean method with password mismatch"""
        self.form_data['password2'] = 'differentpass123'
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to password mismatch
        assert not form.is_valid()
        assert 'password2' in form.errors
        assert 'match' in str(form.errors['password2']).lower()
    
    def test_clean_password1_empty(self):
        """Test clean method with empty password1"""
        self.form_data['password1'] = ''
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to empty password
        assert not form.is_valid()
        assert 'password1' in form.errors
    
    def test_clean_password2_empty(self):
        """Test clean method with empty password2"""
        self.form_data['password2'] = ''
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to empty password confirmation
        assert not form.is_valid()
        assert 'password2' in form.errors
    
    def test_clean_both_passwords_empty(self):
        """Test clean method with both passwords empty"""
        self.form_data['password1'] = ''
        self.form_data['password2'] = ''
        form = CustomUserCreationForm(data=self.form_data)
        
        # Form should not be valid due to empty passwords
        assert not form.is_valid()
        assert 'password1' in form.errors
        assert 'password2' in form.errors
    
    def test_save_success(self):
        """Test save method with valid data"""
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        user = form.save()
        
        assert user.email == 'test@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.check_password('testpass123')
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_save_with_commit_false(self):
        """Test save method with commit=False"""
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        user = form.save(commit=False)
        
        assert user.email == 'test@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.check_password('testpass123')
        
        # User should not be saved to database
        assert user.pk is None
    
    def test_save_email_normalization(self):
        """Test save method normalizes email"""
        self.form_data['email'] = 'UPPERCASE@EXAMPLE.COM'
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        user = form.save()
        
        assert user.email == 'uppercase@example.com'
    
    def test_save_with_whitespace_in_names(self):
        """Test save method handles whitespace in names"""
        self.form_data['first_name'] = '  John  '
        self.form_data['last_name'] = '  Doe  '
        form = CustomUserCreationForm(data=self.form_data)
        form.is_valid()
        
        user = form.save()
        
        # Django strips whitespace during form cleaning
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
    
    def test_form_validation_success(self):
        """Test complete form validation with valid data"""
        form = CustomUserCreationForm(data=self.form_data)
        
        assert form.is_valid()
        assert len(form.errors) == 0
    
    def test_form_validation_missing_required_fields(self):
        """Test form validation with missing required fields"""
        incomplete_data = {
            'first_name': 'John',
            'email': 'test@example.com'
            # Missing last_name, password1, password2
        }
        form = CustomUserCreationForm(data=incomplete_data)
        
        assert not form.is_valid()
        assert 'last_name' in form.errors
        assert 'password1' in form.errors
        assert 'password2' in form.errors
    
    def test_form_validation_invalid_email(self):
        """Test form validation with invalid email format"""
        self.form_data['email'] = 'invalid-email'
        form = CustomUserCreationForm(data=self.form_data)
        
        assert not form.is_valid()
        assert 'email' in form.errors
    
    def test_form_validation_weak_password(self):
        """Test form validation with weak password"""
        self.form_data['password1'] = '123'
        self.form_data['password2'] = '123'
        self.form_data['email'] = 'newtest@example.com'  # Use fresh email
        form = CustomUserCreationForm(data=self.form_data)
        
        assert not form.is_valid()
        assert 'password2' in form.errors  # Django puts password errors in password2 field 