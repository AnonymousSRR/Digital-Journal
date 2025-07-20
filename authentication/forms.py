"""
Forms for user authentication.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Form for user registration with custom validation.
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'first-name-input',
            'data-testid': 'first-name-input',
            'placeholder': 'Enter your first name'
        }),
        help_text='Enter your first name'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'last-name-input',
            'data-testid': 'last-name-input',
            'placeholder': 'Enter your last name'
        }),
        help_text='Enter your last name'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email-input',
            'data-testid': 'email-input',
            'placeholder': 'Enter your email address'
        }),
        help_text='Your email will be used as your username'
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password-input',
            'data-testid': 'password-input',
            'placeholder': 'Enter your password'
        }),
        help_text='Enter a strong password'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'confirm-password-input',
            'data-testid': 'confirm-password-input',
            'placeholder': 'Confirm your password'
        }),
        help_text='Enter the same password as before'
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        """
        Validate that the email is unique and properly formatted.
        """
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if CustomUser.objects.filter(email=email).exists():
                raise ValidationError('A user with this email already exists.')
        return email
    
    def clean(self):
        """
        Validate the entire form data.
        """
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Save the user with proper data handling.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """
    Form for user login with custom styling.
    """
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'username-input',
            'data-testid': 'username-input',
            'placeholder': 'Your email is your username'
        }),
        help_text='Enter your email address'
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password-input',
            'data-testid': 'password-input',
            'placeholder': 'Enter your password'
        }),
        help_text='Enter your password'
    )
    
    def clean_username(self):
        """
        Normalize the email address.
        """
        username = self.cleaned_data.get('username')
        if username:
            return username.lower()
        return username
    
    def confirm_login_allowed(self, user):
        """
        Check if the user is allowed to log in.
        """
        super().confirm_login_allowed(user)
        if not user.is_active:
            raise ValidationError('This account is inactive.') 