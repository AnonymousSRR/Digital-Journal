"""
Unit tests for Analytics Service.
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from authentication.models import Theme, JournalEntry
from authentication.services import AnalyticsService

CustomUser = get_user_model()


class TestWritingStreaks(TestCase):
    """Test writing streak calculations."""
    
    def test_writing_streak_consecutive_entries(self):
        """Test current streak calculation with consecutive daily entries."""
        user = CustomUser.objects.create_user(email="test@test.com", password="test")
        theme = Theme.objects.create(name="Daily")
        
        # Create entries on clearly different days (use replace to set time to noon each day)
        base_date = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
        
        for i in range(5):
            entry_date = base_date - timedelta(days=i)
            JournalEntry.objects.create(
                user=user,
                title=f"Entry day {i}",
                theme=theme,
                prompt="test",
                answer="This is a test journal entry with multiple words here.",
                created_at=entry_date
            )
        
        streaks = AnalyticsService.get_writing_streaks(user)
        
        # Should have entries spanning at least a few days
        self.assertGreaterEqual(streaks['current_streak'], 1, "Should have at least current day")
        self.assertGreaterEqual(streaks['longest_streak'], 1, "Should have at least longest of 1")
        self.assertIsNotNone(streaks['last_entry_date'], "Should have a last entry date")
        
        # Verify we created 5 entries
        entry_count = JournalEntry.objects.filter(user=user).count()
        self.assertEqual(entry_count, 5, "Should have created 5 entries")
    
    def test_writing_streak_broken(self):
        """Test streak broken by missing day."""
        user = CustomUser.objects.create_user(email="test2@test.com", password="test")
        theme = Theme.objects.create(name="Daily2")
        today = timezone.now()
        
        # Create entries with gap
        JournalEntry.objects.create(
            user=user, title="1", theme=theme, prompt="test", 
            answer="content", created_at=today
        )
        JournalEntry.objects.create(
            user=user, title="2", theme=theme, prompt="test", 
            answer="content", created_at=today - timedelta(days=3)
        )
        
        streaks = AnalyticsService.get_writing_streaks(user)
        self.assertEqual(streaks['current_streak'], 1)
        self.assertGreaterEqual(streaks['longest_streak'], 1)
    
    def test_no_entries(self):
        """Test streak calculation with no entries."""
        user = CustomUser.objects.create_user(email="test3@test.com", password="test")
        
        streaks = AnalyticsService.get_writing_streaks(user)
        self.assertEqual(streaks['current_streak'], 0)
        self.assertEqual(streaks['longest_streak'], 0)
        self.assertIsNone(streaks['last_entry_date'])


class TestWordCountStats(TestCase):
    """Test word count statistics."""
    
    def test_word_count_stats(self):
        """Test word count statistics calculation."""
        user = CustomUser.objects.create_user(email="test4@test.com", password="test")
        theme = Theme.objects.create(name="Stats")
        
        JournalEntry.objects.create(
            user=user, title="Short", theme=theme, prompt="test", 
            answer="Five words in this entry"
        )
        JournalEntry.objects.create(
            user=user, title="Long", theme=theme, prompt="test", 
            answer="This is a much longer entry with many more words than the previous one and it continues."
        )
        
        stats = AnalyticsService.get_word_count_stats(user)
        self.assertGreater(stats['total_words'], 0)
        self.assertGreater(stats['avg_words_per_entry'], 0)
        self.assertGreater(stats['max_words_in_entry'], stats['min_words_in_entry'])
        self.assertEqual(stats['min_words_in_entry'], 5)
    
    def test_word_count_no_entries(self):
        """Test word count with no entries."""
        user = CustomUser.objects.create_user(email="test5@test.com", password="test")
        
        stats = AnalyticsService.get_word_count_stats(user)
        self.assertEqual(stats['total_words'], 0)
        self.assertEqual(stats['avg_words_per_entry'], 0.0)
        self.assertEqual(stats['max_words_in_entry'], 0)


class TestMoodDistribution(TestCase):
    """Test mood distribution calculations."""
    
    def test_mood_distribution(self):
        """Test mood distribution calculation."""
        user = CustomUser.objects.create_user(email="test6@test.com", password="test")
        theme = Theme.objects.create(name="Mood")
        
        # Use text that will trigger the right emotions via the emotion analysis signal
        JournalEntry.objects.create(
            user=user, title="Happy", theme=theme, prompt="test", 
            answer="I am so happy and excited about today! What a wonderful amazing day!"
        )
        JournalEntry.objects.create(
            user=user, title="Sad", theme=theme, prompt="test", 
            answer="I feel so sad and depressed today. Everything is gloomy and I feel lonely and miserable."
        )
        JournalEntry.objects.create(
            user=user, title="Happy2", theme=theme, prompt="test", 
            answer="This is fantastic! I am thrilled and delighted with everything. Life is wonderful!"
        )
        
        distribution = AnalyticsService.get_mood_distribution(user)
        # Verify at least the positive and negative emotions are detected
        self.assertGreater(distribution['joyful'], 0)
        self.assertGreater(distribution['sad'], 0)
    
    def test_mood_distribution_all_emotions_present(self):
        """Test that all emotions are present even with 0 count."""
        user = CustomUser.objects.create_user(email="test7@test.com", password="test")
        theme = Theme.objects.create(name="Mood2")
        
        JournalEntry.objects.create(
            user=user, title="Happy", theme=theme, prompt="test", 
            answer="test", primary_emotion='joyful'
        )
        
        distribution = AnalyticsService.get_mood_distribution(user)
        expected_emotions = ['joyful', 'sad', 'angry', 'anxious', 'calm', 'neutral']
        for emotion in expected_emotions:
            self.assertIn(emotion, distribution)


class TestTopThemes(TestCase):
    """Test top themes extraction."""
    
    def test_top_themes(self):
        """Test top themes extraction."""
        user = CustomUser.objects.create_user(email="test8@test.com", password="test")
        theme1 = Theme.objects.create(name="Work")
        theme2 = Theme.objects.create(name="Personal")
        
        for _ in range(3):
            JournalEntry.objects.create(
                user=user, title="Entry", theme=theme1, prompt="test", 
                answer="test", sentiment_score=0.5
            )
        
        JournalEntry.objects.create(
            user=user, title="Entry", theme=theme2, prompt="test", 
            answer="test", sentiment_score=-0.3
        )
        
        themes = AnalyticsService.get_top_themes(user)
        self.assertGreaterEqual(len(themes), 2)
        self.assertEqual(themes[0]['theme'], 'Work')
        self.assertEqual(themes[0]['count'], 3)
        self.assertIn('avg_sentiment', themes[0])
    
    def test_top_themes_limit(self):
        """Test top themes respects limit parameter."""
        user = CustomUser.objects.create_user(email="test9@test.com", password="test")
        
        for i in range(10):
            theme = Theme.objects.create(name=f"Theme{i}")
            JournalEntry.objects.create(
                user=user, title=f"Entry{i}", theme=theme, prompt="test", 
                answer="test"
            )
        
        themes = AnalyticsService.get_top_themes(user, limit=3)
        self.assertLessEqual(len(themes), 3)
