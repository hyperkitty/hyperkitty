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

import json
from urlparse import urljoin
from email import message_from_file

from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils.http import urlunquote

from hyperkitty.lib import get_store
from kittystore.utils import get_message_id_hash

import logging
logger = logging.getLogger(__name__)


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


def urls(request):
    result = _get_url(request.GET["mlist"], request.GET.get("msgid"))
    return HttpResponse(json.dumps(result),
                        content_type='application/javascript')


def archive(request):
    if request.method != 'POST':
        raise SuspiciousOperation
    mlist_fqdn = request.POST["mlist"]
    if "message" not in request.FILES:
        raise SuspiciousOperation
    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    msg = message_from_file(request.FILES['message'])
    store.add_to_list(mlist, msg)
    store.commit()
    url = _get_msg_link(mlist_fqdn, msg['Message-Id'])
    logger.info("Archived message %s to %s",
                msg['Message-Id'].strip(), url)
    return HttpResponse(json.dumps({"url": url}),
                        content_type='application/javascript')
