"""
Tests for modal basic functionality without analytics
Phase 4: Remove Analytics Code Temporarily
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class ModalBasicFunctionalityTests(TestCase):
    """Test suite to verify modal works without analytics code"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.show_quick_add_fab = True
        self.user.save()
        
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
    
    def test_no_analytics_tracking_code_present(self):
        """Test case 1: No analytics tracking code in modal JS"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: No analytics code present
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('modalOpenTime', html)
        self.assertNotIn('trackModalClose', html)
        self.assertNotIn('/home/api/analytics/track/', html)
        self.assertNotIn('event: \'quick_add_fab_clicked\'', html)
    
    def test_modal_open_code_simplified(self):
        """Test case 2: Modal open code is simplified without analytics"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Simple modal open code
        self.assertEqual(response.status_code, 200)
        self.assertIn("quickAddBtn.addEventListener('click'", html)
        self.assertIn("quickAddModal.removeAttribute('hidden')", html)
        self.assertIn('console.log', html)  # Simple logging instead of analytics
    
    def test_close_modal_simplified(self):
        """Test case 3: Close modal function is simplified"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Simple closeModal function
        self.assertEqual(response.status_code, 200)
        self.assertIn('function closeModal()', html)
        self.assertIn('quickAddForm.reset()', html)
        # No tracking calls
        self.assertNotIn('trackModalClose', html)
    
    def test_no_console_errors_setup(self):
        """Test case 4: Defensive checks ensure no console errors"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Modal JavaScript is present and contains defensive checks
        self.assertEqual(response.status_code, 200)
        self.assertIn('quickAddBtn', html)
        self.assertIn('quickAddModal', html)
    
    def test_form_submission_handler_present(self):
        """Test case 5: Form submission handler works without analytics"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Form submission code present and simplified
        self.assertEqual(response.status_code, 200)
        self.assertIn("quickAddForm.addEventListener('submit'", html)
        self.assertIn("fetch('/home/api/journals/quick-add/'", html)
        # No analytics tracking on submit
        self.assertNotIn('trackModalClose(\'form_submit\')', html)
    
    def test_timer_for_regular_journal_creation(self):
        """Test case 6: Timer for regular journal creation still works"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Timer code present
        self.assertEqual(response.status_code, 200)
        self.assertIn("createJournalBtn.addEventListener('click'", html)
        self.assertIn('sessionStorage.setItem(\'journalWritingStartTime\'', html)
