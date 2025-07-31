"""
Custom user model for the journal application.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    Provides methods for creating users and superusers.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model that uses email as the primary identifier.
    """
    username = None  # Disable username field
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email address',
        help_text='Your email address will be used as your username'
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name='First name',
        help_text='Enter your first name'
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name='Last name',
        help_text='Enter your last name'
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        db_table = 'custom_user'
    
    def __str__(self):
        """
        Return a string representation of the user.
        """
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """
        Return the full name of the user.
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """
        Return the short name of the user.
        """
        return self.first_name
    
    def clean(self):
        """
        Validate the user data.
        """
        super().clean()
        if self.email:
            self.email = self.email.lower()
    
    def save(self, *args, **kwargs):
        """
        Save the user with cleaned data.
        """
        self.clean()
        super().save(*args, **kwargs)


class Theme(models.Model):
    """
    Theme model for journal entries.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class JournalEntry(models.Model):
    """
    Journal entry model for user journal entries.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    theme = models.ForeignKey(Theme, on_delete=models.PROTECT)
    prompt = models.TextField()  # dynamically generated prompt
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    bookmarked = models.BooleanField(default=False)  # New field for bookmarking
    writing_time = models.IntegerField(default=0, help_text="Time spent writing in seconds")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.created_at.date()} - {self.theme.name}"
