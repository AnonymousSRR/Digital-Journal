"""
Helper functions for emotion analysis API responses and reminder serialization.
"""
from datetime import datetime


def serialize_journal_entry_emotion(entry):
    """Serialize a JournalEntry for emotion API responses."""
    return {
        'id': entry.id,
        'title': entry.title,
        'primary_emotion': entry.primary_emotion,
        'sentiment_score': entry.sentiment_score,
        'emotion_data': entry.emotion_data,
        'created_at': entry.created_at.isoformat(),
        'theme_name': entry.theme.name
    }


def serialize_reminder(reminder):
    """Serialize a Reminder for API responses."""
    return {
        'id': reminder.id,
        'journal_entry_id': reminder.journal_entry_id,
        'entry_title': reminder.journal_entry.title if hasattr(reminder.journal_entry, 'title') else None,
        'type': reminder.type,
        'timezone': reminder.timezone,
        'run_at': reminder.run_at.isoformat() if reminder.run_at else None,
        'frequency': reminder.frequency,
        'day_of_week': reminder.day_of_week,
        'day_of_month': reminder.day_of_month,
        'time_of_day': reminder.time_of_day.isoformat() if reminder.time_of_day else None,
        'next_run_at': reminder.next_run_at.isoformat() if reminder.next_run_at else None,
        'last_sent_at': reminder.last_sent_at.isoformat() if reminder.last_sent_at else None,
        'is_active': reminder.is_active,
        'created_at': reminder.created_at.isoformat(),
        'updated_at': reminder.updated_at.isoformat(),
    }

