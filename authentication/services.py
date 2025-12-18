"""
Service module for emotion analysis of journal entries and reminder scheduling.
"""
import re
from datetime import datetime, timedelta, time as dt_time, date
from zoneinfo import ZoneInfo
from typing import Dict, Optional, List, Tuple
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, Case, When, Value, IntegerField


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


class AnalyticsService:
    """Service for calculating journal analytics and writing statistics."""
    
    @staticmethod
    def get_writing_streaks(user, days_lookback: int = 365) -> Dict:
        """
        Calculate current and longest writing streaks.
        
        Args:
            user: CustomUser instance
            days_lookback: Number of days to analyze (default 365)
            
        Returns:
            {
                'current_streak': int,
                'longest_streak': int,
                'last_entry_date': date,
                'streak_start_date': date
            }
        """
        from authentication.models import JournalEntry
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        entry_dates = list(JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).order_by('-created_at__date').values_list('created_at__date', flat=True).distinct())
        
        if not entry_dates:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'last_entry_date': None,
                'streak_start_date': None
            }
        
        current_date = timezone.now().date()
        
        # Initialize streak tracking
        longest_streak = 1
        current_streak = 0
        temp_streak = 1
        current_streak_start = None
        
        # Check if we have a current streak (today or yesterday)
        if entry_dates[0] >= (current_date - timedelta(days=1)):
            current_streak = 1
            current_streak_start = entry_dates[0]
            
            # Count consecutive days from most recent entry backwards
            for i in range(len(entry_dates) - 1):
                day_diff = (entry_dates[i] - entry_dates[i + 1]).days
                if day_diff == 1:
                    current_streak += 1
                else:
                    break
        
        # Calculate longest streak across all entries
        for i in range(len(entry_dates) - 1):
            day_diff = (entry_dates[i] - entry_dates[i + 1]).days
            if day_diff == 1:
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak, current_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_entry_date': entry_dates[0].isoformat() if entry_dates else None,
            'streak_start_date': current_streak_start.isoformat() if current_streak_start else None
        }
    
    @staticmethod
    def get_word_count_stats(user, days_lookback: int = 365) -> Dict:
        """
        Calculate word count statistics.
        
        Args:
            user: CustomUser instance
            days_lookback: Number of days to analyze
            
        Returns:
            {
                'total_words': int,
                'avg_words_per_entry': float,
                'max_words_in_entry': int,
                'min_words_in_entry': int
            }
        """
        from authentication.models import JournalEntry
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).values_list('answer', flat=True)
        
        if not entries:
            return {
                'total_words': 0,
                'avg_words_per_entry': 0.0,
                'max_words_in_entry': 0,
                'min_words_in_entry': 0
            }
        
        word_counts = [len(entry.split()) for entry in entries]
        total_words = sum(word_counts)
        
        return {
            'total_words': total_words,
            'avg_words_per_entry': round(total_words / len(word_counts), 1),
            'max_words_in_entry': max(word_counts),
            'min_words_in_entry': min(word_counts)
        }
    
    @staticmethod
    def get_mood_distribution(user, days_lookback: int = 365) -> Dict[str, int]:
        """
        Get distribution of primary emotions across entries.
        
        Returns: {emotion: count, ...}
        """
        from authentication.models import JournalEntry
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        distribution = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).values('primary_emotion').annotate(count=Count('primary_emotion'))
        
        result = {item['primary_emotion']: item['count'] for item in distribution}
        # Ensure all emotions present (even with 0 count)
        for emotion in ['joyful', 'sad', 'angry', 'anxious', 'calm', 'neutral']:
            result.setdefault(emotion, 0)
        
        return result
    
    @staticmethod
    def get_top_themes(user, days_lookback: int = 365, limit: int = 5) -> List[Dict]:
        """
        Get most frequently used themes.
        
        Returns: [{'theme': str, 'count': int, 'avg_sentiment': float}, ...]
        """
        from authentication.models import JournalEntry
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        themes = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).values('theme__name').annotate(
            count=Count('theme'),
            avg_sentiment=Avg('sentiment_score')
        ).order_by('-count')[:limit]
        
        return [
            {
                'theme': item['theme__name'],
                'count': item['count'],
                'avg_sentiment': round(item['avg_sentiment'] or 0.0, 2)
            }
            for item in themes
        ]
    
    @staticmethod
    def get_word_count_trend(user, granularity: str = 'daily', days_lookback: int = 90) -> List[Dict]:
        """
        Get word count trend over time.
        
        Returns: [{'date': 'YYYY-MM-DD', 'words': int, 'entries': int}, ...]
        """
        from authentication.models import JournalEntry
        from django.db.models import F
        from django.db.models.functions import TruncDate
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        
        # Fetch all entries in one query with needed fields only
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).values('created_at__date', 'answer')
        
        # Manual aggregation for accurate word count
        date_data = {}
        for entry in entries:
            entry_date = entry['created_at__date']
            if entry_date not in date_data:
                date_data[entry_date] = {'words': 0, 'entries': 0}
            date_data[entry_date]['words'] += len(entry['answer'].split())
            date_data[entry_date]['entries'] += 1
        
        if granularity == 'weekly':
            # Aggregate by week
            weekly_data = {}
            for date_key, data in sorted(date_data.items()):
                week_start = date_key - timedelta(days=date_key.weekday())
                week_key = week_start.isoformat()
                if week_key not in weekly_data:
                    weekly_data[week_key] = {'words': 0, 'entries': 0}
                weekly_data[week_key]['words'] += data['words']
                weekly_data[week_key]['entries'] += data['entries']
            
            return [
                {'date': date_str, 'words': data['words'], 'entries': data['entries']}
                for date_str, data in sorted(weekly_data.items())
            ]
        
        return [
            {'date': date_key.isoformat(), 'words': data['words'], 'entries': data['entries']}
            for date_key, data in sorted(date_data.items())
        ]
    
    @staticmethod
    def get_mood_trend(user, granularity: str = 'weekly', days_lookback: int = 90) -> List[Dict]:
        """
        Get mood distribution as time series.
        
        Returns: [{'date': 'YYYY-MM-DD', 'moods': {emotion: count}}, ...]
        """
        from authentication.models import JournalEntry
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).values('created_at__date', 'primary_emotion').order_by('created_at__date')
        
        date_moods = {}
        for entry in entries:
            entry_date = entry['created_at__date']
            if entry_date not in date_moods:
                date_moods[entry_date] = {
                    'joyful': 0, 'sad': 0, 'angry': 0, 'anxious': 0, 'calm': 0, 'neutral': 0
                }
            date_moods[entry_date][entry['primary_emotion']] += 1
        
        if granularity == 'weekly':
            weekly_moods = {}
            for date_key, moods in date_moods.items():
                week_start = date_key - timedelta(days=date_key.weekday())
                week_key = week_start.isoformat()
                if week_key not in weekly_moods:
                    weekly_moods[week_key] = {
                        'joyful': 0, 'sad': 0, 'angry': 0, 'anxious': 0, 'calm': 0, 'neutral': 0
                    }
                for emotion, count in moods.items():
                    weekly_moods[week_key][emotion] += count
            
            return [
                {'date': date_str, 'moods': moods}
                for date_str, moods in sorted(weekly_moods.items())
            ]
        
        return [
            {'date': date_key.isoformat(), 'moods': moods}
            for date_key, moods in sorted(date_moods.items())
        ]
    
    @staticmethod
    def export_analytics_csv(user, export_type: str = 'full', days_lookback: int = 365) -> str:
        """
        Generate CSV export of analytics data.
        
        Args:
            user: CustomUser instance
            export_type: 'full', 'summary', or 'mood_trends'
            days_lookback: Days to include in export
            
        Returns: CSV string
        """
        import csv
        from io import StringIO
        from authentication.models import JournalEntry
        
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).select_related('theme').order_by('-created_at')
        
        output = StringIO()
        
        if export_type == 'full':
            writer = csv.writer(output)
            writer.writerow([
                'Date', 'Title', 'Theme', 'Word Count', 'Primary Emotion',
                'Sentiment Score', 'Writing Time (sec)', 'Visibility'
            ])
            
            for entry in entries:
                writer.writerow([
                    entry.created_at.date().isoformat(),
                    entry.title,
                    entry.theme.name,
                    len(entry.answer.split()),
                    entry.primary_emotion,
                    entry.sentiment_score,
                    entry.writing_time,
                    entry.visibility
                ])
        
        elif export_type == 'summary':
            writer = csv.writer(output)
            writer.writerow(['Metric', 'Value'])
            
            streaks = AnalyticsService.get_writing_streaks(user, days_lookback)
            stats = AnalyticsService.get_word_count_stats(user, days_lookback)
            
            writer.writerow(['Current Streak (days)', streaks['current_streak']])
            writer.writerow(['Longest Streak (days)', streaks['longest_streak']])
            writer.writerow(['Total Words Written', stats['total_words']])
            writer.writerow(['Average Words Per Entry', stats['avg_words_per_entry']])
            writer.writerow(['Total Entries', entries.count()])
        
        elif export_type == 'mood_trends':
            writer = csv.writer(output)
            writer.writerow(['Date', 'Joyful', 'Sad', 'Angry', 'Anxious', 'Calm', 'Neutral'])
            
            mood_trend = AnalyticsService.get_mood_trend(user, granularity='daily', days_lookback=days_lookback)
            for item in mood_trend:
                row = [item['date']]
                row.extend([
                    item['moods'].get('joyful', 0),
                    item['moods'].get('sad', 0),
                    item['moods'].get('angry', 0),
                    item['moods'].get('anxious', 0),
                    item['moods'].get('calm', 0),
                    item['moods'].get('neutral', 0)
                ])
                writer.writerow(row)
        
        return output.getvalue()
