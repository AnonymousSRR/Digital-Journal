"""
Django signals for automatic emotion analysis of journal entries.
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver
from authentication.models import JournalEntry
from authentication.services import EmotionAnalysisService


@receiver(pre_save, sender=JournalEntry)
def analyze_entry_emotions(sender, instance, **kwargs):
    """
    Signal handler to analyze emotions before saving a journal entry.
    This runs synchronously when the entry is saved.
    """
    if instance.answer:  # Only analyze if answer exists
        emotion_analysis = EmotionAnalysisService.analyze_emotions(instance.answer)
        instance.primary_emotion = emotion_analysis['primary_emotion']
        instance.sentiment_score = emotion_analysis['sentiment_score']
        instance.emotion_data = emotion_analysis['emotion_data']
