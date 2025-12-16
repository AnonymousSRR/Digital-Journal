"""
Service module for emotion analysis of journal entries and reminder scheduling.
"""
import re
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from typing import Dict, Optional
from django.utils import timezone


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


class ReminderScheduler:
    """Service for computing next run times for reminders."""
    
    def compute_next_run(self, reminder, now: Optional[datetime] = None) -> Optional[datetime]:
        """
        Compute the next run time for a reminder.
        
        Args:
            reminder: Reminder instance
            now: Current datetime (defaults to timezone.now())
            
        Returns:
            Next run datetime or None if no future runs
        """
        from authentication.models import Reminder
        
        tz = ZoneInfo(reminder.timezone or 'UTC')
        now = (now or timezone.now()).astimezone(tz)
        
        if reminder.type == Reminder.ONE_TIME:
            if reminder.run_at:
                run = reminder.run_at.astimezone(tz)
                return run if run > now else None
            return None
        
        # Recurring
        tod = reminder.time_of_day or dt_time(9, 0)
        base = now.replace(hour=tod.hour, minute=tod.minute, second=0, microsecond=0)
        
        if reminder.frequency == 'daily':
            candidate = base
            if candidate <= now:
                candidate = candidate + timedelta(days=1)
            return candidate
        
        if reminder.frequency == 'weekly':
            target_dow = reminder.day_of_week if reminder.day_of_week is not None else 0
            days_ahead = (target_dow - now.weekday()) % 7
            candidate = base + timedelta(days=days_ahead)
            if candidate <= now:
                candidate = candidate + timedelta(days=7)
            return candidate
        
        if reminder.frequency == 'monthly':
            dom = reminder.day_of_month or 1
            month = now.month
            year = now.year
            # Try to set to this month's dom
            try:
                candidate = now.replace(day=dom, hour=tod.hour, minute=tod.minute, second=0, microsecond=0)
            except ValueError:
                # Invalid dom (e.g., Feb 30) - move to next month's first day
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                candidate = now.replace(year=year, month=month, day=1, hour=tod.hour, minute=tod.minute, second=0, microsecond=0)
            
            if candidate <= now:
                # Move to next month
                month = candidate.month + 1
                year = candidate.year
                if month > 12:
                    month = 1
                    year += 1
                try:
                    candidate = candidate.replace(year=year, month=month, day=dom)
                except ValueError:
                    # Invalid dom in next month - use first day
                    candidate = candidate.replace(year=year, month=month, day=1)
            
            return candidate
        
        return None


def send_reminder(reminder):
    """
    Send a reminder notification.
    
    Args:
        reminder: Reminder instance
        
    This is a placeholder function that will integrate with
    actual notification/email service.
    """
    # Placeholder implementation
    # TODO: Integrate with email/notification service
    pass
