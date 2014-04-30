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

import json

from hyperkitty.tests.utils import ViewTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mailman.email.message import Message

from kittystore.utils import get_message_id_hash
from kittystore.test import FakeList



class MessageViewsTestCase(ViewTestCase):

    def setUp(self):
        self.user = User.objects.create_user(
                'testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        # use a temp variable below because self.client.session is actually a
        # property which returns a new instance en each call :-/
        session = self.client.session
        session["user_id"] = u"testuser"
        session.save()
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
