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
import json

from mock import Mock

from hyperkitty.tests.utils import ViewTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mailman.email.message import Message

import kittystore
from kittystore.test import FakeList, SettingsModule

from hyperkitty.models import Tag



class ReattachTestCase(ViewTestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testPass')
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



class ThreadTestCase(ViewTestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testPass')
        self.ml = FakeList("list@example.com")
        self.ml.subject_prefix = u"[example] "
        msg = self._make_msg("msgid")
        self.threadid = msg["Message-ID-Hash"]

    def _make_msg(self, msgid, reply_to=None):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<%s>" % msgid
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy message")
        if reply_to is not None:
            msg["In-Reply-To"] = "<%s>" % reply_to
        msg["Message-ID-Hash"] = self.store.add_to_list(self.ml, msg)
        return msg

    def _do_post(self, data):
        url = reverse('tags', args=["list@example.com", self.threadid])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def test_add_tag(self):
        result = self._do_post({ "tag": "testtag", "action": "add" })
        self.assertEqual(result["tags"], [u"testtag"])

    def test_add_tag_stripped(self):
        result = self._do_post({ "tag": " testtag ", "action": "add" })
        self.assertEqual(result["tags"], [u"testtag"])
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(Tag.objects.all()[0].tag, u"testtag")

    def test_add_tag_twice(self):
        # A second adding of the same tag should just be ignored
        Tag(list_address="list@example.com", threadid=self.threadid,
            tag="testtag", user=self.user).save()
        result = self._do_post({ "tag": "testtag", "action": "add" })
        self.assertEqual(result["tags"], [u"testtag"])
        self.assertEqual(Tag.objects.count(), 1)

    def test_add_multiple_tags(self):
        result = self._do_post({ "tag": "testtag 1, testtag 2 ; testtag 3", "action": "add" })
        expected = [u"testtag 1", u"testtag 2", u"testtag 3"]
        self.assertEqual(result["tags"], expected)
        self.assertEqual(Tag.objects.count(), 3)
        self.assertEqual(sorted(t.tag for t in Tag.objects.all()), expected)

    def test_num_comments(self):
        self._make_msg("msgid2", "msgid")
        self._make_msg("msgid3", "msgid2")
        self._make_msg("msgid4", "msgid3")
        url = reverse('thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("num_comments" in response.context)
        self.assertEqual(response.context["num_comments"], 3)
