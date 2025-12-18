"""
Unit tests for Analytics API Endpoints.
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from authentication.models import Theme, JournalEntry
from authentication.services import AnalyticsService

CustomUser = get_user_model()


class TestAnalyticsAPIEndpoints(TestCase):
    """Test analytics API endpoints."""
    
    def setUp(self):
        """Set up test user and client."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email="analytics@test.com",
            password="testpassword123"
        )
        self.client.login(email="analytics@test.com", password="testpassword123")
        self.theme = Theme.objects.create(name="TestTheme")
    
    def test_api_writing_streaks_endpoint(self):
        """Test writing streaks API endpoint returns valid JSON."""
        # Create some entries
        today = timezone.now()
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user,
                title=f"Entry {i}",
                theme=self.theme,
                prompt="test",
                answer="Test content here",
                created_at=today - timedelta(days=i)
            )
        
        response = self.client.get(reverse('authentication:api_writing_streaks'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('current_streak', data)
        self.assertIn('longest_streak', data)
        self.assertIn('last_entry_date', data)
    
    def test_api_word_count_stats_endpoint(self):
        """Test word count stats endpoint."""
        JournalEntry.objects.create(
            user=self.user,
            title="Test",
            theme=self.theme,
            prompt="test",
            answer="This entry has exactly five words"
        )
        
        response = self.client.get(reverse('authentication:api_word_count_stats'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total_words', data)
        self.assertIn('avg_words_per_entry', data)
        self.assertGreater(data['total_words'], 0)
    
    def test_api_mood_distribution_endpoint(self):
        """Test mood distribution endpoint."""
        JournalEntry.objects.create(
            user=self.user,
            title="Happy Entry",
            theme=self.theme,
            prompt="test",
            answer="I am so happy and joyful today! Everything is wonderful and amazing!"
        )
        
        response = self.client.get(reverse('authentication:api_mood_distribution'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Should have all emotion types
        expected_emotions = ['joyful', 'sad', 'angry', 'anxious', 'calm', 'neutral']
        for emotion in expected_emotions:
            self.assertIn(emotion, data)
    
    def test_api_top_themes_endpoint(self):
        """Test top themes endpoint."""
        # Create entries with the same theme
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user,
                title=f"Entry {i}",
                theme=self.theme,
                prompt="test",
                answer="Content here"
            )
        
        response = self.client.get(reverse('authentication:api_top_themes'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('themes', data)
        self.assertIsInstance(data['themes'], list)
        if data['themes']:
            self.assertIn('theme', data['themes'][0])
            self.assertIn('count', data['themes'][0])
    
    def test_api_word_count_trend_endpoint(self):
        """Test word count trend endpoint."""
        today = timezone.now()
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user,
                title=f"Entry {i}",
                theme=self.theme,
                prompt="test",
                answer="Test content with several words here",
                created_at=today - timedelta(days=i)
            )
        
        response = self.client.get(reverse('authentication:api_word_count_trend'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('trend', data)
        self.assertIsInstance(data['trend'], list)
    
    def test_api_mood_trend_endpoint(self):
        """Test mood trend endpoint."""
        today = timezone.now()
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user,
                title=f"Entry {i}",
                theme=self.theme,
                prompt="test",
                answer="Some content for the entry",
                created_at=today - timedelta(days=i)
            )
        
        response = self.client.get(reverse('authentication:api_mood_trend'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('trend', data)
        self.assertIsInstance(data['trend'], list)
    
    def test_api_requires_authentication(self):
        """Test that analytics endpoints require authentication."""
        self.client.logout()
        
        endpoints = [
            'api_writing_streaks',
            'api_word_count_stats',
            'api_mood_distribution',
            'api_top_themes',
            'api_word_count_trend',
            'api_mood_trend',
        ]
        
        for endpoint_name in endpoints:
            response = self.client.get(reverse(f'authentication:{endpoint_name}'))
            # Should redirect to login or return 302/401
            self.assertIn(response.status_code, [302, 401])
    
    def test_api_word_count_trend_granularity(self):
        """Test word count trend with different granularity."""
        today = timezone.now()
        for i in range(7):
            JournalEntry.objects.create(
                user=self.user,
                title=f"Entry {i}",
                theme=self.theme,
                prompt="test",
                answer="Content with words",
                created_at=today - timedelta(days=i)
            )
        
        # Test daily granularity
        response = self.client.get(
            reverse('authentication:api_word_count_trend'),
            {'granularity': 'daily', 'days': 7}
        )
        self.assertEqual(response.status_code, 200)
        daily_data = response.json()
        
        # Test weekly granularity
        response = self.client.get(
            reverse('authentication:api_word_count_trend'),
            {'granularity': 'weekly', 'days': 14}
        )
        self.assertEqual(response.status_code, 200)
        weekly_data = response.json()
        
        # Weekly should aggregate more entries
        self.assertIsInstance(daily_data['trend'], list)
        self.assertIsInstance(weekly_data['trend'], list)


class TestWordCountTrend(TestCase):
    """Test word count trend calculations."""
    
    def test_word_count_trend_daily(self):
        """Test daily word count trend."""
        user = CustomUser.objects.create_user(email="trend@test.com", password="test")
        theme = Theme.objects.create(name="Daily")
        today = timezone.now()
        
        JournalEntry.objects.create(
            user=user, title="1", theme=theme, prompt="test", 
            answer="Five words in this one.",
            created_at=today - timedelta(days=1)
        )
        JournalEntry.objects.create(
            user=user, title="2", theme=theme, prompt="test", 
            answer="Another test entry here.",
            created_at=today
        )
        
        trend = AnalyticsService.get_word_count_trend(user, granularity='daily', days_lookback=2)
        self.assertGreater(len(trend), 0)
        self.assertIn('date', trend[0])
        self.assertIn('words', trend[0])
        self.assertIn('entries', trend[0])
    
    def test_word_count_trend_weekly(self):
        """Test weekly word count aggregation."""
        user = CustomUser.objects.create_user(email="weekly@test.com", password="test")
        theme = Theme.objects.create(name="Weekly")
        today = timezone.now()
        
        # Create entries on different days within same week
        for i in range(3):
            JournalEntry.objects.create(
                user=user, title=f"Entry {i}", theme=theme, prompt="test",
                answer="Test content with words.",
                created_at=today - timedelta(days=i)
            )
        
        trend = AnalyticsService.get_word_count_trend(user, granularity='weekly', days_lookback=7)
        self.assertGreater(len(trend), 0)


class TestMoodTrend(TestCase):
    """Test mood trend over time."""
    
    def test_mood_trend(self):
        """Test mood trend calculation."""
        user = CustomUser.objects.create_user(email="moodtrend@test.com", password="test")
        theme = Theme.objects.create(name="Mood")
        today = timezone.now()
        
        JournalEntry.objects.create(
            user=user, title="1", theme=theme, prompt="test",
            answer="I feel so happy and joyful today!",
            created_at=today - timedelta(days=2)
        )
        JournalEntry.objects.create(
            user=user, title="2", theme=theme, prompt="test",
            answer="I am sad and feeling down today.",
            created_at=today - timedelta(days=1)
        )
        
        trend = AnalyticsService.get_mood_trend(user, days_lookback=3)
        self.assertGreater(len(trend), 0)
        self.assertIn('date', trend[0])
        self.assertIn('moods', trend[0])
        self.assertIsInstance(trend[0]['moods'], dict)
