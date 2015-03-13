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
from email import message_from_file
from functools import wraps

from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.http import urlunquote
from django.views.decorators.csrf import csrf_exempt

from hyperkitty.lib.incoming import add_to_list, DuplicateMessage
from hyperkitty.lib.utils import get_message_id_hash

import logging
logger = logging.getLogger(__name__)


def key_and_ip_auth(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        for attr in ('MAILMAN_ARCHIVER_KEY', 'MAILMAN_ARCHIVER_FROM'):
            if not hasattr(settings, attr):
                msg = "Missing setting: %s" % attr
                logger.error(msg)
                raise ImproperlyConfigured(msg)
        if request.META.get("REMOTE_ADDR") not in settings.MAILMAN_ARCHIVER_FROM:
            # pylint: disable=logging-format-interpolation
            logger.error(
                "Access to the archiving API endpoint was forbidden from "
                "IP {}, your MAILMAN_ARCHIVER_FROM setting may be "
                "misconfigured".format(request.META["REMOTE_ADDR"]))
            return HttpResponse("""
                <html><title>Forbidden</title><body>
                <h1>Access is forbidden</h1></body></html>""",
                content_type="text/html", status=403)
        if request.GET.get("key") != settings.MAILMAN_ARCHIVER_KEY:
            return HttpResponse("""
                <html><title>Auth required</title><body>
                <h1>Authorization Required</h1></body></html>""",
                content_type="text/html", status=401)
        return func(request, *args, **kwargs)
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


@key_and_ip_auth
def urls(request):
    result = _get_url(request.GET["mlist"], request.GET.get("msgid"))
    return HttpResponse(json.dumps({"url": result}),
                        content_type='application/javascript')


@key_and_ip_auth
@csrf_exempt
def archive(request):
    if request.method != 'POST':
        raise SuspiciousOperation
    mlist_fqdn = request.POST["mlist"]
    if "message" not in request.FILES:
        raise SuspiciousOperation
    msg = message_from_file(request.FILES['message'])
    try:
        add_to_list(mlist_fqdn, msg)
    except DuplicateMessage as e:
        logger.info("Duplicate email with message-id '%s'", e.args[0])
    url = _get_url(mlist_fqdn, msg['Message-Id'])
    logger.info("Archived message %s to %s", msg['Message-Id'], url)
    return HttpResponse(json.dumps({"url": url}),
                        content_type='application/javascript')
