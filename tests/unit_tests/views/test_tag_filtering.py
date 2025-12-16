from django.test import TestCase, Client
from django.urls import reverse
from authentication.models import CustomUser, Theme, JournalEntry, Tag


class TagFilterViewTests(TestCase):
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
        self.work = Tag.objects.create(user=self.user, name='Work', slug='work')
        self.personal = Tag.objects.create(user=self.user, name='Personal', slug='personal')
        
        # Create entries with different tags
        e1 = JournalEntry.objects.create(
            user=self.user,
            title='A',
            theme=self.theme,
            prompt='p',
            answer='a',
            bookmarked=True
        )
        e2 = JournalEntry.objects.create(
            user=self.user,
            title='B',
            theme=self.theme,
            prompt='p',
            answer='a',
            bookmarked=False
        )
        e1.tags.add(self.work)
        e2.tags.add(self.personal)

    def test_filter_by_work_tag(self):
        """Test filtering by work tag returns only entries with that tag"""
        url = reverse('my_journals') + '?tag=work'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        # Only entries with Work tag should be present
        bookmarked = list(resp.context['bookmarked_entries'])
        regular = list(resp.context['regular_entries'])
        all_entries = bookmarked + regular
        
        self.assertEqual(len(all_entries), 1)
        self.assertTrue(all('work' in [t.slug for t in e.tags.all()] for e in all_entries))

    def test_filter_combination(self):
        """Test combining search, visibility, and tag filters works correctly"""
        # Create another shared entry with Work tag
        e3 = JournalEntry.objects.create(
            user=self.user,
            title='Work Report',
            theme=self.theme,
            prompt='p',
            answer='a',
            visibility='shared'
        )
        e3.tags.add(self.work)
        
        url = reverse('my_journals') + '?tag=work&search=Report&visibility=shared'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        entries = list(resp.context['bookmarked_entries']) + list(resp.context['regular_entries'])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, 'Work Report')

    def test_tag_list_in_context(self):
        """Test that tags with entry counts are provided in context"""
        url = reverse('my_journals')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        tags = resp.context['tags']
        self.assertEqual(len(tags), 2)
        
        # Check that tags have entry_count annotation
        tag_data = {t.slug: t.entry_count for t in tags}
        self.assertEqual(tag_data['work'], 1)
        self.assertEqual(tag_data['personal'], 1)
