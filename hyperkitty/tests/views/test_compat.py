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


from __future__ import absolute_import, print_function, unicode_literals

from email.message import Message
from django.core.urlresolvers import reverse
from hyperkitty.models import MailingList
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.tests.utils import TestCase


class CompatURLsTestCase(TestCase):

    def setUp(self):
        MailingList.objects.create(name="list@example.com")
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msgid>"
        msg["Subject"] = "Dummy message"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0000"
        msg.set_payload("Dummy message")
        msg["Message-ID-Hash"] = self.msgid = add_to_list("list@example.com", msg)

    def test_redirect_month(self):
        url_list = ["pipermail/list/2015-February/",
                    "list/list@example.com/2015-February/"]
        expected_url = reverse('hk_archives_with_month', kwargs={
            'mlist_fqdn': 'list@example.com',
            'year': '2015', 'month': '02' })
        for url in url_list:
            response = self.client.get(reverse("hk_root") + url)
            self.assertRedirects(response, expected_url)

    def test_redirect_message(self):
        url_list = ["pipermail/list/2015-February/000001.html",
                    "list/list@example.com/2015-February/000001.html"]
        expected_url = reverse('hk_message_index', kwargs={
            'mlist_fqdn': 'list@example.com',
            'message_id_hash': self.msgid })
        for url in url_list:
            response = self.client.get(reverse("hk_root") + url)
            self.assertRedirects(response, expected_url)
