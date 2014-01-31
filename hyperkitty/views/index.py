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


import datetime

from django.shortcuts import render
from django.conf import settings
from mailman.interfaces.archiver import ArchivePolicy

from hyperkitty.lib import get_store
from hyperkitty.lib.view_helpers import show_mlist
from hyperkitty.lib.mailman import is_mlist_authorized


def index(request):
    now = datetime.datetime.now()
    store = get_store(request)
    lists = [ l for l in store.get_lists()
              if not settings.FILTER_VHOST or show_mlist(l, request) ]
    initials = set()
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
        if mlist.created_at and \
                now - mlist.created_at <= datetime.timedelta(days=30):
            mlist.is_new = True
        else:
            mlist.is_new = False
        initials.add(mlist.name[0])

    # sorting
    sort_mode = request.GET.get('sort')
    if sort_mode == "active":
        lists.sort(key=lambda l: l.recent_threads_count, reverse=True)
    elif sort_mode == "popular":
        lists.sort(key=lambda l: l.recent_participants_count, reverse=True)
    elif sort_mode == "creation":
        lists.sort(key=lambda l: l.created_at, reverse=True)
    else:
        sort_mode = None

    context = {
        'view_name': 'all_lists',
        'all_lists': lists,
        'initials': sorted(list(initials)),
        'sort_mode': sort_mode,
        }
    return render(request, "index.html", context)
