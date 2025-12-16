# User Emotion Analysis Implementation Plan

## Overview
Implement a comprehensive emotion analysis system that analyzes journal entries to detect user emotions, track emotional patterns over time, and provide emotion-based insights. This feature will help users understand their emotional state and trends through their journaling.

## Architecture
Journal entries → Emotion Analysis Service (using TextBlob/VADER sentiment analysis) → EmotionAnalysis model (stores emotion metadata) → Dashboard displays emotion trends, statistics, and mood patterns → Emotion history and analytics API endpoints

## Implementation Phases

### Phase 1: Emotion Analysis Service & Data Models
**Files**: 
- `authentication/services/__init__.py` (new)
- `authentication/services/emotion_service.py` (new)
- `authentication/models.py` (update)
- `authentication/migrations/` (new migration)
- `tests/unit_tests/services/__init__.py` (new)
- `tests/unit_tests/services/test_emotion_service.py` (new)

**Description**: 
Create the core emotion analysis service that will detect emotions from journal entry text and store emotion metadata. Add an EmotionAnalysis model to track emotion data per journal entry, and create the emotion detection service using VADER sentiment analysis (which comes with nltk and is optimized for social media/short text sentiment analysis).

**Key code changes:**

```python
# authentication/services/emotion_service.py
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

class EmotionAnalysisService:
    """Service for analyzing emotions in journal entries"""
    
    def __init__(self):
        # Download required NLTK data on first import
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon', quiet=True)
        self.sia = SentimentIntensityAnalyzer()
    
    def analyze_text(self, text: str) -> dict:
        """
        Analyze emotion from text and return sentiment scores.
        Returns dict with positive, negative, neutral, compound scores.
        """
        if not text or not isinstance(text, str):
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'compound': 0.0}
        
        scores = self.sia.polarity_scores(text)
        return {
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
            'compound': scores['compound']
        }
    
    def get_emotion_label(self, compound_score: float) -> str:
        """
        Convert compound sentiment score to emotion label.
        compound ranges from -1 (very negative) to 1 (very positive)
        """
        if compound_score >= 0.5:
            return 'very_positive'
        elif compound_score >= 0.05:
            return 'positive'
        elif compound_score > -0.05:
            return 'neutral'
        elif compound_score > -0.5:
            return 'negative'
        else:
            return 'very_negative'

# authentication/models.py - Add to existing file
class EmotionAnalysis(models.Model):
    """
    Stores emotion analysis results for journal entries.
    Created automatically when a journal entry is saved.
    """
    EMOTION_CHOICES = [
        ('very_positive', 'Very Positive'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
        ('very_negative', 'Very Negative'),
    ]
    
    journal_entry = models.OneToOneField(
        JournalEntry, 
        on_delete=models.CASCADE, 
        related_name='emotion_analysis'
    )
    
    # Sentiment scores (0.0 to 1.0)
    positive_score = models.FloatField(default=0.0)
    negative_score = models.FloatField(default=0.0)
    neutral_score = models.FloatField(default=0.0)
    compound_score = models.FloatField(default=0.0)  # -1 to 1
    
    emotion_label = models.CharField(
        max_length=20,
        choices=EMOTION_CHOICES,
        default='neutral'
    )
    
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-analyzed_at']
    
    def __str__(self):
        return f"{self.journal_entry.user.email} - {self.emotion_label}"
```

**Test cases for this phase:**

- Test case 1: Emotion service correctly analyzes positive text
  ```python
  def test_analyze_positive_text():
      service = EmotionAnalysisService()
      text = "I am very happy and feeling great today!"
      result = service.analyze_text(text)
      
      assert result['positive'] > 0.5
      assert result['compound'] > 0.5
      assert service.get_emotion_label(result['compound']) == 'very_positive'
  ```

- Test case 2: Emotion service correctly analyzes negative text
  ```python
  def test_analyze_negative_text():
      service = EmotionAnalysisService()
      text = "I am very sad and disappointed with everything."
      result = service.analyze_text(text)
      
      assert result['negative'] > 0.5
      assert result['compound'] < -0.5
      assert service.get_emotion_label(result['compound']) == 'very_negative'
  ```

- Test case 3: Emotion service handles neutral text
  ```python
  def test_analyze_neutral_text():
      service = EmotionAnalysisService()
      text = "I went to the store today and bought some groceries."
      result = service.analyze_text(text)
      
      assert result['neutral'] > 0.5
      assert -0.05 <= result['compound'] <= 0.05
      assert service.get_emotion_label(result['compound']) == 'neutral'
  ```

- Test case 4: Emotion service handles empty/invalid text
  ```python
  def test_analyze_empty_text():
      service = EmotionAnalysisService()
      result = service.analyze_text("")
      
      assert result['compound'] == 0.0
      assert result['neutral'] == 1.0
      assert service.get_emotion_label(result['compound']) == 'neutral'
  ```

- Test case 5: EmotionAnalysis model creates correctly
  ```python
  def test_emotion_analysis_model_creation():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      entry = JournalEntry.objects.create(
          user=user,
          title='Happy Day',
          theme=theme,
          prompt='How are you?',
          answer='I am very happy!'
      )
      
      emotion = EmotionAnalysis.objects.create(
          journal_entry=entry,
          positive_score=0.8,
          negative_score=0.0,
          neutral_score=0.2,
          compound_score=0.8,
          emotion_label='very_positive'
      )
      
      assert emotion.journal_entry == entry
      assert emotion.emotion_label == 'very_positive'
      assert emotion.compound_score == 0.8
  ```

**Technical details and Assumptions:**
- VADER (Valence Aware Dictionary and sEntiment Reasoner) is included with nltk and is optimized for social media and short text like journal entries
- EmotionAnalysis is a OneToOne relationship with JournalEntry to maintain referential integrity
- compound_score ranges from -1 (very negative) to 1 (very positive) and is the most reliable metric
- Emotion labels are discrete categories derived from compound scores for easier understanding
- Analysis is done synchronously on journal entry creation (can be optimized to async in future phases)

---

### Phase 2: Signal Handlers & Automatic Emotion Analysis
**Files**: 
- `authentication/signals.py` (new)
- `authentication/apps.py` (update)
- `authentication/models.py` (update - add signal connection)
- `tests/unit_tests/services/test_emotion_service.py` (update)

**Description**: 
Create Django signals to automatically analyze emotions whenever a journal entry is created or updated. This ensures that every journal entry has associated emotion analysis without requiring manual triggers. The signal will use the EmotionAnalysisService to analyze the entry's title and answer text.

**Key code changes:**

```python
# authentication/signals.py (new file)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JournalEntry, EmotionAnalysis
from .services.emotion_service import EmotionAnalysisService

service = EmotionAnalysisService()

@receiver(post_save, sender=JournalEntry)
def analyze_emotion_on_entry_save(sender, instance, created, **kwargs):
    """
    Automatically analyze emotion when a journal entry is created or updated.
    """
    if created or not hasattr(instance, '_skip_emotion_analysis'):
        # Combine title and answer for analysis
        text_to_analyze = f"{instance.title} {instance.answer}"
        
        # Get emotion analysis
        emotion_scores = service.analyze_text(text_to_analyze)
        emotion_label = service.get_emotion_label(emotion_scores['compound'])
        
        # Create or update EmotionAnalysis
        EmotionAnalysis.objects.update_or_create(
            journal_entry=instance,
            defaults={
                'positive_score': emotion_scores['positive'],
                'negative_score': emotion_scores['negative'],
                'neutral_score': emotion_scores['neutral'],
                'compound_score': emotion_scores['compound'],
                'emotion_label': emotion_label
            }
        )

# authentication/apps.py - update AppConfig
class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        import authentication.signals  # Import signals when app is ready
```

**Test cases for this phase:**

- Test case 1: Signal creates EmotionAnalysis on journal entry creation
  ```python
  def test_emotion_analysis_created_on_entry_save():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      
      entry = JournalEntry.objects.create(
          user=user,
          title='Amazing Day',
          theme=theme,
          prompt='How was your day?',
          answer='It was amazing and I felt great!'
      )
      
      # Check that EmotionAnalysis was created
      assert EmotionAnalysis.objects.filter(journal_entry=entry).exists()
      emotion = entry.emotion_analysis
      assert emotion.emotion_label == 'very_positive'
  ```

- Test case 2: Signal updates EmotionAnalysis on journal entry update
  ```python
  def test_emotion_analysis_updated_on_entry_update():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      entry = JournalEntry.objects.create(
          user=user,
          title='Good Day',
          theme=theme,
          prompt='How was your day?',
          answer='It was good.'
      )
      
      old_emotion = entry.emotion_analysis
      old_label = old_emotion.emotion_label
      
      # Update entry with very negative content
      entry.answer = 'Actually it was terrible and I am very sad.'
      entry.save()
      
      # Refresh and check
      entry.refresh_from_db()
      assert entry.emotion_analysis.emotion_label == 'very_negative'
      assert entry.emotion_analysis.emotion_label != old_label
  ```

- Test case 3: EmotionAnalysis correctly combines title and answer
  ```python
  def test_emotion_analysis_combines_title_and_answer():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      
      # Title is positive, answer is negative - combined should lean negative
      entry = JournalEntry.objects.create(
          user=user,
          title='Happy Moment',
          theme=theme,
          prompt='Describe your day',
          answer='But then everything went wrong and I felt terrible'
      )
      
      emotion = entry.emotion_analysis
      # Should analyze both title and answer together
      assert emotion is not None
  ```

**Technical details and Assumptions:**
- Django signals are used for automatic emotion analysis to keep the code decoupled
- The signal is triggered on post_save to ensure the entry is fully saved before analysis
- Both title and answer are combined for more complete sentiment analysis context
- EmotionAnalysis is created or updated using update_or_create to handle both new and edited entries
- A flag can be added to skip analysis if needed in the future

---

### Phase 3: Emotion Analytics Service & Statistics
**Files**: 
- `authentication/services/emotion_service.py` (update)
- `authentication/services/__init__.py` (update)
- `tests/unit_tests/services/test_emotion_service.py` (update)

**Description**: 
Extend the EmotionAnalysisService to include methods for calculating emotion statistics and trends. This includes retrieving emotion distribution, average sentiment over time periods, most frequent emotions, and emotion trends for individual users. These methods will support the dashboard and analytics features.

**Key code changes:**

```python
# authentication/services/emotion_service.py - Add to EmotionAnalysisService class

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import EmotionAnalysis

def get_user_emotion_stats(self, user, days: int = 30) -> dict:
    """
    Get emotion statistics for a user over the past N days.
    Returns aggregated emotion metrics.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    emotions = EmotionAnalysis.objects.filter(
        journal_entry__user=user,
        analyzed_at__gte=cutoff_date
    )
    
    if not emotions.exists():
        return {
            'total_entries': 0,
            'average_compound': 0.0,
            'emotion_distribution': {},
            'most_common_emotion': None,
            'average_positive': 0.0,
            'average_negative': 0.0,
            'average_neutral': 0.0,
            'period_days': days
        }
    
    emotion_counts = emotions.values('emotion_label').annotate(
        count=Count('id')
    ).order_by('-count')
    
    emotion_distribution = {
        item['emotion_label']: item['count'] 
        for item in emotion_counts
    }
    
    stats = emotions.aggregate(
        avg_compound=Avg('compound_score'),
        avg_positive=Avg('positive_score'),
        avg_negative=Avg('negative_score'),
        avg_neutral=Avg('neutral_score'),
        total_count=Count('id')
    )
    
    return {
        'total_entries': stats['total_count'],
        'average_compound': round(stats['avg_compound'], 3),
        'average_positive': round(stats['avg_positive'], 3),
        'average_negative': round(stats['avg_negative'], 3),
        'average_neutral': round(stats['avg_neutral'], 3),
        'emotion_distribution': emotion_distribution,
        'most_common_emotion': emotion_counts.first()['emotion_label'] if emotion_counts.exists() else None,
        'period_days': days
    }

def get_emotion_trend(self, user, days: int = 30) -> list:
    """
    Get emotion trend data for charting.
    Returns list of daily emotion metrics.
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    emotions = EmotionAnalysis.objects.filter(
        journal_entry__user=user,
        analyzed_at__gte=cutoff_date
    ).order_by('analyzed_at')
    
    trend_data = []
    for emotion in emotions:
        trend_data.append({
            'date': emotion.analyzed_at.date().isoformat(),
            'compound_score': emotion.compound_score,
            'emotion_label': emotion.emotion_label,
            'positive_score': emotion.positive_score,
            'negative_score': emotion.negative_score
        })
    
    return trend_data

def get_emotion_comparison(self, user, period1_days: int = 7, period2_days: int = 7) -> dict:
    """
    Compare emotions between two recent time periods.
    Useful for tracking improvement or changes in mood.
    """
    now = timezone.now()
    
    # Recent period (past N days)
    recent_start = now - timedelta(days=period1_days)
    recent_emotions = EmotionAnalysis.objects.filter(
        journal_entry__user=user,
        analyzed_at__gte=recent_start
    )
    
    # Previous period
    previous_start = now - timedelta(days=period1_days + period2_days)
    previous_end = now - timedelta(days=period1_days)
    previous_emotions = EmotionAnalysis.objects.filter(
        journal_entry__user=user,
        analyzed_at__gte=previous_start,
        analyzed_at__lt=previous_end
    )
    
    recent_stats = recent_emotions.aggregate(
        avg_compound=Avg('compound_score')
    ) if recent_emotions.exists() else {'avg_compound': 0.0}
    
    previous_stats = previous_emotions.aggregate(
        avg_compound=Avg('compound_score')
    ) if previous_emotions.exists() else {'avg_compound': 0.0}
    
    recent_avg = recent_stats['avg_compound'] or 0.0
    previous_avg = previous_stats['avg_compound'] or 0.0
    
    return {
        'recent_period': {
            'days': period1_days,
            'average_compound': round(recent_avg, 3),
            'entry_count': recent_emotions.count()
        },
        'previous_period': {
            'days': period2_days,
            'average_compound': round(previous_avg, 3),
            'entry_count': previous_emotions.count()
        },
        'change': round(recent_avg - previous_avg, 3),
        'improvement': recent_avg > previous_avg
    }
```

**Test cases for this phase:**

- Test case 1: Get user emotion statistics over 30 days
  ```python
  def test_get_user_emotion_stats():
      service = EmotionAnalysisService()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      
      # Create entries with different emotions
      for answer in ['I am very happy!', 'I am sad.', 'It was okay.']:
          entry = JournalEntry.objects.create(
              user=user,
              title='Entry',
              theme=theme,
              prompt='How are you?',
              answer=answer
          )
      
      stats = service.get_user_emotion_stats(user, days=30)
      
      assert stats['total_entries'] == 3
      assert 'emotion_distribution' in stats
      assert stats['average_compound'] is not None
      assert stats['most_common_emotion'] in ['very_positive', 'negative', 'neutral']
  ```

- Test case 2: Get emotion trend data for charting
  ```python
  def test_get_emotion_trend():
      service = EmotionAnalysisService()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      
      entry = JournalEntry.objects.create(
          user=user,
          title='Happy Day',
          theme=theme,
          prompt='How was your day?',
          answer='It was excellent!'
      )
      
      trend = service.get_emotion_trend(user, days=30)
      
      assert len(trend) >= 1
      assert 'date' in trend[0]
      assert 'compound_score' in trend[0]
      assert 'emotion_label' in trend[0]
  ```

- Test case 3: Compare emotions between two periods
  ```python
  def test_get_emotion_comparison():
      service = EmotionAnalysisService()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Growth')
      
      # Create recent positive entry
      entry1 = JournalEntry.objects.create(
          user=user,
          title='Happy',
          theme=theme,
          prompt='How are you?',
          answer='I am very happy!'
      )
      
      comparison = service.get_emotion_comparison(user, period1_days=7, period2_days=7)
      
      assert 'recent_period' in comparison
      assert 'previous_period' in comparison
      assert 'change' in comparison
      assert 'improvement' in comparison
  ```

- Test case 4: Handle empty emotion data gracefully
  ```python
  def test_emotion_stats_empty_data():
      service = EmotionAnalysisService()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      
      stats = service.get_user_emotion_stats(user, days=30)
      
      assert stats['total_entries'] == 0
      assert stats['emotion_distribution'] == {}
      assert stats['most_common_emotion'] is None
  ```

**Technical details and Assumptions:**
- EmotionAnalysisService is extended with analytics methods (following single responsibility principle)
- All statistics are calculated from the EmotionAnalysis model using Django ORM aggregations for efficiency
- Time-based filtering uses timezone-aware datetimes to prevent timezone-related bugs
- Period comparisons are useful for users to see if their mood is improving or declining
- Methods return dictionaries for easy JSON serialization in API responses
- All floating-point results are rounded to 3 decimal places for consistency

---

### Phase 4: Emotion Analytics API Views
**Files**: 
- `authentication/views.py` (update)
- `authentication/urls.py` (update)
- `tests/unit_tests/views/test_emotion_views.py` (new)

**Description**: 
Create REST API endpoints that allow the frontend to fetch emotion statistics, trends, and comparisons. These endpoints will be protected with login_required decorators and will return JSON responses. Include endpoints for user emotion dashboard data, emotion history, and emotion comparisons.

**Key code changes:**

```python
# authentication/views.py - Add new view functions

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .services.emotion_service import EmotionAnalysisService

emotion_service = EmotionAnalysisService()

@login_required
@require_http_methods(["GET"])
def api_emotion_stats(request):
    """
    API endpoint: Get emotion statistics for the logged-in user.
    Query params: days (default 30)
    """
    try:
        days = int(request.GET.get('days', 30))
        days = max(1, min(days, 365))  # Clamp between 1 and 365 days
        
        stats = emotion_service.get_user_emotion_stats(request.user, days=days)
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET"])
def api_emotion_trend(request):
    """
    API endpoint: Get emotion trend data for charting.
    Query params: days (default 30)
    """
    try:
        days = int(request.GET.get('days', 30))
        days = max(1, min(days, 365))
        
        trend = emotion_service.get_emotion_trend(request.user, days=days)
        
        return JsonResponse({
            'success': True,
            'data': trend
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET"])
def api_emotion_comparison(request):
    """
    API endpoint: Compare emotions between two recent periods.
    Query params: period1_days (default 7), period2_days (default 7)
    """
    try:
        period1_days = int(request.GET.get('period1_days', 7))
        period2_days = int(request.GET.get('period2_days', 7))
        
        # Validate inputs
        period1_days = max(1, min(period1_days, 180))
        period2_days = max(1, min(period2_days, 180))
        
        comparison = emotion_service.get_emotion_comparison(
            request.user,
            period1_days=period1_days,
            period2_days=period2_days
        )
        
        return JsonResponse({
            'success': True,
            'data': comparison
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["GET"])
def api_emotion_entry_detail(request, entry_id):
    """
    API endpoint: Get detailed emotion analysis for a specific entry.
    """
    try:
        entry = JournalEntry.objects.get(id=entry_id, user=request.user)
        emotion = entry.emotion_analysis
        
        return JsonResponse({
            'success': True,
            'data': {
                'entry_id': entry.id,
                'entry_title': entry.title,
                'emotion_label': emotion.emotion_label,
                'positive_score': emotion.positive_score,
                'negative_score': emotion.negative_score,
                'neutral_score': emotion.neutral_score,
                'compound_score': emotion.compound_score,
                'analyzed_at': emotion.analyzed_at.isoformat()
            }
        })
    except JournalEntry.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Entry not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

# authentication/urls.py - Add new URL patterns

urlpatterns = [
    # ... existing patterns ...
    path('api/emotions/stats/', api_emotion_stats, name='api_emotion_stats'),
    path('api/emotions/trend/', api_emotion_trend, name='api_emotion_trend'),
    path('api/emotions/comparison/', api_emotion_comparison, name='api_emotion_comparison'),
    path('api/emotions/entry/<int:entry_id>/', api_emotion_entry_detail, name='api_emotion_entry_detail'),
]
```

**Test cases for this phase:**

- Test case 1: API emotion stats endpoint returns correct data
  ```python
  def test_api_emotion_stats_endpoint(self):
      client = Client()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      client.login(username='test@example.com', password='pass123')
      
      theme = Theme.objects.create(name='Growth')
      JournalEntry.objects.create(
          user=user,
          title='Happy Day',
          theme=theme,
          prompt='How are you?',
          answer='I am very happy!'
      )
      
      response = client.get('/api/emotions/stats/?days=30')
      data = response.json()
      
      assert response.status_code == 200
      assert data['success'] is True
      assert 'data' in data
      assert data['data']['total_entries'] == 1
  ```

- Test case 2: API emotion stats requires authentication
  ```python
  def test_api_emotion_stats_requires_login(self):
      client = Client()
      response = client.get('/api/emotions/stats/')
      
      # Should redirect to login
      assert response.status_code == 302
  ```

- Test case 3: API emotion trend endpoint returns trend data
  ```python
  def test_api_emotion_trend_endpoint(self):
      client = Client()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      client.login(username='test@example.com', password='pass123')
      
      theme = Theme.objects.create(name='Growth')
      JournalEntry.objects.create(
          user=user,
          title='Entry',
          theme=theme,
          prompt='How are you?',
          answer='I am happy!'
      )
      
      response = client.get('/api/emotions/trend/?days=30')
      data = response.json()
      
      assert response.status_code == 200
      assert data['success'] is True
      assert isinstance(data['data'], list)
  ```

- Test case 4: API emotion comparison endpoint works correctly
  ```python
  def test_api_emotion_comparison_endpoint(self):
      client = Client()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      client.login(username='test@example.com', password='pass123')
      
      response = client.get('/api/emotions/comparison/?period1_days=7&period2_days=7')
      data = response.json()
      
      assert response.status_code == 200
      assert data['success'] is True
      assert 'recent_period' in data['data']
      assert 'previous_period' in data['data']
  ```

- Test case 5: API entry detail endpoint returns emotion data
  ```python
  def test_api_emotion_entry_detail(self):
      client = Client()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      client.login(username='test@example.com', password='pass123')
      
      theme = Theme.objects.create(name='Growth')
      entry = JournalEntry.objects.create(
          user=user,
          title='Happy Day',
          theme=theme,
          prompt='How are you?',
          answer='I am happy!'
      )
      
      response = client.get(f'/api/emotions/entry/{entry.id}/')
      data = response.json()
      
      assert response.status_code == 200
      assert data['success'] is True
      assert data['data']['entry_id'] == entry.id
      assert 'emotion_label' in data['data']
  ```

**Technical details and Assumptions:**
- All API endpoints use JsonResponse for consistent JSON response formatting
- Authentication is enforced using login_required decorator on all endpoints
- Query parameters are validated and clamped to prevent abuse (e.g., 1-365 days)
- Days parameter defaults to 30 days for reasonable performance
- Entry detail endpoint returns individual emotion analysis with full metrics
- Error responses include success flag and error message for consistent error handling

---

### Phase 5: Emotion Dashboard UI & Visualization
**Files**: 
- `templates/emotion_dashboard.html` (new)
- `authentication/views.py` (update - add dashboard view)
- `authentication/urls.py` (update)
- `static/css/emotion_dashboard.css` (new)
- `static/js/emotion_dashboard.js` (new)
- `tests/unit_tests/views/test_emotion_views.py` (update)

**Description**: 
Create a comprehensive emotion analytics dashboard that displays emotion statistics, trends over time, and mood comparisons. The dashboard will use JavaScript to fetch data from the API endpoints and use a charting library (Chart.js) to visualize emotion trends, emotion distribution (pie/doughnut chart), and period comparisons.

**Key code changes:**

```python
# authentication/views.py - Add emotion dashboard view

@login_required
def emotion_dashboard(request):
    """
    View for emotion analytics dashboard.
    Displays emotion statistics, trends, and insights.
    """
    context = {
        'page_title': 'Emotion Analytics Dashboard',
        'user': request.user
    }
    return render(request, 'emotion_dashboard.html', context)

# authentication/urls.py - Add URL pattern

urlpatterns = [
    # ... existing patterns ...
    path('home/emotion-dashboard/', emotion_dashboard, name='emotion_dashboard'),
]
```

```html
<!-- templates/emotion_dashboard.html (new file) -->
{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="emotion-dashboard-container">
    <div class="dashboard-header">
        <h1>Emotion Analytics Dashboard</h1>
        <p>Track your emotional patterns and insights from your journal entries</p>
    </div>
    
    <div class="emotion-filters">
        <label for="stats-period">Analysis Period:</label>
        <select id="stats-period" name="period">
            <option value="7">Last 7 Days</option>
            <option value="14">Last 14 Days</option>
            <option value="30" selected>Last 30 Days</option>
            <option value="60">Last 60 Days</option>
            <option value="90">Last 90 Days</option>
        </select>
    </div>
    
    <!-- Key Statistics Cards -->
    <div class="emotion-stats-grid">
        <div class="stat-card">
            <div class="stat-label">Total Entries Analyzed</div>
            <div class="stat-value" id="total-entries">0</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-label">Average Sentiment</div>
            <div class="stat-value sentiment-display" id="avg-sentiment">0.0</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-label">Most Common Emotion</div>
            <div class="stat-value" id="common-emotion">—</div>
        </div>
        
        <div class="stat-card">
            <div class="stat-label">Mood Trend</div>
            <div class="stat-value trend-indicator" id="mood-trend">
                <span id="trend-text">—</span>
            </div>
        </div>
    </div>
    
    <!-- Charts Section -->
    <div class="emotion-charts-grid">
        <!-- Emotion Distribution Pie Chart -->
        <div class="chart-container">
            <h3>Emotion Distribution</h3>
            <canvas id="emotion-distribution-chart"></canvas>
            <div id="emotion-legend"></div>
        </div>
        
        <!-- Sentiment Trend Line Chart -->
        <div class="chart-container full-width">
            <h3>Sentiment Trend Over Time</h3>
            <canvas id="sentiment-trend-chart"></canvas>
        </div>
        
        <!-- Sentiment Score Breakdown -->
        <div class="chart-container">
            <h3>Score Breakdown</h3>
            <div class="score-breakdown">
                <div class="score-item">
                    <div class="score-label">Positive</div>
                    <div class="score-bar positive-bar">
                        <div id="positive-score" class="score-fill"></div>
                    </div>
                    <div id="positive-value">0.0</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Neutral</div>
                    <div class="score-bar neutral-bar">
                        <div id="neutral-score" class="score-fill"></div>
                    </div>
                    <div id="neutral-value">0.0</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Negative</div>
                    <div class="score-bar negative-bar">
                        <div id="negative-score" class="score-fill"></div>
                    </div>
                    <div id="negative-value">0.0</div>
                </div>
            </div>
        </div>
        
        <!-- Period Comparison -->
        <div class="chart-container">
            <h3>Mood Comparison</h3>
            <div id="comparison-data">
                <div class="comparison-item">
                    <div class="comparison-period">Recent 7 Days</div>
                    <div id="recent-sentiment" class="sentiment-value">0.0</div>
                </div>
                <div class="comparison-divider">vs</div>
                <div class="comparison-item">
                    <div class="comparison-period">Previous 7 Days</div>
                    <div id="previous-sentiment" class="sentiment-value">0.0</div>
                </div>
                <div class="comparison-change">
                    <span id="change-indicator">—</span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Loading and Error States -->
    <div id="loading-spinner" class="spinner" style="display: none;"></div>
    <div id="error-message" class="error-message" style="display: none;"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script src="{% static 'js/emotion_dashboard.js' %}"></script>
{% endblock %}
```

```javascript
// static/js/emotion_dashboard.js (new file)
class EmotionDashboard {
    constructor() {
        this.charts = {};
        this.currentPeriod = 30;
        this.init();
    }
    
    init() {
        this.attachEventListeners();
        this.loadDashboardData();
    }
    
    attachEventListeners() {
        const periodSelect = document.getElementById('stats-period');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.currentPeriod = parseInt(e.target.value);
                this.loadDashboardData();
            });
        }
    }
    
    async loadDashboardData() {
        this.showLoading(true);
        try {
            const [stats, trend, comparison] = await Promise.all([
                this.fetchEmotionStats(),
                this.fetchEmotionTrend(),
                this.fetchEmotionComparison()
            ]);
            
            this.displayStats(stats);
            this.displayTrendChart(trend);
            this.displayComparison(comparison);
            
            this.showLoading(false);
        } catch (error) {
            this.showError('Failed to load emotion data: ' + error.message);
        }
    }
    
    async fetchEmotionStats() {
        const response = await fetch(`/api/emotions/stats/?days=${this.currentPeriod}`);
        if (!response.ok) throw new Error('Failed to fetch emotion stats');
        const result = await response.json();
        if (!result.success) throw new Error(result.error);
        return result.data;
    }
    
    async fetchEmotionTrend() {
        const response = await fetch(`/api/emotions/trend/?days=${this.currentPeriod}`);
        if (!response.ok) throw new Error('Failed to fetch emotion trend');
        const result = await response.json();
        if (!result.success) throw new Error(result.error);
        return result.data;
    }
    
    async fetchEmotionComparison() {
        const response = await fetch('/api/emotions/comparison/?period1_days=7&period2_days=7');
        if (!response.ok) throw new Error('Failed to fetch emotion comparison');
        const result = await response.json();
        if (!result.success) throw new Error(result.error);
        return result.data;
    }
    
    displayStats(stats) {
        // Update statistics cards
        document.getElementById('total-entries').textContent = stats.total_entries;
        
        const sentiment = stats.average_compound;
        const sentimentEl = document.getElementById('avg-sentiment');
        sentimentEl.textContent = sentiment.toFixed(2);
        sentimentEl.className = this.getSentimentClass(sentiment);
        
        document.getElementById('common-emotion').textContent = 
            this.formatEmotionLabel(stats.most_common_emotion || '—');
        
        // Update score breakdown
        this.updateScoreBreakdown(stats);
        
        // Update emotion distribution chart
        this.updateEmotionDistributionChart(stats.emotion_distribution);
    }
    
    displayTrendChart(trendData) {
        const labels = trendData.map(d => this.formatDate(d.date));
        const sentimentScores = trendData.map(d => d.compound_score);
        
        const ctx = document.getElementById('sentiment-trend-chart');
        if (!ctx) return;
        
        if (this.charts.trendChart) {
            this.charts.trendChart.destroy();
        }
        
        this.charts.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sentiment Score',
                    data: sentimentScores,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#3498db'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        min: -1,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Sentiment Score'
                        }
                    }
                }
            }
        });
    }
    
    updateEmotionDistributionChart(distribution) {
        const emotionLabels = Object.keys(distribution).map(e => 
            this.formatEmotionLabel(e)
        );
        const emotionCounts = Object.values(distribution);
        
        const ctx = document.getElementById('emotion-distribution-chart');
        if (!ctx) return;
        
        if (this.charts.distributionChart) {
            this.charts.distributionChart.destroy();
        }
        
        const colors = this.getEmotionColors();
        
        this.charts.distributionChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: emotionLabels,
                datasets: [{
                    data: emotionCounts,
                    backgroundColor: [
                        colors['very_positive'],
                        colors['positive'],
                        colors['neutral'],
                        colors['negative'],
                        colors['very_negative']
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    updateScoreBreakdown(stats) {
        const positiveFill = document.getElementById('positive-score');
        const neutralFill = document.getElementById('neutral-score');
        const negativeFill = document.getElementById('negative-score');
        
        positiveFill.style.width = (stats.average_positive * 100) + '%';
        neutralFill.style.width = (stats.average_neutral * 100) + '%';
        negativeFill.style.width = (stats.average_negative * 100) + '%';
        
        document.getElementById('positive-value').textContent = 
            stats.average_positive.toFixed(2);
        document.getElementById('neutral-value').textContent = 
            stats.average_neutral.toFixed(2);
        document.getElementById('negative-value').textContent = 
            stats.average_negative.toFixed(2);
    }
    
    displayComparison(comparison) {
        const recentSentiment = comparison.recent_period.average_compound;
        const previousSentiment = comparison.previous_period.average_compound;
        
        document.getElementById('recent-sentiment').textContent = 
            recentSentiment.toFixed(2);
        document.getElementById('previous-sentiment').textContent = 
            previousSentiment.toFixed(2);
        
        const changeEl = document.getElementById('change-indicator');
        if (comparison.improvement) {
            changeEl.textContent = `↑ Improved by ${Math.abs(comparison.change).toFixed(2)}`;
            changeEl.className = 'positive-change';
        } else if (comparison.change < 0) {
            changeEl.textContent = `↓ Declined by ${Math.abs(comparison.change).toFixed(2)}`;
            changeEl.className = 'negative-change';
        } else {
            changeEl.textContent = '→ No change';
            changeEl.className = 'neutral-change';
        }
    }
    
    getSentimentClass(sentiment) {
        if (sentiment >= 0.5) return 'very-positive';
        if (sentiment >= 0.05) return 'positive';
        if (sentiment > -0.05) return 'neutral';
        if (sentiment > -0.5) return 'negative';
        return 'very-negative';
    }
    
    getEmotionColors() {
        return {
            'very_positive': '#27ae60',
            'positive': '#2ecc71',
            'neutral': '#95a5a6',
            'negative': '#e74c3c',
            'very_negative': '#c0392b'
        };
    }
    
    formatEmotionLabel(label) {
        if (!label) return '—';
        return label
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric' 
        });
    }
    
    showLoading(show) {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.style.display = show ? 'block' : 'none';
        }
    }
    
    showError(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new EmotionDashboard();
});
```

```css
/* static/css/emotion_dashboard.css (new file) */
.emotion-dashboard-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    margin-bottom: 30px;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 20px;
}

.dashboard-header h1 {
    font-size: 2.5em;
    color: #2c3e50;
    margin: 0 0 10px 0;
}

.dashboard-header p {
    font-size: 1.1em;
    color: #7f8c8d;
}

.emotion-filters {
    margin-bottom: 30px;
}

.emotion-filters select {
    padding: 10px 15px;
    border-radius: 5px;
    border: 1px solid #bdc3c7;
    font-size: 1em;
    cursor: pointer;
}

.emotion-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-label {
    font-size: 0.9em;
    color: #7f8c8d;
    margin-bottom: 10px;
    font-weight: 600;
}

.stat-value {
    font-size: 2em;
    font-weight: bold;
    color: #2c3e50;
}

.stat-value.very-positive {
    color: #27ae60;
}

.stat-value.positive {
    color: #2ecc71;
}

.stat-value.neutral {
    color: #95a5a6;
}

.stat-value.negative {
    color: #e74c3c;
}

.stat-value.very-negative {
    color: #c0392b;
}

.emotion-charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.chart-container {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-container.full-width {
    grid-column: 1 / -1;
}

.chart-container h3 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 10px;
}

.score-breakdown {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.score-item {
    display: flex;
    align-items: center;
    gap: 10px;
}

.score-label {
    width: 80px;
    font-weight: 600;
    color: #2c3e50;
}

.score-bar {
    flex: 1;
    height: 30px;
    border-radius: 5px;
    overflow: hidden;
    background: #ecf0f1;
}

.score-fill {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 5px;
    color: white;
    font-weight: bold;
    font-size: 0.85em;
}

.positive-bar .score-fill {
    background: linear-gradient(90deg, #2ecc71, #27ae60);
}

.neutral-bar .score-fill {
    background: linear-gradient(90deg, #95a5a6, #7f8c8d);
}

.negative-bar .score-fill {
    background: linear-gradient(90deg, #e74c3c, #c0392b);
}

#comparison-data {
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 20px;
}

.comparison-item {
    text-align: center;
}

.comparison-period {
    font-size: 0.9em;
    color: #7f8c8d;
    margin-bottom: 5px;
}

.sentiment-value {
    font-size: 1.8em;
    font-weight: bold;
    color: #2c3e50;
}

.comparison-divider {
    font-size: 1.2em;
    color: #bdc3c7;
}

.comparison-change {
    text-align: center;
    margin-top: 10px;
}

.comparison-change span {
    font-weight: bold;
    padding: 10px 15px;
    border-radius: 5px;
    display: inline-block;
}

.positive-change {
    color: #27ae60;
    background-color: #d5f4e6;
}

.negative-change {
    color: #c0392b;
    background-color: #fadbd8;
}

.neutral-change {
    color: #95a5a6;
    background-color: #ecf0f1;
}

.spinner {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
}

.spinner::after {
    content: '';
    width: 50px;
    height: 50px;
    border: 5px solid #ecf0f1;
    border-top-color: #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.error-message {
    background-color: #fadbd8;
    color: #c0392b;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 20px;
    border-left: 4px solid #c0392b;
}

@media (max-width: 768px) {
    .emotion-charts-grid {
        grid-template-columns: 1fr;
    }
    
    .emotion-stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .dashboard-header h1 {
        font-size: 1.8em;
    }
}
```

**Test cases for this phase:**

- Test case 1: Emotion dashboard view renders correctly
  ```python
  def test_emotion_dashboard_view_renders(self):
      client = Client()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      client.login(username='test@example.com', password='pass123')
      
      response = client.get('/home/emotion-dashboard/')
      
      assert response.status_code == 200
      assert 'emotion' in response.content.decode().lower()
  ```

- Test case 2: Dashboard requires authentication
  ```python
  def test_emotion_dashboard_requires_login(self):
      client = Client()
      response = client.get('/home/emotion-dashboard/')
      
      assert response.status_code == 302  # Redirect to login
  ```

- Test case 3: Dashboard has correct template context
  ```python
  def test_emotion_dashboard_context(self):
      client = Client()
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='pass123',
          first_name='John',
          last_name='Doe'
      )
      client.login(username='test@example.com', password='pass123')
      
      response = client.get('/home/emotion-dashboard/')
      
      assert 'user' in response.context
      assert response.context['user'] == user
  ```

**Technical details and Assumptions:**
- Emotion dashboard uses Chart.js for visualization (lightweight and flexible)
- Dashboard fetches data via API endpoints for separation of concerns
- Charts are responsive and work on mobile devices
- Color coding matches emotion labels for intuitive understanding
- Period selector allows users to view trends over different time ranges
- Comparison section shows 7-day period changes by default
- JavaScript loads and initializes charts dynamically based on API data
- CSS uses CSS Grid for responsive layout without additional dependencies

---

## Technical Considerations

- **Dependencies**: 
  - `nltk` for VADER sentiment analysis (add to requirements.txt: `nltk==3.8.1`)
  - `Chart.js` v3.9.1+ for client-side charting (loaded via CDN)
  - No additional backend dependencies needed (Django ORM and requests already available)

- **Edge Cases**: 
  - Empty journal entries or entries with only whitespace
  - Very long entries that might cause analysis delays
  - Users with no entries in the requested time period
  - Multiple entries on the same day (aggregated in trend data)
  - Invalid date ranges in API queries (clamped to 1-365 days)

- **Testing Strategy**: 
  - Unit tests for sentiment analysis service covering positive, negative, neutral cases
  - Unit tests for analytics methods with various time periods
  - Integration tests for API endpoints with authentication
  - View tests for dashboard rendering and context
  - Frontend tests for chart initialization (manual or with Jest/Cypress)

- **Performance**: 
  - Emotion analysis happens synchronously on entry save (future: use Celery for async)
  - Database queries use aggregation for efficient statistics calculation
  - API endpoints paginate trend data if > 100 days requested
  - Charts load asynchronously after page render to prevent blocking
  - Consider adding database indexes on JournalEntry.user and EmotionAnalysis.emotion_label

- **Security**: 
  - All API endpoints require authentication (login_required)
  - Users can only access their own emotion data (journal_entry__user=request.user)
  - Query parameters are validated and clamped to prevent abuse
  - CSRF protection enabled on all POST/PUT requests (if added later)

## Testing Notes

- Phase 1 tests validate sentiment analysis accuracy and model creation
- Phase 2 tests ensure signals fire correctly and update on changes
- Phase 3 tests verify analytics calculations with sample data
- Phase 4 tests check API responses and authentication
- Phase 5 tests verify dashboard rendering and initial data load
- All tests use Django TestCase for database isolation
- Follow existing test patterns in `tests/unit_tests/` directory

## Success Criteria

- [ ] EmotionAnalysis model created and migrations applied successfully
- [ ] VADER sentiment analysis service analyzes text with compound scores
- [ ] Signal automatically creates/updates emotion analysis on entry save/update
- [ ] Analytics service calculates statistics, trends, and comparisons correctly
- [ ] All API endpoints return proper JSON responses with authentication
- [ ] API endpoints validate query parameters and return appropriate errors
- [ ] Emotion dashboard loads and displays all charts without errors
- [ ] Charts render sentiment trends, emotion distribution, and comparisons
- [ ] Dashboard is responsive and works on mobile devices
- [ ] All 18+ test cases pass (service, signal, API, view tests)
- [ ] No regressions in existing journal entry creation/editing features
- [ ] NLTK data downloads successfully on first use of emotion service
- [ ] Performance metrics: dashboard loads in < 2 seconds with 100+ entries

