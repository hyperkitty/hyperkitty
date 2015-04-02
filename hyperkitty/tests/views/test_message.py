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

from __future__ import absolute_import, print_function, unicode_literals

import json
from email.message import Message

from mock import patch
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail
from django.utils import timezone
from django_gravatar.helpers import get_gravatar_url

from hyperkitty.lib.utils import get_message_id_hash
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import Email
from hyperkitty.tests.utils import TestCase



class MessageViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
                'testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        # Create a dummy message to test on
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("Dummy message")
        add_to_list("list@example.com", msg)

    def test_vote_up(self):
        url = reverse('hk_message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "1"})
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 1)
        self.assertEqual(result["dislike"], 0)

    def test_vote_down(self):
        url = reverse('hk_message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "-1"})
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 0)
        self.assertEqual(result["dislike"], 1)

    def test_vote_cancel(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg1>"
        msg.set_payload("Dummy message")
        add_to_list("list@example.com", msg)
        msg.replace_header("Message-ID", "<msg2>")
        add_to_list("list@example.com", msg)
        msg1 = Email.objects.get(mailinglist__name="list@example.com",
                                 message_id="msg1")
        msg1.vote(1, self.user)
        msg2 = Email.objects.get(mailinglist__name="list@example.com",
                                 message_id="msg2")
        msg2.vote(-1, self.user)
        self.assertEqual(msg1.get_votes()["likes"], 1)
        self.assertEqual(msg2.get_votes()["dislikes"], 1)
        for msg in (msg1, msg2):
            url = reverse('hk_message_vote', args=("list@example.com",
                          msg.message_id_hash))
            resp = self.client.post(url, {"vote": "0"})
            self.assertEqual(resp.status_code, 200)
            votes = msg.get_votes()
            self.assertEqual(votes["likes"], 0)
            self.assertEqual(votes["dislikes"], 0)
            result = json.loads(resp.content)
            self.assertEqual(result["like"], 0)
            self.assertEqual(result["dislike"], 0)

    def test_unauth_vote(self):
        self.client.logout()
        url = reverse('hk_message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_message_page(self):
        url = reverse('hk_message_index', args=("list@example.com",
                      get_message_id_hash("msg")))
        with self.settings(USE_L10N=False, DATETIME_FORMAT='Y-m-d H:i:s',
                           TIME_FORMAT="H:i:s"):
            with timezone.override(timezone.utc):
                response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dummy message")
        self.assertContains(response, "Dummy Sender", count=1)
        self.assertContains(response, "Dummy Subject", count=3)
        self.assertNotContains(response, "dummy@example.com")
        self.assertContains(response,
            get_gravatar_url("dummy@example.com", 40).replace("&", "&amp;"))
        self.assertContains(response, "list@example.com")
        self.assertContains(response, url)
        sender_time = '<span title="Sender\'s time: 2015-02-02 13:00:00">10:00:00</span>'
        self.assertIn(sender_time, response.content.decode("utf-8"))

    def test_reply(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        url = reverse('hk_message_reply', args=("list@example.com",
                      get_message_id_hash("msg")))
        with patch("hyperkitty.lib.posting.mailman.subscribe") as sub_fn:
            response = self.client.post(url, {"message": "dummy reply content"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(sub_fn.called)
        result = json.loads(response.content)
        #print(result["message_html"])
        self.assertIn("Django User", result["message_html"])
        self.assertIn("dummy reply content", result["message_html"])
        self.assertIn(
            get_gravatar_url("test@example.com", 40).replace("&", "&amp;"),
            result["message_html"])
        self.assertEqual(len(mail.outbox), 1)
        #print(mail.outbox[0].message())
        self.assertEqual(mail.outbox[0].recipients(), ["list@example.com"])
        self.assertEqual(mail.outbox[0].from_email, '"Django User" <test@example.com>')
        self.assertEqual(mail.outbox[0].subject, 'Re: Dummy Subject')
        self.assertEqual(mail.outbox[0].body, "dummy reply content")
        self.assertEqual(mail.outbox[0].message().get("references"), "<msg>")
        self.assertEqual(mail.outbox[0].message().get("in-reply-to"), "<msg>")

    def test_reply_newthread(self):
        url = reverse('hk_message_reply', args=("list@example.com",
                      get_message_id_hash("msg")))
        with patch("hyperkitty.lib.posting.mailman.subscribe") as sub_fn:
            response = self.client.post(url,
                {"message": "dummy reply content",
                 "newthread": 1, "subject": "new subject"})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(sub_fn.called)
        result = json.loads(response.content)
        self.assertEqual(result["message_html"], None)
        self.assertEqual(len(mail.outbox), 1)
        #print(mail.outbox[0].message())
        self.assertEqual(mail.outbox[0].recipients(), ["list@example.com"])
        self.assertEqual(mail.outbox[0].from_email, 'test@example.com')
        self.assertEqual(mail.outbox[0].subject, 'new subject')
        self.assertEqual(mail.outbox[0].body, "dummy reply content")
        self.assertNotIn("references", mail.outbox[0].message())
        self.assertNotIn("in-reply-to", mail.outbox[0].message())

    def test_new_message_page(self):
        url = reverse('hk_message_new', args=["list@example.com"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_new_message_post(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        url = reverse('hk_message_new', args=["list@example.com"])
        with patch("hyperkitty.lib.posting.mailman.subscribe") as sub_fn:
            response = self.client.post(url, {
                "subject": "Test subject",
                "message": "Test message content"})
        self.assertTrue(sub_fn.called)
        redirect_url = reverse(
                'hk_archives_with_month', kwargs={
                    "mlist_fqdn": "list@example.com",
                    'year': timezone.now().year,
                    'month': timezone.now().month})
        redirect_url += "?msg=sent-ok"
        self.assertRedirects(response, redirect_url)
        self.assertEqual(len(mail.outbox), 1)
        #print(mail.outbox[0].message())
        self.assertEqual(mail.outbox[0].recipients(), ["list@example.com"])
        self.assertEqual(mail.outbox[0].from_email, '"Django User" <test@example.com>')
        self.assertEqual(mail.outbox[0].subject, 'Test subject')
        self.assertEqual(mail.outbox[0].body, "Test message content")
        self.assertIsNone(mail.outbox[0].message().get("references"))
        self.assertIsNone(mail.outbox[0].message().get("in-reply-to"))
