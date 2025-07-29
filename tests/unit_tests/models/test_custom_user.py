"""
Unit tests for CustomUser model and CustomUserManager
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from authentication.models import CustomUser, CustomUserManager, Theme, JournalEntry


class CustomUserModelTest(TestCase):
    """Test cases for CustomUser model custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
    
    def test_user_string_representation(self):
        """Test custom string representation method"""
        expected = "John Doe (test@example.com)"
        self.assertEqual(str(self.user), expected)
    
    def test_get_full_name(self):
        """Test custom get_full_name method"""
        self.assertEqual(self.user.get_full_name(), "John Doe")
    
    def test_get_short_name(self):
        """Test custom get_short_name method"""
        self.assertEqual(self.user.get_short_name(), "John")
    
    def test_get_full_name_with_empty_names(self):
        """Test get_full_name with empty names"""
        user = CustomUser.objects.create_user(
            email='empty@example.com',
            password='testpass123',
            first_name='',
            last_name=''
        )
        self.assertEqual(user.get_full_name(), "")
    
    def test_clean_method(self):
        """Test custom clean method for email normalization"""
        self.user.email = 'MIXED@EXAMPLE.COM'
        self.user.clean()
        self.assertEqual(self.user.email, 'mixed@example.com')
    
    def test_required_fields_configuration(self):
        """Test custom required fields configuration"""
        self.assertEqual(CustomUser.USERNAME_FIELD, 'email')
        self.assertEqual(CustomUser.REQUIRED_FIELDS, ['first_name', 'last_name'])
    
    def test_meta_configuration(self):
        """Test custom meta configuration"""
        self.assertEqual(CustomUser._meta.verbose_name, 'User')
        self.assertEqual(CustomUser._meta.verbose_name_plural, 'Users')
        self.assertEqual(CustomUser._meta.db_table, 'custom_user')


class ThemeModelTest(TestCase):
    """Test cases for Theme model custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.theme = Theme.objects.create(
            name='Leadership',
            description='Leadership and management themes'
        )
    
    def test_theme_string_representation(self):
        """Test custom string representation method"""
        self.assertEqual(str(self.theme), 'Leadership')


class JournalEntryModelTest(TestCase):
    """Test cases for JournalEntry model custom methods"""
    
    def setUp(self):
        """Set up test data"""
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.theme = Theme.objects.create(
            name='Leadership',
            description='Leadership themes'
        )
        self.journal_entry = JournalEntry.objects.create(
            user=self.user,
            title='My Leadership Journey',
            theme=self.theme,
            prompt='How have you grown as a leader?',
            answer='I have learned to listen more and delegate effectively.'
        )
    
    def test_journal_entry_string_representation(self):
        """Test custom string representation method"""
        expected = f"{self.user.email} - {self.journal_entry.created_at.date()} - {self.theme.name}"
        self.assertEqual(str(self.journal_entry), expected)
    
    def test_journal_entry_ordering(self):
        """Test custom ordering configuration"""
        # Create another entry
        second_entry = JournalEntry.objects.create(
            user=self.user,
            title='Another Entry',
            theme=self.theme,
            prompt='Another prompt',
            answer='Another answer'
        )
        
        entries = JournalEntry.objects.all()
        self.assertEqual(entries[0], second_entry)  # Newest first
        self.assertEqual(entries[1], self.journal_entry) 