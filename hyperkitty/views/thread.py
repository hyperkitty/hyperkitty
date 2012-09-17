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

import datetime

import django.utils.simplejson as simplejson

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)

from hyperkitty.models import Rating, Tag
#from hyperkitty.lib.mockup import *
from forms import *
from hyperkitty.lib import get_months, get_store


def thread_index (request, mlist_fqdn, threadid):
    ''' Displays all the email for a given thread identifier '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('thread.html')
    store = get_store(request)
    messages = store.get_messages_in_thread(mlist_fqdn, threadid)
    #prev_thread = mongo.get_thread_name(list_name, int(threadid) - 1)
    prev_thread = []
    if len(prev_thread) > 30:
        prev_thread = '%s...' % prev_thread[:31]
    #next_thread = mongo.get_thread_name(list_name, int(threadid) + 1)
    next_thread = []
    if len(next_thread) > 30:
        next_thread = '%s...' % next_thread[:31]

    participants = {}
    cnt = 0

    for message in messages:
        # @TODO: Move this logic inside KittyStore?
        message.sender_email = message.sender_email.strip()

        # Extract all the votes for this message
        try:
            votes = Rating.objects.filter(messageid=message.message_id)
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

        message.votes = votes
        message.likes = likes
        message.dislikes = dislikes

        # Statistics on how many participants and messages this month
        participants[message.sender_name] = {'email': message.sender_email}
        cnt = cnt + 1

    archives_length = get_months(store, mlist_fqdn)
    from_url = '/thread/%s/%s/' % (mlist_fqdn, threadid)
    tag_form = AddTagForm(initial={'from_url' : from_url})

    try:
        tags = Tag.objects.filter(threadid=threadid)
    except Tag.DoesNotExist:
        tags = {}

    # Extract relative dates
    today = datetime.date.today()
    days_old = today - messages[0].date.date()
    days_inactive = today - messages[-1].date.date()

    c = RequestContext(request, {
        'list_name' : list_name,
        'threadid' : threadid,
        'tags' : tags,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'addtag_form': tag_form,
        'month': 'Thread',
        'participants': participants,
        'answers': cnt,
        'first_mail': messages[0],
        'replies': messages[1:],
        'next_thread': next_thread,
        'next_thread_id': 0,
        'prev_thread': prev_thread,
        'prev_thread_id': 0,
        'archives_length': archives_length,
        'days_inactive': days_inactive.days,
        'days_old': days_old.days,
    })
    return HttpResponse(t.render(c))


@login_required
def add_tag(request, mlist_fqdn, email_id):
    """ Add a tag to a given thread. """

    if request.method == 'POST':
        form = AddTagForm(request.POST)
        if form.is_valid():
            print "Adding tag..."

            tag = form.data['tag']

            try:
                tag_obj = Tag.objects.get(threadid=email_id, list_address=mlist_fqdn, tag=tag)
            except Tag.DoesNotExist:
                tag_obj = Tag(list_address=mlist_fqdn, threadid=email_id, tag=tag) 

            tag_obj.save()
            response_dict = { }
        else:
            response_dict = {'error' : 'Error adding tag, enter valid data' }

    return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')

