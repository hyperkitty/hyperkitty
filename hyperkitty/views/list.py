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

import re
import os
import json
import urllib
import logging
import datetime
from calendar import timegm
from urlparse import urljoin
from collections import namedtuple, defaultdict

import django.utils.simplejson as simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)

from hyperkitty.models import Tag, Favorite
from hyperkitty.lib import get_months, get_store, get_display_dates, get_votes
from forms import *


logger = logging.getLogger(__name__)

if settings.USE_MOCKUPS:
    from hyperkitty.lib.mockup import generate_top_author, generate_thread_per_category



def archives(request, mlist_fqdn, year=None, month=None, day=None):
    # @TODO : modify url.py to account for page number

    if year is None and month is None:
        today = datetime.date.today()
        return HttpResponseRedirect(reverse(
                'archives_with_month', kwargs={
                    "mlist_fqdn": mlist_fqdn,
                    'year': today.year,
                    'month': today.month}))

    begin_date, end_date = get_display_dates(year, month, day)

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('month_view.html')
    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    all_threads = store.get_threads(mlist_fqdn, start=begin_date,
                                    end=end_date)

    participants = set()
    #cnt = 0
    for thread in all_threads:
        participants.update(thread.participants)

        highestlike = 0
        highestdislike = 0

        totalvotes = 0
        totallikes = 0
        totaldislikes = 0

        for message_id_hash in thread.email_id_hashes:
            # Extract all the votes for this message
            likes, dislikes = get_votes(message_id_hash)
            totallikes = totallikes + likes
            totalvotes = totalvotes + likes + dislikes
            totaldislikes = totaldislikes + dislikes

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

        #threads[cnt] = thread
        #cnt = cnt + 1

        # Favorites
        thread.favorite = False
        if request.user.is_authenticated():
            try:
                Favorite.objects.get(list_address=mlist_fqdn,
                                     threadid=thread.thread_id,
                                     user=request.user)
            except Favorite.DoesNotExist:
                pass
            else:
                thread.favorite = True

    paginator = Paginator(all_threads, 10)
    pageNo = request.GET.get('page')

    try:
        threads = paginator.page(pageNo)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        threads = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        threads = paginator.page(paginator.num_pages)


    archives_length = get_months(store, mlist_fqdn)

    c = RequestContext(request, {
        'mlist' : mlist,
        'objects': threads.object_list,
        'page': pageNo,
        'has_previous': threads.has_previous(),
        'has_next': threads.has_next(),
        'previous': threads.previous_page_number(),
        'next': threads.next_page_number(),
        'is_first': pageNo == 1,
        'is_last': pageNo == paginator.num_pages,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'month': begin_date,
        'month_num': begin_date.month,
        'month_participants': len(participants),
        'month_discussions': len(all_threads),
        'threads': threads,
        'pages' : paginator.object_list,
        'archives_length': archives_length,
        'use_mockups': settings.USE_MOCKUPS,
    })
    return HttpResponse(t.render(c))



def overview(request, mlist_fqdn=None):
    if not mlist_fqdn:
        return HttpResponseRedirect('/')
    t = loader.get_template('recent_activities.html')
    search_form = SearchForm(auto_id=False)

    # Get stats for last 30 days
    today = datetime.datetime.utcnow()
    # the upper boundary is excluded in the search, add one day
    end_date = today + datetime.timedelta(days=1)
    begin_date = end_date - datetime.timedelta(days=32)

    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    threads_result = store.get_threads(list_name=mlist_fqdn, start=begin_date,
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

    archives_length = get_months(store, mlist_fqdn)

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
    emails_in_month = store.get_messages(list_name=mlist_fqdn,
                                         start=begin_date, end=end_date)
    dates = defaultdict(lambda: 0) # no activity by default
    for email in emails_in_month:
        date_str = email.date.strftime("%Y-%m-%d")
        dates[date_str] = dates[date_str] + 1
    days = dates.keys()
    days.sort()
    evolution = [dates[d] for d in days]
    if not evolution:
        evolution.append(0)

    # threads per category is the top thread titles in each category
    if settings.USE_MOCKUPS:
        threads_per_category = generate_thread_per_category()
    else:
        threads_per_category = {}

    c = RequestContext(request, {
        'mlist' : mlist,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'month': None,
        'month_participants': len(participants),
        'month_discussions': len(threads),
        'top_threads': top_threads[:5],
        'most_active_threads': active_threads[:5],
        'top_author': authors,
        'threads_per_category': threads_per_category,
        'archives_length': archives_length,
        'evolution': evolution,
        'days': days,
        'use_mockups': settings.USE_MOCKUPS,
    })
    return HttpResponse(t.render(c))


def _search_results_page(request, mlist_fqdn, threads, search_type,
                         page=1, num_threads=25, limit=None):
    search_form = SearchForm(auto_id=False)
    t = loader.get_template('search.html')
    list_name = mlist_fqdn.split('@')[0]
    res_num = len(threads)

    participants = set()
    for msg in threads:
        participants.add(msg.sender_name)

    paginator = Paginator(threads, num_threads)

    #If page request is out of range, deliver last page of results.
    try:
        threads = paginator.page(page)
    except (EmptyPage, InvalidPage):
        threads = paginator.page(paginator.num_pages)

    store = get_store(request)
    cnt = 0
    for thread in threads.object_list:
        #msg.email = msg.sender_email.strip()
        # Statistics on how many participants and threads this month
        participants.update(thread.participants)
        threads.object_list[cnt] = thread
        cnt = cnt + 1

    c = RequestContext(request, {
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'search_type': search_type,
        'month_participants': len(participants),
        'month_discussions': res_num,
        'threads': threads,
        'full_path': request.get_full_path(),
    })
    return HttpResponse(t.render(c))


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
    return HttpResponseRedirect(url)


def search_keyword(request, mlist_fqdn, target, keyword, page=1):
    ## Should we remove the code below?
    ## If urls.py does it job we should never need it
    store = get_store(request)
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


def search_tag(request, mlist_fqdn, tag=None, page=1):
    '''Returns threads having a particular tag'''

    store = get_store(settings.KITTYSTORE_URL)
    list_name = mlist_fqdn.split('@')[0]

    try:
        thread_ids = Tag.objects.filter(tag=tag)
    except Tag.DoesNotExist:
        thread_ids = {}

    threads = []
    for thread_id in thread_ids:
        threads.append(store.get_thread(mlist_fqdn, thread_id))

    return _search_results_page(request, mlist_fqdn, threads,
        'Tag search', page, limit=50)

