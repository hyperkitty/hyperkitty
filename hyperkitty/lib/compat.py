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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, unicode_literals, print_function

import re
import datetime

from django.http import Http404
from hyperkitty.models import MailingList

PORT_IN_URL = re.compile(r':\d+$')


def get_list_by_name(list_name, domain):
    matching = list(MailingList.objects.filter(name__startswith=list_name+"@"))
    if len(matching) == 0: # no candidate found
        raise Http404("No archived mailinglist by that name")
    if len(matching) == 1: # only one candidate
        return matching[0]

    # more than one result, try using the hostname
    domain = PORT_IN_URL.sub('', domain)
    list_fqdn = "%s@%s" % (list_name, domain)
    try:
        return MailingList.objects.get(name=list_fqdn)
    except MailingList.DoesNotExist:
        # return the first match, arbitrarily
        return matching[0]

def month_name_to_num(month_name):
    """map month names to months numbers"""
    today = datetime.date.today()
    months = dict( (today.replace(month=num).strftime('%B'), num)
                   for num in range(1, 12) )
    return months[month_name]
