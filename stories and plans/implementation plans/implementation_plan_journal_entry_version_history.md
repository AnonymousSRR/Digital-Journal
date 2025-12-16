# Journal Entry Version History Implementation Plan

## Overview
Add comprehensive version history tracking for journal entries so every edit creates a new version. Users can view a timeline of all versions, compare two versions side-by-side, restore any previous version, and optionally export a version as PDF.

## Architecture
- **Data**: Create `JournalEntryVersion` model to store snapshots of each entry state with timestamp, changes metadata, and user who made the edit.
- **Tracking**: Create a signal on `JournalEntry` post-save to automatically create version records when content changes.
- **Views**: Add views for version timeline, version comparison, version restore, and PDF export.
- **API**: Expose JSON endpoints for version timeline, diff operations, and restore actions.
- **Frontend**: Add a "Version History" tab to the entry detail view with timeline visualization, compare modal, and restore confirmation.

✓ [Recommended] Use Django signals (`post_save`) to capture version history automatically rather than manual API calls. This matches the pattern of emotion analysis tagging in the codebase (see `authentication/signals.py`).

✓ [Recommended] Store full snapshots in `JournalEntryVersion` rather than diffs for reliability and simplicity. Version snapshots are relatively small and provide complete audit trail.

✓ [Recommended] Use `reportlab` for PDF export (common Python library for PDF generation). If not already in requirements, add it alongside existing export functionality.

## Implementation Phases

### Phase 1: Data Model & Version Capture Infrastructure
**Files**: `authentication/models.py`, `authentication/signals.py`, `authentication/migrations/`  
**Test Files**: `tests/unit_tests/models/test_version_history.py`

Create `JournalEntryVersion` model and set up signal-based automatic versioning.

**Key code changes:**
```python
# authentication/models.py - Add JournalEntryVersion model before JournalEntry class

class JournalEntryVersion(models.Model):
    """
    Stores version snapshots of journal entries for history tracking.
    Each edit creates a new version record with full content snapshot.
    """
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField()  # Sequential version counter per entry
    
    # Snapshot of entry content at this version
    title = models.CharField(max_length=200)
    answer = models.TextField()
    theme = models.ForeignKey(Theme, on_delete=models.SET_NULL, null=True)
    prompt = models.TextField()
    visibility = models.CharField(
        max_length=10,
        choices=[('private', 'Private'), ('shared', 'Shared')],
        default='private'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)  # When this version was created
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_versions')
    
    # Change tracking
    change_summary = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable description of what changed (e.g., 'Title and answer updated')"
    )
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ('entry', 'version_number')
        indexes = [
            models.Index(fields=['entry', '-version_number']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.entry.title} - v{self.version_number}"
    
    def is_original(self):
        """Check if this is the original version (v1)."""
        return self.version_number == 1
    
    def is_current(self):
        """Check if this is the current/latest version."""
        return self.version_number == self.entry.versions.latest('version_number').version_number


# Extend existing JournalEntry class (~authentication/models.py: class JournalEntry)
class JournalEntry(models.Model):
    # ... existing fields ...
    last_modified_at = models.DateTimeField(auto_now=True)  # Track last modification
    
    class Meta:
        ordering = ['-created_at']
    
    def get_current_version(self):
        """Get the latest version of this entry."""
        return self.versions.latest('version_number')
    
    def get_version(self, version_number):
        """Get a specific version by number."""
        return self.versions.get(version_number=version_number)
    
    def version_count(self):
        """Get total number of versions."""
        return self.versions.count()
```

```python
# authentication/signals.py - Create new file with version tracking signal

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JournalEntry, JournalEntryVersion
from django.utils.text import slugify

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
        change_summary = "Entry created"
    else:
        # Get the current version count to determine next version number
        current_count = instance.versions.count()
        version_number = current_count + 1
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
        change_summary=change_summary
    )


# Register signal
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        import authentication.signals
```

Update `authentication/apps.py`:
```python
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    
    def ready(self):
        import authentication.signals
```

**Test cases for this phase:**

- Test case 1: When a `JournalEntry` is created, automatically create version 1.

  ```python
  # tests/unit_tests/models/test_version_history.py
  from django.test import TestCase
  from authentication.models import CustomUser, JournalEntry, Theme, JournalEntryVersion
  
  class VersionHistoryModelTests(TestCase):
      def setUp(self):
          self.user = CustomUser.objects.create_user(
              email='v@example.com',
              password='x',
              first_name='V',
              last_name='U'
          )
          self.theme = Theme.objects.create(name='Tech', description='Tech theme')
      
      def test_version_created_on_entry_creation(self):
          """Test that v1 is automatically created when JournalEntry is created"""
          entry = JournalEntry.objects.create(
              user=self.user,
              title='Test Entry',
              theme=self.theme,
              prompt='A prompt',
              answer='My answer'
          )
          
          # Verify version was created
          self.assertEqual(entry.versions.count(), 1)
          version = entry.versions.first()
          self.assertEqual(version.version_number, 1)
          self.assertEqual(version.title, 'Test Entry')
          self.assertEqual(version.answer, 'My answer')
          self.assertTrue(version.is_original())
  ```

- Test case 2: When a `JournalEntry` is updated, a new version is created with incremented version_number.

  ```python
  def test_version_created_on_entry_update(self):
      """Test that a new version is created when JournalEntry is updated"""
      entry = JournalEntry.objects.create(
          user=self.user,
          title='Original Title',
          theme=self.theme,
          prompt='A prompt',
          answer='Original answer'
      )
      
      # Update the entry
      entry.title = 'Updated Title'
      entry.answer = 'Updated answer'
      entry.save()
      
      # Verify versions
      self.assertEqual(entry.versions.count(), 2)
      v1 = entry.get_version(1)
      v2 = entry.get_version(2)
      
      self.assertEqual(v1.title, 'Original Title')
      self.assertEqual(v2.title, 'Updated Title')
      self.assertEqual(v2.version_number, 2)
  ```

- Test case 3: Version records are ordered by version number descending.

  ```python
  def test_version_ordering_and_latest(self):
      """Test that versions are properly ordered and latest version is accessible"""
      entry = JournalEntry.objects.create(
          user=self.user,
          title='T1',
          theme=self.theme,
          prompt='p',
          answer='a1'
      )
      
      for i in range(2, 5):
          entry.answer = f'a{i}'
          entry.save()
      
      # Check order
      versions = list(entry.versions.all())
      self.assertEqual(versions[0].version_number, 4)  # Latest first
      self.assertEqual(versions[3].version_number, 1)  # Oldest last
      
      # Check latest retrieval
      current = entry.get_current_version()
      self.assertEqual(current.version_number, 4)
  ```

**Technical details and Assumptions:**
- Signal-based approach requires proper signal registration in `apps.py`.
- Version creation happens within the same transaction as the entry save.
- `change_summary` can be enhanced in future phases to detect specific field changes.
- Versions inherit theme by reference (FK) to preserve theme information; set null if theme is deleted.

---

### Phase 2: Version Timeline & Comparison Views
**Files**: `authentication/views.py`, `authentication/urls.py`, `templates/`  
**Test Files**: `tests/unit_tests/views/test_version_history_views.py`

Add views for viewing version timeline and comparing two versions.

**Key code changes:**
```python
# authentication/views.py - Add new view functions

from django.utils.safestring import mark_safe
from difflib import unified_diff
import json

@login_required
def entry_version_history(request, entry_id):
    """
    Display timeline of all versions for a journal entry.
    Shows version list with metadata and links to view/compare/restore.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    versions = entry.versions.all().order_by('-version_number')
    
    context = {
        'entry': entry,
        'versions': versions,
        'page_title': f'Version History - {entry.title}'
    }
    return render(request, 'authentication/entry_version_history.html', context)


@login_required
def view_version(request, entry_id, version_number):
    """
    Display a specific version of a journal entry.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    version = get_object_or_404(entry.versions, version_number=version_number)
    
    # Check if this is the current version
    is_current = version.is_current()
    
    context = {
        'entry': entry,
        'version': version,
        'is_current': is_current,
        'page_title': f'{entry.title} - Version {version_number}'
    }
    return render(request, 'authentication/view_version.html', context)


@login_required
def compare_versions(request, entry_id):
    """
    Compare two versions of a journal entry side-by-side.
    Query params: v1=version_number, v2=version_number
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    v1_num = request.GET.get('v1')
    v2_num = request.GET.get('v2')
    
    if not v1_num or not v2_num:
        messages.error(request, 'Please select two versions to compare.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    try:
        v1 = get_object_or_404(entry.versions, version_number=int(v1_num))
        v2 = get_object_or_404(entry.versions, version_number=int(v2_num))
    except (ValueError, Http404):
        messages.error(request, 'One or both versions not found.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    # Generate text diff for answer field
    v1_lines = v1.answer.splitlines(keepends=True)
    v2_lines = v2.answer.splitlines(keepends=True)
    diff_lines = list(unified_diff(v1_lines, v2_lines, lineterm=''))
    
    # Prepare comparison data
    comparison = {
        'v1': v1,
        'v2': v2,
        'title_changed': v1.title != v2.title,
        'prompt_changed': v1.prompt != v2.prompt,
        'answer_changed': v1.answer != v2.answer,
        'diff': diff_lines,
    }
    
    context = {
        'entry': entry,
        'comparison': comparison,
        'page_title': f'Compare Versions {v1_num} & {v2_num}'
    }
    return render(request, 'authentication/compare_versions.html', context)


@login_required
def api_version_timeline(request, entry_id):
    """
    API endpoint: Get JSON timeline of all versions for an entry.
    Response: [
        {
            'version_number': 3,
            'created_at': '2025-01-15T10:30:00Z',
            'created_by': 'user@example.com',
            'change_summary': 'Title updated',
            'title': 'Entry Title',
            'is_current': true
        },
        ...
    ]
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    versions = entry.versions.all().order_by('-version_number')
    
    data = [
        {
            'version_number': v.version_number,
            'created_at': v.created_at.isoformat(),
            'created_by': v.created_by.email if v.created_by else 'System',
            'change_summary': v.change_summary,
            'title': v.title,
            'is_current': v.is_current()
        }
        for v in versions
    ]
    
    return JsonResponse({'versions': data, 'entry_id': entry_id})


@login_required
def api_version_diff(request, entry_id):
    """
    API endpoint: Get unified diff between two versions.
    Query params: v1=version_number, v2=version_number
    Response: {
        'v1': {...version_data...},
        'v2': {...version_data...},
        'diff': [...diff_lines...],
        'title_changed': bool,
        'answer_changed': bool
    }
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    v1_num = request.GET.get('v1')
    v2_num = request.GET.get('v2')
    
    if not v1_num or not v2_num:
        return JsonResponse({'error': 'Missing v1 or v2 parameter'}, status=400)
    
    try:
        v1 = get_object_or_404(entry.versions, version_number=int(v1_num))
        v2 = get_object_or_404(entry.versions, version_number=int(v2_num))
    except ValueError:
        return JsonResponse({'error': 'Invalid version number'}, status=400)
    
    # Generate diff
    v1_lines = v1.answer.splitlines(keepends=True)
    v2_lines = v2.answer.splitlines(keepends=True)
    diff_lines = list(unified_diff(v1_lines, v2_lines, lineterm=''))
    
    data = {
        'v1': {'version_number': v1.version_number, 'title': v1.title, 'created_at': v1.created_at.isoformat()},
        'v2': {'version_number': v2.version_number, 'title': v2.title, 'created_at': v2.created_at.isoformat()},
        'diff': diff_lines,
        'title_changed': v1.title != v2.title,
        'answer_changed': v1.answer != v2.answer,
        'prompt_changed': v1.prompt != v2.prompt
    }
    
    return JsonResponse(data)
```

Update URLs:
```python
# authentication/urls.py - Add version history routes

urlpatterns = [
    # ... existing paths ...
    path('entry/<int:entry_id>/versions/', views.entry_version_history, name='entry_version_history'),
    path('entry/<int:entry_id>/version/<int:version_number>/', views.view_version, name='view_version'),
    path('entry/<int:entry_id>/compare/', views.compare_versions, name='compare_versions'),
    path('api/entry/<int:entry_id>/versions/', views.api_version_timeline, name='api_version_timeline'),
    path('api/entry/<int:entry_id>/diff/', views.api_version_diff, name='api_version_diff'),
]
```

**Test cases for this phase:**

- Test case 1: Version history view returns all versions for an entry with proper context.

  ```python
  # tests/unit_tests/views/test_version_history_views.py
  from django.test import TestCase, Client
  from django.urls import reverse
  from authentication.models import CustomUser, JournalEntry, Theme
  
  class VersionHistoryViewTests(TestCase):
      def setUp(self):
          self.client = Client()
          self.user = CustomUser.objects.create_user(
              email='vh@example.com',
              password='pass',
              first_name='VH',
              last_name='User'
          )
          self.theme = Theme.objects.create(name='Reflection')
          self.entry = JournalEntry.objects.create(
              user=self.user,
              title='Test Entry',
              theme=self.theme,
              prompt='Reflect',
              answer='Original'
          )
          # Create additional versions
          for i in range(2, 4):
              self.entry.answer = f'Version {i}'
              self.entry.save()
      
      def test_entry_version_history_view_requires_login(self):
          """Test that version history view requires authentication"""
          response = self.client.get(
              reverse('authentication:entry_version_history', args=[self.entry.id])
          )
          self.assertEqual(response.status_code, 302)  # Redirect to login
      
      def test_entry_version_history_view_shows_all_versions(self):
          """Test that version history displays all versions"""
          self.client.login(email='vh@example.com', password='pass')
          response = self.client.get(
              reverse('authentication:entry_version_history', args=[self.entry.id])
          )
          
          self.assertEqual(response.status_code, 200)
          self.assertEqual(len(response.context['versions']), 3)
          self.assertContains(response, 'Version History')
      
      def test_entry_version_history_forbids_other_users(self):
          """Test that users cannot view version history of other users' entries"""
          other_user = CustomUser.objects.create_user(
              email='other@example.com',
              password='pass',
              first_name='O',
              last_name='U'
          )
          self.client.login(email='other@example.com', password='pass')
          response = self.client.get(
              reverse('authentication:entry_version_history', args=[self.entry.id])
          )
          self.assertEqual(response.status_code, 404)
  ```

- Test case 2: Compare versions view returns diff and comparison data.

  ```python
  def test_compare_versions_returns_diff(self):
      """Test that compare view returns diff between two versions"""
      self.client.login(email='vh@example.com', password='pass')
      response = self.client.get(
          reverse('authentication:compare_versions', args=[self.entry.id]),
          {'v1': 1, 'v2': 2}
      )
      
      self.assertEqual(response.status_code, 200)
      comparison = response.context['comparison']
      self.assertTrue(comparison['answer_changed'])
      self.assertEqual(comparison['v1'].version_number, 1)
      self.assertEqual(comparison['v2'].version_number, 2)
  ```

- Test case 3: API endpoint returns JSON timeline.

  ```python
  def test_api_version_timeline_returns_json(self):
      """Test that API endpoint returns JSON version timeline"""
      self.client.login(email='vh@example.com', password='pass')
      response = self.client.get(
          reverse('authentication:api_version_timeline', args=[self.entry.id])
      )
      
      self.assertEqual(response.status_code, 200)
      data = response.json()
      self.assertEqual(len(data['versions']), 3)
      self.assertTrue(data['versions'][0]['is_current'])
  ```

**Technical details and Assumptions:**
- Version comparison uses Python's `difflib.unified_diff` for clean text diffs.
- API endpoints return JSON for flexible frontend integration.
- Views enforce user ownership via `get_object_or_404` with `user=request.user`.

---

### Phase 3: Restore Version & Edit History Tracking
**Files**: `authentication/views.py`, `authentication/models.py`  
**Test Files**: `tests/unit_tests/views/test_version_restore.py`

Add functionality to restore previous versions and track edit metadata.

**Key code changes:**
```python
# authentication/models.py - Extend JournalEntryVersion to track edit source

class JournalEntryVersion(models.Model):
    # ... existing fields ...
    
    # NEW: Track what triggered this version
    edit_source = models.CharField(
        max_length=20,
        choices=[
            ('initial', 'Initial Creation'),
            ('edit', 'Manual Edit'),
            ('restore', 'Restored from Version'),
        ],
        default='initial'
    )
    restored_from_version = models.IntegerField(
        null=True,
        blank=True,
        help_text="If edit_source='restore', the version number that was restored"
    )


# authentication/views.py - Add restore function

@login_required
def restore_version(request, entry_id, version_number):
    """
    Restore a journal entry to a previous version.
    Creates a new version with the content from the specified version.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    source_version = get_object_or_404(entry.versions, version_number=version_number)
    
    if request.method == 'POST':
        try:
            # Update entry with content from source version
            entry.title = source_version.title
            entry.answer = source_version.answer
            entry.prompt = source_version.prompt
            entry.theme = source_version.theme
            entry.visibility = source_version.visibility
            entry.save()
            
            # Update the newly created version to mark it as a restore
            latest_version = entry.get_current_version()
            latest_version.edit_source = 'restore'
            latest_version.restored_from_version = version_number
            latest_version.change_summary = f'Restored from version {version_number}'
            latest_version.save()
            
            messages.success(
                request,
                f'Entry restored to version {version_number} successfully. '
                f'A new version has been created.'
            )
            return redirect('authentication:entry_version_history', entry_id=entry_id)
        
        except Exception as e:
            messages.error(request, f'Error restoring version: {str(e)}')
            return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    # GET request: show confirmation page
    context = {
        'entry': entry,
        'source_version': source_version,
        'page_title': f'Restore to Version {version_number}?'
    }
    return render(request, 'authentication/confirm_restore_version.html', context)


@login_required
def api_restore_version(request, entry_id, version_number):
    """
    API endpoint: Restore version (POST request).
    Response: {'success': true, 'new_version_number': N, 'message': '...'}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    source_version = get_object_or_404(entry.versions, version_number=version_number)
    
    try:
        # Restore content
        entry.title = source_version.title
        entry.answer = source_version.answer
        entry.prompt = source_version.prompt
        entry.theme = source_version.theme
        entry.visibility = source_version.visibility
        entry.save()
        
        # Mark the new version as restore
        latest_version = entry.get_current_version()
        latest_version.edit_source = 'restore'
        latest_version.restored_from_version = version_number
        latest_version.change_summary = f'Restored from version {version_number}'
        latest_version.save()
        
        return JsonResponse({
            'success': True,
            'new_version_number': latest_version.version_number,
            'message': f'Version {version_number} restored successfully.'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

Update signals to track edit source:
```python
# authentication/signals.py - Update signal to track edit_source

@receiver(post_save, sender=JournalEntry)
def create_journal_entry_version(sender, instance, created, **kwargs):
    """
    Automatically create a version record whenever a JournalEntry is saved.
    """
    if created:
        version_number = 1
        edit_source = 'initial'
        change_summary = "Entry created"
    else:
        current_count = instance.versions.count()
        version_number = current_count + 1
        edit_source = 'edit'
        change_summary = "Entry updated"
    
    JournalEntryVersion.objects.create(
        entry=instance,
        version_number=version_number,
        title=instance.title,
        answer=instance.answer,
        theme=instance.theme,
        prompt=instance.prompt,
        visibility=instance.visibility,
        created_by=instance.user,
        edit_source=edit_source,  # NEW
        change_summary=change_summary
    )
```

Update URLs:
```python
# authentication/urls.py

urlpatterns = [
    # ... existing paths ...
    path('entry/<int:entry_id>/version/<int:version_number>/restore/', views.restore_version, name='restore_version'),
    path('api/entry/<int:entry_id>/version/<int:version_number>/restore/', views.api_restore_version, name='api_restore_version'),
]
```

**Test cases for this phase:**

- Test case 1: Restoring a version creates a new version marked as "restore".

  ```python
  # tests/unit_tests/views/test_version_restore.py
  from django.test import TestCase, Client
  from django.urls import reverse
  from authentication.models import CustomUser, JournalEntry, Theme, JournalEntryVersion
  
  class VersionRestoreTests(TestCase):
      def setUp(self):
          self.client = Client()
          self.user = CustomUser.objects.create_user(
              email='restore@example.com',
              password='pass',
              first_name='R',
              last_name='U'
          )
          self.theme = Theme.objects.create(name='Reflection')
          self.entry = JournalEntry.objects.create(
              user=self.user,
              title='Entry Title',
              theme=self.theme,
              prompt='Prompt',
              answer='Version 1'
          )
          # Create v2
          self.entry.answer = 'Version 2'
          self.entry.save()
          # Create v3
          self.entry.answer = 'Version 3'
          self.entry.save()
      
      def test_restore_version_creates_new_version(self):
          """Test that restoring a version creates a new version marked as restore"""
          self.client.login(email='restore@example.com', password='pass')
          
          # Restore v1
          response = self.client.post(
              reverse('authentication:restore_version', args=[self.entry.id, 1])
          )
          
          # Reload entry
          self.entry.refresh_from_db()
          
          # Should now have v4 (the restore)
          self.assertEqual(self.entry.version_count(), 4)
          v4 = self.entry.get_current_version()
          self.assertEqual(v4.version_number, 4)
          self.assertEqual(v4.edit_source, 'restore')
          self.assertEqual(v4.restored_from_version, 1)
          # Content should match v1
          self.assertEqual(v4.answer, 'Version 1')
  ```

- Test case 2: Restore forbidden for other users' entries.

  ```python
  def test_restore_forbids_other_users(self):
      """Test that users cannot restore versions of other users' entries"""
      other_user = CustomUser.objects.create_user(
          email='other_restore@example.com',
          password='pass',
          first_name='O',
          last_name='R'
      )
      self.client.login(email='other_restore@example.com', password='pass')
      response = self.client.post(
          reverse('authentication:restore_version', args=[self.entry.id, 1])
      )
      self.assertEqual(response.status_code, 404)
  ```

- Test case 3: API endpoint for restore returns JSON response.

  ```python
  def test_api_restore_version_returns_json(self):
      """Test that API restore endpoint returns JSON"""
      self.client.login(email='restore@example.com', password='pass')
      response = self.client.post(
          reverse('authentication:api_restore_version', args=[self.entry.id, 1])
      )
      
      self.assertEqual(response.status_code, 200)
      data = response.json()
      self.assertTrue(data['success'])
      self.assertEqual(data['new_version_number'], 4)
  ```

**Technical details and Assumptions:**
- Restore creates a NEW version (snapshot) rather than modifying existing versions.
- The `edit_source` field tracks the type of edit (initial, manual, or restore).
- Restores maintain full audit trail; users can see what was restored and when.

---

### Phase 4: PDF Export for Versions
**Files**: `authentication/views.py`, `requirements.txt`  
**Test Files**: `tests/unit_tests/views/test_version_pdf_export.py`

Add PDF export capability for individual versions and version comparisons.

**Key code changes:**

Update requirements.txt:
```plaintext
# In requirements.txt, add:
reportlab==4.0.9
```

```python
# authentication/views.py - Add PDF export functions

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime
from io import BytesIO

@login_required
def export_version_pdf(request, entry_id, version_number):
    """
    Export a specific version as PDF.
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    version = get_object_or_404(entry.versions, version_number=version_number)
    
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title and metadata
    story.append(Paragraph(f"<b>{version.title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    # Version info
    metadata = f"""
    <b>Entry ID:</b> {entry.id}<br/>
    <b>Version:</b> {version.version_number} of {entry.version_count()}<br/>
    <b>Created:</b> {version.created_at.strftime('%B %d, %Y at %I:%M %p')}<br/>
    <b>Theme:</b> {version.theme.name if version.theme else 'N/A'}<br/>
    <b>Visibility:</b> {version.get_visibility_display()}<br/>
    <b>Edit Source:</b> {version.get_edit_source_display()}
    """
    story.append(Paragraph(metadata, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Prompt section
    if version.prompt:
        story.append(Paragraph("<b>Prompt:</b>", styles['Heading3']))
        story.append(Paragraph(version.prompt, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Answer section
    story.append(Paragraph("<b>Response:</b>", styles['Heading3']))
    story.append(Paragraph(version.answer, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer with export info
    footer = f"<i>Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
    story.append(Paragraph(footer, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return as response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{slugify(version.title)}_v{version.version_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def export_version_comparison_pdf(request, entry_id):
    """
    Export a comparison of two versions as PDF.
    Query params: v1=version_number, v2=version_number
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    
    v1_num = request.GET.get('v1')
    v2_num = request.GET.get('v2')
    
    if not v1_num or not v2_num:
        messages.error(request, 'Please specify v1 and v2 query parameters.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    try:
        v1 = get_object_or_404(entry.versions, version_number=int(v1_num))
        v2 = get_object_or_404(entry.versions, version_number=int(v2_num))
    except ValueError:
        messages.error(request, 'Invalid version number.')
        return redirect('authentication:entry_version_history', entry_id=entry_id)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(f"<b>Version Comparison: {entry.title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    # Comparison summary
    summary = f"""
    <b>Comparing Version {v1.version_number} vs Version {v2.version_number}</b><br/>
    <b>Title Changed:</b> {'Yes' if v1.title != v2.title else 'No'}<br/>
    <b>Content Changed:</b> {'Yes' if v1.answer != v2.answer else 'No'}
    """
    story.append(Paragraph(summary, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Version 1 section
    story.append(Paragraph(f"<b>Version {v1.version_number}</b> ({v1.created_at.strftime('%b %d, %Y')})", styles['Heading3']))
    story.append(Paragraph(f"Title: {v1.title}", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(v1.answer, styles['Normal']))
    story.append(PageBreak())
    
    # Version 2 section
    story.append(Paragraph(f"<b>Version {v2.version_number}</b> ({v2.created_at.strftime('%b %d, %Y')})", styles['Heading3']))
    story.append(Paragraph(f"Title: {v2.title}", styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(v2.answer, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = f"<i>Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>"
    story.append(Paragraph(footer, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return as response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{slugify(entry.title)}_v{v1.version_number}_vs_v{v2.version_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def api_export_version_pdf(request, entry_id, version_number):
    """
    API endpoint: Export version as PDF (returns file stream).
    """
    entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
    version = get_object_or_404(entry.versions, version_number=version_number)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"<b>{version.title}</b>", styles['Heading1']))
    story.append(Spacer(1, 0.2*inch))
    
    metadata = f"<b>Version {version.version_number}</b> | {version.created_at.strftime('%B %d, %Y')}"
    story.append(Paragraph(metadata, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph(version.answer, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"{slugify(version.title)}_v{version.version_number}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
```

Update URLs:
```python
# authentication/urls.py

urlpatterns = [
    # ... existing paths ...
    path('entry/<int:entry_id>/version/<int:version_number>/export-pdf/', views.export_version_pdf, name='export_version_pdf'),
    path('entry/<int:entry_id>/compare-pdf/', views.export_version_comparison_pdf, name='export_version_comparison_pdf'),
    path('api/entry/<int:entry_id>/version/<int:version_number>/export-pdf/', views.api_export_version_pdf, name='api_export_version_pdf'),
]
```

**Test cases for this phase:**

- Test case 1: PDF export for a version returns PDF response.

  ```python
  # tests/unit_tests/views/test_version_pdf_export.py
  from django.test import TestCase, Client
  from django.urls import reverse
  from authentication.models import CustomUser, JournalEntry, Theme
  
  class VersionPDFExportTests(TestCase):
      def setUp(self):
          self.client = Client()
          self.user = CustomUser.objects.create_user(
              email='pdf@example.com',
              password='pass',
              first_name='PDF',
              last_name='Test'
          )
          self.theme = Theme.objects.create(name='Reflection')
          self.entry = JournalEntry.objects.create(
              user=self.user,
              title='PDF Test Entry',
              theme=self.theme,
              prompt='Prompt text',
              answer='Answer text'
          )
      
      def test_export_version_pdf_returns_pdf(self):
          """Test that PDF export returns PDF file"""
          self.client.login(email='pdf@example.com', password='pass')
          response = self.client.get(
              reverse('authentication:export_version_pdf', args=[self.entry.id, 1])
          )
          
          self.assertEqual(response.status_code, 200)
          self.assertEqual(response['Content-Type'], 'application/pdf')
          self.assertTrue(response['Content-Disposition'].startswith('attachment'))
  ```

- Test case 2: PDF export for comparison of two versions.

  ```python
  def test_export_version_comparison_pdf(self):
      """Test that comparison PDF is generated correctly"""
      # Create v2
      self.entry.answer = 'Updated answer'
      self.entry.save()
      
      self.client.login(email='pdf@example.com', password='pass')
      response = self.client.get(
          reverse('authentication:export_version_comparison_pdf', args=[self.entry.id]),
          {'v1': 1, 'v2': 2}
      )
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response['Content-Type'], 'application/pdf')
  ```

- Test case 3: PDF export forbidden for other users' entries.

  ```python
  def test_pdf_export_forbids_other_users(self):
      """Test that users cannot export PDFs of other users' entries"""
      other_user = CustomUser.objects.create_user(
          email='other_pdf@example.com',
          password='pass',
          first_name='O',
          last_name='P'
      )
      self.client.login(email='other_pdf@example.com', password='pass')
      response = self.client.get(
          reverse('authentication:export_version_pdf', args=[self.entry.id, 1])
      )
      self.assertEqual(response.status_code, 404)
  ```

**Technical details and Assumptions:**
- `reportlab` library provides PDF generation.
- PDFs include version metadata (created date, theme, visibility, etc.).
- Filename is slugified entry title for readability.
- Comparison PDFs include both versions on separate pages for easy review.

---

## Technical Considerations

- **Dependencies**: Add `reportlab==4.0.9` to requirements.txt for PDF generation.
- **Database Indexing**: `JournalEntryVersion` includes indexes on `(entry, -version_number)` and `created_at` for fast queries.
- **Signal Performance**: Version creation via signal is synchronous but lightweight (single DB insert).
- **Storage**: Version snapshots are full content copies. For very long entries, consider compression in future iterations.
- **Concurrency**: Version numbering is sequential per entry; Django transaction handling ensures no duplicates.
- **Security**: All views enforce user ownership; no cross-user access possible.

## Testing Notes

- Each phase includes comprehensive unit tests covering happy paths, edge cases, and permission checks.
- Tests use Django's `TestCase` for transaction management and test database isolation.
- API endpoints tested with JSON response validation.
- PDF export tested for content-type and attachment headers.
- Permission tests ensure users cannot access other users' entries or versions.

## Success Criteria

- [ ] Phase 1: Automatic version creation on entry save; version model stores complete snapshots.
- [ ] Phase 1: All version tracking tests pass (creation, updates, ordering).
- [ ] Phase 2: Timeline view displays all versions with metadata; comparison shows unified diff.
- [ ] Phase 2: API endpoints return valid JSON for timeline and diff data.
- [ ] Phase 2: All view tests pass with proper permission enforcement.
- [ ] Phase 3: Users can restore previous versions; new version created with "restore" source.
- [ ] Phase 3: Restore tests verify version chain integrity and proper metadata.
- [ ] Phase 4: PDF export generates valid PDF files with proper formatting.
- [ ] Phase 4: PDF comparison export includes both versions for side-by-side review.
- [ ] All phases: No regressions in existing functionality; edit operations work as before.
- [ ] Performance: Version queries complete in < 200ms even with 100+ versions per entry.
