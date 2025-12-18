# Home Screen Summary Widget Implementation Plan

## Overview
Add a summary widget to the home page that displays three key statistics for the logged-in user: "Total Entries", "Entries This Week", and "Most Common Emotion". This will provide users with a quick overview of their journaling activity.

## Architecture
The summary widget will be displayed on the home page ([templates/home.html](../../templates/home.html)) above the existing dashboard buttons. The statistics will be calculated in the home view ([config/urls.py](../../config/urls.py)) using Django ORM queries on the `JournalEntry` model and passed via template context. The widget will use CSS styling consistent with the existing design patterns.

## Implementation Phases

### Phase 1: Backend Statistics Calculation
**Files**: `config/urls.py`  
**Test Files**: `tests/test_home_summary.py`

Update the `home_view` function in [config/urls.py](../../config/urls.py#L26) to calculate the three statistics and pass them to the template context.

**Key code changes:**
```python
# config/urls.py
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

@login_required
def home_view(request):
    """Home view for authenticated users with summary statistics."""
    # Calculate total entries
    total_entries = JournalEntry.objects.filter(user=request.user).count()
    
    # Calculate entries this week (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    entries_this_week = JournalEntry.objects.filter(
        user=request.user,
        created_at__gte=week_ago
    ).count()
    
    # Calculate most common emotion
    emotion_counts = JournalEntry.objects.filter(
        user=request.user
    ).values('primary_emotion').annotate(
        count=Count('primary_emotion')
    ).order_by('-count').first()
    
    most_common_emotion = emotion_counts['primary_emotion'] if emotion_counts else 'neutral'
    
    # Format emotion for display (capitalize first letter)
    most_common_emotion_display = most_common_emotion.capitalize()
    
    context = {
        'total_entries': total_entries,
        'entries_this_week': entries_this_week,
        'most_common_emotion': most_common_emotion_display,
    }
    
    return render(request, 'home.html', context)
```

**Test cases for this phase:**

- Test case 1: Calculate total entries correctly for user with multiple entries

  ```python
  # tests/test_home_summary.py
  from django.test import TestCase, Client
  from django.urls import reverse
  from authentication.models import CustomUser, JournalEntry, Theme
  from django.utils import timezone
  
  class HomeSummaryWidgetTests(TestCase):
      def setUp(self):
          # Arrange: Create a test user
          self.client = Client()
          self.user = CustomUser.objects.create_user(
              email='test@example.com',
              password='testpass123',
              first_name='Test',
              last_name='User'
          )
          self.client.login(email='test@example.com', password='testpass123')
          
          # Create a test theme
          self.theme = Theme.objects.create(
              name='Test Theme',
              description='Test description'
          )
      
      def test_total_entries_count(self):
          # Arrange: Create 5 journal entries
          for i in range(5):
              JournalEntry.objects.create(
                  user=self.user,
                  title=f'Entry {i}',
                  theme=self.theme,
                  prompt='Test prompt',
                  answer='Test answer',
                  primary_emotion='joyful'
              )
          
          # Act: Request the home page
          response = self.client.get(reverse('home'))
          
          # Assert: Check that total_entries is 5
          self.assertEqual(response.status_code, 200)
          self.assertEqual(response.context['total_entries'], 5)
  ```

- Test case 2: Calculate entries this week correctly

  ```python
  def test_entries_this_week_count(self):
      # Arrange: Create entries from different time periods
      from datetime import timedelta
      
      # Entry from 3 days ago (should be counted)
      three_days_ago = timezone.now() - timedelta(days=3)
      JournalEntry.objects.create(
          user=self.user,
          title='Recent Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer',
          primary_emotion='calm',
          created_at=three_days_ago
      )
      
      # Entry from 10 days ago (should NOT be counted)
      ten_days_ago = timezone.now() - timedelta(days=10)
      old_entry = JournalEntry.objects.create(
          user=self.user,
          title='Old Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer',
          primary_emotion='sad'
      )
      old_entry.created_at = ten_days_ago
      old_entry.save()
      
      # Act: Request the home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check that entries_this_week is 1
      self.assertEqual(response.context['entries_this_week'], 1)
  ```

- Test case 3: Calculate most common emotion correctly

  ```python
  def test_most_common_emotion_calculation(self):
      # Arrange: Create entries with different emotions
      # 3 joyful entries
      for i in range(3):
          JournalEntry.objects.create(
              user=self.user,
              title=f'Joyful Entry {i}',
              theme=self.theme,
              prompt='Test prompt',
              answer='Test answer',
              primary_emotion='joyful'
          )
      
      # 2 sad entries
      for i in range(2):
          JournalEntry.objects.create(
              user=self.user,
              title=f'Sad Entry {i}',
              theme=self.theme,
              prompt='Test prompt',
              answer='Test answer',
              primary_emotion='sad'
          )
      
      # Act: Request the home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check that most_common_emotion is 'Joyful'
      self.assertEqual(response.context['most_common_emotion'], 'Joyful')
  ```

- Test case 4: Handle user with no entries (edge case)

  ```python
  def test_empty_entries_for_new_user(self):
      # Arrange: New user with no entries (already in setUp)
      
      # Act: Request the home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check default values
      self.assertEqual(response.context['total_entries'], 0)
      self.assertEqual(response.context['entries_this_week'], 0)
      self.assertEqual(response.context['most_common_emotion'], 'Neutral')
  ```

- Test case 5: Ensure statistics are user-specific (isolation test)

  ```python
  def test_statistics_are_user_specific(self):
      # Arrange: Create another user with their own entries
      other_user = CustomUser.objects.create_user(
          email='other@example.com',
          password='otherpass123',
          first_name='Other',
          last_name='User'
      )
      
      # Create entries for other user
      for i in range(3):
          JournalEntry.objects.create(
              user=other_user,
              title=f'Other Entry {i}',
              theme=self.theme,
              prompt='Test prompt',
              answer='Test answer',
              primary_emotion='angry'
          )
      
      # Create entry for current user
      JournalEntry.objects.create(
          user=self.user,
          title='My Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer',
          primary_emotion='calm'
      )
      
      # Act: Request the home page as current user
      response = self.client.get(reverse('home'))
      
      # Assert: Check that only current user's data is shown
      self.assertEqual(response.context['total_entries'], 1)
      self.assertEqual(response.context['most_common_emotion'], 'Calm')
  ```

**Technical details and Assumptions:**
- Uses Django's ORM `Count` aggregation for efficient emotion counting
- Week calculation uses `timezone.now()` for timezone awareness
- Falls back to 'neutral' if user has no entries
- Capitalizes emotion for better display formatting
- Import `JournalEntry` model from `authentication.models`

### Phase 2: Template Integration - Summary Widget HTML
**Files**: `templates/home.html`  
**Test Files**: `tests/test_home_summary.py` (integration tests)

Add the summary widget HTML structure to [templates/home.html](../../templates/home.html) above the existing dashboard buttons.

**Key code changes:**
```html
<!-- templates/home.html -->
{% extends 'base.html' %}

{% block title %}Home - Digital Journal App{% endblock %}

{% block content %}
<div class="home-container">
    <div class="welcome-message">
        <h2>Hi {{ user.first_name }}, what's your plan today?</h2>
    </div>
    
    <!-- New Summary Widget -->
    <div class="summary-widget" data-testid="summary-widget">
        <div class="summary-card" data-testid="total-entries-card">
            <div class="summary-icon">📝</div>
            <div class="summary-content">
                <div class="summary-value" data-testid="total-entries-value">{{ total_entries }}</div>
                <div class="summary-label">Total Entries</div>
            </div>
        </div>
        
        <div class="summary-card" data-testid="entries-week-card">
            <div class="summary-icon">📅</div>
            <div class="summary-content">
                <div class="summary-value" data-testid="entries-week-value">{{ entries_this_week }}</div>
                <div class="summary-label">Entries This Week</div>
            </div>
        </div>
        
        <div class="summary-card" data-testid="emotion-card">
            <div class="summary-icon">😊</div>
            <div class="summary-content">
                <div class="summary-value" data-testid="emotion-value">{{ most_common_emotion }}</div>
                <div class="summary-label">Most Common Emotion</div>
            </div>
        </div>
    </div>
    
    <!-- Existing dashboard buttons -->
    <div class="dashboard-buttons">
        <a href="{% url 'theme_selector' %}" class="dashboard-button" id="create-journal-btn" data-testid="create-journal-btn">
            <span class="button-text">Create New Journal</span>
        </a>
        <a href="{% url 'my_journals' %}" class="dashboard-button" id="my-journals-btn" data-testid="my-journals-btn">
            <span class="button-text">My Journals</span>
        </a>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const createJournalBtn = document.getElementById('create-journal-btn');
    
    createJournalBtn.addEventListener('click', function() {
        // Start the timer when user clicks Create New Journal
        const startTime = Date.now();
        sessionStorage.setItem('journalWritingStartTime', startTime.toString());
        console.log('Timer started at:', new Date(startTime));
    });
});
</script>
{% endblock %}
```

**Test cases for this phase:**

- Test case 1: Verify summary widget is rendered on home page

  ```python
  def test_summary_widget_renders_on_home_page(self):
      # Arrange: Create a journal entry
      JournalEntry.objects.create(
          user=self.user,
          title='Test Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer',
          primary_emotion='joyful'
      )
      
      # Act: Request the home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check that summary widget is in the response
      self.assertContains(response, 'summary-widget')
      self.assertContains(response, 'Total Entries')
      self.assertContains(response, 'Entries This Week')
      self.assertContains(response, 'Most Common Emotion')
  ```

- Test case 2: Verify correct data is displayed in widget

  ```python
  def test_summary_widget_displays_correct_values(self):
      # Arrange: Create 2 entries
      for i in range(2):
          JournalEntry.objects.create(
              user=self.user,
              title=f'Entry {i}',
              theme=self.theme,
              prompt='Test prompt',
              answer='Test answer',
              primary_emotion='calm'
          )
      
      # Act: Request the home page
      response = self.client.get(reverse('home'))
      content = response.content.decode()
      
      # Assert: Check that values are correctly displayed
      self.assertIn('data-testid="total-entries-value">2', content)
      self.assertIn('data-testid="entries-week-value">2', content)
      self.assertIn('data-testid="emotion-value">Calm', content)
  ```

- Test case 3: Verify widget displays zero values for new user

  ```python
  def test_summary_widget_shows_zero_for_new_user(self):
      # Arrange: New user with no entries (from setUp)
      
      # Act: Request the home page
      response = self.client.get(reverse('home'))
      content = response.content.decode()
      
      # Assert: Check zero values are displayed
      self.assertIn('data-testid="total-entries-value">0', content)
      self.assertIn('data-testid="entries-week-value">0', content)
      self.assertIn('data-testid="emotion-value">Neutral', content)
  ```

**Technical details and Assumptions:**
- Widget is placed between welcome message and dashboard buttons
- Uses semantic HTML with data-testid attributes for testing
- Icon emojis are used for visual appeal (can be replaced with icon fonts)
- Maintains existing timer functionality in the script section
- Widget structure uses flexbox-friendly classes for styling

### Phase 3: CSS Styling for Summary Widget
**Files**: `static/css/style.css`  
**Test Files**: None (visual styling, manual testing recommended)

Add CSS styles to [static/css/style.css](../../static/css/style.css) for the summary widget to match the existing design patterns in the application.

**Key code changes:**
```css
/* static/css/style.css */

/* Summary Widget Styles */
.summary-widget {
    display: flex;
    gap: 20px;
    margin: 30px 0;
    justify-content: center;
    flex-wrap: wrap;
}

.summary-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 25px;
    min-width: 200px;
    flex: 1;
    max-width: 250px;
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.summary-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}

.summary-icon {
    font-size: 40px;
    flex-shrink: 0;
}

.summary-content {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.summary-value {
    font-size: 32px;
    font-weight: bold;
    color: white;
    line-height: 1;
}

.summary-label {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
}

/* Responsive Design for Summary Widget */
@media (max-width: 768px) {
    .summary-widget {
        flex-direction: column;
        gap: 15px;
    }
    
    .summary-card {
        max-width: 100%;
        min-width: 100%;
    }
}

/* Adjust spacing for home container */
.home-container {
    padding: 20px;
}
```

**Test cases for this phase:**

No automated tests for CSS styling. Manual testing should verify:
- Widget displays correctly on desktop (3 cards in a row)
- Widget displays correctly on mobile (stacked vertically)
- Hover effects work smoothly
- Colors match the existing design theme
- Text is readable and properly sized
- Widget is centered on the page

**Technical details and Assumptions:**
- Uses CSS flexbox for responsive layout
- Gradient background matches existing button styles in the app
- Hover animations provide visual feedback
- Responsive breakpoint at 768px for mobile devices
- Cards have equal width distribution on desktop
- Follows existing color scheme (purple gradient)
- Box shadows provide depth consistent with modern UI design

### Phase 4: Integration Testing and Refinement
**Files**: `tests/test_home_summary.py`  
**Test Files**: `tests/test_home_summary.py`

Create comprehensive integration tests to verify the complete functionality of the summary widget, including edge cases and user experience scenarios.

**Key code changes:**
```python
# tests/test_home_summary.py

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, JournalEntry, Theme
from django.utils import timezone
from datetime import timedelta


class HomeSummaryIntegrationTests(TestCase):
    """Integration tests for the home page summary widget."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(email='test@example.com', password='testpass123')
        
        self.theme = Theme.objects.create(
            name='Test Theme',
            description='Test description'
        )
    
    def test_complete_widget_workflow(self):
        """Test the complete widget functionality with realistic data."""
        # Arrange: Create a realistic set of journal entries
        emotions = ['joyful', 'joyful', 'calm', 'sad', 'joyful', 'anxious']
        
        for i, emotion in enumerate(emotions):
            JournalEntry.objects.create(
                user=self.user,
                title=f'Entry {i+1}',
                theme=self.theme,
                prompt='Test prompt',
                answer='Test answer',
                primary_emotion=emotion
            )
        
        # Act: Get the home page
        response = self.client.get(reverse('home'))
        
        # Assert: Verify all statistics are correct
        self.assertEqual(response.context['total_entries'], 6)
        self.assertEqual(response.context['entries_this_week'], 6)
        self.assertEqual(response.context['most_common_emotion'], 'Joyful')
        
        # Verify HTML rendering
        content = response.content.decode()
        self.assertIn('summary-widget', content)
        self.assertIn('data-testid="total-entries-value">6', content)
        self.assertIn('Joyful', content)
```

**Test cases for this phase:**

- Test case 1: Full integration test with mixed data

  ```python
  def test_mixed_entries_across_time_periods(self):
      # Arrange: Create entries from different time periods
      # 2 entries this week
      for i in range(2):
          JournalEntry.objects.create(
              user=self.user,
              title=f'This Week {i}',
              theme=self.theme,
              prompt='Test',
              answer='Test',
              primary_emotion='joyful'
          )
      
      # 3 entries from 2 weeks ago
      two_weeks_ago = timezone.now() - timedelta(days=14)
      for i in range(3):
          old_entry = JournalEntry.objects.create(
              user=self.user,
              title=f'Old Entry {i}',
              theme=self.theme,
              prompt='Test',
              answer='Test',
              primary_emotion='sad'
          )
          old_entry.created_at = two_weeks_ago
          old_entry.save()
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Verify correct calculations
      self.assertEqual(response.context['total_entries'], 5)
      self.assertEqual(response.context['entries_this_week'], 2)
      # Most common emotion overall is 'sad' (3 vs 2)
      self.assertEqual(response.context['most_common_emotion'], 'Sad')
  ```

- Test case 2: Verify unauthenticated users cannot access

  ```python
  def test_unauthenticated_user_redirected(self):
      # Arrange: Log out the user
      self.client.logout()
      
      # Act: Try to access home page
      response = self.client.get(reverse('home'))
      
      # Assert: Should redirect to login
      self.assertEqual(response.status_code, 302)
      self.assertIn('/authentication/', response.url)
  ```

- Test case 3: Performance test with large dataset

  ```python
  def test_performance_with_many_entries(self):
      # Arrange: Create 100 entries
      import time
      
      for i in range(100):
          emotion = ['joyful', 'sad', 'calm', 'angry'][i % 4]
          JournalEntry.objects.create(
              user=self.user,
              title=f'Entry {i}',
              theme=self.theme,
              prompt='Test',
              answer='Test',
              primary_emotion=emotion
          )
      
      # Act: Time the page load
      start_time = time.time()
      response = self.client.get(reverse('home'))
      end_time = time.time()
      
      # Assert: Should complete in reasonable time (< 1 second)
      self.assertEqual(response.status_code, 200)
      self.assertLess(end_time - start_time, 1.0)
      self.assertEqual(response.context['total_entries'], 100)
  ```

- Test case 4: Test emotion tie-breaking behavior

  ```python
  def test_emotion_tie_returns_first_alphabetically(self):
      # Arrange: Create equal number of two emotions
      for i in range(2):
          JournalEntry.objects.create(
              user=self.user,
              title=f'Angry {i}',
              theme=self.theme,
              prompt='Test',
              answer='Test',
              primary_emotion='angry'
          )
          JournalEntry.objects.create(
              user=self.user,
              title=f'Joyful {i}',
              theme=self.theme,
              prompt='Test',
              answer='Test',
              primary_emotion='joyful'
          )
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Should return one of them consistently
      # (Django's order_by with ties will return first in natural order)
      emotion = response.context['most_common_emotion']
      self.assertIn(emotion, ['Angry', 'Joyful'])
  ```

**Technical details and Assumptions:**
- Integration tests verify both backend logic and template rendering
- Tests cover authentication requirements
- Performance testing ensures scalability with large datasets
- Edge case testing covers tie-breaking scenarios
- Tests use realistic data patterns
- All tests clean up after themselves (Django's TestCase handles this)

## Technical Considerations

- **Dependencies**: No new packages required - uses existing Django ORM and timezone utilities
- **Edge Cases**: 
  - User with no journal entries (shows 0 and "Neutral")
  - Ties in emotion frequency (returns first match from query)
  - Timezone handling for "this week" calculation
  - User isolation (statistics only for logged-in user)
- **Testing Strategy**: Unit tests for backend calculations, integration tests for full flow, manual testing for CSS styling
- **Performance**: Optimized queries with `Count` aggregation and single database hit per statistic
- **Security**: Uses `@login_required` decorator, ensures user-specific data isolation

## Testing Notes
- Each phase includes its own unit tests as part of the implementation
- Tests follow Django's TestCase pattern with arrange-act-assert structure
- Integration tests verify the complete workflow in Phase 4
- CSS styling requires manual visual testing across devices
- All tests use `data-testid` attributes for reliable element selection

## Success Criteria
- [ ] Home page displays summary widget with three statistics
- [ ] Total Entries shows accurate count of all user's journal entries
- [ ] Entries This Week shows count from last 7 days only
- [ ] Most Common Emotion displays the emotion with highest frequency
- [ ] Widget displays correctly on desktop and mobile devices
- [ ] Statistics are user-specific and isolated
- [ ] All unit and integration tests pass
- [ ] Widget styling matches existing design patterns
- [ ] Page loads performantly even with many entries
- [ ] Zero values and "Neutral" emotion shown for users with no entries
