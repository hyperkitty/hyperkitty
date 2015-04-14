# -*- coding: utf-8 -*-
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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, unicode_literals

import datetime
import re
import json

from django.http import HttpResponse, Http404
from django.template import RequestContext, loader
from django.shortcuts import render, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation
from django.utils.timezone import utc
import robot_detection
from haystack.query import SearchQuerySet

from hyperkitty.models import Tag, Tagging, Favorite, LastView, Thread, MailingList, ThreadCategory
from hyperkitty.views.forms import AddTagForm, ReplyForm
from hyperkitty.lib.utils import stripped_subject
from hyperkitty.lib.view_helpers import (get_months, get_category_widget,
        FLASH_MESSAGES, check_mlist_private)


def _get_thread_replies(request, thread, limit, offset=1):
    '''
    Get and sort the replies for a thread.
    By default, offset = 1 to skip the original message.
    '''
    if not thread:
        raise Http404

    sort_mode = request.GET.get("sort", "thread")
    if sort_mode not in ("date", "thread"):
        raise SuspiciousOperation
    if sort_mode == "thread":
        sort_mode = "thread_order"

    mlist = thread.mailinglist
    initial_subject = stripped_subject(mlist, thread.starting_email.subject)
    emails = list(thread.emails.order_by(sort_mode)[offset:offset+limit])
    for email in emails:
        # Extract all the votes for this message
        if request.user.is_authenticated():
            email.myvote = email.votes.filter(user=request.user).first()
        else:
            email.myvote = None
        # Threading position
        if sort_mode == "thread_order":
            email.level = email.thread_depth - 1 # replies start ragged left
            if email.level > 5:
                email.level = 5
            elif email.level < 0:
                email.level = 0
        # Subject change
        subject = stripped_subject(mlist, email.subject)
        if subject.lower().startswith("re:"):
            subject = subject[3:].strip()
        if subject.strip() == initial_subject.strip():
            email.changed_subject = False
        else:
            email.changed_subject = subject
    return emails


@check_mlist_private
def thread_index(request, mlist_fqdn, threadid, month=None, year=None):
    ''' Displays all the email for a given thread identifier '''
    # pylint: disable=unused-argument
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    thread = get_object_or_404(Thread, mailinglist=mlist, thread_id=threadid)
    starting_email = thread.starting_email

    sort_mode = request.GET.get("sort", "thread")
    if request.user.is_authenticated():
        starting_email.myvote = starting_email.votes.filter(
            user=request.user).first()
    else:
        starting_email.myvote = None

    # Tags
    tag_form = AddTagForm()

    # Favorites
    fav_action = "add"
    if request.user.is_authenticated() and Favorite.objects.filter(
            thread=thread, user=request.user).exists():
        fav_action = "rm"

    # Category
    categories = [ (c.name, c.name.upper())
                   for c in ThreadCategory.objects.all() ] \
                 + [("", "no category")]
    category, category_form = get_category_widget(
        request, thread.category, categories)

    # Extract relative dates
    today = datetime.date.today()
    days_old = today - starting_email.date.date()
    days_inactive = today - thread.date_active.date()

    subject = stripped_subject(mlist, starting_email.subject)

    # Last view
    last_view = None
    if request.user.is_authenticated():
        last_view_obj, created = LastView.objects.get_or_create(
                thread=thread, user=request.user)
        if not created:
            last_view = last_view_obj.view_date
            last_view_obj.save() # update timestamp
    # get the number of unread messages
    if last_view is None:
        if request.user.is_authenticated():
            unread_count = thread.emails_count
        else:
            unread_count = 0
    else:
        unread_count = thread.emails.filter(date__gt=last_view).count()

    # Flash messages
    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

    # TODO: eventually move to a middleware ?
    # http://djangosnippets.org/snippets/1865/
    user_agent = request.META.get('HTTP_USER_AGENT', None)
    if user_agent:
        is_bot = robot_detection.is_robot(user_agent)
    else:
        is_bot = True

    context = {
        'mlist': mlist,
        'thread': thread,
        'starting_email': starting_email,
        'subject': subject,
        'addtag_form': tag_form,
        'month': thread.date_active,
        'months_list': get_months(mlist),
        'days_inactive': days_inactive.days,
        'days_old': days_old.days,
        'sort_mode': sort_mode,
        'fav_action': fav_action,
        'reply_form': ReplyForm(),
        'is_bot': is_bot,
        'num_comments': thread.emails_count - 1,
        'last_view': last_view,
        'unread_count': unread_count,
        'category_form': category_form,
        'category': category,
        'flash_messages': flash_messages,
    }

    if is_bot:
        # Don't rely on AJAX to load the replies
        # The limit is a safety measure, don't let a bot kill the DB
        context["replies"] = _get_thread_replies(request, thread, limit=1000)

    return render(request, "hyperkitty/thread.html", context)


@check_mlist_private
def replies(request, mlist_fqdn, threadid):
    """Get JSON encoded lists with the replies and the participants"""
    chunk_size = 6 # must be an even number, or the even/odd cycle will be broken
    offset = int(request.GET.get("offset", "1"))
    thread = get_object_or_404(Thread,
        mailinglist__name=mlist_fqdn, thread_id=threadid)
    # Last view
    last_view = request.GET.get("last_view")
    if last_view:
        try:
            last_view = datetime.datetime.fromtimestamp(int(last_view), utc)
        except ValueError:
            last_view = None
    context = {
        'threadid': thread,
        'reply_form': ReplyForm(),
        'last_view': last_view,
    }
    context["replies"] = _get_thread_replies(request, thread, offset=offset,
                                             limit=chunk_size)

    replies_tpl = loader.get_template('hyperkitty/ajax/replies.html')
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
    """ Add or remove one or more tags on a given thread. """
    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in to add a tag',
                            content_type="text/plain", status=403)
    thread = get_object_or_404(Thread,
        mailinglist__name=mlist_fqdn, thread_id=threadid)

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
    tagnames = [ t.strip() for t in re.findall(r"[\w'_ -]+", tagname) ]
    for tagname in tagnames:
        if action == "add":
            tag = Tag.objects.get_or_create(name=tagname)[0]
            Tagging.objects.get_or_create(
                tag=tag, thread=thread, user=request.user)
        elif action == "rm":
            try:
                Tagging.objects.get(tag__name=tagname, thread=thread,
                                    user=request.user).delete()
            except Tagging.DoesNotExist:
                raise Http404("No such tag: %s" % tagname)
            # cleanup
            if not Tagging.objects.filter(tag__name=tagname).exists():
                Tag.objects.filter(name=tagname).delete()

    # Now refresh the tag list
    tpl = loader.get_template('hyperkitty/threads/tags.html')
    html = tpl.render(RequestContext(request, {
            "thread": thread,
            }))

    response = {"tags": [ t.name for t in thread.tags.distinct() ],
                "html": html}
    return HttpResponse(json.dumps(response),
                        content_type='application/javascript')

@check_mlist_private
def suggest_tags(request, mlist_fqdn, threadid):
    term = request.GET.get("term")
    current_tags = Tag.objects.filter(
            threads__mailing_list__name=mlist_fqdn,
            threads__thread_id=threadid
        ).values_list("name", flat=True)
    if term:
        tags_db = Tag.objects.filter(
            threads__mailing_list__name=mlist_fqdn,
            name__istartswith=term)
    else:
        tags_db = Tag.objects.all()
    tag_names = [ t.encode("utf-8") for t in
             tags_db.exclude(name__in=current_tags
                ).values_list("name", flat=True)[:20] ]
    return HttpResponse(json.dumps(tag_names),
                        content_type='application/javascript')


@check_mlist_private
def favorite(request, mlist_fqdn, threadid):
    """ Add or remove from favorites"""
    if not request.user.is_authenticated():
        return HttpResponse('You must be logged in to have favorites',
                            content_type="text/plain", status=403)
    if request.method != 'POST':
        raise SuspiciousOperation

    thread = get_object_or_404(Thread,
        mailinglist__name=mlist_fqdn, thread_id=threadid)
    if request.POST["action"] == "add":
        Favorite.objects.get_or_create(thread=thread, user=request.user)
    elif request.POST["action"] == "rm":
        Favorite.objects.filter(thread=thread, user=request.user).delete()
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

    thread = get_object_or_404(Thread,
        mailinglist__name=mlist_fqdn, thread_id=threadid)
    category, category_form = get_category_widget(request)
    if not category and thread.category:
        thread.category = None
        thread.save()
    elif category and category.name != thread.category:
        thread.category = category.name
        thread.save()

    # Now refresh the category widget
    context = {
            "category_form": category_form,
            "thread": thread,
            "category": category,
            }
    return render(request, "hyperkitty/threads/category.html", context)


@check_mlist_private
def reattach(request, mlist_fqdn, threadid):
    if not request.user.is_staff:
        return HttpResponse('You must be a staff member to reattach a thread',
                            content_type="text/plain", status=403)
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    thread = get_object_or_404(Thread, mailinglist=mlist, thread_id=threadid)
    context = {
        'mlist': mlist,
        'thread': thread,
        'months_list': get_months(mlist),
        'flash_messages': [],
    }
    template_name = "hyperkitty/reattach.html"

    if request.method == 'POST':
        parent_tid = request.POST.get("parent")
        if not parent_tid:
            parent_tid = request.POST.get("parent-manual")
        if not parent_tid or not re.match(r"\w{32}", parent_tid):
            context["flash_messages"].append(
                {"type": "warning",
                 "msg": "Invalid thread id, it should look "
                        "like OUAASTM6GS4E5TEATD6R2VWMULG44NKJ."})
            return render(request, template_name, context)
        if parent_tid == threadid:
            context["flash_messages"].append(
                {"type": "warning",
                 "msg": "Can't re-attach a thread to "
                        "itself, check your thread ID."})
            return render(request, template_name, context)
        try:
            parent = Thread.objects.get(
                mailinglist=thread.mailinglist, thread_id=parent_tid)
        except Thread.DoesNotExist:
            context["flash_messages"].append(
                {"type": "warning",
                 "msg": "Unknown thread, check your thread ID."})
            return render(request, template_name, context)
        try:
            thread.starting_email.set_parent(parent.starting_email)
        except ValueError as e:
            context["flash_messages"].append({"type": "error", "msg": str(e)})
            return render(request, template_name, context)
        return redirect(reverse(
                'hk_thread', kwargs={
                    "mlist_fqdn": mlist_fqdn,
                    'threadid': parent_tid,
                })+"?msg=attached-ok")
    return render(request, template_name, context)


@check_mlist_private
def reattach_suggest(request, mlist_fqdn, threadid):
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    thread = get_object_or_404(Thread, mailinglist=mlist, thread_id=threadid)

    default_search_query = stripped_subject(
        mlist, thread.subject).lower().replace("re:", "")
    search_query = request.GET.get("q")
    if not search_query:
        search_query = default_search_query
    search_query = search_query.strip()
    messages = SearchQuerySet().filter(
        mailinglist__exact=mlist_fqdn, content=search_query)[:50]
    suggested_threads = []
    for msg in messages:
        sugg_thread = msg.object.thread
        if sugg_thread not in suggested_threads \
            and sugg_thread.thread_id != threadid:
            suggested_threads.append(sugg_thread)

    context = {
        'mlist' : mlist,
        'suggested_threads': suggested_threads[:10],
    }
    return render(request, "hyperkitty/ajax/reattach_suggest.html", context)
