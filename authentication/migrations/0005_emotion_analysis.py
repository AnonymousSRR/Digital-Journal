# Generated migration for adding emotion analysis fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_journalentry_writing_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalentry',
            name='primary_emotion',
            field=models.CharField(
                choices=[
                    ('joyful', 'Joyful'),
                    ('sad', 'Sad'),
                    ('angry', 'Angry'),
                    ('anxious', 'Anxious'),
                    ('calm', 'Calm'),
                    ('neutral', 'Neutral'),
                ],
                default='neutral',
                help_text='Primary emotion detected in the entry',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='sentiment_score',
            field=models.FloatField(
                default=0.0,
                help_text='Sentiment score from -1.0 (negative) to 1.0 (positive)',
            ),
        ),
        migrations.AddField(
            model_name='journalentry',
            name='emotion_data',
            field=models.JSONField(
                default=dict,
                help_text='Breakdown of emotions: {emotion: score}',
            ),
        ),
    ]
