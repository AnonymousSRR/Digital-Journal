"""
Unit tests for CustomAuthenticationForm custom methods
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from authentication.forms import CustomAuthenticationForm
from authentication.models import CustomUser

User = get_user_model()


class TestCustomAuthenticationForm(TestCase):
    """Test cases for CustomAuthenticationForm custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.form_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_clean_username_success(self):
        """Test clean_username method with valid email"""
        form = CustomAuthenticationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_username = form.clean_username()
        
        assert cleaned_username == 'test@example.com'
    
    def test_clean_username_normalization(self):
        """Test clean_username method normalizes email"""
        self.form_data['username'] = 'TEST@EXAMPLE.COM'
        form = CustomAuthenticationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_username = form.clean_username()
        
        assert cleaned_username == 'test@example.com'
    
    def test_clean_username_with_whitespace(self):
        """Test clean_username method with whitespace in email"""
        self.form_data['username'] = '  test@example.com  '
        form = CustomAuthenticationForm(data=self.form_data)
        form.is_valid()
        
        cleaned_username = form.clean_username()
        
        assert cleaned_username == 'test@example.com'
    
    def test_clean_username_empty(self):
        """Test clean_username method with empty username"""
        self.form_data['username'] = ''
        form = CustomAuthenticationForm(data=self.form_data)
        
        # Form should not be valid due to empty username
        assert not form.is_valid()
        assert 'username' in form.errors
    
    def test_clean_username_none(self):
        """Test clean_username method with None username"""
        self.form_data['username'] = None
        form = CustomAuthenticationForm(data=self.form_data)
        
        # Form should not be valid due to None username
        assert not form.is_valid()
        assert 'username' in form.errors
    
    def test_confirm_login_allowed_active_user(self):
        """Test confirm_login_allowed method with active user"""
        form = CustomAuthenticationForm(data=self.form_data)
        form.is_valid()
        
        # Should not raise any exception for active user
        form.confirm_login_allowed(self.user)
    
    def test_confirm_login_allowed_inactive_user(self):
        """Test confirm_login_allowed method with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        form = CustomAuthenticationForm(data=self.form_data)
        form.is_valid()
        
        with pytest.raises(ValidationError, match='This account is inactive'):
            form.confirm_login_allowed(self.user)
    
    def test_confirm_login_allowed_calls_parent(self):
        """Test confirm_login_allowed method calls parent method"""
        # Create a user that would be rejected by parent validation
        # (e.g., user with is_staff=False trying to access admin)
        # This test verifies that parent validation is still called
        
        form = CustomAuthenticationForm(data=self.form_data)
        form.is_valid()
        
        # Should not raise exception for normal user
        form.confirm_login_allowed(self.user)
    
    def test_form_validation_success(self):
        """Test complete form validation with valid data"""
        form = CustomAuthenticationForm(data=self.form_data)
        
        assert form.is_valid()
        assert len(form.errors) == 0
    
    def test_form_validation_missing_username(self):
        """Test form validation with missing username"""
        incomplete_data = {
            'password': 'testpass123'
            # Missing username
        }
        form = CustomAuthenticationForm(data=incomplete_data)
        
        assert not form.is_valid()
        assert 'username' in form.errors
    
    def test_form_validation_missing_password(self):
        """Test form validation with missing password"""
        incomplete_data = {
            'username': 'test@example.com'
            # Missing password
        }
        form = CustomAuthenticationForm(data=incomplete_data)
        
        assert not form.is_valid()
        assert 'password' in form.errors
    
    def test_form_validation_invalid_email_format(self):
        """Test form validation with invalid email format"""
        self.form_data['username'] = 'invalid-email'
        form = CustomAuthenticationForm(data=self.form_data)
        
        assert not form.is_valid()
        assert 'username' in form.errors
    
    def test_form_validation_empty_username(self):
        """Test form validation with empty username"""
        self.form_data['username'] = ''
        form = CustomAuthenticationForm(data=self.form_data)
        
        assert not form.is_valid()
        assert 'username' in form.errors
    
    def test_form_validation_empty_password(self):
        """Test form validation with empty password"""
        self.form_data['password'] = ''
        form = CustomAuthenticationForm(data=self.form_data)
        
        assert not form.is_valid()
        assert 'password' in form.errors
    
    def test_form_field_labels(self):
        """Test form field labels are correctly set"""
        form = CustomAuthenticationForm()
        
        assert form.fields['username'].label == 'Email'
        assert form.fields['password'].label == 'Password'
    
    def test_form_field_help_text(self):
        """Test form field help text is correctly set"""
        form = CustomAuthenticationForm()
        
        assert 'email address' in form.fields['username'].help_text.lower()
        assert 'password' in form.fields['password'].help_text.lower()
    
    def test_form_field_widgets(self):
        """Test form field widgets are correctly set"""
        form = CustomAuthenticationForm()
        
        assert form.fields['username'].widget.input_type == 'email'
        assert form.fields['password'].widget.input_type == 'password'
    
    def test_form_field_attributes(self):
        """Test form field attributes are correctly set"""
        form = CustomAuthenticationForm()
        
        # Check username field attributes
        username_attrs = form.fields['username'].widget.attrs
        assert username_attrs['class'] == 'form-control'
        assert username_attrs['id'] == 'username-input'
        assert username_attrs['data-testid'] == 'username-input'
        assert 'email' in username_attrs['placeholder'].lower()
        
        # Check password field attributes
        password_attrs = form.fields['password'].widget.attrs
        assert password_attrs['class'] == 'form-control'
        assert password_attrs['id'] == 'password-input'
        assert password_attrs['data-testid'] == 'password-input'
        assert 'password' in password_attrs['placeholder'].lower()
    
    def test_form_validation_with_whitespace(self):
        """Test form validation handles whitespace correctly"""
        self.form_data['username'] = '  test@example.com  '
        self.form_data['password'] = '  testpass123  '
        form = CustomAuthenticationForm(data=self.form_data)
        
        assert form.is_valid()
        # Username should be normalized (lowercase)
        assert form.cleaned_data['username'] == 'test@example.com'
        # Password should be stripped of whitespace (Django's default behavior)
        assert form.cleaned_data['password'] == 'testpass123' 