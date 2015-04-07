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

from hyperkitty.lib.paginator import paginate
from hyperkitty.tests.utils import TestCase


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

    def test_default_page(self):
        self.assertEqual(paginate(range(100), None).number, 1)

    def test_last_page(self):
        self.assertEqual(paginate(range(100), 1000).number, 10)
