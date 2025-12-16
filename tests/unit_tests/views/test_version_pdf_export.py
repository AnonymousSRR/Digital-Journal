"""
Unit tests for journal entry version PDF export functionality.
Tests PDF generation for versions and version comparisons.
"""
from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, JournalEntry, Theme


class VersionPDFExportTests(TestCase):
    """Test cases for version PDF export functionality."""
    
    def setUp(self):
        """Set up test data for PDF export tests."""
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
            prompt='Test prompt',
            answer='Test answer'
        )
    
    def test_export_version_pdf_returns_pdf(self):
        """Test that PDF export returns PDF file."""
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_pdf', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))
        self.assertIn('.pdf', response['Content-Disposition'])
    
    def test_export_version_pdf_filename(self):
        """Test that PDF export has correct filename format."""
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_pdf', args=[self.entry.id, 1])
        )
        
        self.assertIn('pdf-test-entry_v1.pdf', response['Content-Disposition'])
    
    def test_export_version_comparison_pdf(self):
        """Test that comparison PDF is generated correctly."""
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
        self.assertIn('_v1_vs_v2.pdf', response['Content-Disposition'])
    
    def test_pdf_export_forbids_other_users(self):
        """Test that users cannot export PDFs of other users' entries."""
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
    
    def test_pdf_export_requires_login(self):
        """Test that PDF export requires authentication."""
        response = self.client.get(
            reverse('authentication:export_version_pdf', args=[self.entry.id, 1])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_api_export_version_pdf(self):
        """Test that API PDF export endpoint works."""
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:api_export_version_pdf', args=[self.entry.id, 1])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # API endpoint should still return PDF with attachment header
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))
    
    def test_comparison_pdf_requires_both_versions(self):
        """Test that comparison PDF requires both v1 and v2 parameters."""
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_comparison_pdf', args=[self.entry.id]),
            {'v1': 1}  # Missing v2
        )
        
        # Should redirect back to version history
        self.assertEqual(response.status_code, 302)
    
    def test_pdf_export_invalid_version_returns_404(self):
        """Test that exporting non-existent version returns 404."""
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_pdf', args=[self.entry.id, 999])
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_pdf_content_not_empty(self):
        """Test that generated PDF has content."""
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_pdf', args=[self.entry.id, 1])
        )
        
        # PDF should have content (more than just headers)
        self.assertGreater(len(response.content), 1000)
        # Check for PDF magic number
        self.assertTrue(response.content.startswith(b'%PDF'))
    
    def test_comparison_pdf_with_title_change(self):
        """Test that comparison PDF handles title changes."""
        # Create version with title change
        self.entry.title = 'Updated Title'
        self.entry.answer = 'Updated answer'
        self.entry.save()
        
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_comparison_pdf', args=[self.entry.id]),
            {'v1': 1, 'v2': 2}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.content), 1000)
    
    def test_pdf_export_handles_special_characters(self):
        """Test that PDF export handles special characters in content."""
        # Create entry with special characters
        special_entry = JournalEntry.objects.create(
            user=self.user,
            title='Entry with "quotes" & <tags>',
            theme=self.theme,
            prompt='Prompt with special chars: @#$%',
            answer='Answer with émojis 😀 and symbols: © ® ™'
        )
        
        self.client.login(email='pdf@example.com', password='pass')
        response = self.client.get(
            reverse('authentication:export_version_pdf', args=[special_entry.id, 1])
        )
        
        # Should still generate valid PDF
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
