#-*- coding: utf-8 -*-

import re
import os
import json
import urllib
import django.utils.simplejson as simplejson

from calendar import timegm
from datetime import datetime, timedelta

from urlparse import urljoin
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)

from hyperkitty.models import Rating
#from hyperkitty.lib.mockup import *
from hyperkitty.lib import get_store
from forms import *
from hyperkitty.utils import log

def index(request):
    t = loader.get_template('index.html')
    search_form = SearchForm(auto_id=False)

    base_url = settings.MAILMAN_API_URL % {
        'username': settings.MAILMAN_USER, 'password': settings.MAILMAN_PASS}

    store = get_store(request)
    list_data = store.get_list_names()
    log("warn", repr(list_data))

    c = RequestContext(request, {
        'lists': list_data,
        'search_form': search_form,
        })
    return HttpResponse(t.render(c))
