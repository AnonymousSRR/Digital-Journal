"""
Tests for home page UX - ensuring quick-add modal doesn't auto-open
Phase 1: Audit and Remove Auto-Open Behavior
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class QuickAddModalAutoOpenTests(TestCase):
    """Test suite to verify quick-add modal never auto-opens"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Create a test theme for quick-add
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
    
    def test_quick_add_modal_hidden_on_page_load(self):
        """Test case 1: Modal remains hidden on page load"""
        # Arrange: User is logged in
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: Modal is hidden by default
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="quickAddModal"', content)
        self.assertIn('hidden', content)
        # Verify the modal div has the hidden attribute
        self.assertIn('<div id="quickAddModal" class="quick-modal" hidden>', content)
    
    def test_no_modal_auto_open_after_login(self):
        """Test case 2: Modal does not auto-open after login"""
        # Arrange: User credentials
        # Act: Perform login and follow redirect to home
        response = self.client.post('/login/signin/', {
            'username': self.user.email,
            'password': 'testpass123'
        }, follow=True)
        
        # Assert: User lands on home without modal opened
        self.assertEqual(response.status_code, 200)
        final_url = response.redirect_chain[-1][0]
        self.assertIn('/home/', final_url)
        
        # Modal should be in hidden state in rendered HTML
        content = response.content.decode()
        self.assertIn('quickAddModal', content)
        self.assertIn('<div id="quickAddModal" class="quick-modal" hidden>', content)
    
    def test_modal_hidden_with_url_parameter(self):
        """Test case 3: Modal remains hidden even with URL parameter"""
        # Arrange: User is logged in
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page with quick-add URL parameter
        response = self.client.get(reverse('home') + '?quick-add=open')
        
        # Assert: Modal is still hidden (JavaScript will handle removal)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="quickAddModal"', content)
        self.assertIn('<div id="quickAddModal" class="quick-modal" hidden>', content)
        # Verify the JavaScript includes code to remove the parameter
        self.assertIn('Removed auto-open behavior from URL parameter', content)
    
    def test_fab_button_exists_on_home_page(self):
        """Verify FAB button exists and is properly configured"""
        # Arrange: User is logged in
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: FAB button exists with correct attributes
        content = response.content.decode()
        self.assertIn('id="quick-add-btn"', content)
        self.assertIn('class="fab"', content)
        self.assertIn('aria-label="Quick add journal entry"', content)
        self.assertIn('data-testid="quick-add-btn"', content)
    
    def test_modal_verification_script_exists(self):
        """Verify JavaScript includes modal verification logic"""
        # Arrange: User is logged in
        self.client.login(email='test@example.com', password='testpass123')
        
        # Act: Navigate to home page
        response = self.client.get(reverse('home'))
        
        # Assert: JavaScript includes verification logic
        content = response.content.decode()
        self.assertIn('CRITICAL: Verify modal starts hidden', content)
        self.assertIn("if (!quickAddModal.hasAttribute('hidden'))", content)
        self.assertIn("quickAddModal.setAttribute('hidden', '')", content)
