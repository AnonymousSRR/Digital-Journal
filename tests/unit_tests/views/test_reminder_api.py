"""
Tests for Reminder API views.
"""
import json
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from authentication.models import CustomUser, Theme, JournalEntry, Reminder


class ReminderAPITests(TestCase):
    """Test cases for Reminder API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
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
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_api_upcoming_reminders_authenticated(self):
        """Test case 1: API returns upcoming reminders for authenticated user."""
        # Create some reminders
        now = timezone.now()
        Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=now + timedelta(hours=2),
            next_run_at=now + timedelta(hours=2),
            timezone='UTC'
        )
        
        response = self.client.get(reverse('authentication:api_upcoming_reminders'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('reminders', data)
        self.assertEqual(len(data['reminders']), 1)
    
    def test_api_create_reminder(self):
        """Test creating a reminder via API."""
        data = {
            'journal_entry_id': self.entry.id,
            'type': 'one_time',
            'timezone': 'UTC',
            'run_at': (timezone.now() + timedelta(hours=3)).isoformat()
        }
        
        response = self.client.post(
            reverse('authentication:api_create_reminder'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        result = json.loads(response.content)
        self.assertEqual(result['type'], 'one_time')
        self.assertIsNotNone(result['next_run_at'])
    
    def test_update_recomputes_next_run(self):
        """Test case 2: Saving reminder recomputes next_run_at."""
        reminder = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='daily',
            time_of_day=time(9, 0),
            timezone='UTC'
        )
        
        data = {
            'time_of_day': '10:00:00'
        }
        
        response = self.client.patch(
            reverse('authentication:api_update_reminder', kwargs={'reminder_id': reminder.id}),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertIsNotNone(result['next_run_at'])
        
        # Verify in DB
        reminder.refresh_from_db()
        self.assertEqual(reminder.time_of_day, time(10, 0))
        self.assertIsNotNone(reminder.next_run_at)
    
    def test_api_list_reminders(self):
        """Test listing all reminders for a user."""
        # Create multiple reminders
        for i in range(3):
            Reminder.objects.create(
                journal_entry=self.entry,
                type=Reminder.ONE_TIME,
                run_at=timezone.now() + timedelta(hours=i+1),
                timezone='UTC'
            )
        
        response = self.client.get(reverse('authentication:api_list_reminders'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['reminders']), 3)
    
    def test_api_get_single_reminder(self):
        """Test getting a single reminder."""
        reminder = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now() + timedelta(hours=1),
            timezone='UTC'
        )
        
        response = self.client.get(
            reverse('authentication:api_get_reminder', kwargs={'reminder_id': reminder.id})
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['id'], reminder.id)
    
    def test_api_delete_reminder(self):
        """Test deleting a reminder."""
        reminder = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now() + timedelta(hours=1),
            timezone='UTC'
        )
        reminder_id = reminder.id
        
        response = self.client.delete(
            reverse('authentication:api_delete_reminder', kwargs={'reminder_id': reminder_id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reminder.objects.filter(id=reminder_id).exists())
    
    def test_api_unauthorized_access(self):
        """Test that unauthenticated users cannot access reminder APIs."""
        self.client.logout()
        
        response = self.client.get(reverse('authentication:api_list_reminders'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_api_user_cannot_access_others_reminders(self):
        """Test that users cannot access other users' reminders."""
        # Create another user and their reminder
        other_user = CustomUser.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        other_entry = JournalEntry.objects.create(
            user=other_user,
            title='Other Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='Test answer'
        )
        other_reminder = Reminder.objects.create(
            journal_entry=other_entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now() + timedelta(hours=1),
            timezone='UTC'
        )
        
        # Try to access as current user
        response = self.client.get(
            reverse('authentication:api_get_reminder', kwargs={'reminder_id': other_reminder.id})
        )
        
        self.assertEqual(response.status_code, 404)
