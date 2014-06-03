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
from traceback import format_exc

from mock import Mock

import mailmanclient
from hyperkitty.tests.utils import ViewTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mailman.email.message import Message

from kittystore.utils import get_message_id_hash
from kittystore.test import FakeList

import hyperkitty.lib.mailman
from hyperkitty.models import LastView



class AccountViewsTestCase(ViewTestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        hyperkitty.lib.mailman.MailmanClient = Mock() # the class
        mailman_client = Mock() # the instance
        mailman_client.get_user.side_effect = mailmanclient.MailmanConnectionError()
        hyperkitty.lib.mailman.MailmanClient.return_value = mailman_client

    def tearDown(self):
        hyperkitty.lib.mailman.MailmanClient = mailmanclient.Client

    def test_login(self):
        # Try to access user profile (private data) without logging in
        response = self.client.get(reverse("user_profile"))
        self.assertRedirects(response,
                "%s?next=%s" % (reverse('user_login'), reverse("user_profile")))

    def test_profile(self):
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, 200)

    def test_public_profile(self):
        user_email = u"dummy@example.com"
        user_id = u"DUMMY"
        self.store.create_user(user_email, user_id)
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("public_user_profile", args=[user_id]))
        self.assertEqual(response.status_code, 200)

    @override_settings(USE_INTERNAL_AUTH=True)
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

    def test_votes_no_mailman_user(self):
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("user_votes"))
        self.assertEqual(response.status_code, 500)

    def test_votes_no_ks_user(self):
        self.client.login(username='testuser', password='testPass')
        # use a temp variable below because self.client.session is actually a
        # property which returns a new instance en each call :-/
        session = self.client.session
        session["user_id"] = u"testuser"
        session.save()

        try:
            response = self.client.get(reverse("user_votes"))
        except AttributeError:
            self.fail("Getting the votes should not fail if "
                      "the user has never voted yet\n%s" % format_exc())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<table>")
        self.assertNotContains(response, "<tbody>")



class LastViewsTestCase(ViewTestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
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
            self.store.add_to_list(ml, msg)
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
        self.store.add_to_list(ml, msg4)

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
