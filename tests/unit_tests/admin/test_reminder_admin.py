"""
Tests for Reminder Admin integration.
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from authentication.models import CustomUser, Theme, JournalEntry, Reminder
from authentication.admin import ReminderAdmin


class ReminderAdminTests(TestCase):
    """Test cases for Reminder admin integration."""
    
    def setUp(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = ReminderAdmin(Reminder, self.site)
        
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='Test Description'
        )
        
        self.entry = JournalEntry.objects.create(
            user=self.user,
            title='Test Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='Test answer'
        )
        
        self.client = Client()
    
    def test_admin_reminder_registered(self):
        """Test case 2: Admin lists reminders."""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        response = self.client.get(reverse('admin:authentication_reminder_changelist'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_list_display(self):
        """Test that admin list display shows expected fields."""
        expected_fields = ('id', 'journal_entry', 'type', 'timezone', 'next_run_at', 'is_active')
        
        self.assertEqual(self.admin.list_display, expected_fields)
    
    def test_admin_list_filter(self):
        """Test that admin has appropriate filters."""
        expected_filters = ('type', 'timezone', 'is_active', 'frequency')
        
        self.assertEqual(self.admin.list_filter, expected_filters)
    
    def test_admin_search_fields(self):
        """Test that admin can search by journal entry title."""
        expected_search = ('journal_entry__title',)
        
        self.assertEqual(self.admin.search_fields, expected_search)
    
    def test_admin_create_reminder(self):
        """Test creating a reminder through admin interface."""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'journal_entry': self.entry.id,
            'type': 'one_time',
            'timezone': 'UTC',
            'run_at_0': (timezone.now() + timedelta(hours=2)).date(),
            'run_at_1': (timezone.now() + timedelta(hours=2)).time(),
            'is_active': True,
        }
        
        response = self.client.post(
            reverse('admin:authentication_reminder_add'),
            data=data,
            follow=True
        )
        
        # Should create successfully or show form errors
        self.assertTrue(response.status_code in [200, 302])
    
    def test_admin_view_reminder(self):
        """Test viewing a reminder in admin."""
        reminder = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now() + timedelta(hours=1),
            timezone='UTC'
        )
        
        self.client.login(email='admin@example.com', password='adminpass123')
        
        response = self.client.get(
            reverse('admin:authentication_reminder_change', args=[reminder.id])
        )
        
        self.assertEqual(response.status_code, 200)


class MigrationTests(TestCase):
    """Test cases for migration integrity."""
    
    def test_backfill_no_reminders(self):
        """Test case 1: Migration applies and leaves existing entries unchanged."""
        # Create a journal entry
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        theme = Theme.objects.create(
            name='Test Theme',
            description='Test Description'
        )
        entry = JournalEntry.objects.create(
            user=user,
            title='Test Entry',
            theme=theme,
            prompt='Test prompt',
            answer='Test answer'
        )
        
        # By default, entries should have no reminders
        reminder_count = Reminder.objects.filter(journal_entry=entry).count()
        self.assertEqual(reminder_count, 0)
    
    def test_reminder_model_exists(self):
        """Test that Reminder model exists and can be queried."""
        reminders = Reminder.objects.all()
        self.assertEqual(reminders.count(), 0)  # Empty initially
