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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from mailmanclient import Client

from hyperkitty.models import Rating


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
    subscriptions = []
    for mlist_id in mm_user.subscription_list_ids:
        mlist = client.get_list(mlist_id).fqdn_listname
        # de-duplicate subscriptions
        if mlist in [ s["list_name"] for s in subscriptions ]:
            continue
        email_hashes = store.get_message_hashes_by_user_id(
                mm_user.user_id, mlist)
        try: # Compute the average vote value
            votes = Rating.objects.filter(list_address=mlist,
                                          messageid__in=email_hashes)
        except Rating.DoesNotExist:
            votes = []
        likes = dislikes = 0
        for v in votes:
            if v.vote == 1:
                likes += 1
            elif v.vote == -1:
                dislikes += 1
        all_posts_url = "%s?list=%s&query=user_id:%s" % \
                (reverse("search"), mlist, urlquote(mm_user.user_id))
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
            "posts_count": len(email_hashes),
        })
    return subscriptions
