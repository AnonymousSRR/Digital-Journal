"""
Tests for FAB analytics tracking
Phase 4: Add Analytics to Track Modal Usage Patterns
"""

from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme, AnalyticsEvent
import json
import time


class FABAnalyticsTests(TestCase):
    """Test suite to verify analytics tracking for FAB interactions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        Theme.objects.get_or_create(
            name='Quick Add',
            defaults={'description': 'Default theme for quick-add journal entries'}
        )
        self.client.login(email='test@example.com', password='testpass123')
    
    def test_fab_click_tracked(self):
        """Test case 1: FAB click is tracked"""
        # Arrange: Clear existing analytics
        AnalyticsEvent.objects.filter(user=self.user).delete()
        
        # Act: Send analytics event
        response = self.client.post('/home/api/analytics/track/', 
            json.dumps({
                'event': 'quick_add_fab_clicked',
                'timestamp': int(time.time() * 1000),
                'page': 'home'
            }),
            content_type='application/json'
        )
        
        # Assert: Event recorded
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        events = AnalyticsEvent.objects.filter(user=self.user, event_type='quick_add_fab_clicked')
        self.assertEqual(events.count(), 1)
    
    def test_modal_close_reasons_tracked(self):
        """Test case 2: Modal close reasons are tracked"""
        # Arrange: Clear existing analytics
        AnalyticsEvent.objects.filter(user=self.user).delete()
        
        # Act: Send different close events
        close_reasons = ['cancel_button', 'overlay_click', 'form_submit']
        for reason in close_reasons:
            self.client.post('/home/api/analytics/track/',
                json.dumps({
                    'event': 'quick_add_modal_closed',
                    'close_reason': reason,
                    'duration': 5000
                }),
                content_type='application/json'
            )
        
        # Assert: All events recorded
        events = AnalyticsEvent.objects.filter(user=self.user, event_type='quick_add_modal_closed')
        self.assertEqual(events.count(), 3)
        
        # Verify event data contains close reasons
        close_reasons_in_db = [
            event.event_data.get('close_reason') 
            for event in events
        ]
        self.assertIn('cancel_button', close_reasons_in_db)
        self.assertIn('overlay_click', close_reasons_in_db)
        self.assertIn('form_submit', close_reasons_in_db)
    
    def test_no_unintended_modal_opens(self):
        """Test case 3: No unintended modal opens detected"""
        # Arrange: Load home page multiple times
        AnalyticsEvent.objects.filter(user=self.user).delete()
        
        # Act: Navigate to home page multiple times
        for _ in range(5):
            self.client.get(reverse('home'))
        
        # Assert: No 'quick_add_modal_opened_auto' events should exist
        auto_open_events = AnalyticsEvent.objects.filter(
            user=self.user, 
            event_type='quick_add_modal_opened_auto'
        )
        self.assertEqual(auto_open_events.count(), 0)
    
    def test_analytics_event_model_structure(self):
        """Verify AnalyticsEvent model has correct structure"""
        # Arrange: Create an analytics event
        event = AnalyticsEvent.objects.create(
            user=self.user,
            event_type='test_event',
            event_data={'key': 'value', 'count': 42}
        )
        
        # Assert: Model fields are correct
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.event_type, 'test_event')
        self.assertEqual(event.event_data['key'], 'value')
        self.assertEqual(event.event_data['count'], 42)
        self.assertIsNotNone(event.timestamp)
    
    def test_analytics_endpoint_requires_authentication(self):
        """Verify analytics endpoint requires authentication"""
        # Arrange: Logout user
        self.client.logout()
        
        # Act: Try to send analytics event
        response = self.client.post('/home/api/analytics/track/',
            json.dumps({'event': 'test_event'}),
            content_type='application/json'
        )
        
        # Assert: Request is redirected to login
        self.assertEqual(response.status_code, 302)
    
    def test_analytics_endpoint_validates_event_type(self):
        """Verify analytics endpoint validates event type"""
        # Act: Send analytics event without event type
        response = self.client.post('/home/api/analytics/track/',
            json.dumps({}),
            content_type='application/json'
        )
        
        # Assert: Request fails with error
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_analytics_events_ordered_by_timestamp(self):
        """Verify analytics events are ordered by timestamp descending"""
        # Arrange: Create multiple events
        AnalyticsEvent.objects.filter(user=self.user).delete()
        
        for i in range(3):
            self.client.post('/home/api/analytics/track/',
                json.dumps({'event': f'test_event_{i}'}),
                content_type='application/json'
            )
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        # Act: Fetch events
        events = AnalyticsEvent.objects.filter(user=self.user)
        
        # Assert: Events are in descending order by timestamp
        timestamps = [event.timestamp for event in events]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
    
    def test_analytics_tracks_modal_duration(self):
        """Verify analytics tracks modal open duration"""
        # Arrange: Clear existing analytics
        AnalyticsEvent.objects.filter(user=self.user).delete()
        
        # Act: Send modal close event with duration
        duration_ms = 12345
        response = self.client.post('/home/api/analytics/track/',
            json.dumps({
                'event': 'quick_add_modal_closed',
                'duration': duration_ms,
                'close_reason': 'form_submit'
            }),
            content_type='application/json'
        )
        
        # Assert: Duration is stored in event data
        self.assertEqual(response.status_code, 200)
        event = AnalyticsEvent.objects.filter(
            user=self.user, 
            event_type='quick_add_modal_closed'
        ).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_data['duration'], duration_ms)
