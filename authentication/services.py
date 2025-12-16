"""
Service module for emotion analysis of journal entries.
"""
import re
from typing import Dict


class EmotionAnalysisService:
    """Service for analyzing emotions in text using sentiment analysis and pattern matching."""
    
    # Emotion keywords mapping
    EMOTION_KEYWORDS = {
        'joyful': ['happy', 'joyful', 'excited', 'ecstatic', 'thrilled', 'wonderful', 
                   'amazing', 'great', 'love', 'beautiful', 'excellent', 'fantastic', 
                   'delighted', 'pleased', 'grateful', 'proud'],
        'sad': ['sad', 'depressed', 'miserable', 'gloomy', 'unhappy', 'down', 'blue', 
                'loss', 'miss', 'lonely', 'devastated', 'heartbroken', 'dismayed'],
        'angry': ['angry', 'furious', 'mad', 'enraged', 'frustrated', 'irritated', 
                  'annoyed', 'upset', 'hate', 'bitter', 'resentful', 'livid'],
        'anxious': ['anxious', 'worried', 'nervous', 'scared', 'afraid', 'stressed', 
                    'overwhelmed', 'panic', 'tension', 'dread', 'uneasy', 'apprehensive'],
        'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'content', 
                 'comfortable', 'at ease', 'still', 'quiet', 'composed', 'meditation'],
    }
    
    # Positive words for sentiment calculation
    POSITIVE_WORDS = {
        'amazing', 'wonderful', 'fantastic', 'excellent', 'great', 'good', 'better',
        'best', 'love', 'beautiful', 'happy', 'joy', 'pleased', 'delighted', 'grateful',
        'proud', 'excited', 'thrilled', 'perfect', 'awesome', 'fantastic', 'tremendous',
        'brilliant', 'superb', 'wonderful', 'nice', 'lovely', 'marvelous'
    }
    
    # Negative words for sentiment calculation
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'hate', 'hated', 'sad', 'sadness',
        'angry', 'upset', 'depressed', 'anxiety', 'anxious', 'stressed', 'stressed',
        'worst', 'worse', 'failure', 'failed', 'pain', 'painful', 'suffering',
        'angry', 'frustrated', 'annoyed', 'disgusted', 'ashamed', 'guilty', 'lonely',
        'scared', 'afraid', 'nervous', 'worried', 'concern', 'concerned', 'unfortunately'
    }
    
    @staticmethod
    def analyze_emotions(text: str) -> Dict:
        """
        Analyze emotions in the given text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary containing:
            - primary_emotion: str - The primary emotion detected
            - sentiment_score: float - Sentiment polarity (-1.0 to 1.0)
            - emotion_data: dict - Breakdown of emotion scores
        """
        text_lower = text.lower()
        
        # Calculate sentiment score based on positive/negative words
        sentiment_score = EmotionAnalysisService._calculate_sentiment_score(text_lower)
        
        # Calculate emotion scores based on keyword matching
        emotion_scores = EmotionAnalysisService._calculate_emotion_scores(text_lower)
        
        # Determine primary emotion
        primary_emotion = EmotionAnalysisService._determine_primary_emotion(
            emotion_scores, sentiment_score
        )
        
        return {
            'primary_emotion': primary_emotion,
            'sentiment_score': round(sentiment_score, 3),
            'emotion_data': emotion_scores
        }
    
    @staticmethod
    def _calculate_sentiment_score(text_lower: str) -> float:
        """Calculate sentiment score based on positive and negative word frequency."""
        words = re.findall(r'\b\w+\b', text_lower)
        word_count = len(words)
        
        if word_count == 0:
            return 0.0
        
        positive_count = sum(1 for word in words if word in EmotionAnalysisService.POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in EmotionAnalysisService.NEGATIVE_WORDS)
        
        # Calculate sentiment as ratio of positive to negative words
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            # No sentiment words found - return neutral
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_sentiment_words
        # Clamp to [-1, 1] range
        return max(-1.0, min(1.0, sentiment_score))
    
    @staticmethod
    def _calculate_emotion_scores(text_lower: str) -> Dict[str, float]:
        """Calculate scores for each emotion based on keyword presence."""
        emotion_scores = {}
        words = re.findall(r'\b\w+\b', text_lower)
        word_count = len(words)
        
        if word_count == 0:
            return {emotion: 0.0 for emotion in EmotionAnalysisService.EMOTION_KEYWORDS}
        
        for emotion, keywords in EmotionAnalysisService.EMOTION_KEYWORDS.items():
            matches = sum(1 for word in words if word in keywords)
            emotion_scores[emotion] = round(matches / word_count, 3)
        
        return emotion_scores
    
    @staticmethod
    def _determine_primary_emotion(emotion_scores: Dict[str, float], sentiment_score: float) -> str:
        """Determine the primary emotion based on scores and sentiment."""
        # If no emotions detected, use sentiment to determine primary emotion
        if max(emotion_scores.values()) == 0:
            if sentiment_score > 0.3:
                return 'joyful'
            elif sentiment_score < -0.3:
                return 'sad'
            else:
                return 'neutral'
        
        # Return emotion with highest score
        return max(emotion_scores, key=emotion_scores.get)
