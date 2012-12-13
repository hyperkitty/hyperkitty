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

from django.test import TestCase

from hyperkitty.lib import get_display_dates


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
