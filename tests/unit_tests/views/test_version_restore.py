"""
Unit tests for journal entry version restore functionality.
Tests version restoration and edit history tracking.
"""
from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, JournalEntry, Theme, JournalEntryVersion


class VersionRestoreTests(TestCase):
    """Test cases for version restore functionality."""
    
    def setUp(self):
        """Set up test data for version restore tests."""
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
        """Test that restoring a version creates a new version marked as restore."""
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
    
    def test_restore_forbids_other_users(self):
        """Test that users cannot restore versions of other users' entries."""
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
    
    def test_api_restore_version_returns_json(self):
        """Test that API restore endpoint returns JSON."""
        self.client.login(email='restore@example.com', password='pass')
        response = self.client.post(
            reverse('authentication:api_restore_version', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['new_version_number'], 4)
        self.assertIn('restored successfully', data['message'])
    
    def test_restore_version_get_shows_confirmation(self):
        """Test that GET request to restore shows confirmation page."""
        self.client.login(email='restore@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:restore_version', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['source_version'].version_number, 1)
        self.assertIn('Restore', response.context['page_title'])
    
    def test_api_restore_requires_post(self):
        """Test that API restore endpoint requires POST method."""
        self.client.login(email='restore@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:api_restore_version', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 405)
        data = response.json()
        self.assertIn('error', data)
    
    def test_restore_preserves_all_fields(self):
        """Test that restore preserves all fields from source version."""
        # Create a version with different field values
        self.entry.title = 'Modified Title'
        self.entry.visibility = 'shared'
        self.entry.save()
        
        self.client.login(email='restore@example.com', password='pass')
        
        # Restore v1
        self.client.post(
            reverse('authentication:restore_version', args=[self.entry.id, 1])
        )
        
        self.entry.refresh_from_db()
        
        # Check that all fields are restored
        self.assertEqual(self.entry.title, 'Entry Title')
        self.assertEqual(self.entry.answer, 'Version 1')
        self.assertEqual(self.entry.visibility, 'private')
    
    def test_restore_redirects_to_version_history(self):
        """Test that successful restore redirects to version history page."""
        self.client.login(email='restore@example.com', password='pass')
        response = self.client.post(
            reverse('authentication:restore_version', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('versions', response.url)
    
    def test_restore_invalid_version_returns_404(self):
        """Test that restoring non-existent version returns 404."""
        self.client.login(email='restore@example.com', password='pass')
        response = self.client.post(
            reverse('authentication:restore_version', args=[self.entry.id, 999])
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_multiple_restores_create_separate_versions(self):
        """Test that multiple restores each create new versions."""
        self.client.login(email='restore@example.com', password='pass')
        
        # Restore v1
        self.client.post(
            reverse('authentication:restore_version', args=[self.entry.id, 1])
        )
        self.assertEqual(self.entry.version_count(), 4)
        
        # Restore v2
        self.client.post(
            reverse('authentication:restore_version', args=[self.entry.id, 2])
        )
        self.assertEqual(self.entry.version_count(), 5)
        
        # Check that both restores are tracked
        v4 = self.entry.get_version(4)
        v5 = self.entry.get_version(5)
        
        self.assertEqual(v4.edit_source, 'restore')
        self.assertEqual(v4.restored_from_version, 1)
        self.assertEqual(v5.edit_source, 'restore')
        self.assertEqual(v5.restored_from_version, 2)
    
    def test_restore_updates_change_summary(self):
        """Test that restore updates change summary with version info."""
        self.client.login(email='restore@example.com', password='pass')
        
        self.client.post(
            reverse('authentication:restore_version', args=[self.entry.id, 2])
        )
        
        latest = self.entry.get_current_version()
        self.assertIn('Restored from version 2', latest.change_summary)
