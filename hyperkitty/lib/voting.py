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


from django.core.cache import cache
from hyperkitty.models import Rating


def get_votes(mlist_fqdn, msgid, user=None):
    """Extract all the votes for this message"""
    likes = dislikes = myvote = 0
    try:
        if isinstance(msgid, basestring):
            votes = Rating.objects.filter(
                        list_address=mlist_fqdn, messageid=msgid)
        elif isinstance(msgid, list):
            votes = Rating.objects.filter(
                        list_address=mlist_fqdn, messageid__in=msgid)
    except Rating.DoesNotExist:
        votes = {}
    for vote in votes:
        if vote.vote == 1:
            likes += 1
        elif vote.vote == -1:
            dislikes += 1
        if user is not None and user.is_authenticated() and vote.user == user:
            if not isinstance(msgid, list) or vote.messageid == msgid[0]:
                # for a thread, only consider the starting email
                myvote = vote.vote
    return likes, dislikes, myvote


def set_message_votes(message, user=None):
    # Extract all the votes for this message
    message.likes, message.dislikes, message.myvote = \
            get_votes(message.list_name, message.message_id_hash, user)
    message.likestatus = "neutral"
    if message.likes - message.dislikes >= 10:
        message.likestatus = "likealot"
    elif message.likes - message.dislikes > 0:
        message.likestatus = "like"
    #elif message.likes - message.dislikes < 0:
    #    message.likestatus = "dislike"


def set_thread_votes(thread):
    likes = dislikes = None
    cache_key = "list:%s:thread:%s:votes" % (thread.list_name, thread.thread_id)
    likes, dislikes = cache.get(cache_key, (None, None))
    if likes is None or dislikes is None:
        # XXX: 1 SQL request per thread, possible optimization here
        likes, dislikes, _myvote = get_votes(thread.list_name, thread.email_id_hashes)
        cache.set(cache_key, (likes, dislikes))
    # How should thread likes and dislikes be counted?
    #thread.likes = likes / thread.emails_count
    #thread.dislikes = dislikes / thread.emails_count
    thread.likes = likes
    thread.dislikes = dislikes
    thread.likestatus = "neutral"
    if thread.likes - thread.dislikes >= 10:
        thread.likestatus = "likealot"
    elif thread.likes - thread.dislikes > 0:
        thread.likestatus = "like"
    #elif thread.likes - thread.dislikes < 0:
    #    thread.likestatus = "dislike"

