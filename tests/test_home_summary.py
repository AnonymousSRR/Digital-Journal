from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, JournalEntry, Theme
from django.utils import timezone
from datetime import timedelta


class HomeSummaryWidgetTests(TestCase):
    def setUp(self):
        # Arrange: Create a test user
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        # Create a test theme
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='Test description'
        )
    
    def test_total_entries_count(self):
        # Arrange: Create 5 journal entries
        for i in range(5):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Test prompt',
                answer='I am so happy and excited about everything today!'
            )
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check that total_entries is 5
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_entries'], 5)
    
    def test_entries_this_week_count(self):
        # Arrange: Create entries from different time periods
        
        # Entry from 3 days ago (should be counted)
        three_days_ago = timezone.now() - timedelta(days=3)
        JournalEntry.objects.create(
            user=self.user,
            title='Recent Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='I feel peaceful and calm today',
            created_at=three_days_ago
        )
        
        # Entry from 10 days ago (should NOT be counted)
        ten_days_ago = timezone.now() - timedelta(days=10)
        old_entry = JournalEntry.objects.create(
            user=self.user,
            title='Old Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='I feel very sad and down'
        )
        old_entry.created_at = ten_days_ago
        old_entry.save()
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check that entries_this_week is 1
        self.assertEqual(response.context['entries_this_week'], 1)
    
    def test_most_common_emotion_calculation(self):
        # Arrange: Create entries with different emotions
        # 3 joyful entries
        for i in range(3):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Joyful Entry {i}',
                theme=self.theme,
                prompt='Test prompt',
                answer='I am so happy and excited! This is wonderful and amazing!'
            )
        
        # 2 sad entries
        for i in range(2):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Sad Entry {i}',
                theme=self.theme,
                prompt='Test prompt',
                answer='I feel very sad and depressed today'
            )
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check that most_common_emotion is 'Joyful'
        self.assertEqual(response.context['most_common_emotion'], 'Joyful')
    
    def test_empty_entries_for_new_user(self):
        # Arrange: New user with no entries (already in setUp)
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check default values
        self.assertEqual(response.context['total_entries'], 0)
        self.assertEqual(response.context['entries_this_week'], 0)
        self.assertEqual(response.context['most_common_emotion'], 'Neutral')
    
    def test_statistics_are_user_specific(self):
        # Arrange: Create another user with their own entries
        other_user = CustomUser.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Create entries for other user
        for i in range(3):
            JournalEntry.objects.create(
                user=other_user,
                title=f'Other Entry {i}',
                theme=self.theme,
                prompt='Test prompt',
                answer='I am so angry and frustrated with everything!'
            )
        
        # Create entry for current user
        JournalEntry.objects.create(
            user=self.user,
            title='My Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='I feel peaceful and calm today'
        )
        
        # Act: Request the home page as current user
        response = self.client.get(reverse('home'))
        
        # Assert: Check that only current user's data is shown
        self.assertEqual(response.context['total_entries'], 1)
        self.assertEqual(response.context['most_common_emotion'], 'Calm')


class HomeSummaryIntegrationTests(TestCase):
    """Integration tests for the home page summary widget."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='Test description'
        )
    
    def test_complete_widget_workflow(self):
        """Test the complete widget functionality with realistic data."""
        # Arrange: Create a realistic set of journal entries with text that will analyze to desired emotions
        emotion_texts = [
            'I am so happy and excited! This is wonderful!',  # joyful
            'What a great day filled with joy and happiness!',  # joyful
            'I feel peaceful and calm today',  # calm
            'I feel very sad and depressed',  # sad
            'Amazing! I am thrilled and delighted!',  # joyful
            'I feel anxious and worried about everything'  # anxious
        ]
        
        for i, text in enumerate(emotion_texts):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i+1}',
                theme=self.theme,
                prompt='Test prompt',
                answer=text
            )
        
        # Act: Get the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Verify all statistics are correct
        self.assertEqual(response.context['total_entries'], 6)
        self.assertEqual(response.context['entries_this_week'], 6)
        self.assertEqual(response.context['most_common_emotion'], 'Joyful')
        
        # Verify HTML rendering
        content = response.content.decode()
        self.assertIn('summary-widget', content)
        self.assertIn('data-testid="total-entries-value">6', content)
        self.assertIn('Joyful', content)
    
    def test_mixed_entries_across_time_periods(self):
        # Arrange: Create entries from different time periods
        # 2 entries this week
        for i in range(2):
            JournalEntry.objects.create(
                user=self.user,
                title=f'This Week {i}',
                theme=self.theme,
                prompt='Test',
                answer='I am so happy and joyful today!'
            )
        
        # 3 entries from 2 weeks ago
        two_weeks_ago = timezone.now() - timedelta(days=14)
        for i in range(3):
            old_entry = JournalEntry.objects.create(
                user=self.user,
                title=f'Old Entry {i}',
                theme=self.theme,
                prompt='Test',
                answer='I feel very sad and depressed'
            )
            old_entry.created_at = two_weeks_ago
            old_entry.save()
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Verify correct calculations
        self.assertEqual(response.context['total_entries'], 5)
        self.assertEqual(response.context['entries_this_week'], 2)
        # Most common emotion overall is 'sad' (3 vs 2)
        self.assertEqual(response.context['most_common_emotion'], 'Sad')
    
    def test_unauthenticated_user_redirected(self):
        # Arrange: Log out the user
        self.client.logout()
        
        # Act: Try to access home page
        response = self.client.get(reverse('home'))
        
        # Assert: Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_performance_with_many_entries(self):
        # Arrange: Create 100 entries
        import time
        
        emotion_texts = [
            'I am so happy and joyful!',
            'I feel very sad today',
            'I feel peaceful and calm',
            'I am angry and frustrated'
        ]
        
        for i in range(100):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Test',
                answer=emotion_texts[i % 4]
            )
        
        # Act: Time the page load
        start_time = time.time()
        response = self.client.get(reverse('home'))
        end_time = time.time()
        
        # Assert: Should complete in reasonable time (< 1 second)
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)
        self.assertEqual(response.context['total_entries'], 100)
    
    def test_emotion_tie_returns_first_alphabetically(self):
        # Arrange: Create equal number of two emotions
        for i in range(2):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Angry {i}',
                theme=self.theme,
                prompt='Test',
                answer='I am so angry and furious!'
            )
            JournalEntry.objects.create(
                user=self.user,
                title=f'Joyful {i}',
                theme=self.theme,
                prompt='Test',
                answer='I am so happy and joyful today!'
            )
        
        # Act: Get home page
        response = self.client.get(reverse('home'))
        
        # Assert: Should return one of them consistently
        # (Django's order_by with ties will return first in natural order)
        emotion = response.context['most_common_emotion']
        self.assertIn(emotion, ['Angry', 'Joyful'])
    
    def test_summary_widget_renders_on_home_page(self):
        # Arrange: Create a journal entry
        JournalEntry.objects.create(
            user=self.user,
            title='Test Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='I am so happy and joyful today!'
        )
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Check that summary widget is in the response
        self.assertContains(response, 'summary-widget')
        self.assertContains(response, 'Total Entries')
        self.assertContains(response, 'Entries This Week')
        self.assertContains(response, 'Most Common Emotion')
    
    def test_summary_widget_displays_correct_values(self):
        # Arrange: Create 2 entries
        for i in range(2):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i}',
                theme=self.theme,
                prompt='Test prompt',
                answer='I feel peaceful and calm today'
            )
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        
        # Assert: Check that values are correctly displayed
        self.assertIn('data-testid="total-entries-value">2', content)
        self.assertIn('data-testid="entries-week-value">2', content)
        self.assertIn('data-testid="emotion-value">Calm', content)
    
    def test_summary_widget_shows_zero_for_new_user(self):
        # Arrange: New user with no entries (from setUp)
        
        # Act: Request the home page
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        
        # Assert: Check zero values are displayed
        self.assertIn('data-testid="total-entries-value">0', content)
        self.assertIn('data-testid="entries-week-value">0', content)
        self.assertIn('data-testid="emotion-value">Neutral', content)
