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
from gsoc.models import Rating
from lib.mockup import *
from forms import *
from gsoc.utils import log

def index(request):
    t = loader.get_template('index.html')
    search_form = SearchForm(auto_id=False)

    base_url = settings.MAILMAN_API_URL % {
        'username': settings.MAILMAN_USER, 'password': settings.MAILMAN_PASS}

    list_data = ['devel@fp.o', 'packaging@fp.o', 'fr-users@fp.o']

    c = RequestContext(request, {
        'lists': list_data,
        'search_form': search_form,
        })
    return HttpResponse(t.render(c))
