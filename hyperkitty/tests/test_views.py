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
from tempfile import mkdtemp
from shutil import rmtree

from mock import Mock

import django.utils.simplejson as json
from hyperkitty.tests.utils import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mailman.email.message import Message
from mailman.interfaces.archiver import ArchivePolicy

import kittystore
from kittystore.utils import get_message_id_hash
from kittystore.test import FakeList, SettingsModule

from hyperkitty.models import LastView



def genericAssertRedirects(self, response, target):
    # A version of assertRedirects that works with view responses
    if hasattr(response, "client"):
        return TestCase.assertRedirects(self, response, target)
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response._headers["location"][1], target)



class AccountViewsTestCase(TestCase):

    def setUp(self):
        store = kittystore.get_store(SettingsModule(),
                                     debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": store,
                                "HTTP_USER_AGENT": "testbot",
                                }
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')

    def test_login(self):
        # Try to access user profile (private data) without logging in
        response = self.client.get(reverse("user_profile"))
        self.assertRedirects(response,
                "%s?next=%s" % (reverse('user_login'), reverse("user_profile")))

    def test_profile(self):
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, 200)

    def test_registration(self):
        self.client.login(username='testuser', password='testPass')
        # If the user if already logged in, redirect to index page...
        # Don't let him register again
        response = self.client.get(reverse('user_registration'))
        self.assertRedirects(response, reverse('root'))

        # Access the user registration page after logging out and try to register now
        self.client.logout()
        response = self.client.get(reverse('user_registration'))
        self.assertEqual(response.status_code, 200)

        # @TODO: Try to register a user and verify its working



class LastViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        store = kittystore.get_store(SettingsModule(), debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": store,
                                "HTTP_USER_AGENT": "testbot",
                                }
        # Create test data
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

    def test_profile(self):
        response = self.client.get(reverse('user_last_views'))
        self.assertContains(response, "<td>dummy@example.com</td>",
                            count=2, status_code=200, html=True)

    def test_thread(self):
        responses = []
        for msgnum in range(3):
            threadid = get_message_id_hash("<id%d>" % (msgnum+1))
            response = self.client.get(reverse('thread', args=(
                        "list@example.com", threadid)))
            responses.append(response)
        # There's always one icon in the right column, so all counts are +1
        self.assertContains(responses[0], "icon-eye-close", count=2, status_code=200)
        self.assertContains(responses[1], "icon-eye-close", count=1, status_code=200)
        self.assertContains(responses[2], "icon-eye-close", count=2, status_code=200)

    def test_thread_list(self):
        now = datetime.datetime.now()
        response = self.client.get(reverse('archives_with_month', args=(
                    "list@example.com", now.year, now.month)))
        self.assertContains(response, "icon-eye-close",
                            count=2, status_code=200)

    def test_overview(self):
        response = self.client.get(reverse('list_overview', args=["list@example.com"]))
        self.assertContains(response, "icon-eye-close",
                            count=4, status_code=200)



class MessageViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
                'testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        # use a temp variable below because self.client.session is actually a
        # property which returns a new instance en each call :-/
        session = self.client.session
        session["user_id"] = u"testuser"
        session.save()
        self.store = kittystore.get_store(SettingsModule(),
                                          debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": self.store,
                                "HTTP_USER_AGENT": "testbot",
                                }
        # Create a dummy message to test on
        ml = FakeList("list@example.com")
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("Dummy message")
        self.store.add_to_list(ml, msg)


    def test_vote_up(self):
        url = reverse('message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "1"})
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 1)
        self.assertEqual(result["dislike"], 0)


    def test_vote_down(self):
        url = reverse('message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "-1"})
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 0)
        self.assertEqual(result["dislike"], 1)


    def test_vote_cancel(self):
        ml = FakeList("list@example.com")
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg1>"
        msg.set_payload("Dummy message")
        self.store.add_to_list(ml, msg)
        msg.replace_header("Message-ID", "<msg2>")
        self.store.add_to_list(ml, msg)
        msg1 = self.store.get_message_by_id_from_list("list@example.com", "msg1")
        msg1.vote(1, u"testuser")
        msg2 = self.store.get_message_by_id_from_list("list@example.com", "msg2")
        msg2.vote(-1, u"testuser")
        self.assertEqual(msg1.likes, 1)
        self.assertEqual(msg2.dislikes, 1)
        for msg in (msg1, msg2):
            url = reverse('message_vote', args=("list@example.com",
                          msg.message_id_hash))
            resp = self.client.post(url, {"vote": "0"})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(msg.likes, 0)
            self.assertEqual(msg.dislikes, 0)
            result = json.loads(resp.content)
            self.assertEqual(result["like"], 0)
            self.assertEqual(result["dislike"], 0)


    def test_unauth_vote(self):
        self.client.logout()
        url = reverse('message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "1"})
        self.assertEqual(resp.status_code, 403)



class ListArchivesTestCase(TestCase):

    def setUp(self):
        store = kittystore.get_store(SettingsModule(),
                                     debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": store,
                                "HTTP_USER_AGENT": "testbot",
                                }
        # Create the list by adding a dummy message
        ml = FakeList("list@example.com")
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("Dummy message")
        store.add_to_list(ml, msg)

    def test_no_date(self):
        today = datetime.date.today()
        response = self.client.get(reverse(
                'archives_latest', args=['list@example.com']))
        final_url = reverse('archives_with_month',
                kwargs={'mlist_fqdn': 'list@example.com',
                        'year': today.year,
                        'month': today.month,
                })
        self.assertRedirects(response, final_url)



class ReattachTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testPass')
        self.store = kittystore.get_store(SettingsModule(), debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": self.store,
                                "HTTP_USER_AGENT": "testbot",
                                }
        ml = FakeList("list@example.com")
        ml.subject_prefix = u"[example] "
        # Create 2 threads
        self.messages = []
        for msgnum in range(2):
            msg = Message()
            msg["From"] = "dummy@example.com"
            msg["Message-ID"] = "<id%d>" % (msgnum+1)
            msg["Subject"] = "Dummy message"
            msg.set_payload("Dummy message")
            msg["Message-ID-Hash"] = self.store.add_to_list(ml, msg)
            self.messages.append(msg)

    def test_suggestions(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        msg2 = self.store.get_message_by_id_from_list("list@example.com", "id2")
        self.store.search = Mock(return_value={"results": [msg2]})
        self.store.search_index = True
        response = self.client.get(reverse('thread_reattach_suggest',
                                   args=["list@example.com", threadid]))
        self.store.search.assert_called_with(
            u'dummy message', 'list@example.com', 1, 50)
        other_threadid = self.messages[1]["Message-ID-Hash"]
        expected = '<input type="radio" name="parent" value="%s" />' % other_threadid
        self.assertContains(response, expected, count=1, status_code=200)

    def test_reattach(self):
        threadid1 = self.messages[0]["Message-ID-Hash"]
        threadid2 = self.messages[1]["Message-ID-Hash"]
        response = self.client.post(reverse('thread_reattach',
                                   args=["list@example.com", threadid2]),
                                   data={"parent": threadid1})
        now = datetime.datetime.now()
        threads = list(self.store.get_threads("list@example.com",
                now - datetime.timedelta(days=1),
                now + datetime.timedelta(days=1)))
        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0].thread_id, threadid1)
        expected_url = reverse('thread', args=["list@example.com", threadid1]) + "?msg=attached-ok"
        self.assertRedirects(response, expected_url)

    def test_reattach_manual(self):
        threadid1 = self.messages[0]["Message-ID-Hash"]
        threadid2 = self.messages[1]["Message-ID-Hash"]
        response = self.client.post(reverse('thread_reattach',
                                    args=["list@example.com", threadid2]),
                                    data={"parent": "",
                                          "parent-manual": threadid1})
        now = datetime.datetime.now()
        threads = list(self.store.get_threads("list@example.com",
                now - datetime.timedelta(days=1),
                now + datetime.timedelta(days=1)))
        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0].thread_id, threadid1)
        expected_url = reverse('thread', args=["list@example.com", threadid1]) + "?msg=attached-ok"
        self.assertRedirects(response, expected_url)

    def test_reattach_invalid(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        self.store.attach_to_thread = Mock()
        response = self.client.post(reverse('thread_reattach',
                                    args=["list@example.com", threadid]),
                                    data={"parent": "invalid-data"})
        self.assertFalse(self.store.attach_to_thread.called)
        now = datetime.datetime.now()
        threads = list(self.store.get_threads("list@example.com",
                now - datetime.timedelta(days=1),
                now + datetime.timedelta(days=1)))
        self.assertEqual(len(threads), 2)
        self.assertContains(response, '<div class="alert alert-warning">',
                count=1, status_code=200)
        self.assertContains(response, "Invalid thread id, it should look")

    def test_reattach_on_itself(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        self.store.attach_to_thread = Mock()
        response = self.client.post(reverse('thread_reattach',
                                    args=["list@example.com", threadid]),
                                    data={"parent": threadid})
        self.assertFalse(self.store.attach_to_thread.called)
        now = datetime.datetime.now()
        threads = list(self.store.get_threads("list@example.com",
                now - datetime.timedelta(days=1),
                now + datetime.timedelta(days=1)))
        self.assertEqual(len(threads), 2)
        self.assertContains(response, '<div class="alert alert-warning">',
                count=1, status_code=200)
        self.assertContains(response, "Can&#39;t re-attach a thread to itself")

    def test_reattach_on_unknown(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        threadid_unknown = "L36TVP2EFFDSXGVNQJCY44W5AB2YMJ65"
        self.store.attach_to_thread = Mock()
        response = self.client.post(reverse('thread_reattach',
                                    args=["list@example.com", threadid]),
                                    data={"parent": threadid_unknown})
        self.assertFalse(self.store.attach_to_thread.called)
        self.assertContains(response, '<div class="alert alert-warning">',
                count=1, status_code=200)
        self.assertContains(response, "Unknown thread")

    def test_reattach_old_to_new(self):
        threadid1 = self.messages[0]["Message-ID-Hash"]
        threadid2 = self.messages[1]["Message-ID-Hash"]
        self.store.attach_to_thread = Mock()
        response = self.client.post(reverse('thread_reattach',
                                    args=["list@example.com", threadid1]),
                                    data={"parent": threadid2})
        self.assertFalse(self.store.attach_to_thread.called)
        now = datetime.datetime.now()
        threads = list(self.store.get_threads("list@example.com",
                now - datetime.timedelta(days=1),
                now + datetime.timedelta(days=1)))
        self.assertEqual(len(threads), 2)
        self.assertContains(response, '<div class="alert alert-error">',
                count=1, status_code=200)
        self.assertContains(response, "Can&#39;t attach an older thread to a newer thread.",
                count=1, status_code=200)



class PrivateArchivesTestCase(TestCase):

    def setUp(self):
        self.tmpdir = mkdtemp(prefix="hyperkitty-testing-")
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        settings = SettingsModule()
        settings.KITTYSTORE_SEARCH_INDEX = self.tmpdir
        self.store = kittystore.get_store(settings, debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": self.store,
                                "HTTP_USER_AGENT": "testbot",
                                }
        ml = FakeList("list@example.com")
        ml.subject_prefix = u"[example] "
        ml.archive_policy = ArchivePolicy.private
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msgid>"
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy message")
        msg["Message-ID-Hash"] = self.msgid = self.store.add_to_list(ml, msg)

    def tearDown(self):
        rmtree(self.tmpdir)


    def _do_test(self, url, query={}):
        response = self.client.get(url, query)
        self.assertEquals(response.status_code, 403)
        self.client.login(username='testuser', password='testPass')
        # use a temp variable below because self.client.session is actually a
        # property which returns a new instance en each call :-/
        session = self.client.session
        session["subscribed"] = ["list@example.com"]
        session.save()
        response = self.client.get(url, query)
        self.assertContains(response, "Dummy message", status_code=200)


    def test_month_view(self):
        now = datetime.datetime.now()
        self._do_test(reverse('archives_with_month', args=["list@example.com", now.year, now.month]))

    def test_overview(self):
        self._do_test(reverse('list_overview', args=["list@example.com"]))

    def test_thread_view(self):
        self._do_test(reverse('thread', args=["list@example.com", self.msgid]))

    def test_message_view(self):
        self._do_test(reverse('message_index', args=["list@example.com", self.msgid]))

    def test_search_list(self):
        self._do_test(reverse('search'), {"list": "list@example.com", "query": "dummy"})

    def test_search_all_lists(self):
        # When searching all lists, we only search public lists regardless of
        # the user's subscriptions
        response = self.client.get(reverse('search'), {"query": "dummy"})
        self.assertNotContains(response, "Dummy message", status_code=200)
