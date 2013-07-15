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
from collections import namedtuple, defaultdict

from django.shortcuts import redirect, render
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import formats
from django.utils.dateformat import format as date_format
from django.utils.timezone import utc
from django.http import Http404

from hyperkitty.models import Tag, Favorite
from hyperkitty.lib import get_store
from hyperkitty.lib.view_helpers import FLASH_MESSAGES, paginate, \
        get_category_widget, get_months, get_display_dates, daterange, \
        is_thread_unread
from hyperkitty.lib.voting import get_votes, set_message_votes, set_thread_votes


if settings.USE_MOCKUPS:
    from hyperkitty.lib.mockup import generate_top_author, generate_thread_per_category


Thread = namedtuple('Thread', [
    "thread_id", "subject", "participants", "length", "date_active",
    "likes", "dislikes", "likestatus", "category", "unread",
    ])


def archives(request, mlist_fqdn, year=None, month=None, day=None):
    if year is None and month is None:
        today = datetime.date.today()
        return redirect(reverse(
                'archives_with_month', kwargs={
                    "mlist_fqdn": mlist_fqdn,
                    'year': today.year,
                    'month': today.month}))

    begin_date, end_date = get_display_dates(year, month, day)
    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    threads = store.get_threads(mlist_fqdn, start=begin_date, end=end_date)
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
    return _thread_list(request, mlist, threads, extra_context=extra_context)


def _thread_list(request, mlist, threads, template_name='thread_list.html', extra_context={}):
    if mlist is None:
        raise Http404("No archived mailing-list by that name.")
    store = get_store(request)

    participants = set()
    for thread in threads:
        participants.update(thread.participants)

        # Votes
        set_thread_votes(thread, request.user)

        # Favorites
        thread.favorite = False
        if request.user.is_authenticated():
            try:
                Favorite.objects.get(list_address=mlist.name,
                                     threadid=thread.thread_id,
                                     user=request.user)
            except Favorite.DoesNotExist:
                pass
            else:
                thread.favorite = True

        # Tags
        try:
            thread.tags = Tag.objects.filter(threadid=thread.thread_id,
                                             list_address=mlist.name)
        except Tag.DoesNotExist:
            thread.tags = []

        # Category
        thread.category_hk, thread.category_form = \
                get_category_widget(request, thread.category)

        # Unread status
        thread.unread = is_thread_unread(request, mlist.name, thread)

    threads = paginate(threads, request.GET.get('page'))

    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

    context = {
        'mlist' : mlist,
        'threads': threads,
        'participants': len(participants),
        'months_list': get_months(store, mlist.name),
        'flash_messages': flash_messages,
    }
    context.update(extra_context)
    return render(request, template_name, context)


def overview(request, mlist_fqdn=None):
    if not mlist_fqdn:
        return redirect('/')

    # Get stats for last 30 days
    today = datetime.datetime.utcnow()
    #today -= datetime.timedelta(days=365) #debug
    # the upper boundary is excluded in the search, add one day
    end_date = today + datetime.timedelta(days=1)
    begin_date = end_date - datetime.timedelta(days=32)

    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    if mlist is None:
        raise Http404("No archived mailing-list by that name.")
    threads_result = store.get_threads(
            list_name=mlist.name, start=begin_date, end=end_date)

    threads = []
    participants = set()
    for thread_obj in threads_result:
        # Votes
        set_thread_votes(thread_obj, request.user)
        thread = Thread(thread_obj.thread_id, thread_obj.subject,
                        thread_obj.participants, len(thread_obj),
                        thread_obj.date_active.replace(tzinfo=utc),
                        thread_obj.likes, thread_obj.dislikes,
                        thread_obj.likestatus,
                        get_category_widget(None, thread_obj.category)[0],
                        is_thread_unread(request, mlist.name, thread_obj),
                        )
        # Statistics on how many participants and threads this month
        participants.update(thread.participants)
        threads.append(thread)

    # top threads are the one with the most answers
    top_threads = sorted(threads, key=lambda t: t.length, reverse=True)

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

    # Top posters
    top_posters = []
    for poster in store.get_top_participants(list_name=mlist.name,
                start=begin_date, end=end_date, limit=5):
        top_posters.append({"name": poster[0], "email": poster[1],
                            "count": poster[2]})

    # Popular threads
    pop_threads = sorted([ t for t in threads if t.likes - t.dislikes > 0 ],
                         key=lambda t: t.likes - t.dislikes,
                         reverse=True)

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

    # List activity
    # Use get_messages and not get_threads to count the emails, because
    # recently active threads include messages from before the start date
    emails_in_month = store.get_messages(list_name=mlist.name,
                                         start=begin_date, end=end_date)
    # graph
    dates = defaultdict(lambda: 0) # no activity by default
    # populate with all days before adding data.
    for single_date in daterange(begin_date, end_date):
        dates[single_date.strftime("%Y-%m-%d")] = 0

    for email in emails_in_month:
        date_str = email.date.strftime("%Y-%m-%d")
        dates[date_str] = dates[date_str] + 1
    days = dates.keys()
    days.sort()
    evolution = [dates[d] for d in days]
    if not evolution:
        evolution.append(0)
    archives_baseurl = reverse("archives_latest",
                               kwargs={'mlist_fqdn': mlist.name})
    archives_baseurl = archives_baseurl.rpartition("/")[0]

    context = {
        'view_name': 'overview',
        'mlist' : mlist,
        'top_threads': top_threads[:5],
        'most_active_threads': active_threads[:5],
        'top_author': authors,
        'top_posters': top_posters,
        'pop_threads': pop_threads[:5],
        'threads_by_category': threads_by_category,
        'months_list': get_months(store, mlist.name),
        'evolution': evolution,
        'days': days,
        'archives_baseurl': archives_baseurl,
        'num_threads': len(threads),
        'num_participants': len(participants),
    }
    return render(request, "overview.html", context)
