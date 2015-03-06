#-*- coding: utf-8 -*-
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
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

from __future__ import absolute_import, unicode_literals

import json
from urlparse import urljoin, urlparse
from email import message_from_file
from functools import wraps

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils.http import urlunquote

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.lib.utils import get_message_id_hash

import logging
logger = logging.getLogger(__name__)


def basic_auth(func):
    # Inspired by:
    # https://djangosnippets.org/snippets/2468/
    # https://djangosnippets.org/snippets/1304/*
    # https://djangosnippets.org/snippets/243/
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTP_AUTHORIZATION'):
            authentication = request.META['HTTP_AUTHORIZATION']
            (authmeth, auth) = authentication.split(' ',1)
            if 'basic' == authmeth.lower():
                auth = auth.strip().decode('base64')
                username, password = auth.split(':', 1)
                if username == settings.MAILMAN_ARCHIVER_API_USER \
                    and password == settings.MAILMAN_ARCHIVER_API_PASS:
                    return func(request, *args, **kwargs)
        response = HttpResponse("""
            <html><title>Auth required</title><body>
            <h1>Authorization Required</h1></body></html>""",
            content_type="text/html")
        response['WWW-Authenticate'] = 'Basic realm="Mailman Archiver API"'
        response.status_code = 401
        return response
    return _decorator


def _get_url(mlist_fqdn, msg_id=None):
    # I don't think we can use HttpRequest.build_absolute_uri() because the
    # mailman API may be accessed via localhost
    # https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.build_absolute_uri
    # https://docs.djangoproject.com/en/dev/ref/contrib/sites/#getting-the-current-domain-for-full-urls
    #result = urljoin(public_url, urlunquote(
    #        reverse('hk_list_overview', args=[mlist_fqdn])))
    # So we return the relative URL and let the admin configure the public URL in Mailman
    if msg_id is None:
        url = reverse('hk_list_overview', args=[mlist_fqdn])
    else:
        msg_hash = get_message_id_hash(msg_id.strip().strip("<>"))
        url = reverse('hk_message_index', kwargs={
            "mlist_fqdn": mlist_fqdn, "message_id_hash": msg_hash})
    return urlunquote(url)


@basic_auth
def urls(request):
    result = _get_url(request.GET["mlist"], request.GET.get("msgid"))
    return HttpResponse(json.dumps({"url": result}),
                        content_type='application/javascript')


@basic_auth
def archive(request):
    allowed_from = urlparse(settings.MAILMAN_REST_SERVER).netloc
    allowed_from = allowed_from.partition(":")[0]
    if request.META["REMOTE_ADDR"] != allowed_from and \
        request.META["REMOTE_HOST"] != allowed_from:
        logger.info("Access to the archiving API endpoint was forbidden from "
                    "IP {}, your MAILMAN_REST_SERVER setting may be "
                    "misconfigured".format(request.META["REMOTE_ADDR"]))
        response = HttpResponse("""
            <html><title>Forbidden</title><body>
            <h1>Access is forbidden</h1></body></html>""",
            content_type="text/html")
        response.status_code = 403
        return response
    if request.method != 'POST':
        raise SuspiciousOperation
    mlist_fqdn = request.POST["mlist"]
    if "message" not in request.FILES:
        raise SuspiciousOperation
    msg = message_from_file(request.FILES['message'])
    add_to_list(mlist_fqdn, msg)
    url = _get_url(mlist_fqdn, msg['Message-Id'])
    logger.info("Archived message %s to %s", msg['Message-Id'], url)
    return HttpResponse(json.dumps({"url": url}),
                        content_type='application/javascript')
