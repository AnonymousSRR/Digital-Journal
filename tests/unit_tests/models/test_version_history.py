"""
Unit tests for journal entry version history models.
Tests automatic version creation and version tracking functionality.
"""
from django.test import TestCase
from authentication.models import CustomUser, JournalEntry, Theme, JournalEntryVersion


class VersionHistoryModelTests(TestCase):
    """Test cases for JournalEntryVersion model and automatic versioning."""
    
    def setUp(self):
        """Set up test data for version history tests."""
        self.user = CustomUser.objects.create_user(
            email='v@example.com',
            password='x',
            first_name='V',
            last_name='U'
        )
        self.theme = Theme.objects.create(name='Tech', description='Tech theme')
    
    def test_version_created_on_entry_creation(self):
        """Test that v1 is automatically created when JournalEntry is created."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Test Entry',
            theme=self.theme,
            prompt='A prompt',
            answer='My answer'
        )
        
        # Verify version was created
        self.assertEqual(entry.versions.count(), 1)
        version = entry.versions.first()
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.title, 'Test Entry')
        self.assertEqual(version.answer, 'My answer')
        self.assertTrue(version.is_original())
        self.assertEqual(version.edit_source, 'initial')
        self.assertEqual(version.change_summary, 'Entry created')
    
    def test_version_created_on_entry_update(self):
        """Test that a new version is created when JournalEntry is updated."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Original Title',
            theme=self.theme,
            prompt='A prompt',
            answer='Original answer'
        )
        
        # Update the entry
        entry.title = 'Updated Title'
        entry.answer = 'Updated answer'
        entry.save()
        
        # Verify versions
        self.assertEqual(entry.versions.count(), 2)
        v1 = entry.get_version(1)
        v2 = entry.get_version(2)
        
        self.assertEqual(v1.title, 'Original Title')
        self.assertEqual(v1.answer, 'Original answer')
        self.assertEqual(v2.title, 'Updated Title')
        self.assertEqual(v2.answer, 'Updated answer')
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v2.edit_source, 'edit')
    
    def test_version_ordering_and_latest(self):
        """Test that versions are properly ordered and latest version is accessible."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='T1',
            theme=self.theme,
            prompt='p',
            answer='a1'
        )
        
        # Create multiple versions
        for i in range(2, 5):
            entry.answer = f'a{i}'
            entry.save()
        
        # Check order
        versions = list(entry.versions.all())
        self.assertEqual(versions[0].version_number, 4)  # Latest first
        self.assertEqual(versions[3].version_number, 1)  # Oldest last
        
        # Check latest retrieval
        current = entry.get_current_version()
        self.assertEqual(current.version_number, 4)
        self.assertTrue(current.is_current())
    
    def test_version_count_method(self):
        """Test that version_count method returns correct count."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Count Test',
            theme=self.theme,
            prompt='p',
            answer='a'
        )
        
        self.assertEqual(entry.version_count(), 1)
        
        entry.answer = 'updated'
        entry.save()
        
        self.assertEqual(entry.version_count(), 2)
    
    def test_version_preserves_all_fields(self):
        """Test that version snapshot includes all entry fields."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Field Test',
            theme=self.theme,
            prompt='Test prompt',
            answer='Test answer',
            visibility='shared'
        )
        
        version = entry.versions.first()
        self.assertEqual(version.title, 'Field Test')
        self.assertEqual(version.prompt, 'Test prompt')
        self.assertEqual(version.answer, 'Test answer')
        self.assertEqual(version.visibility, 'shared')
        self.assertEqual(version.theme, self.theme)
        self.assertEqual(version.created_by, self.user)
    
    def test_version_unique_together_constraint(self):
        """Test that entry and version_number combination is unique."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Unique Test',
            theme=self.theme,
            prompt='p',
            answer='a'
        )
        
        # Try to create duplicate version manually (should fail)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            JournalEntryVersion.objects.create(
                entry=entry,
                version_number=1,
                title='Duplicate',
                answer='Duplicate',
                theme=self.theme,
                prompt='p',
                visibility='private',
                created_by=self.user
            )
    
    def test_last_modified_at_field(self):
        """Test that last_modified_at field is updated on save."""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='Modified Test',
            theme=self.theme,
            prompt='p',
            answer='a'
        )
        
        original_modified = entry.last_modified_at
        self.assertIsNotNone(original_modified)
        
        # Update entry
        import time
        time.sleep(0.1)  # Small delay to ensure different timestamp
        entry.answer = 'updated'
        entry.save()
        
        entry.refresh_from_db()
        self.assertGreater(entry.last_modified_at, original_modified)
