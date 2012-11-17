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

import re
import os
import json
import urllib
import logging
from calendar import timegm
from datetime import datetime, timedelta
from urlparse import urljoin

import django.utils.simplejson as simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)

from hyperkitty.models import Rating, Tag
from hyperkitty.lib import get_months, get_store
from forms import *


logger = logging.getLogger(__name__)

if settings.USE_MOCKUPS:
    from hyperkitty.lib.mockup import generate_top_author, generate_thread_per_category



def archives(request, mlist_fqdn, year=None, month=None, day=None):
    # No year/month: past 32 days
    # year and month: find the 32 days for that month
    # @TODO : modify url.py to account for page number

    end_date = None
    if year or month or day:
        try:
            start_day = 1
            end_day = 1
            start_month = int(month)
            end_month = int(month) + 1
            start_year = int(year)
            end_year = int(year)
            if day:
                start_day = int(day)
                end_day = start_day + 1
                end_month = start_month
            if start_month == 12:
                end_month = 1
                end_year = start_year + 1

            begin_date = datetime(start_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
            month_string = begin_date.strftime('%B %Y')
        except ValueError, err:
            print err
            logger.error('Wrong format given for the date')

    if not end_date:
        today = datetime.utcnow()
        begin_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month + 1, 1)
        month_string = 'Past thirty days'

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

        for message_id in thread.email_ids:
            # Extract all the votes for this message
            try:
                votes = Rating.objects.filter(messageid=message_id)
            except Rating.DoesNotExist:
                votes = {}

            likes = 0
            dislikes = 0

            for vote in votes:
                if vote.vote == 1:
                    likes = likes + 1
                elif vote.vote == -1:
                    dislikes = dislikes + 1
                else:
                    pass

            totallikes = totallikes + likes
            totalvotes = totalvotes + likes + dislikes
            totaldislikes = totaldislikes + dislikes

        try:
            thread.avglike = totallikes / totalvotes
        except:
            thread.avglike = 0

        try:
            thread.avgdislike = totaldislikes / totalvotes
        except:
            thread.avgdislike = 0

        thread.likestatus = "neutral"
        if thread.avglike - thread.avgdislike >= 10:
            thread.likestatus = "likealot"
        elif thread.avglike - thread.avgdislike > 0:
            thread.likestatus = "like"
        #elif thread.avglike - thread.avgdislike < 0:
        #    thread.likestatus = "dislike"

        #threads[cnt] = thread
        #cnt = cnt + 1

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

def list(request, mlist_fqdn=None):
    if not mlist_fqdn:
        return HttpResponseRedirect('/')
    t = loader.get_template('recent_activities.html')
    search_form = SearchForm(auto_id=False)

    # Get stats for last 30 days
    today = datetime.utcnow()
    end_date = datetime(today.year, today.month, today.day)
    begin_date = end_date - timedelta(days=32)

    store = get_store(request)
    mlist = store.get_list(mlist_fqdn)
    threads = store.get_threads(list_name=mlist_fqdn, start=begin_date,
        end=end_date)

    participants = set()
    dates = {}
    for thread in threads:
        month = thread.date_active.month
        if month < 10:
            month = '0%s' % month
        day = thread.date_active.day
        if day < 10:
            day = '0%s' % day
        key = '%s%s%s' % (thread.date_active.year, month, day)
        if key in dates:
            dates[key] = dates[key] + 1
        else:
            dates[key] = 1
        # Statistics on how many participants and threads this month
        participants.update(thread.participants)

    # top threads are the one with the most answers
    top_threads = sorted(threads, key=lambda entry: len(entry), reverse=True)

    # active threads are the ones that have the most recent posting
    active_threads = sorted(threads, key=lambda entry: entry.date_active, reverse=True)

    archives_length = get_months(store, mlist_fqdn)

    # top authors are the ones that have the most kudos.  How do we determine
    # that?  Most likes for their post?
    if settings.USE_MOCKUPS:
        authors = generate_top_author()
        authors = sorted(authors, key=lambda author: author.kudos)
        authors.reverse()
    else:
        authors = []

    # Get the list activity per day
    days = dates.keys()
    days.sort()
    dates_string = ["%s/%s/%s" % (key[0:4], key[4:6], key[6:8]) for key in days]
    evolution = [dates[key] for key in days]
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
        'dates_string': dates_string,
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
        'month': search_type,
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

