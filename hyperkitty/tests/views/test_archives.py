# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 by the Free Software Foundation, Inc.
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

# pylint: disable=unnecessary-lambda

from __future__ import absolute_import, print_function, unicode_literals

import datetime
from email.message import Message

from mock import Mock
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from hyperkitty.models import MailingList, ArchivePolicy
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.lib.mailman import FakeMMList
from hyperkitty.tests.utils import TestCase


class ListArchivesTestCase(TestCase):

    def setUp(self):
        # Create the list by adding a dummy message
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("Dummy message")
        add_to_list("list@example.com", msg)

    def test_no_date(self):
        today = datetime.date.today()
        response = self.client.get(reverse(
                'hk_archives_latest', args=['list@example.com']))
        final_url = reverse('hk_archives_with_month',
                kwargs={'mlist_fqdn': 'list@example.com',
                        'year': today.year,
                        'month': today.month,
                })
        self.assertRedirects(response, final_url)

    def test_wrong_date(self):
        response = self.client.get(reverse(
                'hk_archives_with_month', kwargs={
                    'mlist_fqdn': 'list@example.com',
                    'year': '9999',
                    'month': '0',
                }))
        self.assertEqual(response.status_code, 404)


class PrivateArchivesTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        MailingList.objects.create(
            name="list@example.com", subject_prefix="[example] ",
            archive_policy=ArchivePolicy.private.value)
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msgid>"
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy message")
        msg["Message-ID-Hash"] = self.msgid = add_to_list("list@example.com", msg)
        # Set the mailman_client after the message has been added to the list,
        # otherwise MailingList.update_from_mailman() will overwrite the list
        # properties.
        self.mailman_client.get_list.side_effect = lambda name: FakeMMList(name)
        self.mm_user = Mock()
        self.mm_user.user_id = "dummy"
        self.mailman_client.get_user.side_effect = lambda name: self.mm_user
        self.mm_user.subscription_list_ids = ["list@example.com",]

    def tearDown(self):
        self.client.logout()


    def _do_test(self, url, query=None):
        if query is None:
            query = {}
        response = self.client.get(url, query)
        self.assertEqual(response.status_code, 403)
        self.client.login(username='testuser', password='testPass')
        ## use a temp variable below because self.client.session is actually a
        ## property which returns a new instance en each call :-/
        ## http://blog.joshcrompton.com/2012/09/how-to-use-sessions-in-django-unit-tests.html
        #session = self.client.session
        #session["subscribed"] = ["list@example.com"]
        #session.save()
        #self.user.hyperkitty_profile.get_subscriptions = lambda: ["list@example.com"]
        response = self.client.get(url, query)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dummy message")


    def test_month_view(self):
        now = datetime.datetime.now()
        self._do_test(reverse('hk_archives_with_month', args=["list@example.com", now.year, now.month]))

    def test_overview(self):
        self._do_test(reverse('hk_list_overview', args=["list@example.com"]))

    def test_thread_view(self):
        self._do_test(reverse('hk_thread', args=["list@example.com", self.msgid]))

    def test_message_view(self):
        self._do_test(reverse('hk_message_index', args=["list@example.com", self.msgid]))
