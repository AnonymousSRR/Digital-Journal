"""
Unit tests for quick add journal entry endpoint.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, JournalEntry, Theme


class TestQuickAddEntry(TestCase):
    """Test suite for quick add entry endpoint."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email="testuser@test.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.client.force_login(self.user)
        self.url = reverse('quick_add_entry')
    
    def test_quick_add_creates_entry(self):
        """Test that quick add successfully creates a journal entry."""
        payload = {"title": "Quick Test", "body": "Test body content"}
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("entry", data)
        self.assertEqual(data["entry"]["title"], "Quick Test")
        
        # Verify entry was created in database
        entry = JournalEntry.objects.filter(user=self.user, title="Quick Test").first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.answer, "Test body content")
        self.assertEqual(entry.prompt, "Quick add entry")
        self.assertEqual(entry.writing_time, 0)
        self.assertEqual(entry.visibility, "private")
    
    def test_quick_add_requires_title_and_body(self):
        """Test that missing title or body returns 400 error."""
        # Missing body
        response = self.client.post(
            self.url,
            data=json.dumps({"title": "Test"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        
        # Missing title
        response = self.client.post(
            self.url,
            data=json.dumps({"body": "Test body"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        
        # Empty strings
        response = self.client.post(
            self.url,
            data=json.dumps({"title": "", "body": ""}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
    
    def test_quick_add_uses_default_theme(self):
        """Test that quick add creates or uses a default 'Quick Add' theme."""
        payload = {"title": "Theme Test", "body": "Testing theme"}
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify the entry has the Quick Add theme
        entry = JournalEntry.objects.get(user=self.user, title="Theme Test")
        self.assertIsNotNone(entry.theme)
        self.assertEqual(entry.theme.name, "Quick Add")
        
        # Verify theme exists in database
        theme = Theme.objects.filter(name="Quick Add").first()
        self.assertIsNotNone(theme)
    
    def test_quick_add_requires_authentication(self):
        """Test that unauthenticated requests are rejected."""
        client = Client()
        payload = {"title": "Test", "body": "Body"}
        
        response = client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json"
        )
        
        # Should redirect to login (302)
        self.assertEqual(response.status_code, 302)
    
    def test_quick_add_invalid_json(self):
        """Test that invalid JSON returns 400 error."""
        response = self.client.post(
            self.url,
            data="invalid json{",
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("errors", data)
    
    def test_quick_add_only_accepts_post(self):
        """Test that only POST method is allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        
        response = self.client.put(
            self.url,
            data=json.dumps({"title": "Test", "body": "Body"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 405)


class TestMyJournalsHighlight(TestCase):
    """Test suite for My Journals highlight functionality."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email="testuser@test.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.client.force_login(self.user)
        
        # Create a theme
        self.theme = Theme.objects.create(name="Test Theme")
        
        # Create test entries
        self.entry1 = JournalEntry.objects.create(
            user=self.user,
            title="Entry 1",
            prompt="Test prompt",
            answer="Test answer 1",
            theme=self.theme
        )
        self.entry2 = JournalEntry.objects.create(
            user=self.user,
            title="Entry 2",
            prompt="Test prompt",
            answer="Test answer 2",
            theme=self.theme
        )
    
    def test_highlight_parameter_passed_to_template(self):
        """Test that highlight parameter is passed to template context."""
        url = reverse('my_journals')
        response = self.client.get(f"{url}?highlight={self.entry1.id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['highlight_id'], self.entry1.id)
    
    def test_highlight_class_applied_to_correct_entry(self):
        """Test that newly-added class is applied to highlighted entry."""
        url = reverse('my_journals')
        response = self.client.get(f"{url}?highlight={self.entry1.id}")
        
        content = response.content.decode()
        self.assertIn('newly-added', content)
        # Verify it appears with the correct entry
        self.assertIn(f'data-entry-id="{self.entry1.id}"', content)
    
    def test_highlight_with_invalid_id(self):
        """Test that invalid highlight ID doesn't break the view."""
        url = reverse('my_journals')
        response = self.client.get(f"{url}?highlight=invalid")
        
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['highlight_id'])
    
    def test_my_journals_ordering_newest_first(self):
        """Test that entries are ordered by newest first."""
        url = reverse('my_journals')
        response = self.client.get(url)
        
        regular_entries = list(response.context['regular_entries'])
        self.assertEqual(len(regular_entries), 2)
        # entry2 was created after entry1, so should appear first
        self.assertEqual(regular_entries[0].id, self.entry2.id)
        self.assertEqual(regular_entries[1].id, self.entry1.id)
