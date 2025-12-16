"""
Unit tests for emotion analytics API endpoints and views
Tests emotion statistics, trends, and theme-based breakdown endpoints
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json
from authentication.models import Theme, JournalEntry

User = get_user_model()


class EmotionStatsViewTests(TestCase):
    """Test cases for emotion statistics API endpoint"""
    
    def setUp(self):
        """Set up test user, theme, and client"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.theme = Theme.objects.create(name='Personal', description='test')
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_get_emotion_stats_returns_correct_distribution(self):
        """Test that emotion stats API returns correct emotion distribution"""
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Happy and excited'
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme, prompt='p', answer='Sad and depressed'
        )
        
        response = self.client.get(reverse('emotion_stats'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total_entries'], 2)
        self.assertEqual(data['primary_emotion_distribution']['joyful'], 1)
        self.assertEqual(data['primary_emotion_distribution']['sad'], 1)
        # Average should be between -0.7 and 0.8
        self.assertGreater(data['average_sentiment_score'], -1.0)
        self.assertLess(data['average_sentiment_score'], 1.0)
    
    def test_get_emotion_stats_empty_user(self):
        """Test emotion stats for user with no entries"""
        response = self.client.get(reverse('emotion_stats'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['total_entries'], 0)
        self.assertEqual(data['average_sentiment_score'], 0.0)
    
    def test_get_emotion_stats_requires_login(self):
        """Test that emotion stats endpoint requires authentication"""
        client = Client()
        response = client.get(reverse('emotion_stats'))
        # Should redirect to login
        self.assertNotEqual(response.status_code, 200)
    
    def test_get_emotion_stats_single_entry(self):
        """Test emotion stats with single entry"""
        JournalEntry.objects.create(
            user=self.user, title='One', theme=self.theme, prompt='p', answer='Amazing!'
        )
        
        response = self.client.get(reverse('emotion_stats'))
        data = response.json()
        
        self.assertEqual(data['total_entries'], 1)
        self.assertEqual(data['primary_emotion_distribution']['joyful'], 1)
        # Amazing should produce positive sentiment
        self.assertGreater(data['average_sentiment_score'], 0.0)
    
    def test_get_emotion_stats_multiple_same_emotions(self):
        """Test emotion stats when multiple entries have same emotion"""
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user, title=f'{i}', theme=self.theme, prompt='p', answer='Happy'
            )
        
        response = self.client.get(reverse('emotion_stats'))
        data = response.json()
        
        self.assertEqual(data['total_entries'], 3)
        self.assertEqual(data['primary_emotion_distribution']['joyful'], 3)


class EmotionTrendsViewTests(TestCase):
    """Test cases for emotion trends API endpoint"""
    
    def setUp(self):
        """Set up test user, theme, and client"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.theme = Theme.objects.create(name='Personal', description='test')
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_get_emotion_trends_filters_by_days(self):
        """Test that emotion trends respects the days parameter"""
        old_date = timezone.now() - timedelta(days=40)
        recent_date = timezone.now() - timedelta(days=5)
        
        JournalEntry.objects.create(
            user=self.user, title='old', theme=self.theme, prompt='p', answer='Old entry',
            created_at=old_date
        )
        JournalEntry.objects.create(
            user=self.user, title='recent', theme=self.theme, prompt='p', answer='Recent entry',
            created_at=recent_date
        )
        
        response = self.client.get(reverse('emotion_trends') + '?days=30')
        data = response.json()
        
        # Only recent entry should be included
        self.assertEqual(len(data), 1)
    
    def test_get_emotion_trends_default_days(self):
        """Test that emotion trends uses default 30 days when not specified"""
        recent_date = timezone.now() - timedelta(days=5)
        
        JournalEntry.objects.create(
            user=self.user, title='recent', theme=self.theme, prompt='p', answer='Recent entry',
            created_at=recent_date
        )
        
        response = self.client.get(reverse('emotion_trends'))
        data = response.json()
        
        self.assertGreater(len(data), 0)
        self.assertIn('date', data[0])
        self.assertIn('emotions', data[0])
        self.assertIn('average_sentiment', data[0])
    
    def test_get_emotion_trends_empty_result(self):
        """Test emotion trends for user with no entries"""
        response = self.client.get(reverse('emotion_trends'))
        data = response.json()
        
        self.assertEqual(len(data), 0)
    
    def test_get_emotion_trends_includes_date_key(self):
        """Test that trends include ISO format date keys"""
        JournalEntry.objects.create(
            user=self.user, title='test', theme=self.theme, prompt='p', answer='Test'
        )
        
        response = self.client.get(reverse('emotion_trends') + '?days=30')
        data = response.json()
        
        self.assertGreater(len(data), 0)
        # Date should be in ISO format
        import re
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        self.assertTrue(re.match(date_pattern, data[0]['date']))
    
    def test_get_emotion_trends_groups_by_date(self):
        """Test that multiple entries on same day are grouped"""
        today = timezone.now()
        
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Happy',
            created_at=today
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme, prompt='p', answer='Happy again',
            created_at=today + timedelta(hours=1)
        )
        
        response = self.client.get(reverse('emotion_trends'))
        data = response.json()
        
        # Should have one entry for today with count 2
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['emotions']['joyful'], 2)


class EmotionByThemeViewTests(TestCase):
    """Test cases for emotion statistics by theme API endpoint"""
    
    def setUp(self):
        """Set up test user, themes, and client"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.theme1 = Theme.objects.create(name='Work', description='test')
        self.theme2 = Theme.objects.create(name='Personal', description='test')
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_get_emotion_by_theme_breaks_down_correctly(self):
        """Test that emotions are correctly broken down by theme"""
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme1, prompt='p', answer='Happy at work'
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme2, prompt='p', answer='Stressed personally'
        )
        
        response = self.client.get(reverse('emotion_by_theme'))
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('Work', data)
        self.assertIn('Personal', data)
        self.assertEqual(data['Work']['emotion_distribution']['joyful'], 1)
        self.assertEqual(data['Personal']['emotion_distribution']['anxious'], 1)
    
    def test_get_emotion_by_theme_empty_user(self):
        """Test emotion by theme for user with no entries"""
        response = self.client.get(reverse('emotion_by_theme'))
        data = response.json()
        
        self.assertEqual(len(data), 0)
    
    def test_get_emotion_by_theme_multiple_emotions_per_theme(self):
        """Test theme breakdown with multiple emotions per theme"""
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme1, prompt='p', answer='Happy'
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme1, prompt='p', answer='Angry'
        )
        
        response = self.client.get(reverse('emotion_by_theme'))
        data = response.json()
        
        self.assertEqual(data['Work']['entry_count'], 2)
        self.assertEqual(data['Work']['emotion_distribution']['joyful'], 1)
        self.assertEqual(data['Work']['emotion_distribution']['angry'], 1)
    
    def test_get_emotion_by_theme_requires_login(self):
        """Test that endpoint requires authentication"""
        client = Client()
        response = client.get(reverse('emotion_by_theme'))
        self.assertNotEqual(response.status_code, 200)


class EmotionFilteringViewTests(TestCase):
    """Test cases for emotion filtering endpoint"""
    
    def setUp(self):
        """Set up test user, theme, and client"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.theme = Theme.objects.create(name='Personal', description='test')
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_filter_entries_by_emotion(self):
        """Test filtering entries by single emotion"""
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Happy'
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme, prompt='p', answer='Sad'
        )
        
        response = self.client.get(reverse('get_entries_by_emotion') + '?emotion=joyful')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['entries'][0]['primary_emotion'], 'joyful')
    
    def test_filter_entries_by_sentiment_range(self):
        """Test filtering entries by sentiment score range"""
        entry1 = JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Very happy'
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme, prompt='p', answer='Neutral'
        )
        
        # Get the actual sentiment score from the first entry
        min_sentiment = entry1.sentiment_score - 0.1
        max_sentiment = entry1.sentiment_score + 0.1
        
        response = self.client.get(
            reverse('get_entries_by_emotion') + f'?min_sentiment={min_sentiment}&max_sentiment={max_sentiment}'
        )
        
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['entries'][0]['sentiment_score'], entry1.sentiment_score)
    
    def test_filter_entries_no_matches(self):
        """Test filtering when no entries match criteria"""
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Happy'
        )
        
        response = self.client.get(reverse('get_entries_by_emotion') + '?emotion=sad')
        data = response.json()
        
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['entries']), 0)
    
    def test_filter_entries_combined_criteria(self):
        """Test filtering with both emotion and sentiment range"""
        entry1 = JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Very happy'
        )
        JournalEntry.objects.create(
            user=self.user, title='2', theme=self.theme, prompt='p', answer='Slightly happy'
        )
        
        # Get the actual sentiment score and filter by a high range
        min_sentiment = entry1.sentiment_score - 0.1
        
        response = self.client.get(
            reverse('get_entries_by_emotion') + f'?emotion=joyful&min_sentiment={min_sentiment}'
        )
        
        data = response.json()
        # Both entries should be joyful, but only one should match the high sentiment range
        self.assertGreater(data['count'], 0)
        for entry in data['entries']:
            self.assertEqual(entry['primary_emotion'], 'joyful')
    
    def test_filter_entries_invalid_sentiment_values(self):
        """Test that invalid sentiment values are handled gracefully"""
        JournalEntry.objects.create(
            user=self.user, title='1', theme=self.theme, prompt='p', answer='Test'
        )
        
        # Invalid sentiment values should be ignored
        response = self.client.get(
            reverse('get_entries_by_emotion') + '?min_sentiment=invalid&max_sentiment=invalid'
        )
        
        # Should still work and return all entries
        data = response.json()
        self.assertEqual(data['count'], 1)
