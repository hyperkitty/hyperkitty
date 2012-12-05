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

from django.test import TestCase

from hyperkitty.templatetags.hk_generic import snip_quoted

class SnipQuotedTestCase(TestCase):

    quotemsg = "[SNIP]"

    def test_quote_1(self):
        contents = """
On Fri, 09.11.12 11:27, Someone wrote:
&gt; This is the first quoted line
&gt; This is the second quoted line
This is the response.
"""
        expected = """
On Fri, 09.11.12 11:27, Someone wrote:
<a href="#" class="quoted-switch">%s</a><span class="quoted-text">
&gt; This is the first quoted line
&gt; This is the second quoted line</span>
This is the response.
""" % self.quotemsg
        result = snip_quoted(contents, self.quotemsg)
        self.assertEqual(result, expected)

    def test_quote_2(self):
        """The quote starts with a newline"""
        contents = """
On Fri, 09.11.12 11:27, Someone wrote:

&gt; This is the first quoted line
&gt; This is the second quoted line
This is the response.
"""
        expected = """
On Fri, 09.11.12 11:27, Someone wrote:
<a href="#" class="quoted-switch">%s</a><span class="quoted-text">
&gt; This is the first quoted line
&gt; This is the second quoted line</span>
This is the response.
""" % self.quotemsg
        result = snip_quoted(contents, self.quotemsg)
        self.assertEqual(result, expected)
