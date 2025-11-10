from django.test import TestCase
from django.urls import reverse

class HomepageTests(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_homepage_template_used(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'index.html')
