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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import

from functools import wraps

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.decorators import available_attrs
from django.shortcuts import render
from django.http import Http404
from mailman.interfaces.archiver import ArchivePolicy
from mailmanclient import Client

from hyperkitty.lib import get_store


def subscribe(list_address, user):
    client = Client('%s/3.0' % settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER, settings.MAILMAN_API_PASS)
    rest_list = client.get_list(list_address)
    try:
        member = rest_list.get_member(user.email)
    except ValueError:
        # not subscribed yet, subscribe the user without email delivery
        member = rest_list.subscribe(user.email,
                "%s %s" % (user.first_name, user.last_name))
        member.preferences["delivery_status"] = "by_user"
        member.preferences.save()


def get_subscriptions(store, client, mm_user):
    if not mm_user:
        return []
    ks_user = store.get_user(mm_user.user_id)
    subscriptions = []
    for mlist_id in mm_user.subscription_list_ids:
        mlist = client.get_list(mlist_id).fqdn_listname
        # de-duplicate subscriptions
        if mlist in [ s["list_name"] for s in subscriptions ]:
            continue
        posts_count = store.get_message_count_by_user_id(
                mm_user.user_id, mlist)
        likes, dislikes = ks_user.get_votes_in_list(mlist)
        all_posts_url = "%s?list=%s" % \
                (reverse("user_posts", args=[mm_user.user_id]), mlist)
        likestatus = "neutral"
        if likes - dislikes >= 10:
            likestatus = "likealot"
        elif likes - dislikes > 0:
            likestatus = "like"
        subscriptions.append({
            "list_name": mlist,
            "first_post": store.get_first_post(mlist, mm_user.user_id),
            "likes": likes,
            "dislikes": dislikes,
            "likestatus": likestatus,
            "all_posts_url": all_posts_url,
            "posts_count": posts_count,
        })
    return subscriptions


# View decorator: check that the list is authorized
def check_mlist_private(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if "mlist_fqdn" in kwargs:
            mlist_fqdn = kwargs["mlist_fqdn"]
        else:
            mlist_fqdn = args[0]
        try:
            store = get_store(request)
        except KeyError:
            return func(request, *args, **kwargs) # Unittesting?
        mlist = store.get_list(mlist_fqdn)
        if mlist is None:
            raise Http404("No archived mailing-list by that name.")
        #return HttpResponse(request.session.get("subscribed", "NO KEY"), content_type="text/plain")
        if not is_mlist_authorized(request, mlist):
            return render(request, "errors/private.html", {
                            "mlist": mlist,
                          }, status=403)
        return func(request, *args, **kwargs)
    return inner

def is_mlist_authorized(request, mlist):
    if mlist.archive_policy == ArchivePolicy.private and \
            not (request.user.is_authenticated() and
                 hasattr(request, "session") and
                 mlist.name in request.session.get("subscribed", [])):
        return False
    return True
