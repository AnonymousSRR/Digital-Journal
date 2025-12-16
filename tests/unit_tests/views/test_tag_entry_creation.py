from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme, JournalEntry, Tag


class EntryCreationTagsTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='u@example.com',
            password='x',
            first_name='U',
            last_name='S'
        )
        self.client = Client()
        self.client.login(username='u@example.com', password='x')
        self.theme = Theme.objects.create(name='Tech', description='')

    def test_tags_created_and_attached(self):
        """Test that posting with tags creates tags and associates them with the entry"""
        url = reverse('answer_prompt') + f'?theme_id={self.theme.id}'
        resp = self.client.post(url, data={
            'prompt': 'p',
            'title': 't',
            'answer': 'a',
            'visibility': 'private',
            'tags': 'Work, Personal'
        })
        self.assertEqual(resp.status_code, 302)
        
        entry = JournalEntry.objects.get(title='t')
        self.assertEqual({t.name for t in entry.tags.all()}, {'Work', 'Personal'})
        self.assertEqual(Tag.objects.filter(user=self.user, name='Work').count(), 1)

    def test_duplicate_and_whitespace_handling(self):
        """Test that duplicate tags and whitespace are handled properly"""
        url = reverse('answer_prompt') + f'?theme_id={self.theme.id}'
        # Create an existing tag with lowercase name
        Tag.objects.create(user=self.user, name='ideas', slug='ideas')
        
        # Post with duplicate tags (different case) and whitespace
        self.client.post(url, data={
            'prompt': 'p',
            'title': 't2',
            'answer': 'a',
            'visibility': 'private',
            'tags': 'Ideas, , ideas '
        })
        
        entry = JournalEntry.objects.get(title='t2')
        # Should normalize to the same slug and only have one tag
        self.assertEqual([t.slug for t in entry.tags.all()], ['ideas'])
        # Should not create duplicate tags
        self.assertEqual(Tag.objects.filter(user=self.user, slug='ideas').count(), 1)
