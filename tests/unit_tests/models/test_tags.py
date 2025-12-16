from django.test import TestCase
from django.db import IntegrityError
from authentication.models import CustomUser, Tag, JournalEntry, Theme


class TagModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='u@example.com',
            password='x',
            first_name='U',
            last_name='S'
        )

    def test_slug_auto_generation_and_uniqueness(self):
        """Test that slug is auto-generated and uniqueness is enforced per user"""
        t1 = Tag.objects.create(user=self.user, name='Work Notes')
        self.assertEqual(t1.slug, 'work-notes')
        
        # Attempting to create another tag with the same name should fail
        with self.assertRaises(IntegrityError):
            Tag.objects.create(user=self.user, name='Work Notes')

    def test_same_name_allowed_for_different_users(self):
        """Test that different users can have tags with the same name"""
        other = CustomUser.objects.create_user(
            email='o@example.com',
            password='x',
            first_name='O',
            last_name='T'
        )
        tag1 = Tag.objects.create(user=self.user, name='Ideas')
        tag2 = Tag.objects.create(user=other, name='Ideas')
        
        # Both tags should exist with the same slug but different users
        self.assertEqual(tag1.slug, tag2.slug)
        self.assertNotEqual(tag1.user, tag2.user)


class JournalEntryTagRelationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='u2@example.com',
            password='x',
            first_name='U2',
            last_name='S2'
        )
        self.theme = Theme.objects.create(name='Tech', description='Tech theme')

    def test_attach_and_reverse_lookup(self):
        """Test attaching tags to entries and reverse lookup"""
        entry = JournalEntry.objects.create(
            user=self.user,
            title='T',
            theme=self.theme,
            prompt='p',
            answer='a'
        )
        t1 = Tag.objects.create(user=self.user, name='Work')
        t2 = Tag.objects.create(user=self.user, name='Personal')
        entry.tags.add(t1, t2)
        
        # Check forward relation
        self.assertEqual({t.name for t in entry.tags.all()}, {'Work', 'Personal'})
        
        # Check reverse relation
        self.assertEqual(t1.entries.filter(user=self.user).count(), 1)
        self.assertEqual(t2.entries.filter(user=self.user).count(), 1)
