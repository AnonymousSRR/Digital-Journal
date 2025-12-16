"""
Unit tests for Reminder model.
"""
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from django.test import TestCase
from django.utils import timezone
from authentication.models import CustomUser, Theme, JournalEntry, Reminder
from authentication.services import ReminderScheduler


class ReminderModelTests(TestCase):
    """Test cases for the Reminder model."""
    
    def setUp(self):
        """Set up test data."""
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
    
    def test_create_one_time_reminder_defaults(self):
        """Test case 1: Create one-time reminder stores run_at and computes next_run_at."""
        run_time = timezone.now() + timedelta(hours=1)
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=run_time
        )
        
        self.assertIsNotNone(rem.run_at)
        self.assertEqual(rem.type, Reminder.ONE_TIME)
        self.assertTrue(rem.is_active)
        self.assertEqual(rem.timezone, 'UTC')
    
    def test_create_recurring_daily_reminder(self):
        """Test case 2: Create recurring reminder with daily frequency."""
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='daily',
            time_of_day=time(9, 0),
            timezone='America/Los_Angeles',
        )
        
        self.assertEqual(rem.frequency, 'daily')
        self.assertEqual(rem.type, Reminder.RECURRING)
        self.assertEqual(rem.time_of_day, time(9, 0))
        self.assertEqual(rem.timezone, 'America/Los_Angeles')
        self.assertTrue(rem.is_active)
    
    def test_reminder_cascade_delete_with_entry(self):
        """Test that reminders are deleted when journal entry is deleted."""
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now() + timedelta(hours=1)
        )
        reminder_id = rem.id
        
        self.entry.delete()
        
        self.assertFalse(Reminder.objects.filter(id=reminder_id).exists())
    
    def test_reminder_string_representation(self):
        """Test string representation of reminder."""
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now()
        )
        
        expected = f"Reminder<{rem.id}> for entry {self.entry.id}"
        self.assertEqual(str(rem), expected)
    
    def test_create_weekly_reminder(self):
        """Test creating a weekly recurring reminder."""
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='weekly',
            day_of_week=2,  # Wednesday
            time_of_day=time(14, 30),
            timezone='UTC'
        )
        
        self.assertEqual(rem.frequency, 'weekly')
        self.assertEqual(rem.day_of_week, 2)
        self.assertEqual(rem.time_of_day, time(14, 30))
    
    def test_create_monthly_reminder(self):
        """Test creating a monthly recurring reminder."""
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='monthly',
            day_of_month=15,
            time_of_day=time(10, 0),
            timezone='Europe/London'
        )
        
        self.assertEqual(rem.frequency, 'monthly')
        self.assertEqual(rem.day_of_month, 15)
        self.assertEqual(rem.time_of_day, time(10, 0))
        self.assertEqual(rem.timezone, 'Europe/London')


class ReminderSchedulerTests(TestCase):
    """Test cases for the ReminderScheduler service."""
    
    def setUp(self):
        """Set up test data."""
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
        self.scheduler = ReminderScheduler()
    
    def test_daily_next_run_tomorrow_when_past(self):
        """Test case 1: Daily reminder sets next run to tomorrow if past time."""
        now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='daily',
            time_of_day=time(9, 0),
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.date(), (now.date() + timedelta(days=1)))
        self.assertEqual(nxt.hour, 9)
        self.assertEqual(nxt.minute, 0)
    
    def test_daily_next_run_today_when_future(self):
        """Test daily reminder sets next run to today if time is in future."""
        now = datetime(2025, 12, 16, 8, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='daily',
            time_of_day=time(9, 0),
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.date(), now.date())
        self.assertEqual(nxt.hour, 9)
        self.assertEqual(nxt.minute, 0)
    
    def test_weekly_next_run_target_weekday(self):
        """Test case 2: Weekly reminder computes next correct weekday."""
        now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))  # Tuesday
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='weekly',
            day_of_week=2,  # Wednesday
            time_of_day=time(9, 0),
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.weekday(), 2)  # Wednesday
        self.assertEqual(nxt.hour, 9)
    
    def test_weekly_next_run_wraps_to_next_week(self):
        """Test weekly reminder wraps to next week if current week's day has passed."""
        now = datetime(2025, 12, 17, 10, 0, tzinfo=ZoneInfo('UTC'))  # Wednesday 10 AM
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='weekly',
            day_of_week=2,  # Wednesday
            time_of_day=time(9, 0),  # 9 AM (already passed)
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.weekday(), 2)  # Wednesday
        # Should be next week
        self.assertGreater((nxt - now).days, 5)
    
    def test_monthly_next_run_this_month(self):
        """Test monthly reminder computes next run for current month if date hasn't passed."""
        now = datetime(2025, 12, 5, 10, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='monthly',
            day_of_month=15,
            time_of_day=time(9, 0),
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.day, 15)
        self.assertEqual(nxt.month, 12)
        self.assertEqual(nxt.year, 2025)
    
    def test_monthly_next_run_next_month(self):
        """Test monthly reminder moves to next month if date has passed."""
        now = datetime(2025, 12, 20, 10, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='monthly',
            day_of_month=15,
            time_of_day=time(9, 0),
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.day, 15)
        self.assertEqual(nxt.month, 1)  # January
        self.assertEqual(nxt.year, 2026)
    
    def test_one_time_next_run_future(self):
        """Test one-time reminder returns run_at if in future."""
        now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))
        run_time = datetime(2025, 12, 20, 15, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=run_time,
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        self.assertEqual(nxt.replace(tzinfo=ZoneInfo('UTC')), run_time)
    
    def test_one_time_next_run_past_returns_none(self):
        """Test one-time reminder returns None if run_at is in past."""
        now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))
        run_time = datetime(2025, 12, 10, 15, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=run_time,
            timezone='UTC'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNone(nxt)
    
    def test_timezone_conversion(self):
        """Test that timezone conversion works correctly."""
        # 10 AM UTC on Dec 16
        now = datetime(2025, 12, 16, 10, 0, tzinfo=ZoneInfo('UTC'))
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='daily',
            time_of_day=time(9, 0),  # 9 AM in America/Los_Angeles
            timezone='America/Los_Angeles'
        )
        
        nxt = self.scheduler.compute_next_run(rem, now=now)
        
        self.assertIsNotNone(nxt)
        # Should be scheduled for 9 AM LA time
        la_time = nxt.astimezone(ZoneInfo('America/Los_Angeles'))
        self.assertEqual(la_time.hour, 9)
        self.assertEqual(la_time.minute, 0)


class ProcessRemindersCommandTests(TestCase):
    """Test cases for the process_reminders management command."""
    
    def setUp(self):
        """Set up test data."""
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
        self.scheduler = ReminderScheduler()
    
    def test_process_onetime_deactivates(self):
        """Test case 1: One-time reminders are sent and deactivated."""
        from django.core.management import call_command
        
        now = timezone.now()
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=now - timedelta(minutes=5),
            next_run_at=now - timedelta(minutes=5),
            timezone='UTC'
        )
        
        call_command('process_reminders')
        
        rem.refresh_from_db()
        self.assertFalse(rem.is_active)
        self.assertIsNone(rem.next_run_at)
        self.assertIsNotNone(rem.last_sent_at)
    
    def test_process_recurring_updates_next_run(self):
        """Test case 2: Recurring reminder updates next_run_at."""
        from django.core.management import call_command
        
        now = timezone.now()
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.RECURRING,
            frequency='daily',
            time_of_day=time(9, 0),
            next_run_at=now - timedelta(hours=1),
            timezone='UTC'
        )
        prev_next_run = rem.next_run_at
        
        call_command('process_reminders')
        
        rem.refresh_from_db()
        self.assertIsNotNone(rem.next_run_at)
        self.assertGreater(rem.next_run_at, prev_next_run)
        self.assertTrue(rem.is_active)
        self.assertIsNotNone(rem.last_sent_at)
    
    def test_process_no_due_reminders(self):
        """Test processing when no reminders are due."""
        from django.core.management import call_command
        from io import StringIO
        
        # Create a future reminder
        Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=timezone.now() + timedelta(hours=2),
            next_run_at=timezone.now() + timedelta(hours=2),
            timezone='UTC'
        )
        
        out = StringIO()
        call_command('process_reminders', stdout=out)
        
        self.assertIn('0 reminder', out.getvalue())
    
    def test_process_inactive_reminders_ignored(self):
        """Test that inactive reminders are not processed."""
        from django.core.management import call_command
        
        now = timezone.now()
        rem = Reminder.objects.create(
            journal_entry=self.entry,
            type=Reminder.ONE_TIME,
            run_at=now - timedelta(hours=1),
            next_run_at=now - timedelta(hours=1),
            is_active=False,
            timezone='UTC'
        )
        
        call_command('process_reminders')
        
        rem.refresh_from_db()
        self.assertIsNone(rem.last_sent_at)  # Should not be updated
    
    def test_process_multiple_reminders(self):
        """Test processing multiple due reminders at once."""
        from django.core.management import call_command
        from io import StringIO
        
        now = timezone.now()
        
        # Create multiple due reminders
        for i in range(3):
            entry = JournalEntry.objects.create(
                user=self.user,
                title=f'Test Entry {i}',
                theme=self.theme,
                prompt='Test prompt',
                answer='Test answer'
            )
            Reminder.objects.create(
                journal_entry=entry,
                type=Reminder.ONE_TIME,
                run_at=now - timedelta(minutes=5),
                next_run_at=now - timedelta(minutes=5),
                timezone='UTC'
            )
        
        out = StringIO()
        call_command('process_reminders', stdout=out)
        
        self.assertIn('3 reminder', out.getvalue())
        
        # Verify all were deactivated
        active_count = Reminder.objects.filter(is_active=True).count()
        self.assertEqual(active_count, 0)
