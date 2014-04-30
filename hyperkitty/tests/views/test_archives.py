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

from hyperkitty.tests.utils import TestCase, ViewTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mailman.email.message import Message
from mailman.interfaces.archiver import ArchivePolicy

import kittystore
from kittystore.test import FakeList, SettingsModule



class ListArchivesTestCase(ViewTestCase):

    def setUp(self):
        # Create the list by adding a dummy message
        ml = FakeList("list@example.com")
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("Dummy message")
        self.store.add_to_list(ml, msg)

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



class PrivateArchivesTestCase(TestCase):

    def setUp(self):
        self.tmpdir = mkdtemp(prefix="hyperkitty-testing-")
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testPass')
        # Setup KittyStore with a working search index
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
