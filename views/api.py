import re
import os
import json
import logging
import urllib
import django.utils.simplejson as simplejson

from calendar import timegm
from datetime import datetime, timedelta

from urlparse import urljoin
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from kittystore.kittysastore import KittySAStore

from gsoc.models import Rating
from lib.mockup import *

logger = logging.getLogger(__name__)

def api(request):
    t = loader.get_template('api.html')
    c = RequestContext(request, {
        })
    return HttpResponse(t.render(c))


