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

import datetime
import re

from dateutil.tz import tzutc, tzoffset
from django import template
from django.utils.datastructures import SortedDict
from django.templatetags.tz import localtime
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def trimString(str):
    return re.sub('\s+', ' ', str)


@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        new_dict = SortedDict()
        key_list = value.keys()
        key_list.sort()
        key_list.reverse()
        for key in key_list:
            values = value[key]
            values.sort()
            values.reverse()
            new_dict[key] = values
        return new_dict.items()
    elif isinstance(value, list):
        new_list = list(value)
        new_list.sort()
        return new_list
    else:
        return value
    listsort.is_safe = True


@register.filter(name="monthtodate")
def to_date(month, year):
    return datetime.date(year, month, 1)


@register.filter
def strip_page(value):
    print repr(value), repr(value)[-2]
    if not value:
        return value
    if value.endswith('/') and value[-3] == '/':
        end_with_number = False
        try:
            if int(value[-2]) in range(0,10):
                end_with_number = True
            if end_with_number:
                output = value.rsplit('/', 2)
        except ValueError:
            output = value.rsplit('/', 1)
    else:
        output = value.rsplit('/', 1)
    return output[0]


# From http://djangosnippets.org/snippets/1259/
@register.filter
def truncatesmart(value, limit=80):
    """
    Truncates a string after a given number of chars keeping whole words.

    Usage:
        {{ string|truncatesmart }}
        {{ string|truncatesmart:50 }}
    """
    try:
        limit = int(limit)
    # invalid literal for int()
    except ValueError:
        # Fail silently.
        return value

    # Make sure it's unicode
    value = unicode(value)

    # Return the string itself if length is smaller or equal to the limit
    if len(value) <= limit:
        return value

    # Cut the string
    value = value[:limit]

    # Break into words and remove the last
    words = value.split(' ')[:-1]

    # Join the words and return
    return ' '.join(words) + '...'


MAILTO_RE = re.compile("<a href=['\"]mailto:([^'\"]+)@([^'\"]+)['\"]>[^<]+</a>")
@register.filter(is_safe=True)
def escapeemail(text):
    """To escape email addresses"""
    # reverse the effect of urlize() on email addresses
    text = MAILTO_RE.sub(r"\1(a)\2", text)
    return text.replace("@", u"\uff20")


@register.filter()
def sender_date(email):
    tz = tzoffset(None, email.timezone * 60)
    email_date = email.date.replace(tzinfo=tzutc())
    return email_date.astimezone(tz)


@register.filter()
def viewer_date(email_or_thread):
    if hasattr(email_or_thread, 'date'):
        date_obj = email_or_thread.date
    elif hasattr(email_or_thread, 'date_active'):
        date_obj = email_or_thread.date_active
    return localtime(date_obj.replace(tzinfo=tzutc()))


SNIPPED_RE = re.compile("^(\s*&gt;).*$", re.M)
@register.filter(needs_autoescape=True)
def snip_quoted(content, quotemsg="...", autoescape=None):
    """Snip quoted text in messages"""
    if autoescape:
        content = conditional_escape(content)
    quoted = []
    current_quote = []
    current_quote_orig = []
    lastline = None
    for line in content.split("\n"):
        match = SNIPPED_RE.match(line)
        if match is not None:
            #if lastline == "":
            #    current_quote_orig.append(lastline)
            current_quote_orig.append(line)
            content_start = len(match.group(1))
            current_quote.append(line[content_start:])
        else:
            if current_quote_orig:
                current_quote_orig.append("")
                quoted.append( (current_quote_orig[:], current_quote[:]) )
                current_quote = []
                current_quote_orig = []
        lastline = line
    for quote_orig, quote in quoted:
        replaced = ('<div class="quoted-switch"><a href="#">%s</a></div>' % quotemsg
                   +'<div class="quoted-text">'
                   +"\n".join(quote)
                   +' </div>')
        content = content.replace("\n".join(quote_orig), replaced)
    return mark_safe(content)


@register.filter()
def multiply(num1, num2):
    if int(num2) == float(num2):
        num2 = int(num2)
    else:
        num2 = float(num2)
    return num1 * num2
