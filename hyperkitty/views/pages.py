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
#

import re
import os
import json
import urllib
from calendar import timegm
from datetime import datetime, timedelta
from urlparse import urljoin

import django.utils.simplejson as simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)

from hyperkitty.models import Rating
from hyperkitty.lib import get_store
from forms import *


def index(request):
    t = loader.get_template('index.html')
    search_form = SearchForm(auto_id=False)

    base_url = settings.MAILMAN_API_URL % {
        'username': settings.MAILMAN_USER, 'password': settings.MAILMAN_PASS}

    store = get_store(request)
    list_data = store.get_list_names()

    c = RequestContext(request, {
        'lists': list_data,
        'search_form': search_form,
        })
    return HttpResponse(t.render(c))
