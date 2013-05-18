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

import django.utils.simplejson as json

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from mailmanclient import Client

from hyperkitty.lib import get_store
from forms import SearchForm


def index(request):
    store = get_store(request)
    lists = store.get_lists()

    context = {
        'all_lists': lists,
        'search_form': SearchForm(auto_id=False),
        }
    return render(request, "index.html", context)


def list_properties(request):
    """Get JSON encoded list properties"""
    store = get_store(request)
    lists = store.get_lists()
    client = Client('%s/3.0' % settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER, settings.MAILMAN_API_PASS)
    props = {}
    for ml in lists:
        try:
            mm_list = client.get_list(ml.name)
        except urllib2.HTTPError:
            continue
        props[ml.name] = {
            "display_name": mm_list.display_name,
            "description": mm_list.settings["description"],
        }
        # Update KittyStore if necessary
        if ml.display_name != mm_list.display_name:
            ml.display_name = mm_list.display_name
    return HttpResponse(json.dumps(props),
                        mimetype='application/javascript')
