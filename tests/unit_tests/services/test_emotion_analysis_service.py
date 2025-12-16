"""
Unit tests for EmotionAnalysisService
Tests emotion detection, sentiment analysis, and primary emotion determination.
"""
from django.test import TestCase
from authentication.services import EmotionAnalysisService


class EmotionAnalysisServiceTests(TestCase):
    """Test cases for EmotionAnalysisService emotion detection"""
    
    def test_analyze_emotions_detects_joyful_sentiment(self):
        """Test that emotion analysis detects joyful sentiment from positive text"""
        text = "I feel amazing and excited about the wonderful things happening in my life!"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'joyful')
        self.assertGreater(result['sentiment_score'], 0.3)
        self.assertGreater(result['emotion_data']['joyful'], 0.0)
        self.assertIn('emotion_data', result)
        self.assertIn('primary_emotion', result)
        self.assertIn('sentiment_score', result)
    
    def test_analyze_emotions_detects_sad_sentiment(self):
        """Test that emotion analysis detects sad sentiment from negative text"""
        text = "I feel sad and depressed about the situation. Everything seems gloomy and lonely."
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'sad')
        self.assertLess(result['sentiment_score'], -0.1)
        self.assertGreater(result['emotion_data']['sad'], 0.0)
    
    def test_analyze_emotions_detects_anxious_sentiment(self):
        """Test that emotion analysis detects anxious sentiment from anxiety text"""
        text = "I am anxious and worried about the upcoming presentation. I feel stressed and overwhelmed."
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'anxious')
        self.assertGreater(result['emotion_data']['anxious'], 0.0)
    
    def test_analyze_emotions_detects_angry_sentiment(self):
        """Test that emotion analysis detects angry sentiment from anger text"""
        text = "I am furious and angry about what happened. This is frustrating and annoying."
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'angry')
        self.assertGreater(result['emotion_data']['angry'], 0.0)
    
    def test_analyze_emotions_detects_calm_sentiment(self):
        """Test that emotion analysis detects calm sentiment from peaceful text"""
        text = "I feel calm and peaceful. Everything is serene and tranquil. I am content and at ease."
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'calm')
        self.assertGreater(result['emotion_data']['calm'], 0.0)
    
    def test_analyze_emotions_handles_neutral_text(self):
        """Test that emotion analysis handles neutral text correctly"""
        text = "The cat sat on the table. I walked to the store. The sun was visible. Numbers appear here."
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'neutral')
        self.assertGreaterEqual(result['sentiment_score'], -0.3)
        self.assertLessEqual(result['sentiment_score'], 0.3)
    
    def test_analyze_emotions_handles_empty_text(self):
        """Test that emotion analysis handles empty text gracefully"""
        text = ""
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertIn('primary_emotion', result)
        self.assertIn('sentiment_score', result)
        self.assertIn('emotion_data', result)
        self.assertEqual(result['sentiment_score'], 0.0)
        self.assertEqual(result['primary_emotion'], 'neutral')
    
    def test_sentiment_score_is_within_valid_range(self):
        """Test that sentiment scores are always within -1.0 to 1.0 range"""
        texts = [
            "I love this! It's amazing and wonderful and fantastic and excellent!",
            "I hate this. It's awful and terrible and horrible and bad and worst!",
            "The weather is nice.",
            ""
        ]
        
        for text in texts:
            result = EmotionAnalysisService.analyze_emotions(text)
            self.assertGreaterEqual(result['sentiment_score'], -1.0)
            self.assertLessEqual(result['sentiment_score'], 1.0)
    
    def test_emotion_data_contains_all_emotions(self):
        """Test that emotion_data always contains all emotion types"""
        text = "Happy and sad and angry and anxious and calm"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        expected_emotions = {'joyful', 'sad', 'angry', 'anxious', 'calm'}
        self.assertEqual(set(result['emotion_data'].keys()), expected_emotions)
    
    def test_emotion_scores_are_non_negative(self):
        """Test that emotion scores are always non-negative"""
        text = "I feel many different emotions right now"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        for emotion, score in result['emotion_data'].items():
            self.assertGreaterEqual(score, 0.0)
    
    def test_emotion_scores_sum_to_less_than_or_equal_one(self):
        """Test that emotion scores represent proportions (word-based ratios)"""
        text = "Happy and excited and joyful and wonderful"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        # Each emotion score is words_matching / total_words, so sum should be <= 1
        total_score = sum(result['emotion_data'].values())
        self.assertLessEqual(total_score, 1.0)
    
    def test_sentiment_score_reflects_word_balance(self):
        """Test that sentiment score reflects balance of positive/negative words"""
        positive_text = "amazing wonderful excellent fantastic great"
        negative_text = "terrible awful horrible bad worst"
        mixed_text = "amazing wonderful terrible bad"
        
        positive_result = EmotionAnalysisService.analyze_emotions(positive_text)
        negative_result = EmotionAnalysisService.analyze_emotions(negative_text)
        mixed_result = EmotionAnalysisService.analyze_emotions(mixed_text)
        
        # Positive text should have higher sentiment than negative
        self.assertGreater(positive_result['sentiment_score'], negative_result['sentiment_score'])
        
        # Mixed text should be in between
        self.assertGreater(mixed_result['sentiment_score'], negative_result['sentiment_score'])
        self.assertLess(mixed_result['sentiment_score'], positive_result['sentiment_score'])
    
    def test_primary_emotion_matches_highest_emotion_score(self):
        """Test that primary emotion is the one with highest score"""
        text = "I am so happy, excited, and joyful but also a bit sad"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        max_emotion = max(result['emotion_data'], key=result['emotion_data'].get)
        self.assertEqual(result['primary_emotion'], max_emotion)
    
    def test_case_insensitivity(self):
        """Test that emotion analysis is case-insensitive"""
        text_lower = "i am happy and excited"
        text_upper = "I AM HAPPY AND EXCITED"
        text_mixed = "I Am Happy And Excited"
        
        result_lower = EmotionAnalysisService.analyze_emotions(text_lower)
        result_upper = EmotionAnalysisService.analyze_emotions(text_upper)
        result_mixed = EmotionAnalysisService.analyze_emotions(text_mixed)
        
        # All should produce same primary emotion
        self.assertEqual(result_lower['primary_emotion'], result_upper['primary_emotion'])
        self.assertEqual(result_lower['primary_emotion'], result_mixed['primary_emotion'])
        
        # Sentiment scores should match
        self.assertEqual(result_lower['sentiment_score'], result_upper['sentiment_score'])
        self.assertEqual(result_lower['sentiment_score'], result_mixed['sentiment_score'])
    
    def test_multiple_emotions_in_single_text(self):
        """Test that analysis correctly identifies multiple emotions in one text"""
        text = "I am happy but also worried and anxious about the future"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        # Should have positive score but with anxiety component
        self.assertGreater(result['emotion_data']['joyful'], 0.0)
        self.assertGreater(result['emotion_data']['anxious'], 0.0)
    
    def test_sentiment_score_precision(self):
        """Test that sentiment score is rounded to 3 decimal places"""
        text = "I am happy"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        # Score should be a float with at most 3 decimal places
        score_str = str(result['sentiment_score'])
        if '.' in score_str:
            decimal_places = len(score_str.split('.')[1])
            self.assertLessEqual(decimal_places, 3)
    
    def test_emotion_data_score_precision(self):
        """Test that emotion data scores are rounded to 3 decimal places"""
        text = "I am very happy"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        for emotion, score in result['emotion_data'].items():
            score_str = str(score)
            if '.' in score_str:
                decimal_places = len(score_str.split('.')[1])
                self.assertLessEqual(decimal_places, 3)
    
    def test_long_text_analysis(self):
        """Test that emotion analysis works with longer texts"""
        long_text = """
        Today was an amazing and wonderful day! I felt so happy and excited about everything.
        The weather was beautiful, and I got to spend time with people I love. 
        Everything just felt right, and I was filled with gratitude and joy.
        """
        result = EmotionAnalysisService.analyze_emotions(long_text)
        
        self.assertEqual(result['primary_emotion'], 'joyful')
        self.assertGreater(result['sentiment_score'], 0.5)
    
    def test_text_with_punctuation(self):
        """Test that emotion analysis handles punctuation correctly"""
        text = "I'm so happy! I'm excited? Yes!!! Absolutely... Amazing!"
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'joyful')
        self.assertGreater(result['sentiment_score'], 0.0)
    
    def test_text_with_mixed_emotions_determines_dominant(self):
        """Test that analysis correctly identifies dominant emotion in mixed text"""
        # Much more happy words than sad
        text = """
        Happy happy happy happy happy happy
        Joyful joyful joyful joyful
        Excited excited excited
        Sad sad
        Gloomy gloomy
        """
        result = EmotionAnalysisService.analyze_emotions(text)
        
        self.assertEqual(result['primary_emotion'], 'joyful')
        self.assertGreater(result['emotion_data']['joyful'], result['emotion_data']['sad'])
