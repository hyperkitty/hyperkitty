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

from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, Page
from django.http import Http404

from hyperkitty.models import Tag, MailingList
from hyperkitty.lib.paginator import paginate

from hyperkitty.views.list import _thread_list
from hyperkitty.lib.view_helpers import (
    check_mlist_private, is_mlist_authorized)


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


@check_mlist_private
def search_tag(request, mlist_fqdn, tag):
    '''Returns threads having a particular tag'''
    mlist = get_object_or_404(MailingList, name=mlist_fqdn)
    #tags = Tag.objects.filter(tag=tag).distinct()
    threads = Thread.objects.filter(mailinglist__name=mlist_fqdn, tags__tag=tag)
    #tags = Tag.objects.filter(thread__mailinglist__name=mlist_fqdn, tag=tag)
    extra_context = {
        "tag": tag,
        "list_title": "Search results for tag \"%s\"" % tag,
        "no_results_text": "for this tag",
    }
    return _thread_list(request, mlist, threads, extra_context=extra_context)


def search(request, page=1):
    """ Returns messages corresponding to a query """
    results_per_page = 10
    query = request.GET.get("query")
    mlist_fqdn = request.GET.get("list")
    sort_mode = request.GET.get('sort')

    if mlist_fqdn is None:
        mlist = None
    else:
        try:
            mlist = MailingList.objects.get(name=mlist_fqdn)
        except MailingList.DoesNotExist:
            raise Http404("No archived mailing-list by that name.")
        if not is_mlist_authorized(request, mlist):
            return render(request, "hyperkitty/errors/private.html", {
                            "mlist": mlist,
                          }, status=403)

    # TODO: fulltext search engine necessary from here
    if not getattr(settings, "SEARCH", False):
        return render(request, "hyperkitty/errors/nosearch.html", {"mlist": mlist})

    if not query:
        return render(request, "hyperkitty/search_results.html", {
            'mlist' : mlist,
            "query": query or "",
            'messages': [],
            'total': 0,
            'sort_mode': sort_mode,
        })

    try:
        page_num = int(request.GET.get('page', "1"))
    except ValueError:
        page_num = 1

    sortedby = None
    reverse = False
    if sort_mode == "date-asc":
        sortedby = "date"
    elif sort_mode == "date-desc":
        sortedby = "date"
        reverse = True

    query_result = search(query, mlist_fqdn, page_num, results_per_page,
                          sortedby=sortedby, reverse=reverse)
    total = query_result["total"]
    messages = [ m for m in query_result["results"] if m is not None ]
    for message in messages:
        message.myvote = message.get_vote_by_user_id(
                request.session.get("user_id"))

    paginator = SearchPaginator(messages, 10, total)
    messages = paginate(messages, page_num, paginator=paginator)

    context = {
        'mlist' : mlist,
        "query": query,
        'messages': messages,
        'total': total,
        'sort_mode': sort_mode,
    }
    return render(request, "hyperkitty/search_results.html", context)
