"""
Unit tests for journal entry emotion analysis integration
Tests that emotions are automatically analyzed when entries are created/updated
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from authentication.models import Theme, JournalEntry
from authentication.services import EmotionAnalysisService

User = get_user_model()


class JournalEntryEmotionAnalysisTests(TestCase):
    """Test emotion analysis integration with journal entry creation and updates"""
    
    def setUp(self):
        """Set up test user and theme"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.theme = Theme.objects.create(name='Personal Growth', description='test')
    
    def test_journal_entry_emotions_analyzed_on_creation(self):
        """Test that journal entry emotions are automatically analyzed on creation"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Happy Day',
            theme=self.theme,
            prompt='How was your day?',
            answer='I had an amazing and wonderful day! Everything was great!'
        )
        
        self.assertEqual(entry.primary_emotion, 'joyful')
        self.assertGreater(entry.sentiment_score, 0.3)
        self.assertIsNotNone(entry.emotion_data)
        self.assertIn('joyful', entry.emotion_data)
    
    def test_emotion_analysis_updates_on_entry_modification(self):
        """Test that emotion analysis updates when entry content is modified"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Entry',
            theme=self.theme,
            prompt='Prompt',
            answer='Happy'
        )
        initial_emotion = entry.primary_emotion
        initial_sentiment = entry.sentiment_score
        
        entry.answer = 'I am sad and depressed'
        entry.save()
        entry.refresh_from_db()
        
        self.assertNotEqual(entry.primary_emotion, initial_emotion)
        self.assertEqual(entry.primary_emotion, 'sad')
        self.assertLess(entry.sentiment_score, initial_sentiment)
    
    def test_emotion_analysis_with_joyful_entry(self):
        """Test emotion analysis for joyful journal entry"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Excited',
            theme=self.theme,
            prompt='What are you excited about?',
            answer='I am so excited and thrilled about the amazing opportunities ahead!'
        )
        
        self.assertEqual(entry.primary_emotion, 'joyful')
        self.assertGreater(entry.sentiment_score, 0.4)
        self.assertGreater(entry.emotion_data['joyful'], 0.0)
    
    def test_emotion_analysis_with_sad_entry(self):
        """Test emotion analysis for sad journal entry"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Sad',
            theme=self.theme,
            prompt='How are you feeling?',
            answer='I feel depressed and miserable about recent events'
        )
        
        self.assertEqual(entry.primary_emotion, 'sad')
        self.assertLess(entry.sentiment_score, -0.1)
        self.assertGreater(entry.emotion_data['sad'], 0.0)
    
    def test_emotion_analysis_with_anxious_entry(self):
        """Test emotion analysis for anxious journal entry"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Worried',
            theme=self.theme,
            prompt='What concerns you?',
            answer='I am anxious and stressed about the upcoming challenges'
        )
        
        self.assertEqual(entry.primary_emotion, 'anxious')
        self.assertGreater(entry.emotion_data['anxious'], 0.0)
    
    def test_emotion_analysis_with_calm_entry(self):
        """Test emotion analysis for calm journal entry"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Peaceful',
            theme=self.theme,
            prompt='What brings you peace?',
            answer='I feel calm and peaceful. The serene environment helps me relax.'
        )
        
        self.assertEqual(entry.primary_emotion, 'calm')
        self.assertGreater(entry.emotion_data['calm'], 0.0)
    
    def test_emotion_analysis_preserves_other_fields(self):
        """Test that emotion analysis doesn't affect other entry fields"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Test Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer='Happy emotions here',
            bookmarked=True,
            writing_time=300
        )
        
        # Verify emotion fields were populated
        self.assertEqual(entry.primary_emotion, 'joyful')
        
        # Verify other fields unchanged
        self.assertEqual(entry.title, 'Test Entry')
        self.assertEqual(entry.prompt, 'Test prompt')
        self.assertTrue(entry.bookmarked)
        self.assertEqual(entry.writing_time, 300)
    
    def test_emotion_analysis_with_empty_answer_field(self):
        """Test emotion analysis handles empty answer field"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Empty Entry',
            theme=self.theme,
            prompt='Test prompt',
            answer=''
        )
        
        # Should use default emotion
        self.assertEqual(entry.primary_emotion, 'neutral')
        self.assertEqual(entry.sentiment_score, 0.0)
    
    def test_emotion_analysis_with_very_long_answer(self):
        """Test emotion analysis works with very long journal entries"""
        long_answer = """
        Today was absolutely wonderful! I felt so happy and joyful throughout the day.
        Everything went perfectly, and I accomplished so much. The support from my team
        was amazing and fantastic. I learned new things and grew as a person. This
        experience was truly excellent and I feel grateful for every moment.
        """ * 5
        
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Long Entry',
            theme=self.theme,
            prompt='Tell me everything',
            answer=long_answer
        )
        
        self.assertEqual(entry.primary_emotion, 'joyful')
        self.assertGreater(entry.sentiment_score, 0.4)
        self.assertIsNotNone(entry.emotion_data)
    
    def test_emotion_analysis_multiple_entries_independent(self):
        """Test that emotion analysis is independent for each entry"""
        entry1 = JournalEntry.objects.create(
            user=self.user,
            title='Happy Entry',
            theme=self.theme,
            prompt='Prompt 1',
            answer='I am happy and excited'
        )
        
        entry2 = JournalEntry.objects.create(
            user=self.user,
            title='Sad Entry',
            theme=self.theme,
            prompt='Prompt 2',
            answer='I am sad and depressed'
        )
        
        # Each entry should have its own emotion analysis
        self.assertEqual(entry1.primary_emotion, 'joyful')
        self.assertEqual(entry2.primary_emotion, 'sad')
        self.assertGreater(entry1.sentiment_score, entry2.sentiment_score)
    
    def test_emotion_data_json_structure(self):
        """Test that emotion_data is properly structured as JSON"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Test',
            theme=self.theme,
            prompt='Prompt',
            answer='Happy and sad'
        )
        
        # emotion_data should be a dictionary
        self.assertIsInstance(entry.emotion_data, dict)
        
        # Should contain all emotion types
        expected_emotions = {'joyful', 'sad', 'angry', 'anxious', 'calm'}
        self.assertEqual(set(entry.emotion_data.keys()), expected_emotions)
        
        # All values should be floats
        for score in entry.emotion_data.values():
            self.assertIsInstance(score, (int, float))
    
    def test_emotion_analysis_with_mixed_case_answer(self):
        """Test emotion analysis with mixed case text"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='MixedCase',
            theme=self.theme,
            prompt='Prompt',
            answer='I Am HaPpY AnD ExCiTeD AbOuT ThE FuTuRe!'
        )
        
        self.assertEqual(entry.primary_emotion, 'joyful')
        self.assertGreater(entry.sentiment_score, 0.0)
    
    def test_emotion_analysis_with_special_characters(self):
        """Test emotion analysis with special characters and punctuation"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Special',
            theme=self.theme,
            prompt='Prompt',
            answer='I\'m so happy!!! This is amazing... Wonderful!!! @#$ Fantastic!!!'
        )
        
        self.assertEqual(entry.primary_emotion, 'joyful')
        self.assertGreater(entry.sentiment_score, 0.0)
    
    def test_emotion_scores_consistency(self):
        """Test that repeated analysis of same entry gives consistent results"""
        answer = "I am happy but also worried about the future"
        
        entry1 = JournalEntry.objects.create(
            user=self.user,
            title='Entry 1',
            theme=self.theme,
            prompt='Prompt',
            answer=answer
        )
        
        entry2 = JournalEntry.objects.create(
            user=self.user,
            title='Entry 2',
            theme=self.theme,
            prompt='Prompt',
            answer=answer
        )
        
        # Same answer should produce same emotion analysis
        self.assertEqual(entry1.primary_emotion, entry2.primary_emotion)
        self.assertEqual(entry1.sentiment_score, entry2.sentiment_score)
        self.assertEqual(entry1.emotion_data, entry2.emotion_data)
    
    def test_emotion_analysis_preserves_defaults(self):
        """Test that emotion fields get populated and aren't None"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Test',
            theme=self.theme,
            prompt='Prompt',
            answer='Test answer'
        )
        
        # Should not be None or empty
        self.assertIsNotNone(entry.primary_emotion)
        self.assertNotEqual(entry.primary_emotion, '')
        self.assertIsNotNone(entry.sentiment_score)
        self.assertIsNotNone(entry.emotion_data)
        self.assertIsInstance(entry.emotion_data, dict)
