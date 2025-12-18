# Quick Add Journal Entry Implementation Plan

## Overview
Add a floating Quick Add “+” on the home screen that opens a lightweight modal to capture a journal title and body, persists it via a minimal endpoint, and takes the user to My Journals with the new entry visible at the top.

## Architecture
Home page adds a fixed-position FAB that triggers a modal. Modal submits via `fetch` to a new authenticated JSON endpoint (Django view) that builds a minimal `JournalEntry` using a default/fallback theme and a generated prompt. On success, client redirects to `my_journals` with a `highlight` query parameter; My Journals view uses the existing `-created_at` ordering so the new entry appears first and optionally applies a short highlight state. Signals continue to run (emotion analysis + versioning) without extra work.

## Implementation Phases

### Phase 1: Backend Quick-Add Endpoint & Defaults
**Files**: `authentication/views.py`, `config/urls.py`, `authentication/tests.py` (or new `tests/unit_tests/views/test_quick_add_entry.py`)  
**Test Files**: `tests/unit_tests/views/test_quick_add_entry.py`

- [ ] Add helper to resolve a default theme: reuse existing theme if present else create "Quick Add" ✓ [Recommended] to avoid null theme errors.
- [ ] Implement `quick_add_entry` view (POST, JSON) that requires `title` and `body`, sets `prompt` to a static string (e.g., "Quick add entry"), `answer` to body, `theme` from helper, and `writing_time` = 0; returns JSON `{id, title, created_at}`.
- [ ] Wire route under `config/urls.py` (e.g., `/home/api/journals/quick-add/`), require login, and validate CSRF for fetch requests.
- [ ] Ensure failure responses return HTTP 400 with error messages for missing fields and 403 for unauthenticated.

**Key code changes:**
```python
# authentication/views.py
@login_required
@require_http_methods(["POST"])
def quick_add_entry(request):
    payload = json.loads(request.body or "{}")
    title = payload.get("title", "").strip()
    body = payload.get("body", "").strip()
    if not title or not body:
        return JsonResponse({"success": False, "errors": {"title": "Title and body are required."}}, status=400)
    theme = _get_quick_add_theme(request.user)
    entry = JournalEntry.objects.create(
        user=request.user,
        title=title,
        prompt="Quick add entry",
        answer=body,
        theme=theme,
        writing_time=0,
        visibility="private",
    )
    return JsonResponse({"success": True, "entry": {"id": entry.id, "title": entry.title, "created_at": entry.created_at.isoformat()}})
```

**Test cases for this phase:**

- Test case 1: Successful quick add returns 200/JSON and creates entry for authenticated user.
  ```python
  def test_quick_add_creates_entry(client, django_user_model):
      user = django_user_model.objects.create_user(email="u@test.com", password="pw", first_name="U", last_name="T")
      client.force_login(user)
      resp = client.post("/home/api/journals/quick-add/", data=json.dumps({"title": "T", "body": "B"}), content_type="application/json")
      assert resp.status_code == 200
      data = resp.json()
      assert data["success"] is True
      assert JournalEntry.objects.filter(user=user, title="T").exists()
  ```

- Test case 2: Missing fields yield 400 with error payload.
  ```python
  def test_quick_add_requires_title_and_body(client, django_user_model):
      user = django_user_model.objects.create_user(email="u@test.com", password="pw", first_name="U", last_name="T")
      client.force_login(user)
      resp = client.post("/home/api/journals/quick-add/", data=json.dumps({"title": ""}), content_type="application/json")
      assert resp.status_code == 400
      assert resp.json()["success"] is False
  ```

- Test case 3: Default theme helper creates/fetches fallback theme.
  ```python
  def test_quick_add_uses_default_theme(client, django_user_model):
      user = django_user_model.objects.create_user(email="u@test.com", password="pw", first_name="U", last_name="T")
      client.force_login(user)
      client.post("/home/api/journals/quick-add/", data=json.dumps({"title": "T", "body": "B"}), content_type="application/json")
      entry = JournalEntry.objects.get(user=user, title="T")
      assert entry.theme.name == "Quick Add"
  ```

**Technical details and Assumptions (if any):**
- ✓ [Recommended] Create/get a per-user-agnostic default theme named "Quick Add" to avoid theme selector dependency.
- CSRF protection via standard Django token; fetch must include `X-CSRFToken` header.
- Signals already handle emotion analysis and versioning; no extra hooks needed.

### Phase 2: Home FAB + Modal UI
**Files**: `templates/home.html`, `static/css/style.css`, `templates/base.html` (only if extra script hooks are required)  
**Test Files**: `tests/pages/home_page.py`, `tests/test_journal_app.py`

- [ ] Add floating "+" button (positioned bottom-right) visible on home for authenticated users.
- [ ] Insert minimal modal markup in home template with fields for Title and Body, inline validation messages, and submit/cancel controls.
- [ ] Add JS to open/close modal, capture CSRF, send POST to `/home/api/journals/quick-add/`, handle loading/error states, and on success redirect to My Journals with `?highlight=<id>` ✓ [Recommended] to immediately show the new entry at the top.
- [ ] Extend CSS for FAB, modal overlay, buttons, and success/error states while matching existing design tokens.

**Key code changes:**
```html
<!-- templates/home.html -->
<button id="quick-add-btn" class="fab" aria-label="Quick add journal">+</button>
<div id="quickAddModal" class="quick-modal" hidden>
  <form id="quickAddForm">
    <input name="title" placeholder="Title" required>
    <textarea name="body" placeholder="Write something..." required></textarea>
    <button type="submit">Save</button>
    <button type="button" id="quickAddCancel">Cancel</button>
  </form>
</div>
<script>
  // fetch to /home/api/journals/quick-add/ then window.location = `/home/my-journals/?highlight=${entry.id}`
</script>
```

**Test cases for this phase:**

- Test case 1: UI smoke — FAB renders on home and opens modal.
  ```python
  def test_quick_add_modal_opens(home_page):
      assert home_page.is_quick_add_button_present()
      home_page.click_quick_add_button()
      assert home_page.is_quick_add_modal_visible()
  ```

- Test case 2: End-to-end — submit quick add populates My Journals top entry.
  ```python
  def test_quick_add_creates_entry_and_redirects(home_page, my_journals_page, auth_user):
      home_page.open_quick_add_modal()
      home_page.fill_quick_add_form(title="Today", body="Notes")
      home_page.submit_quick_add_form()
      my_journals_page.wait_for_highlighted_entry()
      assert my_journals_page.first_entry_title() == "Today"
  ```

**Technical details and Assumptions (if any):**
- Redirect flow keeps implementation simple and guarantees visibility order; dynamic DOM injection is optional.
- FAB should not conflict with existing dashboard buttons; ensure responsive behavior on mobile.

### Phase 3: My Journals Highlight & UX Polish
**Files**: `authentication/views.py`, `templates/my_journals.html`, `static/css/style.css`, `tests/pages/my_journals_page.py`  
**Test Files**: `tests/pages/my_journals_page.py`, `tests/test_journal_app.py`

- [ ] Accept optional `highlight` query param in `my_journals_view` context to identify the newly created entry.
- [ ] Render data attribute/class on matching journal card, scroll into view on load, and add a temporary highlight style ✓ [Recommended] for immediate visibility.
- [ ] Ensure ordering remains `-created_at` so new entries naturally appear first; guard against visibility/tag filters hiding the fresh entry by defaulting filters to `all` when `highlight` is present.
- [ ] Update page object to detect highlighted card and first-card title helper.

**Key code changes:**
```html
<!-- templates/my_journals.html -->
<div class="journal-card {% if highlight_id == entry.id %}newly-added{% endif %}" data-entry-id="{{ entry.id }}">
  ...
</div>
<script>
  document.addEventListener('DOMContentLoaded', () => {
    const highlighted = document.querySelector('.newly-added');
    if (highlighted) highlighted.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
</script>
```

**Test cases for this phase:**

- Test case 1: Highlight flag marks the new entry.
  ```python
  def test_highlight_class_applied(client, auth_user, journal_entry_factory):
      entry = journal_entry_factory(user=auth_user)
      resp = client.get(f"/home/my-journals/?highlight={entry.id}")
      assert "newly-added" in resp.content.decode()
  ```

- Test case 2: First card after quick add matches new title.
  ```python
  def test_new_entry_is_first(my_journals_page, created_entries):
      titles = my_journals_page.get_first_card_title()
      assert titles == created_entries[0].title
  ```

**Technical details and Assumptions (if any):**
- Highlight should auto-clear on reload; class can be transient via JS timeout.
- Filters default to `all` when highlight present to avoid hiding the new entry.

## Technical Considerations
- **Dependencies**: None new; rely on existing Django, CSRF middleware, and signals.
- **Edge Cases**: Missing title/body, invalid JSON payloads, lack of themes (handled via default), filters hiding highlighted entry, mobile viewport overlap with FAB.
- **Testing Strategy**: Unit tests for view validation; integration/e2e via Selenium page objects to cover UI open, submit, redirect, and highlight behaviors.
- **Performance**: Single insert and redirect; negligible impact. Use JSON responses to avoid rendering overhead.
- **Security**: Auth-required endpoint with CSRF; sanitize input via `.strip()` and rely on Django ORM escaping.

## Testing Notes
- Each phase introduces tests alongside code. Use Django test client for backend validation and existing Selenium page objects for UI/regression coverage. Keep fixtures minimal and reuse page object helpers for modal interactions.

## Success Criteria
- [ ] Quick Add endpoint creates journal entries with default theme and validation.
- [ ] Home FAB + modal submits successfully and redirects to My Journals.
- [ ] Newly created entry appears first and is visibly highlighted on My Journals after save.
