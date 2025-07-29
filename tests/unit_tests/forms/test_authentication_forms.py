"""
Unit tests for authentication forms custom methods
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from authentication.forms import CustomUserCreationForm, CustomAuthenticationForm
from authentication.models import CustomUser


class CustomUserCreationFormTest(TestCase):
    """Test cases for CustomUserCreationForm custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!'
        }
    
    def test_clean_email_method(self):
        """Test custom clean_email method"""
        form = CustomUserCreationForm(data=self.valid_data)
        form.is_valid()
        cleaned_email = form.clean_email()
        self.assertEqual(cleaned_email, 'john.doe@example.com')
    
    def test_clean_email_normalization(self):
        """Test custom email normalization in clean_email"""
        data = self.valid_data.copy()
        data['email'] = 'JOHN.DOE@EXAMPLE.COM'
        form = CustomUserCreationForm(data=data)
        form.is_valid()
        cleaned_email = form.clean_email()
        self.assertEqual(cleaned_email, 'john.doe@example.com')
    
    def test_save_method(self):
        """Test custom save method"""
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, 'john.doe@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.check_password('TestPassword123!'))
    
    def test_save_method_with_commit_false(self):
        """Test custom save method with commit=False"""
        form = CustomUserCreationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)
        
        self.assertIsInstance(user, CustomUser)
        self.assertEqual(user.email, 'john.doe@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        # User should not be saved to database
        self.assertFalse(CustomUser.objects.filter(email='john.doe@example.com').exists())
    
    def test_form_widget_attributes(self):
        """Test custom form widget attributes"""
        form = CustomUserCreationForm()
        
        # Check first_name field
        self.assertIn('form-control', form.fields['first_name'].widget.attrs['class'])
        self.assertEqual(form.fields['first_name'].widget.attrs['id'], 'first-name-input')
        self.assertEqual(form.fields['first_name'].widget.attrs['data-testid'], 'first-name-input')
        
        # Check email field
        self.assertIn('form-control', form.fields['email'].widget.attrs['class'])
        self.assertEqual(form.fields['email'].widget.attrs['id'], 'email-input')
        self.assertEqual(form.fields['email'].widget.attrs['data-testid'], 'email-input')


class CustomAuthenticationFormTest(TestCase):
    """Test cases for CustomAuthenticationForm custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.valid_data = {
            'username': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_clean_username_method(self):
        """Test custom clean_username method"""
        form = CustomAuthenticationForm(data=self.valid_data)
        form.is_valid()
        cleaned_username = form.clean_username()
        self.assertEqual(cleaned_username, 'test@example.com')
    
    def test_clean_username_normalization(self):
        """Test custom username normalization in clean_username"""
        data = self.valid_data.copy()
        data['username'] = 'TEST@EXAMPLE.COM'
        form = CustomAuthenticationForm(data=data)
        form.is_valid()
        cleaned_username = form.clean_username()
        self.assertEqual(cleaned_username, 'test@example.com')
    
    def test_confirm_login_allowed_with_active_user(self):
        """Test custom confirm_login_allowed with active user"""
        form = CustomAuthenticationForm(data=self.valid_data)
        form.is_valid()
        # Should not raise any exception
        form.confirm_login_allowed(self.user)
    
    def test_confirm_login_allowed_with_inactive_user(self):
        """Test custom confirm_login_allowed with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        form = CustomAuthenticationForm(data=self.valid_data)
        form.is_valid()
        
        with self.assertRaises(ValidationError) as context:
            form.confirm_login_allowed(self.user)
        
        self.assertIn('This account is inactive', str(context.exception))
    
    def test_form_widget_attributes(self):
        """Test custom form widget attributes"""
        form = CustomAuthenticationForm()
        
        # Check username field
        self.assertIn('form-control', form.fields['username'].widget.attrs['class'])
        self.assertEqual(form.fields['username'].widget.attrs['id'], 'username-input')
        self.assertEqual(form.fields['username'].widget.attrs['data-testid'], 'username-input')
        
        # Check password field
        self.assertIn('form-control', form.fields['password'].widget.attrs['class'])
        self.assertEqual(form.fields['password'].widget.attrs['id'], 'password-input')
        self.assertEqual(form.fields['password'].widget.attrs['data-testid'], 'password-input')
    
    def test_username_field_label(self):
        """Test custom username field label"""
        form = CustomAuthenticationForm()
        self.assertEqual(form.fields['username'].label, 'Email')
    
    def test_password_field_label(self):
        """Test custom password field label"""
        form = CustomAuthenticationForm()
        self.assertEqual(form.fields['password'].label, 'Password') 