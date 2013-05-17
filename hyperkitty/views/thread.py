# -*- coding: utf-8 -*-
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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

import datetime
from collections import namedtuple

import django.utils.simplejson as json

from django.http import HttpResponse, Http404
from django.conf import settings
from django.template import RequestContext, loader
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation
import robot_detection

from hyperkitty.models import Tag, Favorite
from forms import SearchForm, AddTagForm, ReplyForm
from hyperkitty.lib import get_months, get_store, stripped_subject
from hyperkitty.lib.voting import set_message_votes


def _get_thread_replies(request, thread, offset=1, limit=None):
    '''
    Get and sort the replies for a thread.
    By default, offset = 1 to skip the original message.
    '''
    if not thread:
        raise Http404

    if "sort" in request.GET and request.GET["sort"] == "date":
        sort_mode = "date"
        emails = thread.emails
    else:
        sort_mode = "thread"
        emails = thread.emails_by_reply

    # XXX: Storm-specific
    emails = emails.find()
    emails.config(offset=offset)
    if limit is not None:
        emails.config(limit=limit)

    emails = list(emails)
    for email in emails:
        # Extract all the votes for this message
        set_message_votes(email, request.user)
        if sort_mode == "thread":
            email.level = email.thread_depth - 1 # replies start ragged left
            if email.level > 5:
                email.level = 5

    return emails


def thread_index(request, mlist_fqdn, threadid, month=None, year=None):
    ''' Displays all the email for a given thread identifier '''
    search_form = SearchForm(auto_id=False)
    store = get_store(request)
    thread = store.get_thread(mlist_fqdn, threadid)
    if not thread:
        raise Http404
    prev_thread, next_thread = store.get_thread_neighbors(mlist_fqdn, threadid)

    sort_mode = request.GET.get("sort", "thread")
    set_message_votes(thread.starting_email, request.user)

    from_url = reverse("thread", kwargs={"mlist_fqdn":mlist_fqdn,
                                         "threadid":threadid})
    # Tags
    tag_form = AddTagForm(initial={'from_url' : from_url})
    try:
        tags = Tag.objects.filter(threadid=threadid, list_address=mlist_fqdn)
    except Tag.DoesNotExist:
        tags = []

    # Favorites
    fav_action = "add"
    if request.user.is_authenticated():
        try:
            Favorite.objects.get(list_address=mlist_fqdn, threadid=threadid,
                                 user=request.user)
        except Favorite.DoesNotExist:
            pass
        else:
            fav_action = "rm"

    # Extract relative dates
    today = datetime.date.today()
    days_old = today - thread.starting_email.date.date()
    days_inactive = today - thread.last_email.date.date()

    mlist = store.get_list(mlist_fqdn)
    subject = stripped_subject(mlist, thread.starting_email.subject)

    # TODO: eventually move to a middleware ?
    # http://djangosnippets.org/snippets/1865/
    is_bot = True
    user_agent = request.META.get('HTTP_USER_AGENT', None)
    if user_agent:
        is_bot = robot_detection.is_robot(user_agent)

    context = {
        'mlist': mlist,
        'threadid': threadid,
        'subject': subject,
        'tags': tags,
        'search_form': search_form,
        'addtag_form': tag_form,
        'month': thread.date_active,
        'first_mail': thread.starting_email,
        'neighbors': (prev_thread, next_thread),
        'months_list': get_months(store, mlist.name),
        'days_inactive': days_inactive.days,
        'days_old': days_old.days,
        'sort_mode': sort_mode,
        'fav_action': fav_action,
        'reply_form': ReplyForm(),
        'is_bot': is_bot,
        'participants': thread.participants,
    }
    context["participants"].sort(key=lambda x: x[0].lower())

    if is_bot:
        # Don't rely on AJAX to load the replies
        context["replies"] = _get_thread_replies(request, thread)

    return render(request, "thread.html", context)


def replies(request, mlist_fqdn, threadid):
    """Get JSON encoded lists with the replies and the participants"""
    chunk_size = 5
    offset = int(request.GET.get("offset", "1"))
    store = get_store(request)
    thread = store.get_thread(mlist_fqdn, threadid)
    mlist = store.get_list(mlist_fqdn)
    context = {
        'mlist': mlist,
        'threadid': threadid,
        'reply_form': ReplyForm(),
    }
    context["replies"] = _get_thread_replies(request, thread, offset=offset,
                                             limit=chunk_size)

    replies_tpl = loader.get_template('threads/replies.html')
    replies_html = replies_tpl.render(RequestContext(request, context))
    response = {"replies_html": replies_html,
                "more_pending": False,
                "next_offset": None,
               }
    if len(context["replies"]) == chunk_size:
        response["more_pending"] = True
        response["next_offset"] = offset + chunk_size
    return HttpResponse(json.dumps(response),
                        mimetype='application/javascript')


def add_tag(request, mlist_fqdn, threadid):
    """ Add a tag to a given thread. """
    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in to add a tag',
                            content_type="text/plain", status=403)

    if request.method != 'POST':
        raise SuspiciousOperation

    form = AddTagForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Error adding tag: invalid data",
                            content_type="text/plain", status=500)
    tag = form.data['tag']
    try:
        tag_obj = Tag.objects.get(threadid=threadid,
                                  list_address=mlist_fqdn, tag=tag)
    except Tag.DoesNotExist:
        tag_obj = Tag(list_address=mlist_fqdn, threadid=threadid, tag=tag)
        tag_obj.save()

    # Now refresh the tag list
    tags = Tag.objects.filter(threadid=threadid, list_address=mlist_fqdn)
    FakeMList = namedtuple("MailingList", ["name"])
    t = loader.get_template('threads/tags.html')
    html = t.render(RequestContext(request, {
            "tags": tags,
            "mlist": FakeMList(name=mlist_fqdn)}))

    response = {"tags": [ t.tag for t in tags ], "html": html}
    return HttpResponse(json.dumps(response),
                        mimetype='application/javascript')



def favorite(request, mlist_fqdn, threadid):
    """ Add or remove from favorites"""
    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in to have favorites',
                            content_type="text/plain", status=403)

    if request.method != 'POST':
        raise SuspiciousOperation

    props = dict(list_address=mlist_fqdn, threadid=threadid, user=request.user)
    if request.POST["action"] == "add":
        try:
            fav = Favorite.objects.get(**props)
        except Favorite.DoesNotExist:
            fav = Favorite(**props)
        fav.save()
    elif request.POST["action"] == "rm":
        try:
            fav = Favorite.objects.get(**props)
        except Favorite.DoesNotExist:
            pass
        else:
            fav.delete()
    else:
        raise SuspiciousOperation
    return HttpResponse("success", mimetype='text/plain')

