from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

class AccountViewsTestCase(TestCase):
        
    def setUp(self):
        self.client = Client()

    def test_login(self):
        # Try to access user profile (private data) without logging in
        response = self.client.get(reverse('user_profile'))
        self.assertRedirects(response, "%s?next=%s" % (reverse('user_login'),reverse('user_profile')))
    
    def test_profile(self):
        User.objects.create_user('testuser', 'syst3m.w0rm+test@gmail.com', 'testPass')
        user = self.client.login(username='testuser', password='testPass')
        
        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)
        
        # Verify that user_profile is present in request context
        self.assertTrue('user_profile' in response.context)
        
        # Verify karma for newly created user is 1
        self.assertEqual(response.context['user_profile'].karma, 1)
        
    
    def test_registration(self):
        
        User.objects.create_user('testuser', 'syst3m.w0rm+test@gmail.com', 'testPass')
        user = self.client.login(username='testuser', password='testPass')
        
        # If the user if already logged in, redirect to index page..don't let him register again
        response = self.client.get(reverse('user_registration'))
        self.assertRedirects(response, reverse('index'))
        self.client.logout()
        
        # Access the user registration page after logging out and try to register now
        response = self.client.get(reverse('user_registration'))
        self.assertEqual(response.status_code, 200)
        
        # @TODO: Try to register a user and verify its working
        
        
        
        
        
        
        