#-*- coding: utf-8 -*-
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

import urllib
from hashlib import md5
import datetime

from django.conf import settings


def gravatar_url(email):
    '''Return a gravatar url for an email address'''
    size = 64
    default = "http://fedoraproject.org/static/images/" + \
            "fedora_infinity_%ix%i.png" % (size, size)
    query_string = urllib.urlencode({'s': size, 'd': default})
    identifier = md5(email).hexdigest()
    return 'http://www.gravatar.com/avatar/%s?%s' % (identifier, query_string)


def get_months(store, list_name):
    """ Return a dictionnary of years, months for which there are
    potentially archives available for a given list (based on the
    oldest post on the list).

    :arg list_name, name of the mailing list in which this email
    should be searched.
    """
    date_first = store.get_start_date(list_name)
    if not date_first:
        return {}
    archives = {}
    now = datetime.datetime.now()
    year = date_first.year
    month = date_first.month
    while year < now.year:
        archives[year] = range(1, 13)[(month -1):]
        year = year + 1
        month = 1
    archives[now.year] = range(1, 13)[:now.month]
    return archives


def get_store(request):
    return request.environ["kittystore.store"]


def stripped_subject(mlist, subject):
    if mlist is None:
        return subject
    list_name = mlist.display_name or mlist.name[:mlist.name.index("@")]
    if subject.lower().startswith("[%s] " % list_name.lower()):
        subject = subject[len(list_name)+3 : ]
    return subject
