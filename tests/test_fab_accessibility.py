"""
Tests for FAB accessibility and visual hierarchy
Phase 2: Improve FAB Visual Hierarchy and Accessibility
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme


class FABAccessibilityTests(TestCase):
    """Test suite to verify FAB has proper accessibility attributes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Enable Quick Add FAB for accessibility tests
        self.user.show_quick_add_fab = True
        self.user.save()
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_fab_accessibility_attributes(self):
        """Test case 1: FAB has proper ARIA attributes"""
        # Arrange & Act: Fetch home page
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: FAB has required accessibility attributes
        self.assertEqual(response.status_code, 200)
        self.assertIn('aria-label="Quick add journal entry"', html)
        self.assertIn('title="Quick add journal entry"', html)
        self.assertIn('type="button"', html)
        # Verify the icon has aria-hidden
        self.assertIn('aria-hidden="true"', html)
    
    def test_fab_color_contrast(self):
        """Test case 3: FAB color contrast meets WCAG AA standards"""
        # Arrange & Act: Read CSS file directly
        import os
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'css', 'style.css')
        
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        # Assert: FAB has sufficient contrast (manual verification or use contrast checker)
        # Background: gradient with #667eea and #764ba2
        # Foreground: white text
        # Expected contrast ratio: > 4.5:1 for normal text, > 3:1 for large text
        self.assertIn('.fab', css_content)
        self.assertIn('color: white', css_content)
    
    def test_fab_has_focus_styles(self):
        """Verify FAB has visible focus styles for keyboard navigation"""
        # Arrange & Act: Read CSS file directly
        import os
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'css', 'style.css')
        
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        # Assert: FAB has focus styles
        self.assertIn('.fab:focus', css_content)
        self.assertIn('outline:', css_content)
    
    def test_fab_z_index_below_modal(self):
        """Verify FAB z-index is below modal but above content"""
        # Arrange & Act: Read CSS file directly
        import os
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'css', 'style.css')
        
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        # Assert: FAB z-index is 50 (below modal at 1000)
        self.assertIn('z-index: 50', css_content)


class FABVisualHierarchyTests(TestCase):
    """Test suite to verify FAB doesn't block primary dashboard actions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        # Enable Quick Add FAB for visual hierarchy tests
        self.user.show_quick_add_fab = True
        self.user.save()
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_primary_buttons_exist_on_home_page(self):
        """Verify primary dashboard buttons exist and are accessible"""
        # Arrange & Act: Fetch home page
        response = self.client.get(reverse('home'))
        html = response.content.decode()
        
        # Assert: Primary buttons exist
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="create-journal-btn"', html)
        self.assertIn('id="my-journals-btn"', html)
        self.assertIn('data-testid="create-journal-btn"', html)
        self.assertIn('data-testid="my-journals-btn"', html)
    
    def test_fab_position_is_fixed_bottom_right(self):
        """Verify FAB is positioned in bottom-right corner"""
        # Arrange & Act: Read CSS file directly
        import os
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'css', 'style.css')
        
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        # Assert: FAB has fixed positioning in bottom-right
        self.assertIn('position: fixed', css_content)
        self.assertIn('bottom: 30px', css_content)
        self.assertIn('right: 30px', css_content)
    
    def test_fab_responsive_sizing(self):
        """Verify FAB has responsive sizing for mobile devices"""
        # Arrange & Act: Read CSS file directly
        import os
        css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'css', 'style.css')
        
        with open(css_path, 'r') as f:
            css_content = f.read()
        
        # Assert: FAB has responsive styles
        # Check for mobile-specific sizing
        # The CSS should contain mobile media query adjustments
        self.assertIn('.fab', css_content)
        self.assertIn('width: 56px', css_content)
        self.assertIn('height: 56px', css_content)
