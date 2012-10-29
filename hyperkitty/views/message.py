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

import re
import os
import urllib

import django.utils.simplejson as simplejson
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)

from hyperkitty.models import Rating
from hyperkitty.lib import get_store
from forms import *


def index(request, mlist_fqdn, hashid):
    '''
    Displays a single message identified by its message_id_hash (derived from
    message_id)
    '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('message.html')
    store = get_store(request)
    message = store.get_message_by_hash_from_list(mlist_fqdn, hashid)
    if message is None:
        raise Http404
    message.sender_email = message.sender_email.strip()

    # Extract all the votes for this message
    try:
        votes = Rating.objects.filter(messageid = hashid)
    except Rating.DoesNotExist:
        votes = {}

    likes = 0
    dislikes = 0

    for vote in votes:
        if vote.vote == 1:
            likes = likes + 1
        elif vote.vote == -1:
            dislikes = dislikes + 1
        else:
            pass

    message.votes = votes
    message.likes = likes
    message.dislikes = dislikes
    message.likestatus = "neutral"
    if message.likes - message.dislikes >= 10:
        message.likestatus = "likealot"
    elif message.likes - message.dislikes > 0:
        message.likestatus = "like"
    #elif message.likes - message.dislikes < 0:
    #    message.likestatus = "dislike"

    mlist = store.get_list(mlist_fqdn)

    c = RequestContext(request, {
        'mlist' : mlist,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'message': message,
        'hashid' : hashid,
        'use_mockups': settings.USE_MOCKUPS,
    })
    return HttpResponse(t.render(c))


def attachment(request, mlist_fqdn, hashid, counter, filename):
    """
    Sends the numbered attachment for download. The filename is not used for
    lookup, but validated nonetheless for security reasons.
    """
    store = get_store(request)
    message = store.get_message_by_hash_from_list(mlist_fqdn, hashid)
    if message is None:
        raise Http404
    attachment = store.get_attachment_by_counter(mlist_fqdn, message.message_id, int(counter))
    if attachment is None or attachment.name != filename:
        raise Http404
    # http://djangosnippets.org/snippets/1710/
    response = HttpResponse(attachment.content)
    response['Content-Type'] = attachment.content_type
    response['Content-Length'] = attachment.size
    if attachment.encoding is not None:
        response['Content-Encoding'] = attachment.encoding
    # Follow RFC2231, browser support is sufficient nowadays (2012-09)
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' \
            % urllib.quote(attachment.name.encode('utf-8'))
    return response


@login_required
def vote(request, mlist_fqdn):
    """ Add a rating to a given message identified by messageid. """
    if not request.user.is_authenticated():
        return redirect('user_login')

    value = request.POST['vote']
    hashid = request.POST['hashid']

    # Checks if the user has already voted for a this message. If yes modify db entry else create a new one.
    try:
        v = Rating.objects.get(user = request.user, messageid = hashid, list_address = mlist_fqdn)
    except Rating.DoesNotExist:
        v = Rating(list_address=mlist_fqdn, messageid = hashid, vote = value)

    v.user = request.user
    v.vote = value
    v.save()
    response_dict = { }

    return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
