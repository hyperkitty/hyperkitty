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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

# pylint: disable=unnecessary-lambda

from __future__ import absolute_import, print_function, unicode_literals

import string
import random
import uuid
from email.message import Message
from traceback import format_exc

from mock import Mock
from django.contrib.auth.models import User

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.lib.mailman import FakeMMList
from hyperkitty.models import MailingList, Email, Thread, Sender, Tag
from hyperkitty.tests.utils import TestCase


class TagTestCase(TestCase):
    fixtures = ['tag_testdata.json']

    def setUp(self):
        super(TagTestCase, self).setUp()
        self.tag_1 = Tag.objects.get(pk=1)


class ThreadTestCase(TestCase):

    def test_starting_message_1(self):
        # A basic thread: msg2 replies to msg1
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1.set_payload("message 1")
        add_to_list("example-list", msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2.set_payload("message 2")
        msg2["In-Reply-To"] = msg1["Message-ID"]
        add_to_list("example-list", msg2)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.starting_email.message_id, "msg1")

    def test_starting_message_2(self):
        # A partially-imported thread: msg1 replies to something we don't have
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["In-Reply-To"] = "<msg0>"
        msg1.set_payload("message 1")
        add_to_list("example-list", msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = msg1["Message-ID"]
        msg2.set_payload("message 2")
        add_to_list("example-list", msg2)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.starting_email.message_id, "msg1")

    def test_starting_message_3(self):
        # A thread where the reply has an anterior date to the first email
        # (the In-Reply-To header must win over the date sort)
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg1.set_payload("message 1")
        add_to_list("example-list", msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["Date"] = "Fri, 01 Nov 2012 16:07:54 +0000"
        msg2.set_payload("message 2")
        msg2["In-Reply-To"] = msg1["Message-ID"]
        add_to_list("example-list", msg2)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.starting_email.message_id, "msg1")

    def test_subject(self):
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["Message-ID"] = "<dummymsg>"
        msg["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg["Subject"] = "Dummy subject"
        msg.set_payload("Dummy message")
        add_to_list("example-list", msg)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.subject, "Dummy subject")

    def test_thread_no_email(self):
        mlist = MailingList.objects.create(name="example-list")
        Thread.objects.create(mailinglist=mlist, thread_id="<msg1>")

    def test_long_subject(self):
        # PostgreSQL will raise an OperationalError if the subject's index is
        # longer than 2712, but SQLite will accept anything, so we must test
        # with assertions here.
        # We use random chars to build the subject, if we use a single repeated
        # char, the index will never be big enough.
        subject = [ random.choice(string.letters + string.digits + " ")
                    for i in range(3000) ]
        subject = "".join(subject)
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["Message-ID"] = "<dummymsg>"
        msg["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg["Subject"] = subject
        msg.set_payload("Dummy message")
        add_to_list("example-list", msg)
        self.assertEqual(Email.objects.count(), 1)
        msg_db = Email.objects.all()[0]
        self.assertTrue(len(msg_db.subject) < 2712,
                "Very long subjects are not trimmed")


def _create_email(num, reply_to=None):
    msg = Message()
    msg["From"] = "sender%d@example.com" % num
    msg["Message-ID"] = "<msg%d>" % num
    msg.set_payload("message %d" % num)
    if reply_to is not None:
        msg["In-Reply-To"] = "<msg%d>" % reply_to
    return add_to_list("example-list", msg)

class VoteTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="dummy")

    def test_msg_1(self):
        # First message in thread is voted for
        _create_email(1)
        _create_email(2, reply_to=1)
        _create_email(3, reply_to=2)
        msg1 = Email.objects.get(message_id="msg1")
        msg1.vote(1, self.user)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        votes = thread.get_votes()
        self.assertEqual(votes["likes"], 1)
        self.assertEqual(votes["dislikes"], 0)
        self.assertEqual(votes["status"], "like")

    def test_msg2(self):
        # Second message in thread is voted against
        _create_email(1)
        _create_email(2, reply_to=1)
        _create_email(3, reply_to=2)
        msg2 = Email.objects.get(message_id="msg2")
        msg2.vote(-1, self.user)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        votes = thread.get_votes()
        self.assertEqual(votes["likes"], 0)
        self.assertEqual(votes["dislikes"], 1)
        self.assertEqual(votes["status"], "neutral")

    def test_likealot(self):
        # All messages in thread are voted for
        for num in range(1, 11):
            if num == 1:
                reply_to = None
            else:
                reply_to = num - 1
            _create_email(num, reply_to=reply_to)
            msg = Email.objects.get(message_id="msg%d" % num)
            msg.vote(1, self.user)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        votes = thread.get_votes()
        self.assertEqual(votes["likes"], 10)
        self.assertEqual(votes["dislikes"], 0)
        self.assertEqual(votes["status"], "likealot")

    def test_same_msgid_different_lists(self):
        # Vote on messages with the same msgid but on different lists
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("message")
        add_to_list("example-list-1", msg)
        add_to_list("example-list-2", msg)
        self.assertEqual(Email.objects.count(), 2)
        for msg in Email.objects.all():
            msg.vote(1, self.user)
        self.assertEqual(Thread.objects.count(), 2)
        for thread in Thread.objects.all():
            votes = thread.get_votes()
            self.assertEqual(votes["likes"], 1)
            self.assertEqual(votes["dislikes"], 0)


class ProfileTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="dummy")

    def test_get_subscriptions(self):
        self.mailman_client.get_list.side_effect = lambda name: FakeMMList(name)
        mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: mm_user
        mm_user.user_id = uuid.uuid1().int
        mm_user.subscription_list_ids = ["test@example.com",]
        MailingList.objects.create(name="test@example.com")
        try:
            subs = self.user.hyperkitty_profile.get_subscriptions()
        except AttributeError, e:
            #print_exc()
            self.fail("Subscriptions should be available even if "
                      "the user has never voted yet\n%s" % format_exc())
        self.assertEqual(subs, ["test@example.com"])

    def test_votes_in_list(self):
        # Count the number of votes in a list
        _create_email(1)
        _create_email(2, reply_to=1)
        _create_email(3, reply_to=2)
        msg1 = Email.objects.get(message_id="msg1")
        msg1.vote(1, self.user)
        msg2 = Email.objects.get(message_id="msg2")
        msg2.vote(-1, self.user)
        self.assertEqual( (1, 1),
            self.user.hyperkitty_profile.get_votes_in_list("example-list"))
