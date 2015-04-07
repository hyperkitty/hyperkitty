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

# pylint: disable=unnecessary-lambda

from __future__ import absolute_import, print_function, unicode_literals

import uuid
from email.message import Message

from mock import Mock
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.lib.mailman import FakeMMList
from hyperkitty.models import MailingList, ArchivePolicy
from hyperkitty.tests.utils import SearchEnabledTestCase



class SearchViewsTestCase(SearchEnabledTestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')
        self.mailman_client.get_list.side_effect = lambda name: FakeMMList(name)
        self.mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: self.mm_user
        self.mm_user.user_id = uuid.uuid1().int
        self.mm_user.addresses = ["testuser@example.com"]

    def _send_message(self, mlist):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Message-ID"] = "<msg>"
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy content with keyword")
        return add_to_list(mlist.name, msg)

    def test_search(self):
        #self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_search"), {"q": "dummy"})
        self.assertEqual(response.status_code, 200)

    def test_search_private_list(self):
        mlist = MailingList.objects.create(
            name="private@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mm_mlist = FakeMMList("private@example.com")
        mm_mlist.settings["archive_policy"] = "private"
        self.mailman_client.get_list.side_effect = lambda name: mm_mlist
        self.mm_user.subscription_list_ids = ["private@example.com",]
        self._send_message(mlist)
        response = self.client.get(reverse("hk_search"),
            {"q": "dummy", "mlist": "private@example.com"})
        self.assertEqual(response.status_code, 403)
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_search"),
            {"q": "dummy", "mlist": "private@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dummy message")

    def test_search_private_lists(self):
        # Create 1 public and 2 private lists
        mlist_public = MailingList.objects.create(name="public@example.com")
        mlist_private = MailingList.objects.create(
            name="private@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mlist_private_sub = MailingList.objects.create(
            name="private-sub@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        # (make sure the mailman client will not reset the archive_policy)
        mailman_lists = {
            "public@example.com": FakeMMList("public@example.com"),
            "private@example.com": FakeMMList("private@example.com"),
            "private-sub@example.com": FakeMMList("private-sub@example.com"),
        }
        mailman_lists["private@example.com"].settings["archive_policy"] = "private"
        mailman_lists["private-sub@example.com"].settings["archive_policy"] = "private"
        self.mailman_client.get_list.side_effect = lambda name: mailman_lists[name]
        # Subscribe the user to one of the private lists
        self.mm_user.subscription_list_ids = ["private-sub@example.com",]
        # Populate the lists with messages
        self._send_message(mlist_public)
        self._send_message(mlist_private)
        self._send_message(mlist_private_sub)
        # There must be a result from the public and the subscribed list only
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_search"), {"q": "keyword"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["messages"].paginator.count, 2)
        self.assertContains(response, "Dummy message", count=2)
