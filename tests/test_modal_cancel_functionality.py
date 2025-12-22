"""
Tests for modal cancel functionality
Phase 2: Fix Cancel Button Event Listener
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class ModalCancelFunctionalityTests(TestCase):
    """Test suite to verify cancel button and modal close functionality"""
    
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
    
    def test_cancel_button_present(self):
        """Test case 1: Cancel button is present in modal"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Cancel button exists
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="quickAddCancel"', html)
        self.assertIn('type="button"', html)
    
    def test_overlay_element_present(self):
        """Test case 2: Overlay element is present"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Overlay exists
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="modal-overlay"', html)
    
    def test_modal_close_function_defined(self):
        """Test case 3: closeModal function is defined in JavaScript"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: closeModal function exists
        self.assertEqual(response.status_code, 200)
        self.assertIn('function closeModal()', html)
        self.assertIn("quickAddModal.setAttribute('hidden', '')", html)
    
    def test_cancel_button_event_listener_attached(self):
        """Test case 4: Cancel button has event listener"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Event listener is attached to cancel button
        self.assertEqual(response.status_code, 200)
        self.assertIn("quickAddCancel.addEventListener('click'", html)
        self.assertIn('closeModal()', html)
    
    def test_overlay_click_event_listener(self):
        """Test case 5: Overlay has click event listener"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Overlay click listener exists
        self.assertEqual(response.status_code, 200)
        self.assertIn('.modal-overlay', html)
        self.assertIn("addEventListener('click'", html)
    
    def test_escape_key_listener_present(self):
        """Test case 6: Escape key listener is present"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Escape key handler exists
        self.assertEqual(response.status_code, 200)
        self.assertIn("e.key === 'Escape'", html)
        self.assertIn('closeModal()', html)
    
    def test_stopPropagation_on_modal_content(self):
        """Test case 7: Modal content stops event propagation"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: stopPropagation is called
        self.assertEqual(response.status_code, 200)
        self.assertIn('e.stopPropagation()', html)
    
    def test_defensive_null_checks(self):
        """Test case 8: Defensive null checks are present"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Defensive checks exist
        self.assertEqual(response.status_code, 200)
        self.assertIn('if (!quickAddBtn', html)
        self.assertIn('if (modalOverlay)', html)
        self.assertIn('if (modalContent)', html)
