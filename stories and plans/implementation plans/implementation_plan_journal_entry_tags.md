# Journal Entry Tags (Many-to-Many) Implementation Plan

## Overview
Add user-scoped tags and a many-to-many relationship so each `JournalEntry` can have multiple tags. Provide UI to assign tags on create and filter journals by tag.

## Architecture
- Data: `Tag` model (owned by `CustomUser`) with `name` and `slug`; `JournalEntry.tags` as `ManyToManyField(Tag)`.
- Views: Extend `answer_prompt_view` to accept tags; extend `my_journals_view` to filter by `tag` (slug) and list user tags for quick filtering.
- Templates: Add tags input (comma-separated) to `answer_prompt.html`; display tag chips on entry cards; add tag filter controls on `my_journals.html`.
- Admin: Register `Tag` for management.

✓ [Recommended] Make tags user-scoped with unique `(user, slug)` to avoid cross-user collisions and preserve privacy. This matches how entries are user-specific (see authentication/models.py `JournalEntry`).

✓ [Recommended] Use a `slug` for filtering (stable in URLs) and derive it from `name` (`django.utils.text.slugify`). Names may include spaces/case; slugs ensure clean links.

## Implementation Phases

### Phase 1: Data Model & Migration
**Files**: `authentication/models.py`, `authentication/admin.py`, `authentication/migrations/`  
**Test Files**: `tests/unit_tests/models/test_tags.py`

Introduce `Tag` and add a many-to-many field on `JournalEntry`.

**Key code changes:**
```python
# authentication/models.py
from django.utils.text import slugify

class Tag(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60)

    class Meta:
        unique_together = ('user', 'slug')
        indexes = [
            models.Index(fields=['user', 'slug']),
            models.Index(fields=['user', 'name']),
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

# Extend existing JournalEntry (~authentication/models.py: class JournalEntry)
class JournalEntry(models.Model):
    # ... existing fields ...
    tags = models.ManyToManyField('Tag', related_name='entries', blank=True)
    # ...
```

```python
# authentication/admin.py
from .models import CustomUser, Theme, JournalEntry, Tag
admin.site.register(Tag)
```

**Test cases for this phase:**
- Test case 1: Create `Tag` for a user; slug auto-generates and uniqueness enforced per user.

  ```python
  # tests/unit_tests/models/test_tags.py
  from django.test import TestCase
  from authentication.models import CustomUser, Tag

  class TagModelTests(TestCase):
      def setUp(self):
          self.user = CustomUser.objects.create_user(email='u@example.com', password='x', first_name='U', last_name='S')

      def test_slug_auto_generation_and_uniqueness(self):
          t1 = Tag.objects.create(user=self.user, name='Work Notes')
          self.assertEqual(t1.slug, 'work-notes')
          with self.assertRaises(Exception):
              Tag.objects.create(user=self.user, name='Work Notes')

      def test_same_name_allowed_for_different_users(self):
          other = CustomUser.objects.create_user(email='o@example.com', password='x', first_name='O', last_name='T')
          Tag.objects.create(user=self.user, name='Ideas')
          Tag.objects.create(user=other, name='Ideas')  # should not raise
  ```

- Test case 2: Attach multiple tags to a `JournalEntry`; retrieval via `entry.tags.all()` and reverse via `tag.entries.all()` works.

  ```python
  from authentication.models import JournalEntry, Theme

  class JournalEntryTagRelationTests(TestCase):
      def setUp(self):
          self.user = CustomUser.objects.create_user(email='u2@example.com', password='x', first_name='U2', last_name='S2')
          self.theme = Theme.objects.create(name='Tech', description='Tech theme')

      def test_attach_and_reverse_lookup(self):
          entry = JournalEntry.objects.create(user=self.user, title='T', theme=self.theme, prompt='p', answer='a')
          t1 = Tag.objects.create(user=self.user, name='Work')
          t2 = Tag.objects.create(user=self.user, name='Personal')
          entry.tags.add(t1, t2)
          self.assertEqual({t.name for t in entry.tags.all()}, {'Work', 'Personal'})
          self.assertEqual(tag_entries_count(t1), 1)

      def tag_entries_count(self, tag):
          return tag.entries.filter(user=self.user).count()
  ```

**Technical details and Assumptions (if any):**
- Tags are immutable enough to rely on slug; if a tag name changes, slug remains the same unless reset manually (acceptable for MVP).
- Use `blank=True` on `JournalEntry.tags` to keep existing flows working without tags.

### Phase 2: Entry Creation — Assign Tags
**Files**: `authentication/views.py`, `templates/answer_prompt.html`  
**Test Files**: `tests/unit_tests/views/test_tag_entry_creation.py`

Add a tags input to the create form. Parse comma-separated tags on POST, `get_or_create` per user, and attach to the new entry.

**Key code changes:**
```python
# authentication/views.py (within answer_prompt_view)
from .models import Tag

if request.method == 'POST':
    # ... existing fields ...
    tags_raw = request.POST.get('tags', '')
    # validate visibility etc.
    # after creating journal_entry
    journal_entry = JournalEntry.objects.create(
        user=request.user,
        theme=theme,
        title=title,
        prompt=prompt,
        answer=answer,
        bookmarked=False,
        writing_time=int(writing_time) if writing_time else 0,
        visibility=visibility,
    )
    tags = []
    for name in [t.strip() for t in tags_raw.split(',') if t.strip()]:
        slug = slugify(name)
        tag, _ = Tag.objects.get_or_create(user=request.user, slug=slug, defaults={'name': name})
        tags.append(tag)
    if tags:
        journal_entry.tags.add(*tags)
```

```html
<!-- templates/answer_prompt.html -->
<div class="form-group">
  <label for="tags" class="form-label">Tags (comma-separated)</label>
  <input type="text" id="tags" name="tags" class="form-control" placeholder="e.g., Work, Personal, Ideas" value="">
</div>
```

**Test cases for this phase:**
- Test case 1: Posting with `tags="Work, Personal"` creates tags (if missing) and associates both to the new entry.

  ```python
  from django.test import TestCase
  from django.urls import reverse
  from authentication.models import CustomUser, Theme, JournalEntry, Tag

  class EntryCreationTagsTests(TestCase):
      def setUp(self):
          self.user = CustomUser.objects.create_user(email='u@example.com', password='x', first_name='U', last_name='S')
          self.client.login(username='u@example.com', password='x')
          self.theme = Theme.objects.create(name='Tech', description='')

      def test_tags_created_and_attached(self):
          url = reverse('answer_prompt') + f'?theme_id={self.theme.id}'
          resp = self.client.post(url, data={
              'prompt': 'p', 'title': 't', 'answer': 'a', 'visibility': 'private', 'tags': 'Work, Personal'
          })
          self.assertEqual(resp.status_code, 302)
          entry = JournalEntry.objects.get(title='t')
          self.assertEqual({t.name for t in entry.tags.all()}, {'Work', 'Personal'})
          self.assertEqual(Tag.objects.filter(user=self.user, name='Work').count(), 1)
  ```

- Test case 2: Duplicate or whitespace-only tags are ignored; existing tags reused.

  ```python
  def test_duplicate_and_whitespace_handling(self):
      url = reverse('answer_prompt') + f'?theme_id={self.theme.id}'
      Tag.objects.create(user=self.user, name='ideas', slug='ideas')
      self.client.post(url, data={'prompt': 'p', 'title': 't2', 'answer': 'a', 'visibility': 'private', 'tags': 'Ideas, , ideas '})
      entry = JournalEntry.objects.get(title='t2')
      self.assertEqual([t.slug for t in entry.tags.all()], ['ideas'])
  ```

**Technical details and Assumptions (if any):**
- Tags optional; empty string results in no changes.
- Case-insensitive semantics achieved via slug normalization.

### Phase 3: Listing & Filtering by Tag
**Files**: `authentication/views.py`, `templates/my_journals.html`, `templates/base.html`  
**Test Files**: `tests/unit_tests/views/test_tag_filtering.py`

Add tag filter support and render tag chips.

**Key code changes:**
```python
# authentication/views.py (within my_journals_view)
from .models import Tag

journal_entries = JournalEntry.objects.filter(user=request.user)

# existing visibility filter ...

# new: tag filter by slug
selected_tag = request.GET.get('tag')
if selected_tag:
    journal_entries = journal_entries.filter(tags__slug=selected_tag)

# existing search ... (kept)

# Build user tag list with counts for the sidebar/filter
user_tags = (
    Tag.objects.filter(user=request.user)
       .annotate(entry_count=models.Count('entries'))
       .order_by('name')
)

return render(request, 'my_journals.html', {
    'bookmarked_entries': bookmarked_entries,
    'regular_entries': regular_entries,
    'search_query': search_query,
    'visibility_filter': visibility_filter,
    'tags': user_tags,
    'selected_tag': selected_tag,
})
```

```html
<!-- templates/my_journals.html (filters section) -->
<div class="filter-group">
  <label class="filter-label">Tags:</label>
  <div class="filter-buttons">
    <a href="?visibility={{ visibility_filter }}{% if search_query %}&search={{ search_query }}{% endif %}"
       class="filter-btn {% if not selected_tag %}active{% endif %}">All Tags</a>
    {% for tag in tags %}
      <a href="?visibility={{ visibility_filter }}{% if search_query %}&search={{ search_query }}{% endif %}&tag={{ tag.slug }}"
         class="filter-btn {% if selected_tag == tag.slug %}active{% endif %}">
        {{ tag.name }} ({{ tag.entry_count }})
      </a>
    {% endfor %}
  </div>
</div>

<!-- Display tags on each card (bookmarked and regular entries) -->
<div class="journal-detail">
  <span class="detail-label">Tags:</span>
  <span class="detail-value">
    {% for tag in entry.tags.all %}
      <span class="tag-chip">{{ tag.name }}</span>
    {% empty %}
      <span class="tag-chip muted">None</span>
    {% endfor %}
  </span>
</div>
```

**Test cases for this phase:**
- Test case 1: Filtering by a tag slug returns only entries having that tag (both bookmarked and regular lists reflect this).

  ```python
  from django.urls import reverse
  from django.test import TestCase
  from authentication.models import CustomUser, Theme, JournalEntry, Tag

  class TagFilterViewTests(TestCase):
      def setUp(self):
          self.user = CustomUser.objects.create_user(email='u@example.com', password='x', first_name='U', last_name='S')
          self.client.login(username='u@example.com', password='x')
          self.theme = Theme.objects.create(name='Tech', description='')
          self.work = Tag.objects.create(user=self.user, name='Work', slug='work')
          self.personal = Tag.objects.create(user=self.user, name='Personal', slug='personal')
          e1 = JournalEntry.objects.create(user=self.user, title='A', theme=self.theme, prompt='p', answer='a', bookmarked=True)
          e2 = JournalEntry.objects.create(user=self.user, title='B', theme=self.theme, prompt='p', answer='a', bookmarked=False)
          e1.tags.add(self.work)
          e2.tags.add(self.personal)

      def test_filter_by_work_tag(self):
          url = reverse('my_journals') + '?tag=work'
          resp = self.client.get(url)
          self.assertEqual(resp.status_code, 200)
          # Only entries with Work tag
          bookmarked = list(resp.context['bookmarked_entries'])
          regular = list(resp.context['regular_entries'])
          self.assertTrue(all('work' in [t.slug for t in e.tags.all()] for e in bookmarked + regular))
  ```

- Test case 2: Combining search/visibility with tag filter works (intersection of filters).

  ```python
  def test_filter_combination(self):
      # Create another shared entry with Work tag
      e3 = JournalEntry.objects.create(user=self.user, title='Work Report', theme=self.theme, prompt='p', answer='a', visibility='shared')
      e3.tags.add(self.work)
      url = reverse('my_journals') + '?tag=work&search=Report&visibility=shared'
      resp = self.client.get(url)
      self.assertEqual(resp.status_code, 200)
      entries = list(resp.context['bookmarked_entries']) + list(resp.context['regular_entries'])
      self.assertEqual(len(entries), 1)
      self.assertEqual(entries[0].title, 'Work Report')
  ```

**Technical details and Assumptions (if any):**
- Filtering by slug avoids issues with spaces/case.
- Tag list displayed only on My Journals page.

### Phase 4: Admin & Optional Serializer Enhancement
**Files**: `authentication/admin.py`, `authentication/serializers.py`  
**Test Files**: `tests/unit_tests/serializers/test_optional_tag_serialization.py` (optional)

Register tags in admin. Optionally, include tags in emotion serializer if needed by front-end (kept off by default to avoid breaking existing tests).

**Key code changes:**
```python
# authentication/serializers.py (optional, only if consumers expect tags)
# def serialize_journal_entry_emotion(entry):
#     return {
#         # ... existing fields ...
#         'tags': [t.name for t in entry.tags.all()],
#     }
```

**Test cases for this phase (optional):**
- Serializer includes `tags` array when enabled.

## Technical Considerations
- **Dependencies**: None beyond Django (already present). Use `slugify` from `django.utils.text`.
- **Edge Cases**: Duplicate names map to same slug; enforce uniqueness per user. Empty/whitespace tags ignored. Very long tag names truncated via field max_length.
- **Testing Strategy**: Unit tests for model/relationship; request tests for creation and filtering; avoid modifying existing behavior.
- **Performance**: Add indexes on `(user, slug)` and `(user, name)`; annotate counts efficiently.
- **Security**: Tags scoped per user; filtering only within `request.user` entries prevents data leakage.

## Testing Notes
- Each phase includes its own unit tests as part of the implementation.
- Prefer creating users and logging in via client where views are tested.
- Validate combinations of filters to match existing `my_journals_view` behavior.

## Success Criteria
- [ ] `Tag` model added with user scope and slug uniqueness
- [ ] `JournalEntry.tags` many-to-many field with migrations
- [ ] Tags can be added on entry creation via UI and stored
- [ ] My Journals page filters entries by tag and shows tag chips
- [ ] Tests pass for model, creation flow, and filtering
