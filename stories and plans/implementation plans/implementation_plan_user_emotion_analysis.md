# User Emotion Analysis Implementation Plan

## Overview
Add emotion analysis to journal entries by integrating sentiment analysis using TextBlob/VADER and emotion detection with transformers. This will allow users to track emotional patterns in their writing, visualize sentiment trends over time, and gain insights into their emotional well-being through the journaling app.

## Architecture
The emotion analysis system will consist of:
1. **Backend Service Layer** - `EmotionAnalysisService` that performs text analysis and emotion detection
2. **Data Model** - Extend `JournalEntry` model to store emotion metrics and detected emotions
3. **Database Migrations** - Add emotion fields to JournalEntry (primary emotion, sentiment score, emotion breakdown)
4. **Background Processing** - Analyze emotions when entries are created/updated
5. **API Endpoints** - Provide emotion data to frontend for visualization
6. **Frontend Display** - Show emotion badges on entries and emotion trend analytics on dashboard
7. **Analytics Views** - New page displaying emotional trends and statistics

## Implementation Phases

### Phase 1: Emotion Analysis Service and Model Extension
**Files**: 
- `authentication/models.py`
- `authentication/services.py` (new)
- `authentication/migrations/` (new migration)
- `tests/unit_tests/services/test_emotion_analysis_service.py` (new)

**Description:**
Create the core emotion analysis service that will detect primary emotion, sentiment score, and emotion breakdown for journal entries. Extend the JournalEntry model to store these emotion metrics. The service will use TextBlob for sentiment polarity/subjectivity and a lightweight emotion detection approach.

**Key code changes:**

```python
# authentication/models.py - Add to JournalEntry model
class JournalEntry(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    theme = models.ForeignKey(Theme, on_delete=models.PROTECT)
    prompt = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    bookmarked = models.BooleanField(default=False)
    writing_time = models.IntegerField(default=0, help_text="Time spent writing in seconds")
    
    # New emotion analysis fields
    primary_emotion = models.CharField(
        max_length=20, 
        default='neutral',
        choices=[
            ('joyful', 'Joyful'),
            ('sad', 'Sad'),
            ('angry', 'Angry'),
            ('anxious', 'Anxious'),
            ('calm', 'Calm'),
            ('neutral', 'Neutral'),
        ],
        help_text="Primary emotion detected in the entry"
    )
    sentiment_score = models.FloatField(
        default=0.0,
        help_text="Sentiment score from -1.0 (negative) to 1.0 (positive)"
    )
    emotion_data = models.JSONField(
        default=dict,
        help_text="Breakdown of emotions: {emotion: score}"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.created_at.date()} - {self.theme.name}"
```

```python
# authentication/services.py (new file)
import re
from textblob import TextBlob
from typing import Dict, Tuple

class EmotionAnalysisService:
    """Service for analyzing emotions in text using sentiment analysis and pattern matching."""
    
    # Emotion keywords mapping
    EMOTION_KEYWORDS = {
        'joyful': ['happy', 'joyful', 'excited', 'ecstatic', 'thrilled', 'wonderful', 'amazing', 'great', 'love', 'beautiful'],
        'sad': ['sad', 'depressed', 'miserable', 'gloomy', 'unhappy', 'down', 'blue', 'loss', 'miss'],
        'angry': ['angry', 'furious', 'mad', 'enraged', 'frustrated', 'irritated', 'annoyed', 'upset', 'hate'],
        'anxious': ['anxious', 'worried', 'nervous', 'scared', 'afraid', 'stressed', 'overwhelmed', 'panic'],
        'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'tranquil', 'content', 'comfortable', 'at ease'],
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
        
        # Calculate sentiment score using TextBlob
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity  # Range: -1 to 1
        
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
```

**Test cases for this phase:**

- Test case 1: Emotion analysis detects positive sentiment from joyful text
  ```python
  def test_analyze_emotions_detects_joyful_sentiment():
      text = "I feel amazing and excited about the wonderful things happening in my life!"
      result = EmotionAnalysisService.analyze_emotions(text)
      
      assert result['primary_emotion'] == 'joyful'
      assert result['sentiment_score'] > 0.3
      assert result['emotion_data']['joyful'] > 0.0
  ```

- Test case 2: Emotion analysis detects negative sentiment from sad text
  ```python
  def test_analyze_emotions_detects_sad_sentiment():
      text = "I feel sad and depressed about the situation. Everything seems gloomy."
      result = EmotionAnalysisService.analyze_emotions(text)
      
      assert result['primary_emotion'] == 'sad'
      assert result['sentiment_score'] < -0.2
      assert result['emotion_data']['sad'] > 0.0
  ```

- Test case 3: Emotion analysis handles neutral text correctly
  ```python
  def test_analyze_emotions_handles_neutral_text():
      text = "The weather is nice. I went to the store today."
      result = EmotionAnalysisService.analyze_emotions(text)
      
      assert result['primary_emotion'] == 'neutral'
      assert -0.2 <= result['sentiment_score'] <= 0.2
  ```

- Test case 4: Empty text returns valid empty emotion data
  ```python
  def test_analyze_emotions_handles_empty_text():
      text = ""
      result = EmotionAnalysisService.analyze_emotions(text)
      
      assert 'primary_emotion' in result
      assert 'sentiment_score' in result
      assert 'emotion_data' in result
      assert result['sentiment_score'] == 0.0
  ```

**Technical details and Assumptions:**
- Use TextBlob library (add to requirements.txt) for sentiment analysis - lightweight and no external API needed
- Emotion detection uses keyword matching as initial approach - can be upgraded to transformer-based models in future phases
- Sentiment score is stored as float with 3 decimal places precision
- Emotion data is stored as JSON for flexibility in displaying breakdown to users
- Analysis is synchronous during entry creation/update (acceptable for user-facing journaling app)

---

### Phase 2: Integration with Journal Entry Creation and Async Processing
**Files**:
- `authentication/views.py` (modify existing journal creation views)
- `authentication/tasks.py` (new - for async processing)
- `authentication/signals.py` (new - for auto-analysis)
- `config/settings.py` (modify to add Celery config if needed)
- `tests/unit_tests/views/test_journal_entry_emotion_analysis.py` (new)

**Description:**
Integrate emotion analysis into the journal entry creation workflow. When users create or update a journal entry, automatically analyze emotions and store the results. Implement this as a signal handler to keep the code decoupled and maintainable. Consider async processing for performance.

**Key code changes:**

```python
# authentication/signals.py (new file)
from django.db.models.signals import post_save, pre_save
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
```

```python
# authentication/apps.py (modify existing)
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        import authentication.signals  # Import signals when app is ready
```

```python
# authentication/views.py (modify answer_prompt view to show emotion data)
# Existing view code, but emotion data now auto-populated via signal
@login_required
def answer_prompt(request):
    """
    View for answering a journal prompt and creating an entry.
    """
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            # Signal handler will automatically analyze emotions before save
            entry.save()
            messages.success(request, 'Journal entry saved successfully with emotion analysis!')
            return redirect('my_journals')
    else:
        form = AnswerForm()
    
    context = {
        'form': form,
    }
    return render(request, 'authentication/answer_prompt.html', context)
```

**Test cases for this phase:**

- Test case 1: Journal entry creation automatically analyzes emotions
  ```python
  def test_journal_entry_emotions_analyzed_on_creation():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal Growth', description='test')
      
      entry = JournalEntry.objects.create(
          user=user,
          title='Happy Day',
          theme=theme,
          prompt='How was your day?',
          answer='I had an amazing and wonderful day! Everything was great!'
      )
      
      assert entry.primary_emotion == 'joyful'
      assert entry.sentiment_score > 0.3
      assert entry.emotion_data is not None
  ```

- Test case 2: Emotion analysis updates when entry is modified
  ```python
  def test_emotion_analysis_updates_on_entry_modification():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal Growth', description='test')
      
      entry = JournalEntry.objects.create(
          user=user,
          title='Entry',
          theme=theme,
          prompt='Prompt',
          answer='Happy'
      )
      initial_emotion = entry.primary_emotion
      
      entry.answer = 'I am sad and depressed'
      entry.save()
      entry.refresh_from_db()
      
      assert entry.primary_emotion != initial_emotion
      assert entry.primary_emotion == 'sad'
  ```

- Test case 3: Emotion analysis works via answer_prompt view
  ```python
  def test_answer_prompt_view_saves_emotions():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal Growth', description='test')
      
      client = Client()
      client.force_login(user)
      
      data = {
          'title': 'My Entry',
          'answer': 'I feel anxious about upcoming events'
      }
      response = client.post(reverse('answer_prompt'), data)
      
      entry = JournalEntry.objects.first()
      assert entry.primary_emotion == 'anxious'
  ```

**Technical details and Assumptions:**
- Use Django signals (pre_save) for automatic emotion analysis - no external task queue needed initially
- Analysis is synchronous and blocking during entry save - acceptable for typical journaling workload
- Emotion data persisted in JSONField for flexibility and querying
- Signal handler in `apps.py` ensures proper initialization
- If performance becomes issue, can migrate to Celery async tasks in future

---

### Phase 3: Emotion Analytics Views and API Endpoints
**Files**:
- `authentication/views.py` (add new analytics views)
- `authentication/serializers.py` (new - for JSON responses)
- `authentication/urls.py` (add new routes)
- `tests/unit_tests/views/test_emotion_analytics_views.py` (new)

**Description:**
Create API endpoints and views to retrieve emotion analytics for the logged-in user. Provide endpoints for:
1. Overall emotion statistics (most common emotion, average sentiment score)
2. Emotion trends over time (daily/weekly/monthly breakdown)
3. Emotion data for individual entries
4. Emotion comparison across themes

**Key code changes:**

```python
# authentication/serializers.py (new file)
from rest_framework import serializers
from authentication.models import JournalEntry

class JournalEntryEmotionSerializer(serializers.ModelSerializer):
    """Serializer for emotion data of journal entries."""
    
    class Meta:
        model = JournalEntry
        fields = ['id', 'title', 'primary_emotion', 'sentiment_score', 'emotion_data', 'created_at', 'theme']
    
    read_only_fields = ['primary_emotion', 'sentiment_score', 'emotion_data', 'created_at']


class EmotionStatsSerializer(serializers.Serializer):
    """Serializer for overall emotion statistics."""
    
    total_entries = serializers.IntegerField()
    primary_emotion_distribution = serializers.DictField()
    average_sentiment_score = serializers.FloatField()
    emotion_over_time = serializers.ListField()
```

```python
# authentication/views.py (add new views)
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Avg, Count
from datetime import datetime, timedelta
from authentication.models import JournalEntry
from authentication.serializers import JournalEntryEmotionSerializer, EmotionStatsSerializer

@login_required
@require_http_methods(['GET'])
def get_emotion_stats(request):
    """
    Get overall emotion statistics for the logged-in user.
    Returns: {
        total_entries: int,
        primary_emotion_distribution: {emotion: count},
        average_sentiment_score: float
    }
    """
    entries = JournalEntry.objects.filter(user=request.user)
    
    # Count emotion distribution
    emotion_distribution = {}
    for entry in entries:
        emotion = entry.primary_emotion
        emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
    
    # Calculate average sentiment
    avg_sentiment = entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0.0
    
    stats = {
        'total_entries': entries.count(),
        'primary_emotion_distribution': emotion_distribution,
        'average_sentiment_score': round(avg_sentiment, 3),
    }
    
    return JsonResponse(stats)


@login_required
@require_http_methods(['GET'])
def get_emotion_trends(request):
    """
    Get emotion trends over time for the logged-in user.
    Query params: days (default 30) - number of days to look back
    Returns: List of daily emotion data
    """
    days = int(request.GET.get('days', 30))
    start_date = datetime.now().date() - timedelta(days=days)
    
    entries = JournalEntry.objects.filter(
        user=request.user,
        created_at__date__gte=start_date
    ).order_by('created_at')
    
    # Group emotions by date
    trends = {}
    for entry in entries:
        date_key = entry.created_at.date().isoformat()
        if date_key not in trends:
            trends[date_key] = {'date': date_key, 'emotions': {}, 'average_sentiment': 0.0}
        
        emotion = entry.primary_emotion
        trends[date_key]['emotions'][emotion] = trends[date_key]['emotions'].get(emotion, 0) + 1
    
    # Calculate average sentiment per date
    for date_key, trend_data in trends.items():
        date_entries = entries.filter(created_at__date=date_key)
        avg_sentiment = date_entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0.0
        trend_data['average_sentiment'] = round(avg_sentiment, 3)
    
    return JsonResponse(list(trends.values()))


@login_required
@require_http_methods(['GET'])
def get_emotion_by_theme(request):
    """
    Get emotion statistics broken down by theme.
    Returns: {theme_name: {primary_emotion_distribution, average_sentiment}}
    """
    entries = JournalEntry.objects.filter(user=request.user)
    
    theme_emotions = {}
    for entry in entries:
        theme_name = entry.theme.name
        if theme_name not in theme_emotions:
            theme_emotions[theme_name] = {
                'emotions': {},
                'sentiments': [],
                'count': 0
            }
        
        emotion = entry.primary_emotion
        theme_emotions[theme_name]['emotions'][emotion] = \
            theme_emotions[theme_name]['emotions'].get(emotion, 0) + 1
        theme_emotions[theme_name]['sentiments'].append(entry.sentiment_score)
        theme_emotions[theme_name]['count'] += 1
    
    # Format response
    result = {}
    for theme_name, data in theme_emotions.items():
        avg_sentiment = sum(data['sentiments']) / len(data['sentiments']) if data['sentiments'] else 0.0
        result[theme_name] = {
            'emotion_distribution': data['emotions'],
            'average_sentiment': round(avg_sentiment, 3),
            'entry_count': data['count']
        }
    
    return JsonResponse(result)
```

```python
# authentication/urls.py (add new routes)
from django.urls import path
from authentication import views

urlpatterns = [
    # ... existing patterns ...
    path('api/emotion-stats/', views.get_emotion_stats, name='emotion_stats'),
    path('api/emotion-trends/', views.get_emotion_trends, name='emotion_trends'),
    path('api/emotion-by-theme/', views.get_emotion_by_theme, name='emotion_by_theme'),
]
```

**Test cases for this phase:**

- Test case 1: Get emotion statistics for user with multiple entries
  ```python
  def test_get_emotion_stats_returns_correct_distribution():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      # Create entries with different emotions
      JournalEntry.objects.create(
          user=user, title='1', theme=theme, prompt='p', answer='Happy and excited',
          primary_emotion='joyful', sentiment_score=0.8
      )
      JournalEntry.objects.create(
          user=user, title='2', theme=theme, prompt='p', answer='Sad and depressed',
          primary_emotion='sad', sentiment_score=-0.7
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('emotion_stats'))
      
      data = response.json()
      assert data['total_entries'] == 2
      assert data['primary_emotion_distribution']['joyful'] == 1
      assert data['primary_emotion_distribution']['sad'] == 1
      assert data['average_sentiment_score'] == 0.05  # (0.8 - 0.7) / 2
  ```

- Test case 2: Get emotion trends over specified days
  ```python
  def test_get_emotion_trends_filters_by_days():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      # Create entry from 40 days ago
      old_date = timezone.now() - timedelta(days=40)
      JournalEntry.objects.create(
          user=user, title='old', theme=theme, prompt='p', answer='Old entry',
          primary_emotion='joyful', sentiment_score=0.5, created_at=old_date
      )
      
      # Create entry from 5 days ago
      recent_date = timezone.now() - timedelta(days=5)
      JournalEntry.objects.create(
          user=user, title='recent', theme=theme, prompt='p', answer='Recent entry',
          primary_emotion='sad', sentiment_score=-0.3, created_at=recent_date
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('emotion_trends') + '?days=30')
      
      data = response.json()
      assert len(data) == 1  # Only recent entry should be included
      assert data[0]['emotions']['sad'] == 1
  ```

- Test case 3: Get emotion statistics by theme
  ```python
  def test_get_emotion_by_theme_breaks_down_correctly():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme1 = Theme.objects.create(name='Work', description='test')
      theme2 = Theme.objects.create(name='Personal', description='test')
      
      JournalEntry.objects.create(
          user=user, title='1', theme=theme1, prompt='p', answer='Happy at work',
          primary_emotion='joyful', sentiment_score=0.7
      )
      JournalEntry.objects.create(
          user=user, title='2', theme=theme2, prompt='p', answer='Stressed personally',
          primary_emotion='anxious', sentiment_score=-0.4
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('emotion_by_theme'))
      
      data = response.json()
      assert data['Work']['emotion_distribution']['joyful'] == 1
      assert data['Personal']['emotion_distribution']['anxious'] == 1
      assert data['Work']['average_sentiment'] == 0.7
  ```

**Technical details and Assumptions:**
- Use Django's built-in JSON response and QuerySet aggregation for efficiency
- Emotion trends default to last 30 days but parameterizable via query string
- All endpoints require authentication (@login_required)
- JSON serialization for API responses enables frontend flexibility
- Can be easily wrapped with Django REST Framework serializers if project adopts DRF later

---

### Phase 4: Frontend UI Components for Emotion Display
**Files**:
- `templates/authentication/my_journals.html` (modify to show emotion badges)
- `templates/authentication/emotion_analytics.html` (new - analytics dashboard)
- `static/css/emotion_styles.css` (new)
- `static/js/emotion_charts.js` (new - for visualization)
- `authentication/views.py` (add emotion_analytics view)
- `authentication/urls.py` (add emotion_analytics route)
- `tests/unit_tests/views/test_emotion_analytics_ui.py` (new)

**Description:**
Create user-facing UI components to display emotion analysis. Add emotion badges to journal entry cards showing the detected primary emotion. Create a dedicated analytics dashboard page showing emotion trends with charts and statistics. Use Chart.js or similar lightweight charting library.

**Key code changes:**

```html
<!-- templates/authentication/my_journals.html (add emotion display to entries) -->
<!-- Add inside journal entry card, near title -->
<div class="journal-entry-card">
    <div class="entry-header">
        <h3>{{ entry.title }}</h3>
        <span class="emotion-badge emotion-{{ entry.primary_emotion }}">
            {{ entry.get_primary_emotion_display }}
        </span>
        <span class="sentiment-score" title="Sentiment Score">
            {{ entry.sentiment_score|floatformat:2 }}
        </span>
    </div>
    <!-- Rest of entry content -->
</div>
```

```html
<!-- templates/authentication/emotion_analytics.html (new file) -->
{% extends 'base.html' %}

{% block content %}
<div class="emotion-analytics-container">
    <h1>Your Emotional Journal Analytics</h1>
    
    <div class="stats-overview">
        <div class="stat-card">
            <h3>Total Entries</h3>
            <p id="totalEntries">-</p>
        </div>
        <div class="stat-card">
            <h3>Average Sentiment</h3>
            <p id="avgSentiment">-</p>
        </div>
        <div class="stat-card">
            <h3>Most Common Emotion</h3>
            <p id="mostCommonEmotion">-</p>
        </div>
    </div>
    
    <div class="charts-container">
        <div class="chart-wrapper">
            <h3>Emotion Distribution</h3>
            <canvas id="emotionDistributionChart"></canvas>
        </div>
        
        <div class="chart-wrapper">
            <h3>Sentiment Trends (Last 30 Days)</h3>
            <canvas id="sentimentTrendsChart"></canvas>
        </div>
        
        <div class="chart-wrapper">
            <h3>Emotions by Theme</h3>
            <canvas id="emotionByThemeChart"></canvas>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="{% static 'js/emotion_charts.js' %}"></script>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        loadEmotionAnalytics();
    });
    
    function loadEmotionAnalytics() {
        // Load emotion stats
        fetch('/api/emotion-stats/')
            .then(response => response.json())
            .then(data => displayStats(data));
        
        // Load emotion trends
        fetch('/api/emotion-trends/?days=30')
            .then(response => response.json())
            .then(data => displayTrends(data));
        
        // Load emotion by theme
        fetch('/api/emotion-by-theme/')
            .then(response => response.json())
            .then(data => displayThemeAnalysis(data));
    }
    
    function displayStats(data) {
        document.getElementById('totalEntries').textContent = data.total_entries;
        document.getElementById('avgSentiment').textContent = 
            (data.average_sentiment_score > 0 ? '+' : '') + 
            data.average_sentiment_score.toFixed(2);
        
        const mostCommon = Object.keys(data.primary_emotion_distribution)
            .reduce((a, b) => 
                data.primary_emotion_distribution[a] > data.primary_emotion_distribution[b] ? a : b
            );
        document.getElementById('mostCommonEmotion').textContent = mostCommon || 'N/A';
        
        createEmotionChart(data.primary_emotion_distribution);
    }
    
    function displayTrends(data) {
        // Chart creation handled in emotion_charts.js
        createTrendsChart(data);
    }
    
    function displayThemeAnalysis(data) {
        createThemeChart(data);
    }
</script>
{% endblock %}
```

```css
/* static/css/emotion_styles.css (new file) */
.emotion-badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-left: 0.5rem;
    text-transform: capitalize;
}

.emotion-joyful {
    background-color: #FFD700;
    color: #333;
}

.emotion-sad {
    background-color: #87CEEB;
    color: #fff;
}

.emotion-angry {
    background-color: #FF6B6B;
    color: #fff;
}

.emotion-anxious {
    background-color: #FFA500;
    color: #fff;
}

.emotion-calm {
    background-color: #90EE90;
    color: #333;
}

.emotion-neutral {
    background-color: #D3D3D3;
    color: #333;
}

.sentiment-score {
    font-size: 0.9rem;
    color: #666;
    margin-left: 0.5rem;
}

.emotion-analytics-container {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    opacity: 0.9;
}

.stat-card p {
    margin: 0;
    font-size: 2rem;
    font-weight: bold;
}

.charts-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
}

.chart-wrapper {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-wrapper h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #333;
}

.chart-wrapper canvas {
    max-height: 300px;
}
```

```python
# authentication/views.py (add emotion_analytics view)
from django.shortcuts import render

@login_required
def emotion_analytics(request):
    """View for displaying emotion analytics dashboard."""
    context = {
        'page_title': 'Emotional Analytics'
    }
    return render(request, 'authentication/emotion_analytics.html', context)
```

```python
# authentication/urls.py (add route)
path('emotion-analytics/', views.emotion_analytics, name='emotion_analytics'),
```

**Test cases for this phase:**

- Test case 1: Emotion badge renders with correct emotion class
  ```python
  def test_emotion_badge_displays_correct_emotion_in_template():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      entry = JournalEntry.objects.create(
          user=user, title='Happy', theme=theme, prompt='p', answer='Amazing!',
          primary_emotion='joyful', sentiment_score=0.8
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('my_journals'))
      
      assert b'emotion-joyful' in response.content
      assert b'Joyful' in response.content
  ```

- Test case 2: Emotion analytics page loads successfully
  ```python
  def test_emotion_analytics_page_loads():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('emotion_analytics'))
      
      assert response.status_code == 200
      assert 'Emotional Journal Analytics' in str(response.content)
  ```

- Test case 3: Sentiment score displays correctly on entry card
  ```python
  def test_sentiment_score_displays_on_entry_card():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      entry = JournalEntry.objects.create(
          user=user, title='Test', theme=theme, prompt='p', answer='Test',
          sentiment_score=0.657
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('my_journals'))
      
      assert b'0.66' in response.content or b'0.657' in response.content
  ```

**Technical details and Assumptions:**
- Use Chart.js CDN for lightweight visualization (no npm build required)
- Emotion colors are consistent across UI: joyful (gold), sad (blue), angry (red), anxious (orange), calm (green), neutral (gray)
- Async fetch API calls to load analytics data dynamically
- Dashboard is read-only for initial implementation
- CSS Grid for responsive layout across device sizes

---

### Phase 5: Emotion Filtering and Advanced Queries
**Files**:
- `authentication/views.py` (add filtering views)
- `authentication/urls.py` (add filter routes)
- `templates/authentication/my_journals.html` (add filter UI)
- `tests/unit_tests/views/test_emotion_filtering.py` (new)

**Description:**
Add ability for users to filter journal entries by emotion and sentiment score range. Implement filtering on both backend (API endpoints) and frontend (UI). This helps users quickly find entries by emotional state or explore specific emotional periods.

**Key code changes:**

```python
# authentication/views.py (add filtering endpoint)
from django.db.models import Q

@login_required
@require_http_methods(['GET'])
def get_entries_by_emotion(request):
    """
    Get journal entries filtered by emotion and optional sentiment range.
    Query params:
    - emotion: primary emotion to filter by (joyful, sad, angry, anxious, calm, neutral)
    - min_sentiment: minimum sentiment score (-1.0 to 1.0)
    - max_sentiment: maximum sentiment score (-1.0 to 1.0)
    """
    emotion = request.GET.get('emotion')
    min_sentiment = request.GET.get('min_sentiment')
    max_sentiment = request.GET.get('max_sentiment')
    
    entries = JournalEntry.objects.filter(user=request.user)
    
    if emotion:
        entries = entries.filter(primary_emotion=emotion)
    
    if min_sentiment:
        try:
            entries = entries.filter(sentiment_score__gte=float(min_sentiment))
        except ValueError:
            pass
    
    if max_sentiment:
        try:
            entries = entries.filter(sentiment_score__lte=float(max_sentiment))
        except ValueError:
            pass
    
    serializer = JournalEntryEmotionSerializer(entries, many=True)
    return JsonResponse({'entries': serializer.data, 'count': entries.count()})
```

**Test cases for this phase:**

- Test case 1: Filter entries by single emotion
  ```python
  def test_filter_entries_by_emotion():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      JournalEntry.objects.create(
          user=user, title='1', theme=theme, prompt='p', answer='Happy',
          primary_emotion='joyful'
      )
      JournalEntry.objects.create(
          user=user, title='2', theme=theme, prompt='p', answer='Sad',
          primary_emotion='sad'
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(reverse('get_entries_by_emotion') + '?emotion=joyful')
      
      data = response.json()
      assert data['count'] == 1
      assert data['entries'][0]['primary_emotion'] == 'joyful'
  ```

- Test case 2: Filter entries by sentiment score range
  ```python
  def test_filter_entries_by_sentiment_range():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      JournalEntry.objects.create(
          user=user, title='1', theme=theme, prompt='p', answer='Very happy',
          sentiment_score=0.9
      )
      JournalEntry.objects.create(
          user=user, title='2', theme=theme, prompt='p', answer='Neutral',
          sentiment_score=0.1
      )
      
      client = Client()
      client.force_login(user)
      response = client.get(
          reverse('get_entries_by_emotion') + '?min_sentiment=0.5&max_sentiment=1.0'
      )
      
      data = response.json()
      assert data['count'] == 1
      assert data['entries'][0]['sentiment_score'] == 0.9
  ```

**Technical details and Assumptions:**
- Sentiment score range: -1.0 (very negative) to 1.0 (very positive)
- Filtering can be combined (emotion AND sentiment range)
- Query parameters are optional and can be used in any combination
- Frontend can send requests to filter API and display results dynamically

---

### Phase 6: Emotion Export and Reporting
**Files**:
- `authentication/views.py` (add export view)
- `authentication/urls.py` (add export route)
- `templates/authentication/emotion_export.html` (new)
- `authentication/utils.py` (new - for report generation)
- `tests/unit_tests/views/test_emotion_export.py` (new)

**Description:**
Allow users to export their emotion data and generate summary reports. Users can download emotion analytics as PDF or CSV for personal records or to share with therapists/counselors. Include emotional trends, statistics, and entry previews in reports.

**Key code changes:**

```python
# authentication/utils.py (new file)
from datetime import datetime, timedelta
from django.db.models import Avg, Count
from authentication.models import JournalEntry
import csv
from io import StringIO

class EmotionReportGenerator:
    """Generate emotion analysis reports in various formats."""
    
    @staticmethod
    def generate_csv_report(user, days=90):
        """
        Generate CSV report of emotion data for specified period.
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
                round(entry.writing_time / 60, 1)
            ])
        
        return output.getvalue()
    
    @staticmethod
    def generate_summary_stats(user, days=90):
        """Generate summary statistics for the report."""
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
```

```python
# authentication/views.py (add export views)
from django.http import HttpResponse
from authentication.utils import EmotionReportGenerator

@login_required
def export_emotion_report_csv(request):
    """Export emotion data as CSV file."""
    days = int(request.GET.get('days', 90))
    csv_content = EmotionReportGenerator.generate_csv_report(request.user, days=days)
    
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="emotion_report_{datetime.now().date()}.csv"'
    return response


@login_required
def export_emotion_report_json(request):
    """Export emotion data and statistics as JSON."""
    days = int(request.GET.get('days', 90))
    stats = EmotionReportGenerator.generate_summary_stats(request.user, days=days)
    return JsonResponse(stats)
```

**Test cases for this phase:**

- Test case 1: CSV export includes all entries within date range
  ```python
  def test_csv_export_includes_recent_entries():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      # Create entry within 90 days
      JournalEntry.objects.create(
          user=user, title='Recent', theme=theme, prompt='p', answer='Recent entry',
          primary_emotion='joyful', sentiment_score=0.7
      )
      
      csv_content = EmotionReportGenerator.generate_csv_report(user, days=90)
      
      assert 'Recent' in csv_content
      assert 'joyful' in csv_content
      assert '0.7' in csv_content
  ```

- Test case 2: CSV export excludes old entries
  ```python
  def test_csv_export_excludes_old_entries():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      # Create old entry
      old_date = timezone.now() - timedelta(days=100)
      JournalEntry.objects.create(
          user=user, title='Old', theme=theme, prompt='p', answer='Old entry',
          primary_emotion='sad', sentiment_score=-0.5, created_at=old_date
      )
      
      csv_content = EmotionReportGenerator.generate_csv_report(user, days=90)
      
      assert 'Old' not in csv_content
  ```

- Test case 3: JSON export calculates correct statistics
  ```python
  def test_json_export_calculates_correct_stats():
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='Test',
          last_name='User'
      )
      theme = Theme.objects.create(name='Personal', description='test')
      
      JournalEntry.objects.create(
          user=user, title='1', theme=theme, prompt='p', answer='Happy',
          primary_emotion='joyful', sentiment_score=0.8
      )
      JournalEntry.objects.create(
          user=user, title='2', theme=theme, prompt='p', answer='Sad',
          primary_emotion='sad', sentiment_score=-0.6
      )
      
      stats = EmotionReportGenerator.generate_summary_stats(user, days=90)
      
      assert stats['total_entries'] == 2
      assert stats['emotion_distribution']['joyful'] == 1
      assert stats['emotion_distribution']['sad'] == 1
      assert stats['average_sentiment'] == 0.1  # (0.8 - 0.6) / 2
  ```

**Technical details and Assumptions:**
- CSV export includes all relevant emotion fields for easy analysis in spreadsheet applications
- JSON export provides machine-readable format for programmatic processing
- Default report period is 90 days, customizable via query parameter
- Filename includes export date for easy file management
- Reports are user-scoped and require authentication

---

## Technical Considerations

- **Dependencies**: Add `textblob` to requirements.txt for sentiment analysis (no API key needed). Optional: `transformers` library for advanced NLP if budget allows.
- **Edge Cases**: 
  - Empty journal entries (handle gracefully)
  - Very long entries (sentiment analysis performance)
  - Non-English text (TextBlob supports basic multilingual, but accuracy varies)
  - Rapid entry creation (emotion data updated correctly with signal)
- **Testing Strategy**: 
  - Unit tests for EmotionAnalysisService with various text samples
  - Integration tests for signal handlers and model saving
  - View tests for API endpoints and filtering
  - Template tests to verify emotion UI renders correctly
  - End-to-end tests for complete user workflows
- **Performance**: 
  - Sentiment analysis is synchronous (acceptable for journal app where entries are created infrequently)
  - Can migrate to async Celery tasks if performance becomes bottleneck
  - JSONField queries are efficient for small emotion_data objects
- **Security**: 
  - All emotion data endpoints protected with @login_required
  - Export functionality scoped to authenticated user only
  - No sensitive emotion data exposed to other users
  - CSV/JSON exports are generated server-side and streamed to client

## Success Criteria

- [x] Emotion analysis service correctly identifies primary emotion and sentiment
- [x] Journal entries automatically analyzed on creation/update via signals
- [x] Emotion data persisted to database (primary_emotion, sentiment_score, emotion_data)
- [x] Emotion badges display on journal entry cards with correct styling
- [x] Emotion analytics dashboard shows statistics and trends
- [x] API endpoints provide emotion data for multiple query patterns
- [x] Users can filter entries by emotion and sentiment score
- [x] Emotion data can be exported as CSV and JSON
- [x] All components have comprehensive test coverage
- [x] UI is responsive and works on desktop and mobile
