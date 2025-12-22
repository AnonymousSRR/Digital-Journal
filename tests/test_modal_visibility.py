"""
Tests for modal visibility CSS behavior
Phase 1: Fix CSS to Respect Hidden Attribute
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class ModalVisibilityTests(TestCase):
    """Test suite to verify modal CSS respects hidden attribute"""
    
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
    
    def test_modal_hidden_by_default_in_css(self):
        """Test case 1: Modal is hidden by default in CSS"""
        # Arrange & Act: Load home page and check CSS
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Modal has hidden attribute in HTML
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="quickAddModal"', html)
        self.assertIn('<div id="quickAddModal" class="quick-modal" hidden>', html)
    
    def test_modal_has_correct_css_classes(self):
        """Test case 2: Modal has correct CSS classes"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Modal has the quick-modal class
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="quick-modal"', html)
        self.assertIn('class="modal-overlay"', html)
        self.assertIn('class="modal-content"', html)
    
    def test_modal_structure_present(self):
        """Test case 3: Modal HTML structure is present"""
        # Arrange & Act: Load home page
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Modal elements are present
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="quickAddModal"', html)
        self.assertIn('id="quickAddForm"', html)
        self.assertIn('id="quick-title"', html)
        self.assertIn('id="quick-body"', html)
        self.assertIn('id="quickAddCancel"', html)
