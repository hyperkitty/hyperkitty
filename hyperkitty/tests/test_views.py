# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# 

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import urllib

class AccountViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_login(self):
        # Try to access user profile (private data) without logging in
        response = self.client.get(reverse('user_profile'))
        self.assertRedirects(response, "%s?next=%s" % (reverse('user_login'), reverse('user_profile')))

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


class MessageViewsTestCase(TestCase):
     def setUp(self):
        self.client = Client()

     def test_good_vote(self):
        User.objects.create_user('testuser', 'syst3m.w0rm+test@gmail.com', 'testPass')
        user = self.client.login(username='testuser', password='testPass')

        resp = self.client.post(reverse('message_vote', kwargs={'mlist_fqdn': 'list@list.com'}), {'vote': 1, 'messageid': 123, })
        self.assertEqual(resp.status_code, 200)

     def test_unauth_vote(self):
        resp = self.client.post(reverse('message_vote', kwargs={'mlist_fqdn': 'list@list.com'}), {'vote': 1, 'messageid': 123, })
        url = "%s?next=%s" % (reverse('user_login'), urllib.quote(reverse('message_vote', kwargs={'mlist_fqdn': 'list@list.com'})))
        self.assertRedirects(resp, url)

