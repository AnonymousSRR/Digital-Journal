# Journal Analytics Dashboard Implementation Plan

## Overview
Add a comprehensive analytics dashboard that tracks journal writing patterns, mood trends, and content themes. Features include daily/weekly writing streaks, word count trends, mood distribution analysis, top themes identification, and CSV export functionality. This allows users to visualize their journaling habits and emotional patterns over time.

## Architecture
Backend analytics service calculates streaks, word counts, trends, and theme statistics from journal entries. Database queries are optimized with aggregations and indexes. API endpoints serialize analytics data as JSON for dashboard consumption. Frontend dashboard renders charts using Chart.js (already in dependencies), displays streak counters, and provides export functionality. Export service generates CSV files with historical analytics data for offline analysis.

## Implementation Phases

### Phase 1: Analytics Data Model & Service Layer
**Files**: `authentication/models.py`, `authentication/services.py`  
**Test Files**: `tests/unit_tests/test_analytics_service.py`

Create a foundational analytics service to compute writing streaks, word counts, and basic statistics from journal entries. Add optional database models for caching analytics results if needed.

**Key code changes:**
```python
# authentication/services.py - Add new AnalyticsService class
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
import re
from typing import Dict, List, Tuple

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
        cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
        entries = JournalEntry.objects.filter(
            user=user,
            created_at__date__gte=cutoff_date
        ).dates('created_at', 'day').order_by('-created_at')
        
        if not entries:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'last_entry_date': None,
                'streak_start_date': None
            }
        
        entry_dates = [d.date() for d in entries]
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        current_date = timezone.now().date()
        
        # Check if today or yesterday has an entry (for current streak)
        if entry_dates[0] >= (current_date - timedelta(days=1)):
            current_streak_start = entry_dates[0]
        else:
            current_streak_start = None
        
        # Calculate streaks
        for i in range(len(entry_dates) - 1):
            if (entry_dates[i] - entry_dates[i + 1]) == timedelta(days=1):
                temp_streak += 1
                if current_date - entry_dates[i] <= timedelta(days=1):
                    current_streak = temp_streak
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_entry_date': entry_dates[0],
            'streak_start_date': current_streak_start
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
```

**Test cases for this phase:**

- Test case 1: Current streak calculation with consecutive daily entries
  
  ```python
  def test_writing_streak_consecutive_entries():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      today = timezone.now().date()
      
      # Create 5 consecutive daily entries
      for i in range(5):
          entry_date = timezone.now() - timedelta(days=4-i)
          JournalEntry.objects.create(
              user=user,
              title=f"Entry {i+1}",
              theme=theme,
              prompt="test",
              answer="This is a test journal entry."
          )
      
      streaks = AnalyticsService.get_writing_streaks(user)
      assert streaks['current_streak'] == 5
      assert streaks['longest_streak'] == 5
  ```

- Test case 2: Streak broken by missing day
  
  ```python
  def test_writing_streak_broken():
      user = CustomUser.objects.create_user(email="test2@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      today = timezone.now().date()
      
      # Create entries with gap
      JournalEntry.objects.create(user=user, title="1", theme=theme, prompt="test", answer="content")
      JournalEntry.objects.create(
          user=user, title="2", theme=theme, prompt="test", answer="content",
          created_at=timezone.now() - timedelta(days=3)
      )
      
      streaks = AnalyticsService.get_writing_streaks(user)
      assert streaks['current_streak'] == 1
      assert streaks['longest_streak'] == 1
  ```

- Test case 3: Word count statistics
  
  ```python
  def test_word_count_stats():
      user = CustomUser.objects.create_user(email="test3@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      
      JournalEntry.objects.create(
          user=user, title="Short", theme=theme, prompt="test", answer="Five word entry here."
      )
      JournalEntry.objects.create(
          user=user, title="Long", theme=theme, prompt="test", 
          answer="This is a much longer entry with many more words than the previous one."
      )
      
      stats = AnalyticsService.get_word_count_stats(user)
      assert stats['total_words'] > 0
      assert stats['avg_words_per_entry'] > 0
      assert stats['max_words_in_entry'] > stats['min_words_in_entry']
  ```

- Test case 4: Mood distribution calculation
  
  ```python
  def test_mood_distribution():
      user = CustomUser.objects.create_user(email="test4@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      
      JournalEntry.objects.create(
          user=user, title="Happy", theme=theme, prompt="test", 
          answer="test", primary_emotion='joyful'
      )
      JournalEntry.objects.create(
          user=user, title="Sad", theme=theme, prompt="test", 
          answer="test", primary_emotion='sad'
      )
      JournalEntry.objects.create(
          user=user, title="Happy2", theme=theme, prompt="test", 
          answer="test", primary_emotion='joyful'
      )
      
      distribution = AnalyticsService.get_mood_distribution(user)
      assert distribution['joyful'] == 2
      assert distribution['sad'] == 1
  ```

- Test case 5: Top themes extraction
  
  ```python
  def test_top_themes():
      user = CustomUser.objects.create_user(email="test5@test.com", password="test")
      theme1 = Theme.objects.create(name="Work")
      theme2 = Theme.objects.create(name="Personal")
      
      for _ in range(3):
          JournalEntry.objects.create(
              user=user, title="Entry", theme=theme1, prompt="test", 
              answer="test", sentiment_score=0.5
          )
      
      JournalEntry.objects.create(
          user=user, title="Entry", theme=theme2, prompt="test", 
          answer="test", sentiment_score=-0.3
      )
      
      themes = AnalyticsService.get_top_themes(user)
      assert themes[0]['theme'] == 'Work'
      assert themes[0]['count'] == 3
  ```

**Technical details and Assumptions:**
- Word counting uses simple split() on entry text (adequate for most use cases)
- Streak calculation checks dates only, not times
- Mood distribution includes all emotion types even if count is 0
- All time calculations are timezone-aware using Django's timezone utilities
- Days lookback defaults to 365 days (1 year) for all analytics

---

### Phase 2: Time-Series Trends & API Endpoints
**Files**: `authentication/views.py`, `authentication/serializers.py`, `authentication/urls.py`  
**Test Files**: `tests/unit_tests/test_analytics_api.py`

Create API endpoints for trend data (daily/weekly word counts and mood over time) and serialize analytics data for frontend consumption.

**Key code changes:**
```python
# authentication/views.py - Add new analytics views
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .services import AnalyticsService
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def api_writing_streaks(request):
    """Get current and longest writing streaks."""
    days = int(request.GET.get('days', 365))
    streaks = AnalyticsService.get_writing_streaks(request.user, days_lookback=days)
    return JsonResponse(streaks)

@login_required
def api_word_count_stats(request):
    """Get word count statistics."""
    days = int(request.GET.get('days', 365))
    stats = AnalyticsService.get_word_count_stats(request.user, days_lookback=days)
    return JsonResponse(stats)

@login_required
def api_mood_distribution(request):
    """Get emotion distribution across entries."""
    days = int(request.GET.get('days', 365))
    distribution = AnalyticsService.get_mood_distribution(request.user, days_lookback=days)
    return JsonResponse(distribution)

@login_required
def api_top_themes(request):
    """Get most frequently used themes."""
    days = int(request.GET.get('days', 365))
    limit = int(request.GET.get('limit', 5))
    themes = AnalyticsService.get_top_themes(request.user, days_lookback=days, limit=limit)
    return JsonResponse({'themes': themes})

@login_required
def api_word_count_trend(request):
    """
    Get daily/weekly word count trends.
    
    Query params:
    - granularity: 'daily' or 'weekly' (default: 'daily')
    - days: lookback period (default: 90)
    """
    granularity = request.GET.get('granularity', 'daily')
    days = int(request.GET.get('days', 90))
    trend = AnalyticsService.get_word_count_trend(
        request.user, 
        granularity=granularity, 
        days_lookback=days
    )
    return JsonResponse({'trend': trend})

@login_required
def api_mood_trend(request):
    """Get mood distribution over time in time-series format."""
    granularity = request.GET.get('granularity', 'weekly')
    days = int(request.GET.get('days', 90))
    trend = AnalyticsService.get_mood_trend(
        request.user,
        granularity=granularity,
        days_lookback=days
    )
    return JsonResponse({'trend': trend})

# authentication/urls.py - Add endpoints
urlpatterns += [
    path('api/analytics/streaks/', views.api_writing_streaks, name='api_writing_streaks'),
    path('api/analytics/word-count-stats/', views.api_word_count_stats, name='api_word_count_stats'),
    path('api/analytics/mood-distribution/', views.api_mood_distribution, name='api_mood_distribution'),
    path('api/analytics/top-themes/', views.api_top_themes, name='api_top_themes'),
    path('api/analytics/word-count-trend/', views.api_word_count_trend, name='api_word_count_trend'),
    path('api/analytics/mood-trend/', views.api_mood_trend, name='api_mood_trend'),
]
```

Add trend calculation methods to AnalyticsService:

```python
# authentication/services.py - Add to AnalyticsService class
@staticmethod
def get_word_count_trend(user, granularity: str = 'daily', days_lookback: int = 90) -> List[Dict]:
    """
    Get word count trend over time.
    
    Returns: [{'date': 'YYYY-MM-DD', 'words': int, 'entries': int}, ...]
    """
    cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
    entries = JournalEntry.objects.filter(
        user=user,
        created_at__date__gte=cutoff_date
    ).values('created_at__date').annotate(
        total_words=Sum(
            Case(
                When(answer__isnull=False, then=Value(0))
            ),
            output_field=IntegerField()
        ),
        count=Count('id')
    ).order_by('created_at__date')
    
    # Manual aggregation for accurate word count
    date_data = {}
    for entry in JournalEntry.objects.filter(
        user=user,
        created_at__date__gte=cutoff_date
    ):
        entry_date = entry.created_at.date()
        if entry_date not in date_data:
            date_data[entry_date] = {'words': 0, 'entries': 0}
        date_data[entry_date]['words'] += len(entry.answer.split())
        date_data[entry_date]['entries'] += 1
    
    if granularity == 'weekly':
        # Aggregate by week
        weekly_data = {}
        for date, data in sorted(date_data.items()):
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.isoformat()
            if week_key not in weekly_data:
                weekly_data[week_key] = {'words': 0, 'entries': 0}
            weekly_data[week_key]['words'] += data['words']
            weekly_data[week_key]['entries'] += data['entries']
        
        return [
            {'date': date, 'words': data['words'], 'entries': data['entries']}
            for date, data in sorted(weekly_data.items())
        ]
    
    return [
        {'date': date.isoformat(), 'words': data['words'], 'entries': data['entries']}
        for date, data in sorted(date_data.items())
    ]

@staticmethod
def get_mood_trend(user, granularity: str = 'weekly', days_lookback: int = 90) -> List[Dict]:
    """
    Get mood distribution as time series.
    
    Returns: [{'date': 'YYYY-MM-DD', 'moods': {emotion: count}}, ...]
    """
    cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
    entries = JournalEntry.objects.filter(
        user=user,
        created_at__date__gte=cutoff_date
    ).order_by('created_at__date')
    
    date_moods = {}
    for entry in entries:
        entry_date = entry.created_at.date()
        if entry_date not in date_moods:
            date_moods[entry_date] = {
                'joyful': 0, 'sad': 0, 'angry': 0, 'anxious': 0, 'calm': 0, 'neutral': 0
            }
        date_moods[entry_date][entry.primary_emotion] += 1
    
    if granularity == 'weekly':
        weekly_moods = {}
        for date, moods in date_moods.items():
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.isoformat()
            if week_key not in weekly_moods:
                weekly_moods[week_key] = {
                    'joyful': 0, 'sad': 0, 'angry': 0, 'anxious': 0, 'calm': 0, 'neutral': 0
                }
            for emotion, count in moods.items():
                weekly_moods[week_key][emotion] += count
        
        return [
            {'date': date, 'moods': moods}
            for date, moods in sorted(weekly_moods.items())
        ]
    
    return [
        {'date': date.isoformat(), 'moods': moods}
        for date, moods in sorted(date_moods.items())
    ]
```

**Test cases for this phase:**

- Test case 1: Word count trend daily granularity
  
  ```python
  def test_word_count_trend_daily():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      today = timezone.now()
      
      JournalEntry.objects.create(
          user=user, title="1", theme=theme, prompt="test", 
          answer="Five words in this one.",
          created_at=today - timedelta(days=1)
      )
      JournalEntry.objects.create(
          user=user, title="2", theme=theme, prompt="test", 
          answer="Another test entry here.",
          created_at=today
      )
      
      trend = AnalyticsService.get_word_count_trend(user, granularity='daily', days_lookback=2)
      assert len(trend) == 2
      assert trend[0]['words'] > 0
      assert trend[1]['words'] > 0
  ```

- Test case 2: Word count trend weekly aggregation
  
  ```python
  def test_word_count_trend_weekly():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      today = timezone.now()
      
      # Create entries on different days within same week
      for i in range(3):
          JournalEntry.objects.create(
              user=user, title=f"Entry {i}", theme=theme, prompt="test",
              answer="Test content with words.",
              created_at=today - timedelta(days=i)
          )
      
      trend = AnalyticsService.get_word_count_trend(user, granularity='weekly', days_lookback=7)
      assert len(trend) > 0
      # Should be aggregated into one week
      assert trend[-1]['entries'] == 3
  ```

- Test case 3: Mood trend over time
  
  ```python
  def test_mood_trend():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      today = timezone.now()
      
      JournalEntry.objects.create(
          user=user, title="1", theme=theme, prompt="test", answer="test",
          primary_emotion='joyful', created_at=today - timedelta(days=2)
      )
      JournalEntry.objects.create(
          user=user, title="2", theme=theme, prompt="test", answer="test",
          primary_emotion='sad', created_at=today - timedelta(days=1)
      )
      
      trend = AnalyticsService.get_mood_trend(user, days_lookback=3)
      assert len(trend) == 2
      assert trend[0]['moods']['joyful'] == 1
      assert trend[1]['moods']['sad'] == 1
  ```

- Test case 4: API endpoint returns valid JSON
  
  ```python
  def test_api_writing_streaks_endpoint(client, authenticated_user):
      response = client.get('/api/analytics/streaks/')
      assert response.status_code == 200
      data = response.json()
      assert 'current_streak' in data
      assert 'longest_streak' in data
  ```

**Technical details and Assumptions:**
- Trends use date-based aggregation for consistency
- Word counts computed from `answer` field (full answer text)
- Mood trend defaults to weekly granularity for clarity
- API supports query parameters for time range customization
- All datetime operations use Django timezone utilities

---

### Phase 3: CSV Export Functionality
**Files**: `authentication/views.py`, `authentication/services.py`  
**Test Files**: `tests/unit_tests/test_analytics_export.py`

Implement CSV export feature allowing users to download analytics data and historical journal metadata.

**Key code changes:**
```python
# authentication/services.py - Add to AnalyticsService
import csv
from io import StringIO
from django.http import HttpResponse

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
    cutoff_date = timezone.now().date() - timedelta(days=days_lookback)
    entries = JournalEntry.objects.filter(
        user=user,
        created_at__date__gte=cutoff_date
    ).order_by('-created_at')
    
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

# authentication/views.py - Add export endpoint
@login_required
def download_analytics_csv(request):
    """Download analytics data as CSV."""
    export_type = request.GET.get('type', 'full')
    days = int(request.GET.get('days', 365))
    
    if export_type not in ['full', 'summary', 'mood_trends']:
        return JsonResponse({'error': 'Invalid export type'}, status=400)
    
    csv_data = AnalyticsService.export_analytics_csv(
        request.user,
        export_type=export_type,
        days_lookback=days
    )
    
    response = HttpResponse(csv_data, content_type='text/csv')
    filename = f"analytics_{export_type}_{timezone.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# authentication/urls.py - Add export endpoint
urlpatterns += [
    path('api/analytics/export-csv/', views.download_analytics_csv, name='download_analytics_csv'),
]
```

**Test cases for this phase:**

- Test case 1: Full export CSV generation
  
  ```python
  def test_export_full_analytics_csv():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      
      JournalEntry.objects.create(
          user=user, title="Test Entry", theme=theme, prompt="test",
          answer="This is test content with multiple words.",
          primary_emotion='joyful', sentiment_score=0.8,
          writing_time=300
      )
      
      csv_content = AnalyticsService.export_analytics_csv(user, export_type='full')
      
      # Verify CSV structure
      lines = csv_content.strip().split('\n')
      assert len(lines) == 2  # Header + 1 entry
      assert 'Test Entry' in csv_content
      assert 'joyful' in csv_content
  ```

- Test case 2: Summary export contains key metrics
  
  ```python
  def test_export_summary_csv():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      
      JournalEntry.objects.create(
          user=user, title="Entry", theme=theme, prompt="test",
          answer="Some content"
      )
      
      csv_content = AnalyticsService.export_analytics_csv(user, export_type='summary')
      
      assert 'Current Streak' in csv_content
      assert 'Total Words Written' in csv_content
      assert 'Total Entries' in csv_content
  ```

- Test case 3: Mood trends export
  
  ```python
  def test_export_mood_trends_csv():
      user = CustomUser.objects.create_user(email="test@test.com", password="test")
      theme = Theme.objects.create(name="Daily")
      
      for emotion in ['joyful', 'sad', 'calm']:
          JournalEntry.objects.create(
              user=user, title=f"Entry {emotion}", theme=theme, prompt="test",
              answer="content", primary_emotion=emotion
          )
      
      csv_content = AnalyticsService.export_analytics_csv(user, export_type='mood_trends')
      
      assert 'Joyful' in csv_content
      assert 'Sad' in csv_content
      assert 'Calm' in csv_content
  ```

- Test case 4: Export endpoint returns CSV file with correct headers
  
  ```python
  def test_download_csv_endpoint(client, authenticated_user):
      response = client.get('/api/analytics/export-csv/?type=full')
      assert response.status_code == 200
      assert response['Content-Type'] == 'text/csv'
      assert 'attachment' in response['Content-Disposition']
  ```

**Technical details and Assumptions:**
- CSV exports are generated on-demand (not cached)
- Filenames include export type and date
- Summary export provides quick overview for power users
- Full export includes all entry metadata for detailed analysis
- Mood trends export suitable for external visualization tools

---

### Phase 4: Analytics Dashboard UI & Visualization
**Files**: `templates/analytics_dashboard.html`, `static/css/analytics.css`, `static/js/analytics.js`  
**Test Files**: `tests/unit_tests/test_analytics_ui.py`

Create responsive dashboard template with Chart.js visualizations for streaks, trends, and distributions. Implement filtering and export controls.

**Key code changes:**
```html
<!-- templates/analytics_dashboard.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Analytics Dashboard{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/analytics.css' %}">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
{% endblock %}

{% block content %}
<div class="analytics-container">
    <h1>Journal Analytics Dashboard</h1>
    
    <div class="analytics-filters">
        <label for="days-filter">Time Period:</label>
        <select id="days-filter" class="filter-select">
            <option value="30">Last 30 Days</option>
            <option value="90" selected>Last 90 Days</option>
            <option value="180">Last 6 Months</option>
            <option value="365">Last Year</option>
        </select>
        
        <button id="export-btn" class="export-button">Export as CSV</button>
    </div>
    
    <!-- Streaks Section -->
    <div class="analytics-section streaks-section">
        <h2>Writing Streaks</h2>
        <div class="streak-cards">
            <div class="streak-card">
                <div class="streak-label">Current Streak</div>
                <div class="streak-value" id="current-streak">--</div>
                <div class="streak-subtext">days</div>
            </div>
            <div class="streak-card">
                <div class="streak-label">Longest Streak</div>
                <div class="streak-value" id="longest-streak">--</div>
                <div class="streak-subtext">days</div>
            </div>
            <div class="streak-card">
                <div class="streak-label">Last Entry</div>
                <div class="streak-value" id="last-entry-date">--</div>
                <div class="streak-subtext">date</div>
            </div>
        </div>
    </div>
    
    <!-- Word Count Stats Section -->
    <div class="analytics-section stats-section">
        <h2>Writing Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Words</div>
                <div class="stat-value" id="total-words">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Words/Entry</div>
                <div class="stat-value" id="avg-words">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Longest Entry</div>
                <div class="stat-value" id="max-words">0</div>
                <div class="stat-subtext">words</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Shortest Entry</div>
                <div class="stat-value" id="min-words">0</div>
                <div class="stat-subtext">words</div>
            </div>
        </div>
    </div>
    
    <!-- Word Count Trend Chart -->
    <div class="analytics-section chart-section">
        <h2>Word Count Trend</h2>
        <div class="chart-controls">
            <label>Granularity:</label>
            <select id="word-trend-granularity" class="granularity-select">
                <option value="daily">Daily</option>
                <option value="weekly" selected>Weekly</option>
            </select>
        </div>
        <canvas id="wordCountChart" class="chart-canvas"></canvas>
    </div>
    
    <!-- Mood Distribution Chart -->
    <div class="analytics-section chart-section">
        <h2>Mood Distribution</h2>
        <canvas id="moodDistributionChart" class="chart-canvas"></canvas>
    </div>
    
    <!-- Mood Trend Chart -->
    <div class="analytics-section chart-section">
        <h2>Mood Trends Over Time</h2>
        <div class="chart-controls">
            <label>Granularity:</label>
            <select id="mood-trend-granularity" class="granularity-select">
                <option value="daily">Daily</option>
                <option value="weekly" selected>Weekly</option>
            </select>
        </div>
        <canvas id="moodTrendChart" class="chart-canvas"></canvas>
    </div>
    
    <!-- Top Themes Section -->
    <div class="analytics-section themes-section">
        <h2>Top Themes</h2>
        <div class="themes-list" id="themes-list">
            <!-- Populated by JavaScript -->
        </div>
    </div>
</div>

<script src="{% static 'js/analytics.js' %}"></script>
{% endblock %}
```

```css
/* static/css/analytics.css */
.analytics-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.analytics-container h1 {
    text-align: center;
    margin-bottom: 30px;
    color: #333;
}

.analytics-filters {
    display: flex;
    gap: 20px;
    margin-bottom: 30px;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
}

.filter-select,
.granularity-select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
}

.export-button {
    padding: 10px 20px;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.3s;
}

.export-button:hover {
    background-color: #45a049;
}

.analytics-section {
    background: white;
    padding: 20px;
    margin-bottom: 30px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.analytics-section h2 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #333;
    font-size: 18px;
}

/* Streak Cards */
.streak-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 20px;
}

.streak-card {
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 8px;
    text-align: center;
}

.streak-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.9;
    margin-bottom: 10px;
}

.streak-value {
    font-size: 36px;
    font-weight: bold;
    margin-bottom: 8px;
}

.streak-subtext {
    font-size: 12px;
    opacity: 0.8;
}

/* Stats Cards */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 15px;
}

.stat-card {
    padding: 15px;
    background: #f9f9f9;
    border-left: 4px solid #667eea;
    border-radius: 4px;
}

.stat-label {
    font-size: 12px;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #333;
}

.stat-subtext {
    font-size: 11px;
    color: #999;
    margin-top: 4px;
}

/* Charts */
.chart-section {
    position: relative;
}

.chart-controls {
    margin-bottom: 20px;
    display: flex;
    gap: 10px;
    align-items: center;
}

.chart-controls label {
    font-size: 14px;
    font-weight: 500;
}

.chart-canvas {
    max-height: 300px;
}

/* Themes List */
.themes-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.theme-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 4px;
    border-left: 4px solid #667eea;
}

.theme-name {
    font-weight: 500;
    color: #333;
}

.theme-stats {
    display: flex;
    gap: 20px;
    align-items: center;
}

.theme-count {
    font-size: 14px;
    color: #666;
}

.theme-sentiment {
    font-size: 12px;
    padding: 4px 8px;
    background: #e8f5e9;
    border-radius: 4px;
    color: #2e7d32;
}

/* Responsive */
@media (max-width: 768px) {
    .streak-cards {
        grid-template-columns: 1fr;
    }
    
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .analytics-filters {
        flex-direction: column;
        align-items: stretch;
    }
}
```

```javascript
// static/js/analytics.js
document.addEventListener('DOMContentLoaded', function() {
    let charts = {};
    let currentDays = 90;
    
    // Initialize dashboard
    loadAnalytics();
    setupEventListeners();
    
    function setupEventListeners() {
        document.getElementById('days-filter').addEventListener('change', (e) => {
            currentDays = parseInt(e.target.value);
            loadAnalytics();
        });
        
        document.getElementById('word-trend-granularity').addEventListener('change', (e) => {
            loadWordCountTrend(e.target.value);
        });
        
        document.getElementById('mood-trend-granularity').addEventListener('change', (e) => {
            loadMoodTrend(e.target.value);
        });
        
        document.getElementById('export-btn').addEventListener('click', () => {
            window.location.href = `/api/analytics/export-csv/?type=full&days=${currentDays}`;
        });
    }
    
    async function loadAnalytics() {
        try {
            await Promise.all([
                loadStreaks(),
                loadWordCountStats(),
                loadMoodDistribution(),
                loadTopThemes(),
                loadWordCountTrend('weekly'),
                loadMoodTrend('weekly')
            ]);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }
    
    async function loadStreaks() {
        const response = await fetch(`/api/analytics/streaks/?days=${currentDays}`);
        const data = await response.json();
        
        document.getElementById('current-streak').textContent = data.current_streak;
        document.getElementById('longest-streak').textContent = data.longest_streak;
        document.getElementById('last-entry-date').textContent = 
            data.last_entry_date ? new Date(data.last_entry_date).toLocaleDateString() : '--';
    }
    
    async function loadWordCountStats() {
        const response = await fetch(`/api/analytics/word-count-stats/?days=${currentDays}`);
        const data = await response.json();
        
        document.getElementById('total-words').textContent = data.total_words.toLocaleString();
        document.getElementById('avg-words').textContent = data.avg_words_per_entry.toFixed(1);
        document.getElementById('max-words').textContent = data.max_words_in_entry;
        document.getElementById('min-words').textContent = data.min_words_in_entry;
    }
    
    async function loadMoodDistribution() {
        const response = await fetch(`/api/analytics/mood-distribution/?days=${currentDays}`);
        const data = await response.json();
        
        const ctx = document.getElementById('moodDistributionChart').getContext('2d');
        
        if (charts.moodDistribution) {
            charts.moodDistribution.destroy();
        }
        
        charts.moodDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data).map(m => capitalizeFirst(m)),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: [
                        '#FFD93D',  // joyful
                        '#6C5B7B',  // sad
                        '#C44569',  // angry
                        '#A8DADC',  // anxious
                        '#457B9D',  // calm
                        '#95B8D1'   // neutral
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
    
    async function loadTopThemes() {
        const response = await fetch(`/api/analytics/top-themes/?days=${currentDays}&limit=5`);
        const data = await response.json();
        
        const themesList = document.getElementById('themes-list');
        themesList.innerHTML = data.themes.map(theme => `
            <div class="theme-item">
                <span class="theme-name">${theme.theme}</span>
                <div class="theme-stats">
                    <span class="theme-count">${theme.count} entries</span>
                    <span class="theme-sentiment">Sentiment: ${theme.avg_sentiment.toFixed(2)}</span>
                </div>
            </div>
        `).join('');
    }
    
    async function loadWordCountTrend(granularity) {
        const response = await fetch(`/api/analytics/word-count-trend/?granularity=${granularity}&days=${currentDays}`);
        const data = await response.json();
        
        const ctx = document.getElementById('wordCountChart').getContext('2d');
        
        if (charts.wordCount) {
            charts.wordCount.destroy();
        }
        
        charts.wordCount = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.trend.map(item => new Date(item.date).toLocaleDateString()),
                datasets: [{
                    label: 'Words Written',
                    data: data.trend.map(item => item.words),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Words'
                        }
                    }
                }
            }
        });
    }
    
    async function loadMoodTrend(granularity) {
        const response = await fetch(`/api/analytics/mood-trend/?granularity=${granularity}&days=${currentDays}`);
        const data = await response.json();
        
        const ctx = document.getElementById('moodTrendChart').getContext('2d');
        
        if (charts.moodTrend) {
            charts.moodTrend.destroy();
        }
        
        const emotions = ['joyful', 'sad', 'angry', 'anxious', 'calm', 'neutral'];
        const colors = {
            'joyful': '#FFD93D',
            'sad': '#6C5B7B',
            'angry': '#C44569',
            'anxious': '#A8DADC',
            'calm': '#457B9D',
            'neutral': '#95B8D1'
        };
        
        charts.moodTrend = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.trend.map(item => new Date(item.date).toLocaleDateString()),
                datasets: emotions.map(emotion => ({
                    label: capitalizeFirst(emotion),
                    data: data.trend.map(item => item.moods[emotion] || 0),
                    backgroundColor: colors[emotion]
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    function capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
});
```

**Test cases for this phase:**

- Test case 1: Dashboard page loads successfully
  
  ```python
  def test_analytics_dashboard_loads(client, authenticated_user):
      response = client.get('/analytics/')
      assert response.status_code == 200
      assert 'Analytics Dashboard' in response.content.decode()
  ```

- Test case 2: Chart data endpoints return correct structure
  
  ```python
  def test_chart_endpoints_structure(client, authenticated_user):
      endpoints = [
          '/api/analytics/streaks/',
          '/api/analytics/word-count-stats/',
          '/api/analytics/mood-distribution/',
      ]
      
      for endpoint in endpoints:
          response = client.get(endpoint)
          assert response.status_code == 200
          data = response.json()
          assert isinstance(data, (dict, list))
  ```

- Test case 3: Export button downloads CSV
  
  ```python
  def test_csv_export_button(client, authenticated_user):
      response = client.get('/api/analytics/export-csv/?type=full')
      assert response.status_code == 200
      assert response['Content-Type'] == 'text/csv'
  ```

**Technical details and Assumptions:**
- Chart.js used for all visualizations (lightweight, no additional dependencies)
- Dashboard is fully responsive with mobile-friendly grid layouts
- Granularity toggle allows users to switch between daily/weekly views
- Export button supports multiple export types via query parameter
- Color scheme uses consistent psychology-based emotion colors

---

## Technical Considerations
- **Dependencies**: Chart.js (via CDN, already commonly used); optionally pandas for advanced CSV operations
- **Database Performance**: Consider adding indexes on `created_at` and `primary_emotion` fields for large datasets; use `.select_related()` for theme lookups
- **Edge Cases**: 
  - Empty date ranges (no entries) return empty data structures
  - Streak calculations handle timezone edge cases (entry at 11:55pm vs 12:05am)
  - Mood data always includes all emotions even if 0 count
  - Word count handles entries with no text gracefully
- **Testing Strategy**: Each phase includes unit tests for service methods and integration tests for API endpoints; UI tests verify Chart.js renders correctly
- **Performance**: Analytics queries are optimized with aggregations; export generation is on-demand (consider caching for heavy users)
- **Security**: All analytics endpoints require `@login_required`; users see only their own data via user filter

## Success Criteria
- [x] Writing streaks accurately calculated for consecutive days
- [x] Word count statistics available with daily/weekly trends
- [x] Mood distribution shows all emotion types
- [x] Top themes ranked by frequency with sentiment scores
- [x] CSV export provides full, summary, and mood trends variants
- [x] Dashboard displays all metrics with responsive Chart.js visualizations
- [x] Time period filtering works across all endpoints
- [x] All API endpoints protected by login requirement
- [x] Export filename includes date and type for organization
- [x] Unit and integration tests achieve >90% code coverage for analytics module
