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

import re
import datetime

PORT_IN_URL = re.compile(':\d+$')


def get_list_by_name(list_name, store, request):
    arch_list_names = store.get_list_names()
    matching = []
    for name in arch_list_names:
        if name[:name.index("@")] == list_name:
            matching.append(name)

    if len(matching) == 0: # no candidate found
        return None
    if len(matching) == 1: # only one candidate
        return store.get_list(matching[0])

    # more than one result, try using the hostname
    domain = request.get_host()
    domain = PORT_IN_URL.sub('', domain)
    list_fqdn = "%s@%s" % (list_name, domain)
    if list_fqdn in matching:
        return store.get_list(list_fqdn)

    # return the first match, arbitrarily
    return store.get_list(matching[0])

def month_name_to_num(month_name):
    """map month names to months numbers"""
    today = datetime.date.today()
    months = dict( (today.replace(month=num).strftime('%B'), num)
                   for num in range(1, 12) )
    return months[month_name]
