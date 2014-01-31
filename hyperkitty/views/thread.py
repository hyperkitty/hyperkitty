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
import re
from collections import namedtuple

import django.utils.simplejson as json

from django.http import HttpResponse, Http404
from django.template import RequestContext, loader
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation
from django.utils.timezone import utc
import robot_detection

from hyperkitty.models import Tag, Favorite, LastView
from hyperkitty.views.forms import AddTagForm, ReplyForm
from hyperkitty.lib import get_store, stripped_subject
from hyperkitty.lib.view_helpers import (get_months, get_category_widget,
        FLASH_MESSAGES)
from hyperkitty.lib.mailman import check_mlist_private


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
    emails.config(offset=offset, limit=limit)

    emails = list(emails)
    for email in emails:
        # Extract all the votes for this message
        email.myvote = email.get_vote_by_user_id(request.session.get("user_id"))
        if sort_mode == "thread":
            email.level = email.thread_depth - 1 # replies start ragged left
            if email.level > 5:
                email.level = 5

    return emails


@check_mlist_private
def thread_index(request, mlist_fqdn, threadid, month=None, year=None):
    ''' Displays all the email for a given thread identifier '''
    store = get_store(request)
    thread = store.get_thread(mlist_fqdn, threadid)
    if not thread:
        raise Http404
    prev_thread, next_thread = store.get_thread_neighbors(mlist_fqdn, threadid)

    sort_mode = request.GET.get("sort", "thread")
    thread.starting_email.myvote = thread.starting_email.get_vote_by_user_id(
            request.session.get("user_id"))

    # Tags
    tag_form = AddTagForm()
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

    # Category
    category, category_form = get_category_widget(request, thread.category)

    # Extract relative dates
    today = datetime.date.today()
    days_old = today - thread.starting_email.date.date()
    days_inactive = today - thread.last_email.date.date()

    mlist = store.get_list(mlist_fqdn)
    subject = stripped_subject(mlist, thread.starting_email.subject)

    # Last view
    last_view = None
    if request.user.is_authenticated():
        last_view_obj, created = LastView.objects.get_or_create(
                list_address=mlist_fqdn, threadid=threadid, user=request.user)
        if not created:
            last_view = last_view_obj.view_date
            last_view_obj.save() # update timestamp
    # get the number of unread messages
    if last_view is None:
        if request.user.is_authenticated():
            unread_count = len(thread)
        else:
            unread_count = 0
    else:
        # XXX: Storm-specific
        unread_count = thread.replies_after(last_view).count()

    # Flash messages
    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

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
        'num_comments': len(thread),
        'participants': thread.participants,
        'last_view': last_view,
        'unread_count': unread_count,
        'category_form': category_form,
        'category': category,
        'flash_messages': flash_messages,
    }
    context["participants"].sort(key=lambda p: p.name.lower())

    if is_bot:
        # Don't rely on AJAX to load the replies
        # The limit is a safety measure, don't let a bot kill the DB
        context["replies"] = _get_thread_replies(request, thread, limit=1000)

    return render(request, "thread.html", context)


@check_mlist_private
def replies(request, mlist_fqdn, threadid):
    """Get JSON encoded lists with the replies and the participants"""
    chunk_size = 5
    offset = int(request.GET.get("offset", "1"))
    store = get_store(request)
    thread = store.get_thread(mlist_fqdn, threadid)
    mlist = store.get_list(mlist_fqdn)
    # Last view
    last_view = request.GET.get("last_view")
    if last_view:
        try:
            last_view = datetime.datetime.fromtimestamp(int(last_view), utc)
        except ValueError:
            last_view = None
    context = {
        'mlist': mlist,
        'threadid': threadid,
        'reply_form': ReplyForm(),
        'last_view': last_view,
    }
    context["replies"] = _get_thread_replies(request, thread, offset=offset,
                                             limit=chunk_size)

    replies_tpl = loader.get_template('ajax/replies.html')
    replies_html = replies_tpl.render(RequestContext(request, context))
    response = {"replies_html": replies_html,
                "more_pending": False,
                "next_offset": None,
               }
    if len(context["replies"]) == chunk_size:
        response["more_pending"] = True
        response["next_offset"] = offset + chunk_size
    return HttpResponse(json.dumps(response),
                        content_type='application/javascript')


@check_mlist_private
def tags(request, mlist_fqdn, threadid):
    """ Add or remove a tag on a given thread. """
    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in to add a tag',
                            content_type="text/plain", status=403)

    if request.method != 'POST':
        raise SuspiciousOperation
    action = request.POST.get("action")

    if action == "add":
        form = AddTagForm(request.POST)
        if not form.is_valid():
            return HttpResponse("Error adding tag: invalid data",
                                content_type="text/plain", status=500)
        tagname = form.data['tag']
    elif action == "rm":
        tagname = request.POST.get('tag')
    else:
        raise SuspiciousOperation
    try:
        tag = Tag.objects.get(threadid=threadid, list_address=mlist_fqdn,
                              tag=tagname)
        if action == "rm":
            tag.delete()
    except Tag.DoesNotExist:
        if action == "add":
            tag = Tag(list_address=mlist_fqdn, threadid=threadid,
                      tag=tagname, user=request.user)
            tag.save()
        elif action == "rm":
            raise Http404("No such tag: %s" % tagname)

    # Now refresh the tag list
    tags = Tag.objects.filter(threadid=threadid, list_address=mlist_fqdn)
    FakeMList = namedtuple("MailingList", ["name"])
    tpl = loader.get_template('threads/tags.html')
    html = tpl.render(RequestContext(request, {
            "tags": tags,
            "mlist": FakeMList(name=mlist_fqdn),
            "threadid": threadid,
            }))

    response = {"tags": [ t.tag for t in tags ], "html": html}
    return HttpResponse(json.dumps(response),
                        content_type='application/javascript')

@check_mlist_private
def suggest_tags(request, mlist_fqdn, threadid):
    term = request.GET.get("term")
    current_tags = Tag.objects.filter(
            list_address=mlist_fqdn, threadid=threadid
            ).values_list("tag", flat=True)
    if term:
        tags = Tag.objects.filter(list_address=mlist_fqdn, tag__istartswith=term)
    else:
        tags = Tag.objects.all()
    tags = tags.exclude(tag__in=current_tags).values_list("tag", flat=True)
    tags = [ t.encode("utf8") for t in tags ]
    return HttpResponse(json.dumps(tags), content_type='application/javascript')


@check_mlist_private
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
    return HttpResponse("success", content_type='text/plain')


@check_mlist_private
def set_category(request, mlist_fqdn, threadid):
    """ Set the category for a given thread. """
    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in to add a tag',
                            content_type="text/plain", status=403)
    if request.method != 'POST':
        raise SuspiciousOperation

    store = get_store(request)
    category, category_form = get_category_widget(request)
    thread = store.get_thread(mlist_fqdn, threadid)
    if not category and thread.category:
        thread.category = None
        store.commit()
    elif category and category.name != thread.category:
        thread.category = category.name
        store.commit()

    # Now refresh the category widget
    FakeMList = namedtuple("MailingList", ["name"])
    context = {
            "category_form": category_form,
            "mlist": FakeMList(name=mlist_fqdn),
            "threadid": threadid,
            "category": category,
            }
    return render(request, "threads/category.html", context)


@check_mlist_private
def reattach(request, mlist_fqdn, threadid):
    if not request.user.is_staff:
        return HttpResponse('You must be a staff member to reattach a thread',
                            content_type="text/plain", status=403)
    flash_messages = []
    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    thread = store.get_thread(mlist_fqdn, threadid)

    if request.method == 'POST':
        parent_tid = request.POST.get("parent")
        if not parent_tid:
            parent_tid = request.POST.get("parent-manual")
        if not parent_tid or not re.match("\w{32}", parent_tid):
            flash_messages.append({"type": "warning",
                                   "msg": "Invalid thread id, it should look "
                                          "like OUAASTM6GS4E5TEATD6R2VWMULG44NKJ."})
        elif parent_tid == threadid:
            flash_messages.append({"type": "warning",
                                   "msg": "Can't re-attach a thread to "
                                          "itself, check your thread ID."})
        else:
            new_thread = store.get_thread(mlist_fqdn, parent_tid)
            if new_thread is None:
                flash_messages.append({"type": "warning",
                                       "msg": "Unknown thread, check your "
                                              "thread ID."})
            elif thread.starting_email.date <= new_thread.starting_email.date:
                flash_messages.append({"type": "error",
                                       "msg": "Can't attach an older thread "
                                              "to a newer thread."})
            else:
                for msg in thread.emails:
                    store.attach_to_thread(msg, new_thread)
                store.delete_thread(mlist_fqdn, threadid)
                return redirect(reverse(
                        'thread', kwargs={
                            "mlist_fqdn": mlist_fqdn,
                            'threadid': parent_tid,
                        })+"?msg=attached-ok")


    context = {
        'mlist' : mlist,
        'thread': thread,
        'months_list': get_months(store, mlist.name),
        'flash_messages': flash_messages,
    }
    return render(request, "reattach.html", context)


@check_mlist_private
def reattach_suggest(request, mlist_fqdn, threadid):
    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    thread = store.get_thread(mlist_fqdn, threadid)

    default_search_query = stripped_subject(
        mlist, thread.subject).lower().replace("re:", "")
    search_query = request.GET.get("q")
    if not search_query:
        search_query = default_search_query
    search_query = search_query.strip()
    if store.search_index:
        search_result = store.search(search_query, mlist_fqdn, 1, 50)
        messages = search_result["results"]
    else:
        messages = []
    suggested_threads = []
    for msg in messages:
        if msg.thread not in suggested_threads and msg.thread_id != threadid:
            suggested_threads.append(msg.thread)

    context = {
        'mlist' : mlist,
        'suggested_threads': suggested_threads[:10],
    }
    return render(request, "ajax/reattach_suggest.html", context)
