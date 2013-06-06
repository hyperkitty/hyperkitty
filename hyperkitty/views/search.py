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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#


from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page

from hyperkitty.models import Tag
from hyperkitty.lib import get_store
from hyperkitty.lib.voting import get_votes, set_message_votes

from .list import _thread_list


class SearchPaginator(Paginator):
    """
    A paginator which does not split the object_list into pages, because Whoosh
    already handles that
    """
    def __init__(self, object_list, per_page, total):
        super(SearchPaginator, self).__init__(object_list, per_page)
        self._count = total

    def page(self, number):
        "Returns the object list without paginating"""
        return Page(self.object_list, number, self)


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
        thread = store.get_thread(mlist_fqdn, t.threadid)
        if thread is not None:
            threads.append(thread)

    extra_context = {
        "tag": tag,
        "list_title": "Search results for tag \"%s\"" % tag,
        "no_results_text": "for this tag",
    }
    return _thread_list(request, mlist, threads, extra_context=extra_context)


def search(request, page=1):
    """ Returns messages corresponding to a query """
    store = get_store(request)
    query = request.GET.get("query")
    mlist_fqdn = request.GET.get("list")
    try:
        page_num = int(request.GET.get('page', "1"))
    except ValueError:
        page_num = 1
    results_per_page = 10
    query_result = store.search(query, mlist_fqdn, page_num, results_per_page)
    total = query_result["total"]
    messages = query_result["results"]
    for message in messages:
        set_message_votes(message, request.user)
    if mlist_fqdn is None:
        mlist = None
    else:
        mlist = store.get_list(mlist_fqdn)
        if mlist is None:
            raise Http404("No archived mailing-list by that name.")

    paginator = SearchPaginator(messages, 10, total)
    try:
        messages = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        messages = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        messages = paginator.page(paginator.num_pages)
    messages.page_range = [ p+1 for p in range(paginator.num_pages) ]

    context = {
        'mlist' : mlist,
        "query": query,
        'current_page': page_num,
        'messages': messages,
        'total': total,
    }
    return render(request, "search_results.html", context)



