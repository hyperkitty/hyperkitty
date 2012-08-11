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
from hyperkitty.models import Rating, Tag

class RatingTestCase(TestCase):
    fixtures = ['rating_testdata.json']

    def setUp(self):
        super(RatingTestCase, self).setUp()
        self.rating_1 = Rating.objects.get(pk=1)
        self.rating_2 = Rating.objects.get(pk=2)

    def test_was_published_today(self):
        # Test the value of Poll should be +1/-1 only.
        self.assertTrue((self.rating_1.vote == 1) | (self.rating_1.vote == -1))
        self.assertTrue((self.rating_2.vote == 1) | (self.rating_2.vote == -1))

class TagTestCase(TestCase):
    fixtures = ['tag_testdata.json']

    def setUp(self):
        super(TagTestCase, self).setUp()
        self.tag_1 = Tag.objects.get(pk=1)
