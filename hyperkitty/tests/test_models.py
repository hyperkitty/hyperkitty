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

import string # pylint: disable=deprecated-module
import random
import uuid
from datetime import datetime
from email.message import Message
from traceback import format_exc

from mock import Mock
from django.contrib.auth.models import User
from django.utils.timezone import utc

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.lib.mailman import FakeMMList
from hyperkitty.models import MailingList, Email, Thread, Tag, ArchivePolicy
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
                    for _i in range(3000) ]
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


class EmailSetParentTestCase(TestCase):
    # pylint: disable=unbalanced-tuple-unpacking

    def _create_tree(self, tree):
        emails = []
        for msgid in tree:
            msg = Message()
            msg["From"] = "sender@example.com"
            msg["Message-ID"] = "<%s>" % msgid
            parent_id = msgid.rpartition(".")[0]
            if Email.objects.filter(message_id=parent_id).exists():
                msg["In-Reply-To"] = "<%s>" % parent_id
            msg.set_payload("dummy message")
            add_to_list("example-list", msg)
            emails.append(Email.objects.get(message_id=msgid))
        return emails

    def test_simple(self):
        email1, email2 = self._create_tree(["msg1", "msg2"])
        email2.set_parent(email1)
        self.assertEqual(email2.parent_id, email1.id)
        self.assertEqual(email2.thread_id, email1.thread_id)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertEqual(thread.id, email1.thread_id)
        self.assertEqual(thread.emails.count(), 2)
        self.assertEqual(
            list(thread.emails.order_by("thread_order")
                .values_list("message_id", flat=True)),
            ["msg1", "msg2"])
        self.assertEqual(thread.date_active, email2.date)

    def test_subthread(self):
        tree = ["msg1", "msg2", "msg2.1", "msg2.1.1", "msg2.1.1.1", "msg2.2"]
        emails = self._create_tree(tree)
        email1 = emails[0]
        email2 = emails[1]
        self.assertEqual(email2.thread.emails.count(), len(tree) - 1)
        email2.set_parent(email1)
        self.assertEqual(email2.parent_id, email1.id)
        self.assertEqual(email2.thread_id, email1.thread_id)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertEqual(thread.id, email1.thread_id)
        self.assertEqual(thread.emails.count(), len(tree))
        for msgid in tree:
            email = Email.objects.get(message_id=msgid)
            self.assertEqual(email.thread_id, email1.thread_id)
        self.assertEqual(tree,
            list(thread.emails.order_by("thread_order")
                .values_list("message_id", flat=True)))

    def test_switch(self):
        email1, email2 = self._create_tree(["msg1", "msg1.1"])
        email1.set_parent(email2)
        self.assertEqual(email1.parent, email2)
        self.assertEqual(email2.parent, None)

    def test_attach_to_child(self):
        emails = self._create_tree(["msg1", "msg1.1", "msg1.1.1", "msg1.1.2"])
        emails[1].set_parent(emails[2])
        self.assertEqual(emails[2].parent_id, emails[0].id)
        self.assertEqual(list(emails[0].thread.emails
            .order_by("thread_order").values_list("message_id", flat=True)),
            ["msg1", "msg1.1.1", "msg1.1", "msg1.1.2"])

    def test_attach_to_grandchild(self):
        emails = self._create_tree(
            ["msg1", "msg1.1", "msg1.1.1", "msg1.1.2", "msg1.1.1.1"])
        emails[1].set_parent(emails[-1])
        self.assertEqual(emails[-1].parent_id, emails[0].id)
        self.assertEqual(list(emails[0].thread.emails
            .order_by("thread_order").values_list("message_id", flat=True)),
            ["msg1", "msg1.1.1.1", "msg1.1", "msg1.1.1", "msg1.1.2"])

    def test_attach_to_itself(self):
        email1 = self._create_tree(["msg1"])[0]
        self.assertRaises(ValueError, email1.set_parent, email1)



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

    def test_revote(self):
        # Overwrite the existing vote
        _create_email(1)
        msg = Email.objects.get(message_id="msg1")
        msg.vote(1, self.user)
        msg.vote(-1, self.user)
        votes = msg.get_votes()
        self.assertEqual(votes["likes"], 0)
        self.assertEqual(votes["dislikes"], 1)

    def test_revote_identical(self):
        # Voting in the same manner twice should not fail
        _create_email(1)
        msg = Email.objects.get(message_id="msg1")
        msg.vote(1, self.user)
        msg.vote(1, self.user)

    def test_vote_invalid(self):
        # Fail on invalid votes
        _create_email(1)
        msg = Email.objects.get(message_id="msg1")
        self.assertRaises(ValueError, msg.vote, 2, self.user)


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
        except AttributeError:
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


class MailingListTestCase(TestCase):

    def setUp(self):
        self.ml = MailingList.objects.create(name="list@example.com")
        self.mailman_ml = FakeMMList("list@example.com")
        self.mailman_client.get_list.side_effect = lambda n: self.mailman_ml

    def test_update_from_mailman(self):
        self.ml.display_name = "original-value"
        self.ml.description = "original-value"
        self.ml.subject_prefix = "original-value"
        self.ml.created_at = datetime(2000, 1, 1, 0, 0, 0, tzinfo=utc)
        self.ml.archive_policy = ArchivePolicy.public.value
        self.ml.save()

        self.mailman_ml.display_name = "new-value"
        self.mailman_ml.settings["description"] = "new-value"
        self.mailman_ml.settings["subject_prefix"] = "new-value"
        self.mailman_ml.settings["archive_policy"] = "private"
        new_date = datetime(2010, 12, 31, 0, 0, 0, tzinfo=utc)
        self.mailman_ml.settings["created_at"] = new_date.isoformat()

        self.ml.update_from_mailman()
        self.assertEqual(self.ml.display_name, "new-value")
        self.assertEqual(self.ml.description, "new-value")
        self.assertEqual(self.ml.subject_prefix, "new-value")
        self.assertEqual(self.ml.created_at, new_date)
        self.assertEqual(self.ml.archive_policy, ArchivePolicy.private.value)

    def test_get_threads_between(self):
        # the get_threads_between method should return all threads that have
        # been active between the two specified dates, including the threads
        # started in between those dates but updated later
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-02-15 00:00:00 UTC"
        msg1.set_payload("message 1")
        add_to_list(self.ml.name, msg1)
        # The thread started in Feb, it should show up in the Feb threads but
        # not in the January or March threads.
        self.assertEqual(Thread.objects.count(), 1)
        jan_threads = self.ml.get_threads_between(
            datetime(2015, 1, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 1, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(jan_threads.count(), 0)
        feb_threads = self.ml.get_threads_between(
            datetime(2015, 2, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 2, 28, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(feb_threads.count(), 1)
        march_threads = self.ml.get_threads_between(
            datetime(2015, 3, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 3, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(march_threads.count(), 0)

    def test_get_threads_between_across_months(self):
        # the get_threads_between method should return all threads that have
        # been active between the two specified dates, including the threads
        # started in between those dates but updated later
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-02-15 00:00:00 UTC"
        msg1.set_payload("message 1")
        add_to_list(self.ml.name, msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = "<msg1>"
        msg2["Date"] = "2015-03-15 00:00:00 UTC"
        msg2.set_payload("message 2")
        add_to_list(self.ml.name, msg2)
        # The thread started in Feb, was updated in March. It should show up in both the Feb threads and the March threads.
        self.assertEqual(Thread.objects.count(), 1)
        feb_threads = self.ml.get_threads_between(
            datetime(2015, 2, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 2, 28, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(feb_threads.count(), 1)
        march_threads = self.ml.get_threads_between(
            datetime(2015, 3, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 3, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(march_threads.count(), 1)

    def test_get_threads_between_across_two_months(self):
        # the get_threads_between method should return all threads that have
        # been active between the two specified dates, including the threads
        # started in between those dates but updated later
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-01-15 00:00:00 UTC"
        msg1.set_payload("message 1")
        add_to_list(self.ml.name, msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = "<msg1>"
        msg2["Date"] = "2015-03-15 00:00:00 UTC"
        msg2.set_payload("message 2")
        add_to_list(self.ml.name, msg2)
        # The thread started in Jan, was updated in March. It should show up in
        # the Jan, Feb and March threads.
        self.assertEqual(Thread.objects.count(), 1)
        jan_threads = self.ml.get_threads_between(
            datetime(2015, 1, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 1, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(jan_threads.count(), 1)
        feb_threads = self.ml.get_threads_between(
            datetime(2015, 2, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 2, 28, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(feb_threads.count(), 1)
        march_threads = self.ml.get_threads_between(
            datetime(2015, 3, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 3, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(march_threads.count(), 1)
