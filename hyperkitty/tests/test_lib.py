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
#

import datetime
from traceback import print_exc, format_exc

from mock import Mock
from django.http import HttpRequest
from django.core.urlresolvers import reverse
import kittystore
from kittystore.test import SettingsModule

from hyperkitty.lib.view_helpers import get_display_dates, show_mlist
from hyperkitty.lib.paginator import paginate
from hyperkitty.lib.mailman import get_subscriptions

from hyperkitty.tests.utils import TestCase


class GetDisplayDatesTestCase(TestCase):

    def test_month(self):
        begin_date, end_date = get_display_dates('2012', '6', None)
        self.assertEqual(begin_date, datetime.datetime(2012, 6, 1))
        self.assertEqual(end_date, datetime.datetime(2012, 7, 1))

    def test_month_december(self):
        try:
            begin_date, end_date = get_display_dates('2012', '12', None)
        except ValueError, e:
            self.fail(e)
        self.assertEqual(begin_date, datetime.datetime(2012, 12, 1))
        self.assertEqual(end_date, datetime.datetime(2013, 1, 1))

    def test_day(self):
        begin_date, end_date = get_display_dates('2012', '4', '2')
        self.assertEqual(begin_date, datetime.datetime(2012, 4, 2))
        self.assertEqual(end_date, datetime.datetime(2012, 4, 3))


class PaginateTestCase(TestCase):

    def test_page_range(self):
        objects = range(1000)
        self.assertEqual(paginate(objects, 1).page_range,
                         [1, 2, 3, 4, '...', 100])
        self.assertEqual(paginate(objects, 2).page_range,
                         [1, 2, 3, 4, 5, '...', 100])
        self.assertEqual(paginate(objects, 3).page_range,
                         [1, 2, 3, 4, 5, 6, '...', 100])
        self.assertEqual(paginate(objects, 4).page_range,
                         [1, 2, 3, 4, 5, 6, 7, '...', 100])
        self.assertEqual(paginate(objects, 5).page_range,
                         [1, 2, 3, 4, 5, 6, 7, 8, '...', 100])
        self.assertEqual(paginate(objects, 6).page_range,
                         [1, 2, 3, 4, 5, 6, 7, 8, 9, '...', 100])
        self.assertEqual(paginate(objects, 7).page_range,
                         [1, '...', 4, 5, 6, 7, 8, 9, 10, '...', 100])
        self.assertEqual(paginate(objects, 8).page_range,
                         [1, '...', 5, 6, 7, 8, 9, 10, 11, '...', 100])
        self.assertEqual(paginate(objects, 9).page_range,
                         [1, '...', 6, 7, 8, 9, 10, 11, 12, '...', 100])
        self.assertEqual(paginate(objects, 10).page_range,
                         [1, '...', 7, 8, 9, 10, 11, 12, 13, '...', 100])
        self.assertEqual(paginate(objects, 40).page_range,
                         [1, '...', 37, 38, 39, 40, 41, 42, 43, '...', 100])
        self.assertEqual(paginate(objects, 90).page_range,
                         [1, '...', 87, 88, 89, 90, 91, 92, 93, '...', 100])
        self.assertEqual(paginate(objects, 91).page_range,
                         [1, '...', 88, 89, 90, 91, 92, 93, 94, '...', 100])
        self.assertEqual(paginate(objects, 92).page_range,
                         [1, '...', 89, 90, 91, 92, 93, 94, 95, '...', 100])
        self.assertEqual(paginate(objects, 93).page_range,
                         [1, '...', 90, 91, 92, 93, 94, 95, 96, '...', 100])
        self.assertEqual(paginate(objects, 94).page_range,
                         [1, '...', 91, 92, 93, 94, 95, 96, 97, '...', 100])
        self.assertEqual(paginate(objects, 95).page_range,
                         [1, '...', 92, 93, 94, 95, 96, 97, 98, 99, 100])
        self.assertEqual(paginate(objects, 96).page_range,
                         [1, '...', 93, 94, 95, 96, 97, 98, 99, 100])
        self.assertEqual(paginate(objects, 97).page_range,
                         [1, '...', 94, 95, 96, 97, 98, 99, 100])
        self.assertEqual(paginate(objects, 98).page_range,
                         [1, '...', 95, 96, 97, 98, 99, 100])
        self.assertEqual(paginate(objects, 99).page_range,
                         [1, '...', 96, 97, 98, 99, 100])
        self.assertEqual(paginate(objects, 100).page_range,
                         [1, '...', 97, 98, 99, 100])


#
# view_helpers.show_mlist()
#

class FakeKSList(object):
    def __init__(self, name):
        self.name = name

class ShowMlistTestCase(TestCase):

    def _do_test(self, listdomain, vhost, expected):
        mlist = FakeKSList("test@%s" % listdomain)
        req = HttpRequest()
        req.META["HTTP_HOST"] = vhost
        self.assertEqual(show_mlist(mlist, req), expected)

    def test_same_domain(self):
        self._do_test("example.com", "example.com", True)
        self._do_test("lists.example.com", "lists.example.com", True)

    def test_web_subdomain(self):
        self._do_test("example.com", "www.example.com", True)
        self._do_test("example.com", "lists.example.com", True)

    def test_mail_subdomain(self):
        self._do_test("lists.example.com", "example.com", True)

    def test_different_subdomains(self):
        self._do_test("lists.example.com", "archives.example.com", True)

    def test_different_domains(self):
        self._do_test("example.com", "another-example.com", False)
        self._do_test("lists.example.com", "archives.another-example.com", False)

    def test_single_component_domain(self):
        self._do_test("intranet", "intranet", True)

    def test_different_single_component_domain(self):
        self._do_test("intranet", "extranet", False)


#
# mailman.get_subscriptions()
#

class FakeMMList:
    def __init__(self, name):
        self.fqdn_listname = name

class MMGetSubTestCase(TestCase):

    def setUp(self):
        self.store = kittystore.get_store(
                SettingsModule(), debug=False, auto_create=True)
        self.client = Mock()
        self.client.get_list.side_effect = lambda name: FakeMMList(name)
        self.mm_user = Mock()
        self.mm_user.user_id = "123456"

    def test_user_not_in_ks(self):
        # The user is not in KittyStore yet, this should not prevent the
        # listing of the subscriptions in Mailman
        self.mm_user.subscription_list_ids = ["test@example.com",]
        try:
            subs = get_subscriptions(self.store, self.client, self.mm_user)
        except AttributeError, e:
            #print_exc()
            self.fail("Subscriptions should be available even if "
                      "the user has never voted yet\n%s" % format_exc())
        expected = [{
            'first_post': None, 'posts_count': 0,
            'likes': 0, 'dislikes': 0, 'likestatus': 'neutral',
            'list_name': "test@example.com",
            'all_posts_url': "%s?list=test@example.com"
                             % reverse("user_posts", args=["123456"]),
            }]
        self.assertEqual(subs, expected)
