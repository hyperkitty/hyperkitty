# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
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

from __future__ import absolute_import, print_function, unicode_literals

from email.message import Message

from django.utils.timezone import now

from hyperkitty.models import MailingList, Email, Thread, Sender
from hyperkitty.lib.analysis import compute_thread_order_and_depth
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.tests.utils import TestCase



class TestThreadOrderDepth(TestCase):

    def setUp(self):
        self.mlist = MailingList.objects.create(name="example-list")

    def make_fake_email(self, num=1, date=None, thread=None):
        sender = Sender.objects.get_or_create(
            address="sender%d@example.com" % num)[0]
        if thread is None:
            thread = Thread.objects.filter(
                mailinglist=self.mlist, thread_id="msg%d" % num)[0]
        if date is None:
            date = now()
        msg = Email(
            mailinglist=self.mlist,
            message_id="msg%d" % num,
            subject="subject %d" % num,
            content="message %d" % num,
            sender=sender,
            thread=thread,
            date=date,
            timezone=0,
        )
        return msg

    def test_simple_thread(self):
        # A basic thread: msg2 replies to msg1
        thread = Thread.objects.create(mailinglist=self.mlist, thread_id="msg1")
        msg1 = self.make_fake_email(1, thread=thread)
        msg1.thread_order = msg1.thread_depth = 42
        msg1.save()
        thread.starting_email = msg1
        thread.save()
        msg2 = self.make_fake_email(2, thread=thread)
        msg2.parent = msg1
        msg2.thread_order = msg2.thread_depth = 42
        msg2.save()
        compute_thread_order_and_depth(thread)
        # Must reload from the database
        msg1 = Email.objects.get(id=msg1.id)
        msg2 = Email.objects.get(id=msg2.id)
        self.assertEqual(msg1.thread_order, 0)
        self.assertEqual(msg1.thread_depth, 0)
        self.assertEqual(msg2.thread_order, 1)
        self.assertEqual(msg2.thread_depth, 1)

    def test_classical_thread(self):
        # msg1
        # |-msg2
        # | `-msg4
        # `-msg3
        thread = Thread.objects.create(mailinglist=self.mlist, thread_id="msg1")
        # All in the same thread
        msg1 = self.make_fake_email(1, thread=thread)
        msg2 = self.make_fake_email(2, thread=thread)
        msg3 = self.make_fake_email(3, thread=thread)
        msg4 = self.make_fake_email(4, thread=thread)
        # Set up the reply tree
        msg1.save()
        thread.starting_email = msg1
        thread.save()
        msg2.parent = msg3.parent = msg1
        msg2.save()
        msg3.save()
        msg4.parent = msg2
        msg4.save()
        # Init with false values
        msg1.thread_order = msg1.thread_depth = \
                msg2.thread_order = msg2.thread_depth = \
                msg3.thread_order = msg3.thread_depth = \
                msg4.thread_order = msg4.thread_depth = 42
        msg1.save()
        msg2.save()
        msg3.save()
        msg4.save()
        compute_thread_order_and_depth(thread)
        msg1 = Email.objects.get(id=msg1.id)
        msg2 = Email.objects.get(id=msg2.id)
        msg3 = Email.objects.get(id=msg3.id)
        msg4 = Email.objects.get(id=msg4.id)
        self.assertEqual(msg1.thread_order, 0)
        self.assertEqual(msg1.thread_depth, 0)
        self.assertEqual(msg2.thread_order, 1)
        self.assertEqual(msg2.thread_depth, 1)
        self.assertEqual(msg3.thread_order, 3)
        self.assertEqual(msg3.thread_depth, 1)
        self.assertEqual(msg4.thread_order, 2)
        self.assertEqual(msg4.thread_depth, 2)

    def test_add_in_classical_thread(self):
        # msg1
        # |-msg2
        # | `-msg4
        # `-msg3
        msgs = []
        for num in range(1, 5):
            msg = Message()
            msg["From"] = "sender%d@example.com" % num
            msg["Message-ID"] = "<msg%d>" % num
            msg.set_payload("message %d" % num)
            msgs.append(msg)
        msgs[1]["In-Reply-To"] = "<msg1>"
        msgs[2]["In-Reply-To"] = "<msg1>"
        msgs[3]["In-Reply-To"] = "<msg2>"
        for msg in msgs:
            add_to_list("example-list", msg)
        msgs = []
        for num in range(1, 5):
            msg = Email.objects.filter(
                mailinglist=self.mlist, message_id="msg%d" % num).first()
            msgs.append(msg)
        msg1, msg2, msg3, msg4 = msgs # pylint: disable=unbalanced-tuple-unpacking
        self.assertEqual(msg1.thread_order, 0)
        self.assertEqual(msg1.thread_depth, 0)
        self.assertEqual(msg2.thread_order, 1)
        self.assertEqual(msg2.thread_depth, 1)
        self.assertEqual(msg3.thread_order, 3)
        self.assertEqual(msg3.thread_depth, 1)
        self.assertEqual(msg4.thread_order, 2)
        self.assertEqual(msg4.thread_depth, 2)

    def test_reply_to_oneself(self):
        # A message replying to itself (yes, it's been spotted in the wild)
        thread = Thread.objects.create(mailinglist=self.mlist, thread_id="msg1")
        msg1 = self.make_fake_email(1)
        msg1.save()
        thread.starting_email = msg1
        thread.save()
        msg1.parent = msg1
        msg1.thread_order = msg1.thread_depth = 42
        msg1.save()
        compute_thread_order_and_depth(thread)
        msg1 = Email.objects.get(id=msg1.id)
        # Don't traceback with a "maximum recursion depth exceeded" error
        self.assertEqual(msg1.thread_order, 0)
        self.assertEqual(msg1.thread_depth, 0)

    def test_reply_loops(self):
        """Loops in message replies"""
        # This implies that someone replies to a message not yet sent, but you
        # never know, Dr Who can be on your mailing-list.
        thread = Thread.objects.create(mailinglist=self.mlist, thread_id="msg1")
        msg1 = self.make_fake_email(1, thread=thread)
        msg1.save()
        thread.starting_email = msg1
        thread.save()
        msg2 = self.make_fake_email(2, thread=thread)
        msg2.parent = msg1
        msg2.save()
        msg1.parent = msg2
        msg1.save()
        compute_thread_order_and_depth(thread)
        # Don't traceback with a "maximum recursion depth exceeded" error
