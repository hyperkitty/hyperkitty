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

from __future__ import absolute_import, unicode_literals, print_function

from xml.sax.saxutils import escape

from django import template
register = template.Library()

@register.filter
def nolongterms(text):
    """
    Remove terms longer than 245 chars, or Xapian will choke on them:
    https://github.com/notanumber/xapian-haystack/issues/77
    The size check is done on the XML-escaped and quotes-escaped encoded
    version of the term, with the XTEXT prefix (thus the '240' limit)
    """
    def _getlen(word):
        return len(escape(word)
            .replace('"', '&quot;').replace("'", "&#39;").encode("utf-8"))
    return ' '.join(word for word in text.split() if _getlen(word) < 240)
