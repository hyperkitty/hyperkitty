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
from hyperkitty.utils import log


def api(request):
    t = loader.get_template('api.html')
    c = RequestContext(request, {
        })
    return HttpResponse(t.render(c))


