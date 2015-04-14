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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, unicode_literals

import datetime

import json
from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import formats
from django.utils.dateformat import format as date_format
from django.http import Http404, HttpResponse

from hyperkitty.models import Favorite, MailingList, ThreadCategory
from hyperkitty.lib.view_helpers import (FLASH_MESSAGES, get_category_widget,
    get_months, get_display_dates, daterange, check_mlist_private)
from hyperkitty.lib.paginator import paginate


if settings.USE_MOCKUPS:
    from hyperkitty.lib.mockup import generate_top_author



@check_mlist_private
def archives(request, mlist_fqdn, year=None, month=None, day=None):
    if year is None and month is None:
        today = datetime.date.today()
        return redirect(reverse(
                'hk_archives_with_month', kwargs={
                    "mlist_fqdn": mlist_fqdn,
                    'year': today.year,
                    'month': today.month}))

    try:
        begin_date, end_date = get_display_dates(year, month, day)
    except ValueError:
        # Wrong date format, for example 9999/0/0
        raise Http404("Wrong date format")
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    threads = mlist.get_threads_between(begin_date, end_date)
    if day is None:
        list_title = date_format(begin_date, "F Y")
        no_results_text = "for this month"
    else:
        #list_title = date_format(begin_date, settings.DATE_FORMAT)
        list_title = formats.date_format(begin_date) # works with i18n
        no_results_text = "for this day"
    extra_context = {
        'month': begin_date,
        'month_num': begin_date.month,
        "list_title": list_title.capitalize(),
        "no_results_text": no_results_text,
    }
    if day is None:
        extra_context["participants_count"] = \
            mlist.get_participants_count_for_month(int(year), int(month))
    return _thread_list(request, mlist, threads, extra_context=extra_context)


def _thread_list(request, mlist, threads, template_name='hyperkitty/thread_list.html', extra_context=None):
    categories = [ (c.name, c.name.upper())
                   for c in ThreadCategory.objects.all() ] \
                 + [("", "no category")]
    threads = paginate(threads, request.GET.get('page'))
    for thread in threads:
        # Favorites
        thread.favorite = False
        if request.user.is_authenticated():
            try:
                Favorite.objects.get(thread=thread, user=request.user)
            except Favorite.DoesNotExist:
                pass
            else:
                thread.favorite = True
        # Category
        thread.category_hk, thread.category_form = \
            get_category_widget(request, thread.category, categories)

    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

    context = {
        'mlist' : mlist,
        'threads': threads,
        'months_list': get_months(mlist),
        'flash_messages': flash_messages,
    }
    if extra_context is not None:
        context.update(extra_context)
    return render(request, template_name, context)


@check_mlist_private
def overview(request, mlist_fqdn=None):
    if not mlist_fqdn:
        return redirect('/')
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    threads = []
    for thread_obj in mlist.recent_threads:
        thread_obj.category_widget = get_category_widget(
                None, thread_obj.category)[0]
        threads.append(thread_obj)

    # top threads are the one with the most answers
    top_threads = sorted(threads, key=lambda t: t.emails_count, reverse=True)

    # active threads are the ones that have the most recent posting
    active_threads = sorted(threads, key=lambda t: t.date_active, reverse=True)

    # top authors are the ones that have the most kudos.  How do we determine
    # that?  Most likes for their post?
    if settings.USE_MOCKUPS:
        authors = generate_top_author()
        authors = sorted(authors, key=lambda author: author.kudos)
        authors.reverse()
    else:
        authors = []

    # Popular threads
    pop_threads = []
    for t in threads:
        votes = t.get_votes()
        if votes["likes"] - votes["dislikes"] > 0:
            pop_threads.append(t)
    def _get_thread_vote_result(t):
        votes = t.get_votes()
        return votes["likes"] - votes["dislikes"]
    pop_threads.sort(key=_get_thread_vote_result, reverse=True)

    # Threads by category
    threads_by_category = {}
    for thread in active_threads:
        if not thread.category:
            continue
        # don't use defaultdict, use .setdefault():
        # http://stackoverflow.com/questions/4764110/django-template-cant-loop-defaultdict
        if len(threads_by_category.setdefault(thread.category, [])) >= 5:
            continue
        threads_by_category[thread.category].append(thread)

    # Personalized discussion groups: flagged/favorited threads and threads by user
    if request.user.is_authenticated():
        favorites = [ f.thread for f in Favorite.objects.filter(
            thread__mailinglist=mlist, user=request.user) ]
        mm_user_id = request.user.hyperkitty_profile.get_mailman_user_id()
        threads_posted_to = mlist.threads.filter(
            emails__sender__mailman_id=mm_user_id).distinct()
    else:
        favorites = []
        threads_posted_to = []

    # Empty messages # TODO: translate this
    empty_messages = {
        "flagged": 'You have not flagged any discussions (yet).',
        "posted": 'You have not posted to this list (yet).',
        "active": 'No discussions this month (yet).',
        "popular": 'No vote has been cast this month (yet).',
    }

    context = {
        'view_name': 'overview',
        'mlist' : mlist,
        'top_threads': top_threads[:20],
        'most_active_threads': active_threads[:20],
        'top_author': authors,
        'pop_threads': pop_threads[:20],
        'threads_by_category': threads_by_category,
        'months_list': get_months(mlist),
        'flagged_threads': favorites,
        'threads_posted_to': threads_posted_to,
        'empty_messages': empty_messages,
    }
    return render(request, "hyperkitty/overview.html", context)


@check_mlist_private
def recent_activity(request, mlist_fqdn):
    """Return the number of emails posted in the last 30 days"""
    # pylint: disable=unused-argument
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    begin_date, end_date = mlist.get_recent_dates()
    days = daterange(begin_date, end_date)

    # Use get_messages and not get_threads to count the emails, because
    # recently active threads include messages from before the start date
    emails_in_month = mlist.emails.filter(
        date__gte=begin_date,
        date__lt=end_date)
    # graph
    emails_per_date = {}
    # populate with all days before adding data.
    for day in days:
        emails_per_date[day.strftime("%Y-%m-%d")] = 0
    # now count the emails
    for email in emails_in_month:
        date_str = email.date.strftime("%Y-%m-%d")
        if date_str not in emails_per_date:
            continue # outside the range
        emails_per_date[date_str] += 1
    # return the proper format for the javascript chart function
    evolution = [ {"date": d, "count": emails_per_date[d]}
             for d in sorted(emails_per_date) ]
    return HttpResponse(json.dumps({"evolution": evolution}),
                        content_type='application/javascript')
