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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

import datetime

from mock import Mock

import django.utils.simplejson as json
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from mailman.email.message import Message
import django_assets.env

import kittystore
from kittystore.utils import get_message_id_hash
from kittystore.test import FakeList

from hyperkitty.models import Rating, LastView


@override_settings(USE_SSL=False, USE_INTERNAL_AUTH=True, DEBUG=True, ASSETS_DEBUG=True)
class AccountViewsTestCase(TestCase):

    def setUp(self):
        # Re-do the settings patching
        # https://github.com/miracle2k/django-assets/issues/3
        django_assets.env.reset()
        django_assets.env.get_env()
        self.client = Client()

    def test_login(self):
        # Try to access user profile (private data) without logging in
        response = self.client.get(reverse('user_profile'))
        self.assertRedirects(response, "%s?next=%s" % (reverse('user_login'), reverse('user_profile')))

    def test_profile(self):
        User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')

        response = self.client.get(reverse('user_profile'))
        self.assertEqual(response.status_code, 200)

        # Verify that user_profile is present in request context
        self.assertTrue('user_profile' in response.context)

        # Verify karma for newly created user is 1
        self.assertEqual(response.context['user_profile'].karma, 1)


    def test_registration(self):
        User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')

        # If the user if already logged in, redirect to index page...
        # Don't let him register again
        response = self.client.get(reverse('user_registration'))
        self.assertRedirects(response, reverse('root'))
        self.client.logout()

        # Access the user registration page after logging out and try to register now
        response = self.client.get(reverse('user_registration'))
        self.assertEqual(response.status_code, 200)

        # @TODO: Try to register a user and verify its working


from hyperkitty.views.accounts import last_views
from hyperkitty.views.thread import thread_index
from hyperkitty.views.list import archives

@override_settings(DEBUG=True, ASSETS_DEBUG=True)
class LastViewsTestCase(TestCase):

    def setUp(self):
        # Re-do the settings patching
        # https://github.com/miracle2k/django-assets/issues/3
        django_assets.env.reset()
        django_assets.env.get_env()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        store = kittystore.get_store("sqlite:", debug=False)
        ml = FakeList("list@example.com")
        ml.subject_prefix = u"[example] "
        # Create 3 threads
        messages = []
        for msgnum in range(3):
            msg = Message()
            msg["From"] = "dummy@example.com"
            msg["Message-ID"] = "<id%d>" % (msgnum+1)
            msg["Subject"] = "Dummy message"
            msg.set_payload("Dummy message")
            store.add_to_list(ml, msg)
            messages.append(msg)
        # 1st is unread, 2nd is read, 3rd is updated
        LastView.objects.create(list_address="list@example.com", user=self.user,
                                threadid=get_message_id_hash("<id2>"))
        LastView.objects.create(list_address="list@example.com", user=self.user,
                                threadid=get_message_id_hash("<id3>"))
        msg4 = Message()
        msg4["From"] = "dummy@example.com"
        msg4["Message-ID"] = "<id4>"
        msg4["Subject"] = "Dummy message"
        msg4["In-Reply-To"] = "<id3>"
        msg4.set_payload("Dummy message")
        store.add_to_list(ml, msg4)
        # Factory
        defaults = {"kittystore.store": store, "HTTP_USER_AGENT": "testbot"}
        self.factory = RequestFactory(**defaults)

    def test_profile(self):
        request = self.factory.get(reverse('user_last_views'))
        request.user = self.user
        response = last_views(request)
        self.assertContains(response, "<td>dummy@example.com</td>",
                            count=2, status_code=200, html=True)

    def test_thread(self):
        responses = []
        for msgnum in range(3):
            threadid = get_message_id_hash("<id%d>" % (msgnum+1))
            request = self.factory.get(reverse('thread',
                        args=["list@example.com", threadid]))
            request.user = self.user
            response = thread_index(request, "list@example.com", threadid)
            responses.append(response)
        self.assertContains(responses[0], "icon-eye-close", count=1, status_code=200)
        self.assertNotContains(responses[1], "icon-eye-close", status_code=200)
        self.assertContains(responses[2], "icon-eye-close", count=1, status_code=200)

    def test_thread_list(self):
        now = datetime.datetime.now()
        request = self.factory.get(reverse('archives_with_month', args=["list@example.com", now.year, now.month]))
        request.user = self.user
        response = archives(request, "list@example.com", now.year, now.month)
        self.assertContains(response, "icon-eye-close",
                            count=2, status_code=200)


from hyperkitty.views.message import vote

class MessageViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
                'testuser', 'test@example.com', 'testPass')
        # Fake KittStore
        class FakeMessage(object):
            def __init__(self, h):
                self.message_id_hash = h
                self.list_name = "list@example.com"
        self.store = Mock()
        self.store.get_message_by_hash_from_list.side_effect = \
                lambda l, h: FakeMessage(h)
        defaults = {"kittystore.store": self.store}
        self.factory = RequestFactory(**defaults)


    def test_vote_up(self):
        request = self.factory.post("/vote", {"vote": "1"})
        request.user = self.user
        resp = vote(request, 'list@example.com', '123')
        self.assertEqual(resp.status_code, 200)
        v = Rating.objects.get(user=self.user, messageid="123",
                               list_address='list@example.com')
        self.assertEqual(v.vote, 1)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 1)
        self.assertEqual(result["dislike"], 0)


    def test_vote_down(self):
        request = self.factory.post("/vote", {"vote": "-1"})
        request.user = self.user
        resp = vote(request, 'list@example.com', '123')
        self.assertEqual(resp.status_code, 200)
        v = Rating.objects.get(user=self.user, messageid="123",
                               list_address='list@example.com')
        self.assertEqual(v.vote, -1)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 0)
        self.assertEqual(result["dislike"], 1)


    def test_vote_cancel(self):
        v = Rating(list_address="list@example.com", messageid="m1", vote=1)
        v.user = self.user
        v.save()
        v = Rating(list_address="list@example.com", messageid="m2", vote=-1)
        v.user = self.user
        v.save()
        for msg in ["m1", "m2"]:
            request = self.factory.post("/vote", {"vote": "0"})
            request.user = self.user
            resp = vote(request, 'list@example.com', msg)
            self.assertEqual(resp.status_code, 200)
            try:
                Rating.objects.get(user=self.user, messageid=msg,
                                   list_address='list@example.com')
            except Rating.DoesNotExist:
                pass
            else:
                self.fail("Vote for msg %s should have been deleted" % msg)
            result = json.loads(resp.content)
            self.assertEqual(result["like"], 0)
            self.assertEqual(result["dislike"], 0)


    def test_unauth_vote(self):
        request = self.factory.post("/vote", {"vote": "1"})
        request.user = AnonymousUser()
        resp = vote(request, 'list@example.com', '123')
        self.assertEqual(resp.status_code, 403)



from hyperkitty.views.list import archives

class ListArchivesTestCase(TestCase):

    def setUp(self):
#        self.store = Mock()
#        self.store.get_threads.return_value = []
#        self.store.get_list.side_effect = lambda n: FakeList(n)
#        defaults = {"kittystore.store": self.store}
#        self.factory = RequestFactory(**defaults)
        self.factory = RequestFactory()

    def test_no_date(self):
        today = datetime.date.today()
        request = self.factory.get("/archives")
        response = archives(request, 'list@example.com')
        final_url = reverse('archives_with_month',
                kwargs={'mlist_fqdn': 'list@example.com',
                        'year': today.year,
                        'month': today.month,
                })
        self.assertEqual(response["location"], final_url)
