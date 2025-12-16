"""
Tests for template integration of reminders in my_journals.html
"""
from django.test import TestCase, Client
from authentication.models import CustomUser, JournalEntry, Theme, Reminder
from django.utils import timezone
from datetime import timedelta


class ReminderTemplateIntegrationTests(TestCase):
    """Test that reminders are properly integrated into the my_journals template."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.theme = Theme.objects.create(name='Test Theme')
        self.entry = JournalEntry.objects.create(
            user=self.user,
            theme=self.theme,
            title='Test Entry',
            prompt='Test prompt?',
            answer='Test answer'
        )

    def test_my_journals_page_loads(self):
        """Test that my_journals page loads successfully."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/home/my-journals/')
        self.assertEqual(response.status_code, 200)

    def test_my_journals_contains_reminders_section(self):
        """Test that my_journals page contains the reminders section."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/home/my-journals/')
        self.assertContains(response, 'upcoming-reminders-section')
        self.assertContains(response, 'reminders-list')
        self.assertContains(response, '⏰ Upcoming Reminders')

    def test_my_journals_contains_reminders_javascript(self):
        """Test that my_journals page includes reminder loading JavaScript."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/home/my-journals/')
        self.assertContains(response, 'loadUpcomingReminders')
        self.assertContains(response, 'renderReminders')
        self.assertContains(response, '/home/api/reminders/upcoming/')

    def test_upcoming_reminders_api_integration(self):
        """Test that the upcoming reminders API works with template."""
        # Create a future reminder
        future_time = timezone.now() + timedelta(days=1)
        reminder = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=future_time,
            next_run_at=future_time,
            timezone='UTC',
            is_active=True
        )
        
        # Login and call the API endpoint
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/home/api/reminders/upcoming/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['reminders']), 1)
        self.assertEqual(data['reminders'][0]['journal_entry_id'], self.entry.id)
        self.assertEqual(data['reminders'][0]['entry_title'], 'Test Entry')

    def test_reminder_contains_entry_title_in_serialized_data(self):
        """Test that serialized reminder includes entry title."""
        future_time = timezone.now() + timedelta(days=1)
        reminder = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=future_time,
            next_run_at=future_time,
            timezone='UTC',
            is_active=True
        )
        
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/home/api/reminders/upcoming/')
        data = response.json()
        
        self.assertIn('entry_title', data['reminders'][0])
        self.assertEqual(data['reminders'][0]['entry_title'], 'Test Entry')
