"""
Utility functions for emotion analysis reporting and export.
"""
from datetime import datetime, timedelta
from django.db.models import Avg
from authentication.models import JournalEntry
import csv
from io import StringIO


class EmotionReportGenerator:
    """Generate emotion analysis reports in various formats."""
    
    @staticmethod
    def generate_csv_report(user, days=90):
        """
        Generate CSV report of emotion data for specified period.
        
        Args:
            user: User object to generate report for
            days: Number of days to look back (default 90)
            
        Returns:
            CSV string content
        """
        start_date = datetime.now().date() - timedelta(days=days)
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=start_date
        ).order_by('created_at')
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Title', 'Theme', 'Primary Emotion', 'Sentiment Score',
            'Emotion Breakdown', 'Writing Time (minutes)'
        ])
        
        # Write entries
        for entry in entries:
            emotion_str = ', '.join([
                f"{e}: {s}" for e, s in entry.emotion_data.items()
            ]) if entry.emotion_data else ''
            
            writer.writerow([
                entry.created_at.date().isoformat(),
                entry.title,
                entry.theme.name,
                entry.primary_emotion,
                round(entry.sentiment_score, 3),
                emotion_str,
                round(entry.writing_time / 60, 1) if entry.writing_time else 0
            ])
        
        return output.getvalue()
    
    @staticmethod
    def generate_summary_stats(user, days=90):
        """
        Generate summary statistics for the report.
        
        Args:
            user: User object to generate stats for
            days: Number of days to look back (default 90)
            
        Returns:
            Dictionary with summary statistics
        """
        start_date = datetime.now().date() - timedelta(days=days)
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=start_date
        )
        
        emotion_counts = {}
        for entry in entries:
            emotion = entry.primary_emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        avg_sentiment = entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0.0
        
        return {
            'period_days': days,
            'total_entries': entries.count(),
            'emotion_distribution': emotion_counts,
            'average_sentiment': round(avg_sentiment, 3),
            'generated_date': datetime.now().isoformat()
        }
