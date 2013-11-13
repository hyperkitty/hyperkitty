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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#


import urllib2
import datetime
from collections import defaultdict

import django.utils.simplejson as json

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from mailmanclient import Client, MailmanConnectionError
from mailman.interfaces.archiver import ArchivePolicy

from hyperkitty.lib import get_store
from hyperkitty.lib.view_helpers import get_recent_list_activity
from hyperkitty.lib.mailman import is_mlist_authorized


def index(request):
    store = get_store(request)
    lists = store.get_lists()
    for mlist in lists:
        if mlist.archive_policy != ArchivePolicy.private:
            mlist.is_private = False
            mlist.can_view = True
        else:
            mlist.is_private = True
            if is_mlist_authorized(request, mlist):
                mlist.can_view = True
            else:
                mlist.can_view = False
        if mlist.can_view:
            mlist.evolution = get_recent_list_activity(store, mlist)

    # sorting
    sort_mode = request.GET.get('sort')
    if sort_mode == "active":
        lists.sort(key=lambda l: l.recent_threads_count)
    elif sort_mode == "popular":
        lists.sort(key=lambda l: l.recent_participants_count)

    context = {
        'view_name': 'all_lists',
        'all_lists': lists,
        }
    return render(request, "index.html", context)
