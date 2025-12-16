"""
Helper functions for emotion analysis API responses.
"""


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

