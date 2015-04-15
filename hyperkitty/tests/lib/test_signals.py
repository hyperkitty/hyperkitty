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

# pylint: disable=too-many-public-methods,invalid-name

from __future__ import absolute_import, print_function, unicode_literals

from email.message import Message

from django.utils.timezone import now

from hyperkitty.models import MailingList, Email, Thread, Sender
from hyperkitty.lib.signals import new_email, new_thread
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.lib.utils import get_message_id_hash
from hyperkitty.tests.utils import TestCase


class EventsTestCase(TestCase):

    def setUp(self):
        self.mlist = MailingList.objects.create(name="example-list")
        self.events = []
        new_email.connect(self._store_events)
        new_thread.connect(self._store_events)

    def _store_events(self, sender, **kwargs):
        self.events.append( (sender, kwargs) )

    def _make_message(self, msg_id="dummy"):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Subject"] = "Fake Subject"
        msg["Message-ID"] = "<" + msg_id + ">"
        msg.set_payload("Fake Message")
        return msg

    def test_new_email_new_thread(self):
        msg = self._make_message()
        add_to_list("example-list", msg)
        #print(repr(self.events))
        self.assertEqual(len(self.events), 2)
        # The new_thread signal is received before the new_email signal,
        # because it is emitted by a listener of the new_email signal, but it
        # does not really matter.
        ## new_thread
        self.assertTrue("thread" in self.events[0][1])
        thread = self.events[0][1]["thread"]
        self.assertTrue(isinstance(thread, Thread))
        self.assertEqual(thread.thread_id, get_message_id_hash("dummy"))
        self.assertEqual(thread.emails.count(), 1)
        ## new_email
        self.assertTrue("email" in self.events[1][1])
        email = self.events[1][1]["email"]
        self.assertTrue(isinstance(email, Email))
        self.assertEqual(email.message_id, "dummy")

    def test_new_email_in_existing_thread(self):
        thread = Thread.objects.create(
            mailinglist=self.mlist, thread_id="dummy")
        sender = Sender.objects.create(address="dummy@example.com")
        email = Email.objects.create(
            mailinglist=self.mlist, sender=sender, thread=thread,
            date=now(), timezone=0, message_id="dummy")
        thread.starting_email = email
        thread.save()
        msg = self._make_message(msg_id="dummy2")
        msg["In-Reply-To"] = "<dummy>"
        add_to_list("example-list", msg)
        self.assertEqual(len(self.events), 1)
        self.assertTrue("email" in self.events[0][1])
        email = self.events[0][1]["email"]
        self.assertTrue(isinstance(email, Email))
        self.assertEqual(email.message_id, "dummy2")
        self.assertEqual(email.thread.thread_id, "dummy")
        self.assertEqual(email.thread.emails.count(), 2)


    #def test_catch_exceptions(self):
    #    def boom(sender, **kwargs):
    #        raise ValueError
    #    new_email.connect(boom)
    #    msg = self._make_message()
    #    try:
    #        add_to_list("example-list", msg)
    #    except Exception as e:
    #        self.fail(e)

    def test_do_not_catch_exceptions(self):
        class SpecificError(Exception):
            pass
        def boom(sender, **kwargs): # pylint: disable=unused-argument
            raise SpecificError
        new_email.connect(boom)
        msg = self._make_message()
        try:
            add_to_list("example-list", msg)
        except SpecificError:
            pass
        else:
            self.fail("The exception should have been propagated")
