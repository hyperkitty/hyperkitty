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

import datetime
import re
from collections import OrderedDict

import json
from dateutil.tz import tzoffset
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.timezone import utc

import hyperkitty.lib.posting
from hyperkitty.lib.utils import stripped_subject

register = template.Library()


@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        new_dict = OrderedDict()
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
def date_with_senders_timezone(email):
    """
    Rebuild the date of an email taking the sender's timezone into account.
    """
    tz = tzoffset(None, email.timezone * 60)
    return email.date.astimezone(tz)


SNIPPED_RE = re.compile(r"^(\s*&gt;).*$", re.M)
@register.filter(needs_autoescape=True)
def snip_quoted(content, quotemsg="...", autoescape=None):
    """Snip quoted text in messages"""
    if autoescape:
        content = conditional_escape(content)
    quoted = []
    current_quote = []
    current_quote_orig = []
    #lastline = None
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
        #lastline = line
    for quote_orig, quote in quoted:
        replaced = ('<div class="quoted-switch"><a style="font-weight:normal" href="#">%s</a></div>' % quotemsg
                   +'<div class="quoted-text">'
                   +"\n".join(quote)
                   +' </div>')
        content = content.replace("\n".join(quote_orig), replaced)
    return mark_safe(content)

SNIPPED_BEGIN_PGP = re.compile("^.*(BEGIN PGP SIGNATURE).*$", re.M)
SNIPPED_END_PGP = re.compile("^.*(END PGP SIGNATURE).*$", re.M)
@register.filter(needs_autoescape=True)
def snip_pgp(content, quotemsg="...PGP SIGNATURE...", autoescape=None):
    """Snip pgp signature in messages"""
    if autoescape:
        content = conditional_escape(content)
    quoted = []
    current_quote = []
    current_quote_orig = []
    pgp_signature = False
    for line in content.split("\n"):
        match_start = SNIPPED_BEGIN_PGP.match(line)
        match_end = SNIPPED_END_PGP.match(line)
        if match_end is not None or match_start is not None or pgp_signature:
            current_quote_orig.append(line)
            current_quote.append(line)
        # start of pgp signature
        if match_start is not None:
            pgp_signature = True
        # end of pgp signature
        elif match_end is not None:
            pgp_signature = False
            if current_quote_orig:
                current_quote_orig.append("")
                quoted.append( (current_quote_orig[:], current_quote[:]) )
                current_quote = []
                current_quote_orig = []
    for quote_orig, quote in quoted:
        replaced = ('<div class="quoted-switch"><a href="#" class="pgp">%s</a></div>' % quotemsg
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


@register.assignment_tag(takes_context=True)
def is_message_new(context, refdate):
    user = context["user"]
    last_view = context.get("last_view")
    refdate = refdate.replace(tzinfo=utc)
    return (user.is_authenticated() and
            (not last_view or refdate > last_view)
           )


@register.simple_tag(takes_context=True)
def add_to_query_string(context, *args, **kwargs):
    qs = context["request"].GET.copy()
    # create a dict from every args couple
    new_qs_elements = dict(zip(args[::2], args[1::2]))
    new_qs_elements.update(kwargs)
    # don't use the .update() method, it appends instead of overwriting
    for key, value in new_qs_elements.iteritems():
        qs[key] = value
    return qs.urlencode()


@register.filter
def until(value, limit):
    return value.partition(limit)[0]


@register.filter
def to_json(value):
    return json.dumps(value)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(is_safe=True)
def num_comments(thread):
    """Returns the number of comments in a thread"""
    try:
        return thread.emails_count - 1
    except (ValueError, TypeError):
        return ''


@register.filter
def reply_subject(value):
    return hyperkitty.lib.posting.reply_subject(value)


@register.filter(name="strip_subject")
def strip_subject(subject, mlist):
    return stripped_subject(mlist, subject)

@register.filter
def is_unread_by(thread, user):
    return thread.is_unread_by(user)

@register.filter
def sort_by_name(p_list):
    return sorted(p_list, key=lambda p: p.name.lower())
