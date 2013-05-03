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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import formats
from django.utils.dateformat import format as date_format
from django.http import Http404

from hyperkitty.models import Tag, Favorite
from hyperkitty.lib import get_months, get_store, get_display_dates, daterange
from hyperkitty.lib import FLASH_MESSAGES
from hyperkitty.lib.voting import get_votes
from forms import SearchForm


if settings.USE_MOCKUPS:
    from hyperkitty.lib.mockup import generate_top_author, generate_thread_per_category


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
    search_form = SearchForm(auto_id=False)

    participants = set()
    for thread in threads:
        participants.update(thread.participants)

        # Votes
        totalvotes = 0
        totallikes = 0
        totaldislikes = 0
        for message_id_hash in thread.email_id_hashes:
            likes, dislikes, myvote = get_votes(message_id_hash, request.user)
            totallikes = totallikes + likes
            totalvotes = totalvotes + likes + dislikes
            totaldislikes = totaldislikes + dislikes
            if message_id_hash == thread.thread_id:
                # Starting email: same id as the thread_id
                thread.myvote = myvote
        try:
            thread.likes = totallikes / totalvotes
        except ZeroDivisionError:
            thread.likes = 0
        try:
            thread.dislikes = totaldislikes / totalvotes
        except ZeroDivisionError:
            thread.dislikes = 0
        thread.likestatus = "neutral"
        if thread.likes - thread.dislikes >= 10:
            thread.likestatus = "likealot"
        elif thread.likes - thread.dislikes > 0:
            thread.likestatus = "like"
        #elif thread.likes - thread.dislikes < 0:
        #    thread.likestatus = "dislike"

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

    all_threads = threads
    paginator = Paginator(threads, 10)
    page_num = request.GET.get('page')
    try:
        threads = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        threads = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        threads = paginator.page(paginator.num_pages)

    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

    context = {
        'mlist' : mlist,
        'current_page': page_num,
        'search_form': search_form,
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
    search_form = SearchForm(auto_id=False)

    # Get stats for last 30 days
    today = datetime.datetime.utcnow()
    # the upper boundary is excluded in the search, add one day
    end_date = today + datetime.timedelta(days=1)
    begin_date = end_date - datetime.timedelta(days=32)

    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    threads_result = store.get_threads(list_name=mlist.name, start=begin_date,
        end=end_date)

    threads = []
    Thread = namedtuple('Thread', ["thread_id", "subject", "participants",
                                   "length", "date_active"])
    participants = set()
    for thread_obj in threads_result:
        thread = Thread(thread_obj.thread_id, thread_obj.subject,
                        thread_obj.participants, len(thread_obj),
                        thread_obj.date_active)
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

    # List activity
    # Use get_messages and not get_threads to count the emails, because
    # recently active threads include messages from before the start date
    emails_in_month = store.get_messages(list_name=mlist.name,
                                         start=begin_date, end=end_date)
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

    # threads per category is the top thread titles in each category
    if settings.USE_MOCKUPS:
        threads_per_category = generate_thread_per_category()
    else:
        threads_per_category = {}

    context = {
        'mlist' : mlist,
        'search_form': search_form,
        'top_threads': top_threads[:5],
        'most_active_threads': active_threads[:5],
        'top_author': authors,
        'threads_per_category': threads_per_category,
        'months_list': get_months(store, mlist.name),
        'evolution': evolution,
        'days': days,
        'archives_baseurl': archives_baseurl,
    }
    return render(request, "recent_activities.html", context)


def search(request, mlist_fqdn):
    keyword = request.GET.get('keyword')
    target = request.GET.get('target')
    page = request.GET.get('page')
    if keyword and target:
        url = reverse('search_keyword',
                      kwargs={'mlist_fqdn': mlist_fqdn,
                              'target': target,
                              'keyword': keyword})
        if page:
            url += '%s/' % page
    else:
        url = reverse('search_list', kwargs={"mlist_fqdn": mlist_fqdn})
    return redirect(url)


def search_keyword(request, mlist_fqdn, target, keyword, page=1):
    store = get_store(request)
    ## Should we remove the code below?
    ## If urls.py does it job we should never need it
    if not keyword:
        keyword = request.GET.get('keyword')
    if not target:
        target = request.GET.get('target')
    if not target:
        target = 'Subject'
    regex = '%%%s%%' % keyword
    list_name = mlist_fqdn.split('@')[0]
    if target.lower() == 'subjectcontent':
        threads = store.search_content_subject(mlist_fqdn, keyword)
    elif target.lower() == 'subject':
        threads = store.search_subject(mlist_fqdn, keyword)
    elif target.lower() == 'content':
        threads = store.search_content(mlist_fqdn, keyword)
    elif target.lower() == 'from':
        threads = store.search_sender(mlist_fqdn, keyword)

    return _search_results_page(request, mlist_fqdn, threads, 'Search', page)


def search_tag(request, mlist_fqdn, tag):
    '''Returns threads having a particular tag'''
    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)

    try:
        tags = Tag.objects.filter(tag=tag)
    except Tag.DoesNotExist:
        tags = {}

    threads = []
    for t in tags:
        threads.append(store.get_thread(mlist_fqdn, t.threadid))

    extra_context = {
        "tag": tag,
        "list_title": "Search results for tag \"%s\"" % tag,
        "no_results_text": "for this tag",
    }
    return _thread_list(request, mlist, threads, extra_context=extra_context)

