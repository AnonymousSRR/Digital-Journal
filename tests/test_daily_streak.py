"""
Tests for Daily Streak Card feature.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from authentication.models import Theme, JournalEntry

User = get_user_model()


class DailyStreakTestCase(TestCase):
    """Test cases for daily streak functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create a theme for journal entries
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='A test theme'
        )

    def test_current_streak_calculation_consecutive_days(self):
        """Test case 1: Verify streak calculation for user with consecutive entries."""
        # Arrange: Create entries for 3 consecutive days
        today = timezone.now().date()
        for i in range(3):
            entry_date = today - timedelta(days=i)
            entry = JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Daily prompt',
                answer='My daily reflection'
            )
            # Manually set created_at to specific date
            entry.created_at = timezone.make_aware(
                timezone.datetime.combine(entry_date, timezone.datetime.min.time())
            )
            entry.save()
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Streak should be 3
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_streak'], 3)

    def test_current_streak_zero_for_new_user(self):
        """Test case 2: Verify streak is zero for new user with no entries."""
        # Arrange: New user with no entries (already in setUp)
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Streak should be 0
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_streak'], 0)

    def test_streak_resets_when_day_missed(self):
        """Test case 3: Verify streak resets when a day is missed."""
        # Arrange: Create entries with a gap
        today = timezone.now().date()
        
        # Entry today
        entry1 = JournalEntry.objects.create(
            user=self.user,
            title='Today entry',
            theme=self.theme,
            prompt='Prompt',
            answer='Answer'
        )
        entry1.created_at = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        entry1.save()
        
        # Entry 3 days ago (gap of 2 days)
        three_days_ago = today - timedelta(days=3)
        entry2 = JournalEntry.objects.create(
            user=self.user,
            title='Old entry',
            theme=self.theme,
            prompt='Prompt',
            answer='Answer'
        )
        entry2.created_at = timezone.make_aware(
            timezone.datetime.combine(three_days_ago, timezone.datetime.min.time())
        )
        entry2.save()
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Streak should be 1 (only today's entry)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_streak'], 1)

    def test_streak_card_visible_on_home_page(self):
        """Test case 1 (Phase 2): Verify streak card is visible on home page."""
        # Arrange: User already logged in (setUp)
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check streak card exists in response
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('streak-card', content)
        self.assertIn('🔥', content)
        self.assertIn('Day Streak', content)

    def test_streak_value_displays_correctly(self):
        """Test case 2 (Phase 2): Verify streak value displays correctly for active streak."""
        # Arrange: Create 5-day streak
        today = timezone.now().date()
        for i in range(5):
            entry_date = today - timedelta(days=i)
            entry = JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Prompt',
                answer='Answer'
            )
            entry.created_at = timezone.make_aware(
                timezone.datetime.combine(entry_date, timezone.datetime.min.time())
            )
            entry.save()
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check streak value is 5
        content = response.content.decode()
        self.assertIn('data-testid="streak-value">5</div>', content)

    def test_streak_card_shows_zero_for_new_user(self):
        """Test case 3 (Phase 2): Verify streak card shows zero for new user."""
        # Arrange: New user with no entries (setUp)
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check streak value is 0
        content = response.content.decode()
        self.assertIn('data-testid="streak-value">0</div>', content)

    def test_streak_card_has_unique_class(self):
        """Test case 1 (Phase 3): Verify streak card has unique styling class."""
        # Arrange: User logged in
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check for streak-card class
        content = response.content.decode()
        self.assertIn('class="summary-card streak-card"', content)

    def test_all_four_cards_render_correctly(self):
        """Test case 2 (Phase 3): Verify all 4 cards render in correct grid layout."""
        # Arrange: Create some entries
        for i in range(2):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Prompt',
                answer='I feel happy today'
            )
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        
        # Assert: All 4 cards present
        self.assertEqual(content.count('summary-card'), 4)
        self.assertIn('total-entries-card', content)
        self.assertIn('entries-week-card', content)
        self.assertIn('emotion-card', content)
        self.assertIn('streak-card', content)

    def test_streak_increases_after_new_entry_today(self):
        """Test case 1 (Phase 4): Verify streak increases after creating new entry today."""
        # Arrange: User with 2-day streak
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        for date in [yesterday, today - timedelta(days=2)]:
            entry = JournalEntry.objects.create(
                user=self.user,
                title='Entry',
                theme=self.theme,
                prompt='Prompt',
                answer='Answer'
            )
            entry.created_at = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.min.time())
            )
            entry.save()
        
        # Verify initial streak is 2
        response1 = self.client.get(reverse('home'))
        self.assertEqual(response1.context['current_streak'], 2)
        
        # Act: Create new entry today
        JournalEntry.objects.create(
            user=self.user,
            title='New entry',
            theme=self.theme,
            prompt='Prompt',
            answer='Answer'
        )
        
        # Assert: Streak should now be 3
        response2 = self.client.get(reverse('home'))
        self.assertEqual(response2.context['current_streak'], 3)

    def test_streak_same_with_multiple_entries_same_day(self):
        """Test case 2 (Phase 4): Verify streak doesn't increase with multiple entries same day."""
        # Arrange: Create first entry today
        JournalEntry.objects.create(
            user=self.user,
            title='Entry 1',
            theme=self.theme,
            prompt='Prompt',
            answer='Answer'
        )
        
        response1 = self.client.get(reverse('home'))
        initial_streak = response1.context['current_streak']
        
        # Act: Create second entry today
        JournalEntry.objects.create(
            user=self.user,
            title='Entry 2',
            theme=self.theme,
            prompt='Prompt',
            answer='Answer'
        )
        
        # Assert: Streak should remain the same
        response2 = self.client.get(reverse('home'))
        self.assertEqual(response2.context['current_streak'], initial_streak)

    def test_streak_resets_after_missing_day(self):
        """Test case 3 (Phase 4): Verify streak resets to 1 after missing a day."""
        # Arrange: Create entries 3 and 4 days ago (no recent entries)
        today = timezone.now().date()
        for i in [3, 4]:
            date = today - timedelta(days=i)
            entry = JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Prompt',
                answer='Answer'
            )
            entry.created_at = timezone.make_aware(
                timezone.datetime.combine(date, timezone.datetime.min.time())
            )
            entry.save()
        
        # Verify streak is 0 (no recent entries)
        response1 = self.client.get(reverse('home'))
        self.assertEqual(response1.context['current_streak'], 0)
        
        # Act: Create new entry today
        JournalEntry.objects.create(
            user=self.user,
            title='New entry',
            theme=self.theme,
            prompt='Prompt',
            answer='Answer'
        )
        
        # Assert: Streak should be 1 (fresh start)
        response2 = self.client.get(reverse('home'))
        self.assertEqual(response2.context['current_streak'], 1)
