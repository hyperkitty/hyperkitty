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

import json
import re

from djangorestframework.views import View
from django.conf.urls.defaults import url
from django.conf import settings
from django.http import HttpResponseNotModified, HttpResponse

from hyperkitty.lib import get_store


class EmailResource(View):
    """ Resource used to retrieve emails from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, messageid):
        list_name = mlist_fqdn.split('@')[0]
        store = get_store(request)
        email = store.get_message_by_hash_from_list(list_name, messageid)
        if not email:
            return HttpResponse(status=404)
        else:
            return email


class ThreadResource(View):
    """ Resource used to retrieve threads from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, threadid):
        list_name = mlist_fqdn.split('@')[0]
        store = get_store(request)
        thread = store.get_thread(list_name, threadid)
        if not thread:
            return HttpResponse(status=404)
        else:
            return thread


class SearchResource(View):
    """ Resource used to search the archives using the REST API.
    """

    def get(self, request, mlist_fqdn, field, keyword):
        list_name = mlist_fqdn.split('@')[0]

        if field not in ['Subject', 'Content', 'SubjectContent', 'From']:
            return HttpResponse(status=404)

        regex = '.*%s.*' % keyword
        if field == 'SubjectContent':
            query_string = {'$or' : [
                {'Subject': re.compile(regex, re.IGNORECASE)},
                {'Content': re.compile(regex, re.IGNORECASE)}
                ]}
        else:
            query_string = {field.capitalize():
                re.compile(regex, re.IGNORECASE)}

        #print query_string, field, keyword
        store = get_store(request)
        threads = store.search_archives(list_name, query_string)
        if not threads:
            return HttpResponse(status=404)
        else:
            return threads
