"""
Unit tests for journal entry version history views.
Tests version timeline, comparison, and API endpoints.
"""
from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, JournalEntry, Theme


class VersionHistoryViewTests(TestCase):
    """Test cases for version history views."""
    
    def setUp(self):
        """Set up test data for version history view tests."""
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
        """Test that version history view requires authentication."""
        response = self.client.get(
            reverse('authentication:entry_version_history', args=[self.entry.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)
    
    def test_entry_version_history_view_shows_all_versions(self):
        """Test that version history displays all versions."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:entry_version_history', args=[self.entry.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['versions']), 3)
        self.assertIn('Version History', response.context['page_title'])
    
    def test_entry_version_history_forbids_other_users(self):
        """Test that users cannot view version history of other users' entries."""
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
    
    def test_view_version_displays_specific_version(self):
        """Test that view_version shows specific version details."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:view_version', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['version'].version_number, 1)
        self.assertEqual(response.context['version'].answer, 'Original')
        self.assertFalse(response.context['is_current'])
    
    def test_view_version_identifies_current(self):
        """Test that view_version correctly identifies current version."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:view_version', args=[self.entry.id, 3])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_current'])
    
    def test_compare_versions_returns_diff(self):
        """Test that compare view returns diff between two versions."""
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
        self.assertIsNotNone(comparison['diff'])
    
    def test_compare_versions_requires_both_parameters(self):
        """Test that compare view requires both v1 and v2 parameters."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:compare_versions', args=[self.entry.id]),
            {'v1': 1}  # Missing v2
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
        # Check that redirect goes back to version history
    
    def test_compare_versions_handles_invalid_version(self):
        """Test that compare view handles invalid version numbers."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:compare_versions', args=[self.entry.id]),
            {'v1': 1, 'v2': 999}  # v2 doesn't exist
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_api_version_timeline_returns_json(self):
        """Test that API endpoint returns JSON version timeline."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:api_version_timeline', args=[self.entry.id])
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['versions']), 3)
        self.assertTrue(data['versions'][0]['is_current'])
        self.assertEqual(data['entry_id'], self.entry.id)
    
    def test_api_version_timeline_requires_login(self):
        """Test that API timeline endpoint requires authentication."""
        response = self.client.get(
            reverse('authentication:api_version_timeline', args=[self.entry.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_api_version_diff_returns_json(self):
        """Test that API diff endpoint returns JSON diff data."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:api_version_diff', args=[self.entry.id]),
            {'v1': 1, 'v2': 2}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['v1']['version_number'], 1)
        self.assertEqual(data['v2']['version_number'], 2)
        self.assertTrue(data['answer_changed'])
        self.assertIsInstance(data['diff'], list)
    
    def test_api_version_diff_requires_parameters(self):
        """Test that API diff endpoint requires v1 and v2 parameters."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:api_version_diff', args=[self.entry.id])
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_api_version_diff_handles_invalid_version(self):
        """Test that API diff endpoint handles invalid version numbers."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:api_version_diff', args=[self.entry.id]),
            {'v1': 'invalid', 'v2': 2}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_version_timeline_ordered_descending(self):
        """Test that version timeline is ordered by version number descending."""
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:entry_version_history', args=[self.entry.id])
        )
        
        versions = response.context['versions']
        version_numbers = [v.version_number for v in versions]
        self.assertEqual(version_numbers, [3, 2, 1])
    
    def test_compare_detects_title_change(self):
        """Test that comparison detects title changes."""
        # Create version with title change
        self.entry.title = 'Updated Title'
        self.entry.save()
        
        self.client.login(email='vh@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:compare_versions', args=[self.entry.id]),
            {'v1': 1, 'v2': 4}
        )
        
        comparison = response.context['comparison']
        self.assertTrue(comparison['title_changed'])
