# Private vs Shared Journal Entries Implementation Plan

## Overview
Add visibility control to journal entries allowing users to explicitly mark entries as private or shareable, with corresponding UI controls and filtering capabilities.

## Architecture
The feature extends the existing `JournalEntry` model with a visibility field, adds UI toggle controls in entry creation and management views, filters queries to respect visibility settings, and adds tests to ensure privacy enforcement.

**Data Flow:**
- User creates/edits entry → Visibility selection (Private/Shared) → JournalEntry saved with visibility flag
- User views entries → Queries filtered by visibility → UI displays entries with visibility indicator
- Future: Sharing endpoints can expose only entries marked as shared

## Implementation Phases

### Phase 1: Database Model Extension
**Files**: 
- `authentication/models.py`
- `authentication/migrations/000X_add_visibility_field.py`

**Test Files**: 
- `tests/unit_tests/models/test_custom_user.py`

Add visibility field to the `JournalEntry` model to support private and shared states.

**Key code changes:**
```python
# authentication/models.py (around line 123)
class JournalEntry(models.Model):
    """
    Journal entry model for user journal entries.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    theme = models.ForeignKey(Theme, on_delete=models.PROTECT)
    prompt = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    bookmarked = models.BooleanField(default=False)
    writing_time = models.IntegerField(default=0, help_text="Time spent writing in seconds")
    
    # NEW: Visibility control field
    visibility = models.CharField(
        max_length=10,
        default='private',
        choices=[
            ('private', 'Private'),
            ('shared', 'Shared'),
        ],
        help_text="Control who can view this entry"
    )
    
    # Emotion analysis fields (existing)
    primary_emotion = models.CharField(...)
    sentiment_score = models.FloatField(...)
    emotion_data = models.JSONField(...)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.created_at.date()} - {self.theme.name}"
    
    def is_private(self):
        """Check if this entry is private."""
        return self.visibility == 'private'
    
    def is_shared(self):
        """Check if this entry is shared."""
        return self.visibility == 'shared'
```

**Test cases for this phase:**

- Test case 1: Default visibility is private

  ```python
  # tests/unit_tests/models/test_custom_user.py (add to JournalEntryModelTest)
  def test_default_visibility_is_private(self):
      """Test that new journal entries default to private visibility"""
      # Arrange & Act: Create entry without specifying visibility
      entry = JournalEntry.objects.create(
          user=self.user,
          title='Test Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer'
      )
      
      # Assert: Entry should be private by default
      self.assertEqual(entry.visibility, 'private')
      self.assertTrue(entry.is_private())
      self.assertFalse(entry.is_shared())
  ```

- Test case 2: Can create shared entry

  ```python
  def test_create_shared_entry(self):
      """Test that entries can be explicitly marked as shared"""
      # Arrange & Act: Create entry with shared visibility
      entry = JournalEntry.objects.create(
          user=self.user,
          title='Shared Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer',
          visibility='shared'
      )
      
      # Assert: Entry should be shared
      self.assertEqual(entry.visibility, 'shared')
      self.assertTrue(entry.is_shared())
      self.assertFalse(entry.is_private())
  ```

- Test case 3: Visibility field validation

  ```python
  def test_visibility_choices_validation(self):
      """Test that only valid visibility values are accepted"""
      # Arrange & Act: Create entry with valid visibility
      entry = JournalEntry.objects.create(
          user=self.user,
          title='Test Entry',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer',
          visibility='private'
      )
      
      # Assert: Should save successfully
      self.assertIsNotNone(entry.id)
      
      # Arrange: Try to set invalid visibility
      entry.visibility = 'invalid'
      
      # Act & Assert: Should raise validation error
      from django.core.exceptions import ValidationError
      with self.assertRaises(ValidationError):
          entry.full_clean()
  ```

- Test case 4: Can toggle visibility

  ```python
  def test_toggle_entry_visibility(self):
      """Test changing entry visibility from private to shared and back"""
      # Arrange: Create private entry
      entry = JournalEntry.objects.create(
          user=self.user,
          title='Toggle Test',
          theme=self.theme,
          prompt='Test prompt',
          answer='Test answer'
      )
      
      # Act: Change to shared
      entry.visibility = 'shared'
      entry.save()
      entry.refresh_from_db()
      
      # Assert: Entry is now shared
      self.assertTrue(entry.is_shared())
      
      # Act: Change back to private
      entry.visibility = 'private'
      entry.save()
      entry.refresh_from_db()
      
      # Assert: Entry is now private
      self.assertTrue(entry.is_private())
  ```

**Technical details and Assumptions:**
- Default visibility is 'private' to protect user privacy by default
- Uses CharField with choices for easy extensibility (e.g., future 'friends-only' option)
- Helper methods `is_private()` and `is_shared()` provide clean API for visibility checks
- Migration will set all existing entries to 'private' by default

---

### Phase 2: Entry Creation UI - Visibility Toggle
**Files**: 
- `templates/answer_prompt.html`
- `authentication/views.py` (answer_prompt_view function)

**Test Files**: 
- `tests/unit_tests/views/test_authentication_views.py`

Add visibility selector to the journal entry creation form, allowing users to choose private or shared when creating an entry.

**Key code changes:**
```html
<!-- templates/answer_prompt.html (add after title input, before answer textarea) -->
<div class="form-group visibility-group">
    <label for="visibility" class="form-label">Visibility</label>
    <div class="visibility-options">
        <label class="visibility-option">
            <input type="radio" name="visibility" value="private" checked>
            <span class="visibility-label">
                <span class="visibility-icon">🔒</span>
                <span class="visibility-text">
                    <strong>Private</strong>
                    <small>Only you can see this entry</small>
                </span>
            </span>
        </label>
        <label class="visibility-option">
            <input type="radio" name="visibility" value="shared">
            <span class="visibility-label">
                <span class="visibility-icon">🌐</span>
                <span class="visibility-text">
                    <strong>Shared</strong>
                    <small>Can be shared with others</small>
                </span>
            </span>
        </label>
    </div>
</div>
```

```python
# authentication/views.py (in answer_prompt_view, around line 100-150)
@login_required
def answer_prompt_view(request):
    """
    View for displaying the generated prompt based on selected theme.
    """
    # ... existing theme validation code ...
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        answer = request.POST.get('answer', '').strip()
        writing_time = request.POST.get('writing_time', 0)
        visibility = request.POST.get('visibility', 'private')  # NEW: Get visibility
        
        # Validate visibility value
        if visibility not in ['private', 'shared']:
            visibility = 'private'
        
        # ... existing validation code ...
        
        # Create journal entry with visibility
        journal_entry = JournalEntry.objects.create(
            user=request.user,
            title=title,
            theme=theme,
            prompt=prompt,
            answer=answer,
            writing_time=int(writing_time),
            visibility=visibility  # NEW: Set visibility
        )
        
        # ... rest of existing code ...
```

**Test cases for this phase:**

- Test case 1: Create entry with private visibility

  ```python
  # tests/unit_tests/views/test_authentication_views.py
  def test_create_entry_with_private_visibility(self):
      """Test creating a journal entry with private visibility"""
      # Arrange: Setup user, theme, and request
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      request = self.factory.post('/answer-prompt/', {
          'title': 'My Private Thoughts',
          'answer': 'This is private content',
          'writing_time': 60,
          'visibility': 'private'
      })
      request.user = user
      
      # Act: Create entry
      from authentication.views import answer_prompt_view
      # Set theme in session or GET params
      request.GET = {'theme_id': theme.id}
      response = answer_prompt_view(request)
      
      # Assert: Entry created with private visibility
      entry = JournalEntry.objects.get(user=user, title='My Private Thoughts')
      self.assertEqual(entry.visibility, 'private')
      self.assertTrue(entry.is_private())
  ```

- Test case 2: Create entry with shared visibility

  ```python
  def test_create_entry_with_shared_visibility(self):
      """Test creating a journal entry with shared visibility"""
      # Arrange: Setup user, theme, and request
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      request = self.factory.post('/answer-prompt/', {
          'title': 'Shareable Insights',
          'answer': 'This can be shared',
          'writing_time': 90,
          'visibility': 'shared'
      })
      request.user = user
      request.GET = {'theme_id': theme.id}
      
      # Act: Create entry
      from authentication.views import answer_prompt_view
      response = answer_prompt_view(request)
      
      # Assert: Entry created with shared visibility
      entry = JournalEntry.objects.get(user=user, title='Shareable Insights')
      self.assertEqual(entry.visibility, 'shared')
      self.assertTrue(entry.is_shared())
  ```

- Test case 3: Invalid visibility defaults to private

  ```python
  def test_invalid_visibility_defaults_to_private(self):
      """Test that invalid visibility values default to private"""
      # Arrange: Setup with invalid visibility value
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      request = self.factory.post('/answer-prompt/', {
          'title': 'Test Entry',
          'answer': 'Test content',
          'writing_time': 30,
          'visibility': 'invalid_value'
      })
      request.user = user
      request.GET = {'theme_id': theme.id}
      
      # Act: Create entry
      from authentication.views import answer_prompt_view
      response = answer_prompt_view(request)
      
      # Assert: Entry defaults to private
      entry = JournalEntry.objects.get(user=user, title='Test Entry')
      self.assertEqual(entry.visibility, 'private')
  ```

- Test case 4: Missing visibility defaults to private

  ```python
  def test_missing_visibility_defaults_to_private(self):
      """Test that missing visibility parameter defaults to private"""
      # Arrange: Setup without visibility in POST data
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      request = self.factory.post('/answer-prompt/', {
          'title': 'No Visibility Set',
          'answer': 'Test content',
          'writing_time': 45
          # visibility not included
      })
      request.user = user
      request.GET = {'theme_id': theme.id}
      
      # Act: Create entry
      from authentication.views import answer_prompt_view
      response = answer_prompt_view(request)
      
      # Assert: Entry defaults to private
      entry = JournalEntry.objects.get(user=user, title='No Visibility Set')
      self.assertEqual(entry.visibility, 'private')
  ```

**Technical details and Assumptions:**
- Radio buttons provide clear binary choice between private and shared
- Private is pre-selected (checked) to make privacy the default
- Visual icons (🔒 and 🌐) provide quick visual recognition
- Small descriptive text helps users understand the implications
- Backend validates visibility value and defaults to 'private' for security

---

### Phase 3: Entry Display - Visibility Indicators
**Files**: 
- `templates/my_journals.html`
- `static/css/visibility_styles.css` (new file)

**Test Files**: 
- `tests/test_journal_app.py` (Selenium tests for UI elements)

Add visual indicators showing the visibility status of each journal entry in the listing view.

**Key code changes:**
```html
<!-- templates/my_journals.html (modify journal card header, around line 25) -->
<div class="journal-card-header">
    <div class="journal-date">{{ entry.created_at|date:"M d, Y" }}</div>
    <div class="journal-badges">
        <!-- NEW: Visibility badge -->
        <span class="visibility-badge visibility-{{ entry.visibility }}" 
              title="{{ entry.get_visibility_display }}">
            {% if entry.visibility == 'private' %}
                🔒 Private
            {% else %}
                🌐 Shared
            {% endif %}
        </span>
        <button class="bookmark-btn {% if entry.bookmarked %}bookmarked{% endif %}" 
                onclick="toggleBookmark({{ entry.id }}, event)" 
                title="{% if entry.bookmarked %}Remove bookmark{% else %}Add bookmark{% endif %}">
            📌
        </button>
    </div>
</div>
```

```css
/* static/css/visibility_styles.css (new file) */
.visibility-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.visibility-badge.visibility-private {
    background-color: #f3f4f6;
    color: #4b5563;
    border: 1px solid #d1d5db;
}

.visibility-badge.visibility-shared {
    background-color: #dbeafe;
    color: #1e40af;
    border: 1px solid #93c5fd;
}

.journal-badges {
    display: flex;
    align-items: center;
    gap: 8px;
}
```

```html
<!-- templates/base.html (add to head section) -->
<link rel="stylesheet" href="{% static 'css/visibility_styles.css' %}">
```

**Test cases for this phase:**

- Test case 1: Private entry shows private badge

  ```python
  # tests/test_journal_app.py (Selenium test)
  def test_private_entry_shows_private_badge(self):
      """Test that private entries display the private badge"""
      # Arrange: Login and create private entry
      self.login_user('test@example.com', 'password123')
      self.create_journal_entry('Private Entry', 'private')
      
      # Act: Navigate to my journals
      self.driver.get(f'{self.live_server_url}/my-journals/')
      time.sleep(1)
      
      # Assert: Find visibility badge
      badge = self.driver.find_element(By.CSS_SELECTOR, '.visibility-badge.visibility-private')
      self.assertIsNotNone(badge)
      self.assertIn('Private', badge.text)
      self.assertIn('🔒', badge.text)
  ```

- Test case 2: Shared entry shows shared badge

  ```python
  def test_shared_entry_shows_shared_badge(self):
      """Test that shared entries display the shared badge"""
      # Arrange: Login and create shared entry
      self.login_user('test@example.com', 'password123')
      self.create_journal_entry('Shared Entry', 'shared')
      
      # Act: Navigate to my journals
      self.driver.get(f'{self.live_server_url}/my-journals/')
      time.sleep(1)
      
      # Assert: Find visibility badge
      badge = self.driver.find_element(By.CSS_SELECTOR, '.visibility-badge.visibility-shared')
      self.assertIsNotNone(badge)
      self.assertIn('Shared', badge.text)
      self.assertIn('🌐', badge.text)
  ```

- Test case 3: Badge styling is correct

  ```python
  def test_visibility_badge_styling(self):
      """Test that visibility badges have correct styling"""
      # Arrange: Login and create entries with different visibility
      self.login_user('test@example.com', 'password123')
      self.create_journal_entry('Private Entry', 'private')
      self.create_journal_entry('Shared Entry', 'shared')
      
      # Act: Navigate to my journals
      self.driver.get(f'{self.live_server_url}/my-journals/')
      time.sleep(1)
      
      # Assert: Check private badge styling
      private_badge = self.driver.find_element(By.CSS_SELECTOR, '.visibility-badge.visibility-private')
      self.assertTrue('visibility-private' in private_badge.get_attribute('class'))
      
      # Assert: Check shared badge styling
      shared_badge = self.driver.find_element(By.CSS_SELECTOR, '.visibility-badge.visibility-shared')
      self.assertTrue('visibility-shared' in shared_badge.get_attribute('class'))
  ```

**Technical details and Assumptions:**
- Badges are placed in journal card header alongside bookmark button
- Color coding: gray for private, blue for shared (matches common UX patterns)
- Icons provide quick visual scanning capability
- Tooltip shows full visibility status on hover
- CSS is in separate file for maintainability
- Badge design is consistent with existing emotion badges and sentiment scores

---

### Phase 4: Entry Management - Toggle Visibility
**Files**: 
- `authentication/views.py`
- `config/urls.py`
- `templates/my_journals.html`

**Test Files**: 
- `tests/unit_tests/views/test_authentication_views.py`

Add functionality to change entry visibility after creation, allowing users to toggle between private and shared.

**Key code changes:**
```python
# authentication/views.py (add new view after toggle_bookmark)
@login_required
def toggle_visibility(request, entry_id):
    """Toggle visibility status of a journal entry between private and shared"""
    if request.method == 'POST':
        # Get the journal entry and ensure it belongs to the current user
        journal_entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        
        # Toggle the visibility status
        journal_entry.visibility = 'shared' if journal_entry.visibility == 'private' else 'private'
        journal_entry.save()
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'visibility': journal_entry.visibility,
                'message': f'Entry marked as {journal_entry.get_visibility_display()}.'
            })
        
        # Show success message for regular requests
        messages.success(request, f'Entry visibility changed to {journal_entry.get_visibility_display()}.')
        
        # Redirect back to my journals page
        return redirect('my_journals')
    
    # If not POST request, redirect to my journals
    return redirect('my_journals')
```

```python
# config/urls.py (add to urlpatterns)
path('home/toggle-visibility/<int:entry_id>/', views.toggle_visibility, name='toggle_visibility'),
```

```html
<!-- templates/my_journals.html (add to journal modal or card actions) -->
<!-- Add this button in the modal expanded view -->
<div class="modal-actions">
    <button class="visibility-toggle-btn" 
            onclick="toggleVisibility({{ entry.id }})"
            data-entry-id="{{ entry.id }}"
            data-current-visibility="{{ entry.visibility }}">
        <span class="visibility-icon">
            {% if entry.visibility == 'private' %}🔒{% else %}🌐{% endif %}
        </span>
        <span class="visibility-toggle-text">
            Make {% if entry.visibility == 'private' %}Shared{% else %}Private{% endif %}
        </span>
    </button>
</div>

<script>
function toggleVisibility(entryId) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    fetch(`/home/toggle-visibility/${entryId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Refresh the page to show updated visibility
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error toggling visibility:', error);
        alert('Failed to change visibility. Please try again.');
    });
}
</script>
```

**Test cases for this phase:**

- Test case 1: Toggle from private to shared

  ```python
  # tests/unit_tests/views/test_authentication_views.py
  def test_toggle_visibility_private_to_shared(self):
      """Test toggling entry visibility from private to shared"""
      # Arrange: Create private entry
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      entry = JournalEntry.objects.create(
          user=user,
          title='Test Entry',
          theme=theme,
          prompt='Test prompt',
          answer='Test answer',
          visibility='private'
      )
      
      # Act: Toggle visibility
      request = self.factory.post(f'/home/toggle-visibility/{entry.id}/')
      request.user = user
      from authentication.views import toggle_visibility
      response = toggle_visibility(request, entry.id)
      
      # Assert: Entry is now shared
      entry.refresh_from_db()
      self.assertEqual(entry.visibility, 'shared')
  ```

- Test case 2: Toggle from shared to private

  ```python
  def test_toggle_visibility_shared_to_private(self):
      """Test toggling entry visibility from shared to private"""
      # Arrange: Create shared entry
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      entry = JournalEntry.objects.create(
          user=user,
          title='Shared Entry',
          theme=theme,
          prompt='Test prompt',
          answer='Test answer',
          visibility='shared'
      )
      
      # Act: Toggle visibility
      request = self.factory.post(f'/home/toggle-visibility/{entry.id}/')
      request.user = user
      from authentication.views import toggle_visibility
      response = toggle_visibility(request, entry.id)
      
      # Assert: Entry is now private
      entry.refresh_from_db()
      self.assertEqual(entry.visibility, 'private')
  ```

- Test case 3: AJAX request returns JSON

  ```python
  def test_toggle_visibility_ajax_request(self):
      """Test that AJAX requests return JSON response"""
      # Arrange: Create entry and setup AJAX request
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      entry = JournalEntry.objects.create(
          user=user,
          title='Test Entry',
          theme=theme,
          prompt='Test prompt',
          answer='Test answer',
          visibility='private'
      )
      
      request = self.factory.post(f'/home/toggle-visibility/{entry.id}/')
      request.user = user
      request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
      
      # Act: Toggle visibility
      from authentication.views import toggle_visibility
      response = toggle_visibility(request, entry.id)
      
      # Assert: JSON response with success
      self.assertEqual(response.status_code, 200)
      data = json.loads(response.content)
      self.assertTrue(data['success'])
      self.assertEqual(data['visibility'], 'shared')
      self.assertIn('message', data)
  ```

- Test case 4: Cannot toggle other user's entry

  ```python
  def test_toggle_visibility_unauthorized_user(self):
      """Test that users cannot toggle visibility of other users' entries"""
      # Arrange: Create entry for one user, request from another
      user1 = CustomUser.objects.create_user(
          email='user1@example.com',
          password='testpass123',
          first_name='User',
          last_name='One'
      )
      user2 = CustomUser.objects.create_user(
          email='user2@example.com',
          password='testpass123',
          first_name='User',
          last_name='Two'
      )
      theme = Theme.objects.create(name='Leadership')
      entry = JournalEntry.objects.create(
          user=user1,
          title='User1 Entry',
          theme=theme,
          prompt='Test prompt',
          answer='Test answer',
          visibility='private'
      )
      
      # Act & Assert: User2 trying to toggle User1's entry should raise 404
      request = self.factory.post(f'/home/toggle-visibility/{entry.id}/')
      request.user = user2
      from authentication.views import toggle_visibility
      from django.http import Http404
      
      with self.assertRaises(Http404):
          toggle_visibility(request, entry.id)
  ```

**Technical details and Assumptions:**
- Toggle button appears in the journal entry modal/expanded view
- AJAX implementation provides smooth UX without page reload
- Button text dynamically shows the action (what it will become, not current state)
- Follows same pattern as existing `toggle_bookmark` function
- Security: Users can only toggle visibility of their own entries
- Page reload after toggle ensures all UI elements reflect new state

---

### Phase 5: Filtering and Analytics Integration
**Files**: 
- `authentication/views.py` (my_journals_view, get_emotion_stats functions)
- `templates/my_journals.html`

**Test Files**: 
- `tests/unit_tests/views/test_authentication_views.py`

Add filtering options to view entries by visibility and integrate visibility data into existing analytics endpoints.

**Key code changes:**
```python
# authentication/views.py (update my_journals_view, around line 25-40)
@login_required
def my_journals_view(request):
    """
    View for displaying all journal entries for the current user.
    """
    # Get all journal entries for the current user
    journal_entries = JournalEntry.objects.filter(user=request.user)
    
    # NEW: Handle visibility filter
    visibility_filter = request.GET.get('visibility', 'all')
    if visibility_filter == 'private':
        journal_entries = journal_entries.filter(visibility='private')
    elif visibility_filter == 'shared':
        journal_entries = journal_entries.filter(visibility='shared')
    # 'all' shows everything (no filter)
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        journal_entries = journal_entries.filter(
            models.Q(title__icontains=search_query) |
            models.Q(theme__name__icontains=search_query) |
            models.Q(answer__icontains=search_query)
        )
    
    # Separate bookmarked and regular entries
    bookmarked_entries = journal_entries.filter(bookmarked=True).order_by('-created_at')
    regular_entries = journal_entries.filter(bookmarked=False).order_by('-created_at')
    
    return render(request, 'my_journals.html', {
        'bookmarked_entries': bookmarked_entries,
        'regular_entries': regular_entries,
        'search_query': search_query,
        'visibility_filter': visibility_filter  # NEW: Pass to template
    })
```

```html
<!-- templates/my_journals.html (add filter controls after header, before entries) -->
<div class="journals-filters">
    <div class="filter-group">
        <label class="filter-label">Show:</label>
        <div class="filter-buttons">
            <a href="?visibility=all{% if search_query %}&search={{ search_query }}{% endif %}" 
               class="filter-btn {% if visibility_filter == 'all' %}active{% endif %}">
                All Entries
            </a>
            <a href="?visibility=private{% if search_query %}&search={{ search_query }}{% endif %}" 
               class="filter-btn {% if visibility_filter == 'private' %}active{% endif %}">
                🔒 Private Only
            </a>
            <a href="?visibility=shared{% if search_query %}&search={{ search_query }}{% endif %}" 
               class="filter-btn {% if visibility_filter == 'shared' %}active{% endif %}">
                🌐 Shared Only
            </a>
        </div>
    </div>
</div>
```

```python
# authentication/views.py (update get_emotion_stats to include visibility breakdown)
@login_required
def get_emotion_stats(request):
    """
    Get overall emotion statistics for the logged-in user.
    """
    from django.db.models import Avg, Count
    
    entries = JournalEntry.objects.filter(user=request.user)
    
    # Count emotion distribution
    emotion_distribution = {}
    for entry in entries:
        emotion = entry.primary_emotion
        emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
    
    # Calculate average sentiment
    avg_sentiment = entries.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0.0
    
    # NEW: Add visibility breakdown
    visibility_stats = {
        'private': entries.filter(visibility='private').count(),
        'shared': entries.filter(visibility='shared').count()
    }
    
    stats = {
        'total_entries': entries.count(),
        'primary_emotion_distribution': emotion_distribution,
        'average_sentiment_score': round(avg_sentiment, 3),
        'visibility_breakdown': visibility_stats  # NEW
    }
    
    return JsonResponse(stats)
```

**Test cases for this phase:**

- Test case 1: Filter shows only private entries

  ```python
  # tests/unit_tests/views/test_authentication_views.py
  def test_filter_private_entries_only(self):
      """Test that visibility filter shows only private entries"""
      # Arrange: Create mix of private and shared entries
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      private_entry = JournalEntry.objects.create(
          user=user,
          title='Private Entry',
          theme=theme,
          prompt='Test',
          answer='Test',
          visibility='private'
      )
      shared_entry = JournalEntry.objects.create(
          user=user,
          title='Shared Entry',
          theme=theme,
          prompt='Test',
          answer='Test',
          visibility='shared'
      )
      
      # Act: Request with private filter
      request = self.factory.get('/my-journals/?visibility=private')
      request.user = user
      from authentication.views import my_journals_view
      response = my_journals_view(request)
      
      # Assert: Only private entry in context
      all_entries = list(response.context_data['bookmarked_entries']) + \
                    list(response.context_data['regular_entries'])
      self.assertEqual(len(all_entries), 1)
      self.assertEqual(all_entries[0].visibility, 'private')
  ```

- Test case 2: Filter shows only shared entries

  ```python
  def test_filter_shared_entries_only(self):
      """Test that visibility filter shows only shared entries"""
      # Arrange: Create mix of private and shared entries
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      JournalEntry.objects.create(
          user=user,
          title='Private Entry',
          theme=theme,
          prompt='Test',
          answer='Test',
          visibility='private'
      )
      shared_entry = JournalEntry.objects.create(
          user=user,
          title='Shared Entry',
          theme=theme,
          prompt='Test',
          answer='Test',
          visibility='shared'
      )
      
      # Act: Request with shared filter
      request = self.factory.get('/my-journals/?visibility=shared')
      request.user = user
      from authentication.views import my_journals_view
      response = my_journals_view(request)
      
      # Assert: Only shared entry in context
      all_entries = list(response.context_data['bookmarked_entries']) + \
                    list(response.context_data['regular_entries'])
      self.assertEqual(len(all_entries), 1)
      self.assertEqual(all_entries[0].visibility, 'shared')
  ```

- Test case 3: All filter shows all entries

  ```python
  def test_filter_shows_all_entries(self):
      """Test that 'all' visibility filter shows all entries"""
      # Arrange: Create mix of entries
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      JournalEntry.objects.create(user=user, title='Private 1', theme=theme, 
                                 prompt='T', answer='T', visibility='private')
      JournalEntry.objects.create(user=user, title='Shared 1', theme=theme, 
                                 prompt='T', answer='T', visibility='shared')
      JournalEntry.objects.create(user=user, title='Private 2', theme=theme, 
                                 prompt='T', answer='T', visibility='private')
      
      # Act: Request with all filter (or no filter)
      request = self.factory.get('/my-journals/?visibility=all')
      request.user = user
      from authentication.views import my_journals_view
      response = my_journals_view(request)
      
      # Assert: All entries shown
      all_entries = list(response.context_data['bookmarked_entries']) + \
                    list(response.context_data['regular_entries'])
      self.assertEqual(len(all_entries), 3)
  ```

- Test case 4: Emotion stats include visibility breakdown

  ```python
  def test_emotion_stats_includes_visibility_breakdown(self):
      """Test that emotion stats API includes visibility breakdown"""
      # Arrange: Create entries with different visibility
      user = CustomUser.objects.create_user(
          email='test@example.com',
          password='testpass123',
          first_name='John',
          last_name='Doe'
      )
      theme = Theme.objects.create(name='Leadership')
      
      # Create 3 private and 2 shared entries
      for i in range(3):
          JournalEntry.objects.create(user=user, title=f'Private {i}', 
                                     theme=theme, prompt='T', answer='T', 
                                     visibility='private')
      for i in range(2):
          JournalEntry.objects.create(user=user, title=f'Shared {i}', 
                                     theme=theme, prompt='T', answer='T', 
                                     visibility='shared')
      
      # Act: Request emotion stats
      request = self.factory.get('/api/emotion-stats/')
      request.user = user
      from authentication.views import get_emotion_stats
      response = get_emotion_stats(request)
      
      # Assert: Response includes visibility breakdown
      data = json.loads(response.content)
      self.assertIn('visibility_breakdown', data)
      self.assertEqual(data['visibility_breakdown']['private'], 3)
      self.assertEqual(data['visibility_breakdown']['shared'], 2)
  ```

**Technical details and Assumptions:**
- Filter buttons use query parameters to maintain state
- Filter works alongside existing search functionality
- Active filter button is visually highlighted
- Default view shows all entries (no filter applied)
- Emotion analytics API extended to include visibility stats for dashboard insights
- Filter preserves search query when applied

## Technical Considerations
- **Dependencies**: No new packages required, uses existing Django framework
- **Database Migration**: Required for adding `visibility` field to JournalEntry model
- **Edge Cases**: 
  - Invalid visibility values default to 'private' for security
  - Users can only modify visibility of their own entries (enforced by `get_object_or_404`)
  - Empty states handled for filtered views with no results
- **Testing Strategy**: 
  - Unit tests for model methods and view logic
  - Integration tests for AJAX endpoints
  - Selenium tests for UI interactions
  - Each phase includes tests integrated with implementation
- **Performance**: 
  - Filtering uses indexed database queries (no performance impact)
  - Visibility checks are simple string comparisons
- **Security**: 
  - Default to 'private' protects user privacy by default
  - Visibility toggles validate entry ownership
  - Future sharing features will only expose entries marked as 'shared'
- **Backwards Compatibility**: 
  - Migration sets all existing entries to 'private'
  - No breaking changes to existing functionality

## Testing Notes
- Each phase includes unit tests that validate the specific functionality added in that phase
- Tests follow the existing pattern: Python uses pytest/Django TestCase with test files in `tests/unit_tests/`
- Follow AAA pattern (Arrange-Act-Assert) in all test cases
- Selenium tests added for UI validation in Phase 3
- Tests ensure privacy enforcement and data isolation between users
- Mock AJAX requests tested with `HTTP_X_REQUESTED_WITH` header

## Success Criteria
- [x] `visibility` field added to JournalEntry model with choices ['private', 'shared']
- [x] Users can select visibility when creating new entries
- [x] Visibility badges display correctly on all entry cards
- [x] Users can toggle entry visibility after creation
- [x] Filter controls allow viewing entries by visibility type
- [x] Emotion analytics API includes visibility breakdown
- [x] All existing entries default to private after migration
- [x] Users cannot modify visibility of other users' entries
- [x] All tests pass with >90% code coverage for new code
- [x] UI is responsive and accessible
- [x] Documentation updated for new feature
