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

from __future__ import absolute_import, unicode_literals, print_function

from django.shortcuts import render
from django.http import Http404
from haystack.query import EmptySearchQuerySet, RelatedSearchQuerySet
from haystack.forms import SearchForm

from hyperkitty.models import MailingList, ArchivePolicy
from hyperkitty.lib.paginator import paginate
from hyperkitty.lib.view_helpers import is_mlist_authorized



def search(request):
    """ Returns messages corresponding to a query """
    mlist_fqdn = request.GET.get("mlist")
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


    query = ''
    results = EmptySearchQuerySet()
    sqs = RelatedSearchQuerySet()

    # Remove private non-subscribed lists
    if mlist is not None:
        sqs = sqs.filter(mailinglist__exact=mlist.name)
    else:
        excluded_mlists = MailingList.objects.filter(
            archive_policy=ArchivePolicy.private.value)
        if request.user.is_authenticated():
            subscriptions = request.user.hyperkitty_profile.get_subscriptions()
            excluded_mlists = excluded_mlists.exclude(name__in=subscriptions)
        excluded_mlists = excluded_mlists.values_list("name", flat=True)
        sqs = sqs.exclude(mailinglist__in=excluded_mlists)

    # Sorting
    sort_mode = request.GET.get('sort')
    if sort_mode == "date-asc":
        sqs = sqs.order_by("date")
    elif sort_mode == "date-desc":
        sqs = sqs.order_by("-date")

    # Handle data
    if request.GET.get('q'):
        form = SearchForm(
            request.GET, searchqueryset=sqs, load_all=True)
        if form.is_valid():
            query = form.cleaned_data['q']
            results = form.search()
    else:
        form = SearchForm(searchqueryset=sqs, load_all=True)

    messages = paginate(results, page_num=request.GET.get('page'))
    for message in messages:
        if request.user.is_authenticated():
            message.object.myvote = message.object.votes.filter(user=request.user).first()
        else:
            message.object.myvote = None


    context = {
        'mlist' : mlist,
        'form': form,
        'messages': messages,
        'query': query,
        'sort_mode': sort_mode,
        'suggestion': None,
    }
    if results.query.backend.include_spelling:
        context['suggestion'] = form.get_suggestion()

    return render(request, "hyperkitty/search_results.html", context)
