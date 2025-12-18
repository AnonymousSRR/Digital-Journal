# Daily Streak Card Implementation Plan

## Overview
Add a persistent "Daily Streak" card on the home screen that displays the user's current journaling streak (consecutive days with at least one entry). The streak updates in real-time after saving an entry and resets automatically when a day is missed. This feature leverages the existing `AnalyticsService.get_writing_streaks()` method.

## Architecture
The implementation follows the existing pattern used for the home summary widget:
- **Backend**: `AnalyticsService.get_writing_streaks()` (already exists) calculates current streak based on consecutive entry dates
- **View**: [authentication/views.py](../../authentication/views.py) `home_view` function passes streak data to template
- **Template**: [templates/home.html](../../templates/home.html) displays the streak card alongside existing summary cards
- **Styling**: [static/css/style.css](../../static/css/style.css) uses existing `.summary-card` pattern with fire emoji

## Implementation Phases

### Phase 1: Backend Streak Calculation Integration
**Files**: `authentication/views.py`  
**Test Files**: `tests/test_daily_streak.py`

Integrate the existing `AnalyticsService.get_writing_streaks()` method into the `home_view` function to calculate and pass the current streak to the template.

**Key code changes:**
```python
# authentication/views.py (in home_view function around line 1541)
from authentication.services import AnalyticsService

@login_required
def home_view(request):
    """Home view for authenticated users with summary statistics."""
    # ... existing code for total_entries, entries_this_week, most_common_emotion ...
    
    # Calculate daily streak using existing AnalyticsService
    streak_data = AnalyticsService.get_writing_streaks(request.user)
    current_streak = streak_data['current_streak']
    
    context = {
        'total_entries': total_entries,
        'entries_this_week': entries_this_week,
        'most_common_emotion': most_common_emotion_display,
        'current_streak': current_streak,  # Add streak to context
    }
    
    return render(request, 'home.html', context)
```

**Test cases for this phase:**

- Test case 1: Verify streak calculation for user with consecutive entries

  ```python
  def test_current_streak_calculation_consecutive_days(self):
      # Arrange: Create entries for 3 consecutive days
      from django.utils import timezone
      from datetime import timedelta
      
      today = timezone.now().date()
      for i in range(3):
          entry_date = today - timedelta(days=i)
          entry = JournalEntry.objects.create(
              user=self.user,
              title=f'Entry {i}',
              theme=self.theme,
              prompt='Daily prompt',
              answer='My daily reflection'
          )
          # Manually set created_at to specific date
          entry.created_at = timezone.make_aware(
              timezone.datetime.combine(entry_date, timezone.datetime.min.time())
          )
          entry.save()
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Streak should be 3
      assert response.context['current_streak'] == 3
  ```

- Test case 2: Verify streak is zero for new user with no entries

  ```python
  def test_current_streak_zero_for_new_user(self):
      # Arrange: New user with no entries (already in setUp)
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Streak should be 0
      assert response.context['current_streak'] == 0
  ```

- Test case 3: Verify streak resets when a day is missed

  ```python
  def test_streak_resets_when_day_missed(self):
      # Arrange: Create entries with a gap
      from django.utils import timezone
      from datetime import timedelta
      
      today = timezone.now().date()
      
      # Entry today
      entry1 = JournalEntry.objects.create(
          user=self.user,
          title='Today entry',
          theme=self.theme,
          prompt='Prompt',
          answer='Answer'
      )
      entry1.created_at = timezone.make_aware(
          timezone.datetime.combine(today, timezone.datetime.min.time())
      )
      entry1.save()
      
      # Entry 3 days ago (gap of 2 days)
      three_days_ago = today - timedelta(days=3)
      entry2 = JournalEntry.objects.create(
          user=self.user,
          title='Old entry',
          theme=self.theme,
          prompt='Prompt',
          answer='Answer'
      )
      entry2.created_at = timezone.make_aware(
          timezone.datetime.combine(three_days_ago, timezone.datetime.min.time())
      )
      entry2.save()
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Streak should be 1 (only today's entry)
      assert response.context['current_streak'] == 1
  ```

**Technical details and Assumptions:**
- The `AnalyticsService.get_writing_streaks()` method already handles all streak calculation logic (lines 230-290 in [authentication/services.py](../../authentication/services.py#L230))
- Streak counts "today or yesterday" as valid (allows for flexibility if user journals at night vs morning)
- The method uses `created_at__date` to get distinct dates per user
- No database migration needed as we're using existing data

---

### Phase 2: Frontend Display of Streak Card
**Files**: `templates/home.html`  
**Test Files**: `tests/test_daily_streak.py`

Add a new summary card to display the daily streak alongside existing summary cards (total entries, entries this week, most common emotion).

**Key code changes:**
```html
<!-- templates/home.html (inside summary-widget div after emotion card) -->
<div class="summary-widget" data-testid="summary-widget">
    <!-- Existing cards: total entries, entries this week, emotion -->
    
    <div class="summary-card streak-card" data-testid="streak-card">
        <div class="summary-icon">🔥</div>
        <div class="summary-content">
            <div class="summary-value" data-testid="streak-value">{{ current_streak }}</div>
            <div class="summary-label">Day Streak</div>
        </div>
    </div>
</div>
```

**Test cases for this phase:**

- Test case 1: Verify streak card is visible on home page

  ```python
  def test_streak_card_visible_on_home_page(self):
      # Arrange: User already logged in (setUp)
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check streak card exists in response
      assert response.status_code == 200
      assert 'streak-card' in response.content.decode()
      assert '🔥' in response.content.decode()
      assert 'Day Streak' in response.content.decode()
  ```

- Test case 2: Verify streak value displays correctly for active streak

  ```python
  def test_streak_value_displays_correctly(self):
      # Arrange: Create 5-day streak
      from django.utils import timezone
      from datetime import timedelta
      
      today = timezone.now().date()
      for i in range(5):
          entry_date = today - timedelta(days=i)
          entry = JournalEntry.objects.create(
              user=self.user,
              title=f'Entry {i}',
              theme=self.theme,
              prompt='Prompt',
              answer='Answer'
          )
          entry.created_at = timezone.make_aware(
              timezone.datetime.combine(entry_date, timezone.datetime.min.time())
          )
          entry.save()
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check streak value is 5
      content = response.content.decode()
      assert 'data-testid="streak-value">5</div>' in content
  ```

- Test case 3: Verify streak card shows zero for new user

  ```python
  def test_streak_card_shows_zero_for_new_user(self):
      # Arrange: New user with no entries (setUp)
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check streak value is 0
      content = response.content.decode()
      assert 'data-testid="streak-value">0</div>' in content
  ```

**Technical details and Assumptions:**
- Follow existing pattern from [templates/home.html](../../templates/home.html) lines 12-34
- Use fire emoji 🔥 to represent streak (common UX pattern for streaks)
- Place as 4th card in the summary widget grid
- CSS styling will be handled in Phase 3

---

### Phase 3: Styling and Visual Polish
**Files**: `static/css/style.css`  
**Test Files**: `tests/test_daily_streak.py` (visual regression tests if available)

Add specific styling for the streak card to differentiate it from other summary cards with an attention-grabbing color scheme.

**Key code changes:**
```css
/* static/css/style.css (add after existing .summary-card styles around line 1440) */

/* Daily Streak Card - Special styling */
.streak-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.streak-card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 10px 20px rgba(245, 87, 108, 0.3);
}

.streak-card .summary-icon {
    animation: flicker 2s infinite;
}

@keyframes flicker {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

/* Responsive adjustment for 4 cards */
@media (max-width: 1024px) {
    .summary-widget {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .summary-widget {
        grid-template-columns: 1fr;
    }
}
```

**Test cases for this phase:**

- Test case 1: Verify streak card has unique styling class

  ```python
  def test_streak_card_has_unique_class(self):
      # Arrange: User logged in
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      
      # Assert: Check for streak-card class
      content = response.content.decode()
      assert 'class="summary-card streak-card"' in content
  ```

- Test case 2: Verify all 4 cards render in correct grid layout

  ```python
  def test_all_four_cards_render_correctly(self):
      # Arrange: Create some entries
      for i in range(2):
          JournalEntry.objects.create(
              user=self.user,
              title=f'Entry {i}',
              theme=self.theme,
              prompt='Prompt',
              answer='I feel happy today'
          )
      
      # Act: Get home page
      response = self.client.get(reverse('home'))
      content = response.content.decode()
      
      # Assert: All 4 cards present
      assert content.count('summary-card') == 4
      assert 'total-entries-card' in content
      assert 'entries-week-card' in content
      assert 'emotion-card' in content
      assert 'streak-card' in content
  ```

**Technical details and Assumptions:**
- Use pink-to-red gradient (`#f093fb` to `#f5576c`) to make streak card stand out
- Add subtle flicker animation to fire emoji to draw attention
- Ensure responsive layout works with 4 cards (2x2 grid on tablets, single column on mobile)
- Follow existing CSS patterns from [static/css/style.css](../../static/css/style.css#L1416-L1484)

---

### Phase 4: Real-time Update After Entry Creation
**Files**: `authentication/views.py`, `templates/answer_prompt.html`  
**Test Files**: `tests/test_daily_streak.py`

Ensure the streak automatically updates when a user creates a new journal entry, either through redirect refresh or by recalculating streak on each page load.

**Key code changes:**
```python
# authentication/views.py (in save_journal_answer view around line 149)
# No changes needed - home_view already recalculates on each load

# However, verify redirect after save goes to home page
@login_required
def save_journal_answer(request):
    # ... existing code to save journal entry ...
    
    if request.method == 'POST':
        # ... save journal entry code ...
        
        # Redirect to home page (streak will auto-update)
        messages.success(request, 'Journal entry saved successfully!')
        return redirect('home')  # Ensure this redirects to home
```

**Test cases for this phase:**

- Test case 1: Verify streak increases after creating new entry today

  ```python
  def test_streak_increases_after_new_entry_today(self):
      # Arrange: User with 2-day streak
      from django.utils import timezone
      from datetime import timedelta
      
      today = timezone.now().date()
      yesterday = today - timedelta(days=1)
      
      for date in [yesterday, today - timedelta(days=2)]:
          entry = JournalEntry.objects.create(
              user=self.user,
              title='Entry',
              theme=self.theme,
              prompt='Prompt',
              answer='Answer'
          )
          entry.created_at = timezone.make_aware(
              timezone.datetime.combine(date, timezone.datetime.min.time())
          )
          entry.save()
      
      # Verify initial streak is 2
      response1 = self.client.get(reverse('home'))
      assert response1.context['current_streak'] == 2
      
      # Act: Create new entry today
      JournalEntry.objects.create(
          user=self.user,
          title='New entry',
          theme=self.theme,
          prompt='Prompt',
          answer='Answer'
      )
      
      # Assert: Streak should now be 3
      response2 = self.client.get(reverse('home'))
      assert response2.context['current_streak'] == 3
  ```

- Test case 2: Verify streak doesn't increase with multiple entries same day

  ```python
  def test_streak_same_with_multiple_entries_same_day(self):
      # Arrange: Create first entry today
      JournalEntry.objects.create(
          user=self.user,
          title='Entry 1',
          theme=self.theme,
          prompt='Prompt',
          answer='Answer'
      )
      
      response1 = self.client.get(reverse('home'))
      initial_streak = response1.context['current_streak']
      
      # Act: Create second entry today
      JournalEntry.objects.create(
          user=self.user,
          title='Entry 2',
          theme=self.theme,
          prompt='Prompt',
          answer='Answer'
      )
      
      # Assert: Streak should remain the same
      response2 = self.client.get(reverse('home'))
      assert response2.context['current_streak'] == initial_streak
  ```

- Test case 3: Verify streak resets to 1 after missing a day

  ```python
  def test_streak_resets_after_missing_day(self):
      # Arrange: Create entries 3 and 4 days ago (no recent entries)
      from django.utils import timezone
      from datetime import timedelta
      
      today = timezone.now().date()
      for i in [3, 4]:
          date = today - timedelta(days=i)
          entry = JournalEntry.objects.create(
              user=self.user,
              title=f'Entry {i}',
              theme=self.theme,
              prompt='Prompt',
              answer='Answer'
          )
          entry.created_at = timezone.make_aware(
              timezone.datetime.combine(date, timezone.datetime.min.time())
          )
          entry.save()
      
      # Verify streak is 0 (no recent entries)
      response1 = self.client.get(reverse('home'))
      assert response1.context['current_streak'] == 0
      
      # Act: Create new entry today
      JournalEntry.objects.create(
          user=self.user,
          title='New entry',
          theme=self.theme,
          prompt='Prompt',
          answer='Answer'
      )
      
      # Assert: Streak should be 1 (fresh start)
      response2 = self.client.get(reverse('home'))
      assert response2.context['current_streak'] == 1
  ```

**Technical details and Assumptions:**
- The streak updates on page load (home_view recalculates each time)
- No client-side JavaScript needed for updates
- The existing `post_save` signal in [authentication/signals.py](../../authentication/signals.py) handles entry creation
- Streak calculation in `AnalyticsService.get_writing_streaks()` automatically handles "today or yesterday" logic
- Multiple entries on the same day count as 1 day in the streak (handled by `.distinct()` on dates)

---

## Technical Considerations

**Dependencies:**
- No new packages required
- Leverages existing `AnalyticsService.get_writing_streaks()` method from [authentication/services.py](../../authentication/services.py#L230-L290)

**Edge Cases:**
- **Zero streak**: Handled by returning 0 when no entries exist or last entry is older than yesterday
- **Multiple entries same day**: Only counts as 1 day due to `.distinct()` on dates
- **Timezone considerations**: Uses `timezone.now().date()` to respect user timezone settings
- **New user**: Returns streak of 0, handled gracefully by existing method
- **Long gaps**: Streak correctly resets when consecutive day chain is broken

**Testing Strategy:**
- Unit tests in each phase verify backend logic, template rendering, and streak calculations
- Tests use Django's `TestCase` with `Client` for integration testing
- Follow existing test patterns from [tests/test_home_summary.py](../../tests/test_home_summary.py)
- Use `created_at` manipulation to simulate different date scenarios

**Performance:**
- Streak calculation uses optimized query with `values_list('created_at__date', flat=True).distinct()`
- Query limited to 365 days lookback by default (configurable)
- No N+1 query issues as calculation happens once per page load
- Consider caching if home page traffic becomes significant

**Security:**
- Uses `@login_required` decorator (already in place)
- Streak data is user-scoped via `user=request.user` filter
- No new security concerns introduced

## Success Criteria
- ✓ [Recommended] Daily Streak card visible on home page alongside existing summary cards
- ✓ Streak displays correct count of consecutive days with entries
- ✓ Streak updates immediately after creating a new journal entry
- ✓ Streak shows 0 for new users or when last entry is older than yesterday
- ✓ Streak resets to 1 when user creates entry after missing days
- ✓ Multiple entries on same day count as 1 day in streak
- ✓ Streak card has distinctive styling (pink-red gradient with fire emoji)
- ✓ All tests pass with >90% code coverage for new functionality
- ✓ Responsive layout works on mobile, tablet, and desktop (4-card grid)
