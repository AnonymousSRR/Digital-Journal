"""
Django signals for automatic emotion analysis of journal entries.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from authentication.models import JournalEntry, JournalEntryVersion
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


@receiver(post_save, sender=JournalEntry)
def create_journal_entry_version(sender, instance, created, **kwargs):
    """
    Automatically create a version record whenever a JournalEntry is saved.
    On creation: captures initial state as v1.
    On update: captures new state as next version.
    """
    # Determine if this is a new entry or an update
    if created:
        # First version
        version_number = 1
        edit_source = 'initial'
        change_summary = "Entry created"
    else:
        # Get the current version count to determine next version number
        current_count = instance.versions.count()
        version_number = current_count + 1
        edit_source = 'edit'
        change_summary = "Entry updated"
    
    # Create version snapshot
    JournalEntryVersion.objects.create(
        entry=instance,
        version_number=version_number,
        title=instance.title,
        answer=instance.answer,
        theme=instance.theme,
        prompt=instance.prompt,
        visibility=instance.visibility,
        created_by=instance.user,
        edit_source=edit_source,
        change_summary=change_summary
    )
