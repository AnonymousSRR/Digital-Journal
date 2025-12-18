"""
Unit tests for Analytics CSV Export.
"""
from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from authentication.models import Theme, JournalEntry
from authentication.services import AnalyticsService

CustomUser = get_user_model()


class TestAnalyticsExport(TestCase):
    """Test CSV export functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = CustomUser.objects.create_user(
            email="export@test.com",
            password="testpass"
        )
        self.theme = Theme.objects.create(name="ExportTheme")
    
    def test_export_full_analytics_csv(self):
        """Test full export CSV generation."""
        JournalEntry.objects.create(
            user=self.user, title="Test Entry", theme=self.theme, prompt="test",
            answer="This is test content with multiple words.",
            writing_time=300
        )
        
        csv_content = AnalyticsService.export_analytics_csv(self.user, export_type='full')
        
        # Verify CSV structure
        lines = csv_content.strip().split('\n')
        self.assertGreaterEqual(len(lines), 2)  # Header + at least 1 entry
        self.assertIn('Test Entry', csv_content)
        self.assertIn('ExportTheme', csv_content)
    
    def test_export_summary_csv(self):
        """Test summary export contains key metrics."""
        JournalEntry.objects.create(
            user=self.user, title="Entry", theme=self.theme, prompt="test",
            answer="Some content"
        )
        
        csv_content = AnalyticsService.export_analytics_csv(self.user, export_type='summary')
        
        self.assertIn('Current Streak', csv_content)
        self.assertIn('Total Words Written', csv_content)
        self.assertIn('Total Entries', csv_content)
    
    def test_export_mood_trends_csv(self):
        """Test mood trends export."""
        for emotion_text in [
            'I am so happy and joyful!',
            'I feel sad and down today.',
            'I am calm and peaceful.'
        ]:
            JournalEntry.objects.create(
                user=self.user, title="Entry", theme=self.theme, prompt="test",
                answer=emotion_text
            )
        
        csv_content = AnalyticsService.export_analytics_csv(self.user, export_type='mood_trends')
        
        # Check header
        self.assertIn('Joyful', csv_content)
        self.assertIn('Sad', csv_content)
        self.assertIn('Calm', csv_content)
        self.assertIn('Date', csv_content)
    
    def test_export_empty_entries(self):
        """Test export with no entries."""
        csv_content = AnalyticsService.export_analytics_csv(self.user, export_type='full')
        
        lines = csv_content.strip().split('\n')
        # Should have header only
        self.assertEqual(len(lines), 1)
    
    def test_download_csv_endpoint(self):
        """Test CSV download endpoint returns file with correct headers."""
        client = Client()
        client.login(email="export@test.com", password="testpass")
        
        JournalEntry.objects.create(
            user=self.user, title="Entry", theme=self.theme, prompt="test",
            answer="Content here"
        )
        
        response = client.get(reverse('authentication:download_analytics_csv'), {'type': 'full'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('analytics_full_', response['Content-Disposition'])
    
    def test_download_csv_requires_auth(self):
        """Test that CSV download requires authentication."""
        client = Client()
        response = client.get(reverse('authentication:download_analytics_csv'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_download_csv_invalid_type(self):
        """Test that invalid export type returns error."""
        client = Client()
        client.login(email="export@test.com", password="testpass")
        
        response = client.get(
            reverse('authentication:download_analytics_csv'),
            {'type': 'invalid_type'}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_export_respects_days_lookback(self):
        """Test that export respects the days lookback parameter."""
        # Create 3 entries
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user, title=f"Entry{i}", theme=self.theme, prompt="test",
                answer=f"Entry content {i}"
            )
        
        # All entries should be in recent export
        csv_content_all = AnalyticsService.export_analytics_csv(self.user, export_type='full', days_lookback=365)
        lines_all = [l for l in csv_content_all.strip().split('\n') if l]
        self.assertEqual(len(lines_all), 4, "Should have header + 3 entries")  # Header + 3 entries
        
        # Even with small lookback, they should all be there since they're created "today"
        csv_content_recent = AnalyticsService.export_analytics_csv(self.user, export_type='full', days_lookback=1)
        lines_recent = [l for l in csv_content_recent.strip().split('\n') if l]
        self.assertEqual(len(lines_recent), 4, "All entries created today should be included")
    
    def test_full_export_includes_all_fields(self):
        """Test that full export includes all required fields."""
        JournalEntry.objects.create(
            user=self.user,
            title="Complete Entry",
            theme=self.theme,
            prompt="test prompt",
            answer="This is the answer with multiple words.",
            writing_time=120,
            visibility='private'
        )
        
        csv_content = AnalyticsService.export_analytics_csv(self.user, export_type='full')
        
        # Check all columns present
        expected_fields = ['Date', 'Title', 'Theme', 'Word Count', 'Primary Emotion', 
                          'Sentiment Score', 'Writing Time', 'Visibility']
        for field in expected_fields:
            self.assertIn(field, csv_content)
        
        # Check data present
        self.assertIn('Complete Entry', csv_content)
        self.assertIn('private', csv_content)
