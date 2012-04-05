#-*- coding: utf-8 -*-

from calendar import timegm
from datetime import datetime, timedelta
import json
import logging
import os
import re
from urlparse import urljoin
import urllib

from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
#import urlgrabber

from bunch import Bunch

from lib.mockup import generate_thread_per_category, generate_top_author

from lib import mongo

# Move this into settings.py
MONTH_PARTICIPANTS = 284
MONTH_DISCUSSIONS = 82
logger = logging.getLogger(__name__)


class SearchForm(forms.Form):
    target =  forms.CharField(label='', help_text=None,
                widget=forms.Select(
                    choices=(('Subject', 'Subject'),
                            ('Content', 'Content'),
                            ('SubjectContent', 'Subject & Content'),
                            ('From', 'From'))
                    )
                )

    keyword = forms.CharField(max_length=100,label='', help_text=None,
                widget=forms.TextInput(
                    attrs={'placeholder': 'Search this list.'}
                    )
                )


def index(request):
    t = loader.get_template('index.html')
    search_form = SearchForm(auto_id=False)
    base_url = settings.MAILMAN_API_URL % {
        'username': settings.MAILMAN_USER, 'password': settings.MAILMAN_PASS}
    #data = json.load(urlgrabber.urlopen(urljoin(base_url, 'lists')))
    #list_data = sorted(data['entries'], key=lambda elem: (elem['mail_host'], elem['list_name']))
    list_data = ['devel@fp.o', 'packaging@fp.o', 'fr-users@fp.o']
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'lists': list_data,
        'search_form': search_form,
        })
    return HttpResponse(t.render(c))


def api(request):
    t = loader.get_template('api.html')
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        })
    return HttpResponse(t.render(c))


def archives(request, mlist_fqdn, year=None, month=None):
    # No year/month: past 32 days
    # year and month: find the 32 days for that month
    end_date = None
    if year or month:
        try:
            begin_date = datetime(int(year), int(month), 1)
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1)
            else:
                end_date = datetime(int(year), int(month) +1, 1)
            month_string = begin_date.strftime('%B %Y')
        except ValueError, err:
            logger.error('Wrong format given for the date')

    if not end_date:
        today = datetime.utcnow()
        begin_date = datetime(today.year, today.month, 1)
        end_date = datetime(today.year, today.month+1, 1)
        month_string = 'Past thirty days'
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('month_view.html')
    threads = mongo.get_archives(list_name, start=begin_date,
        end=end_date)

    participants = set()
    cnt = 0
    for msg in threads:
        msg = Bunch(msg)
        # Statistics on how many participants and threads this month
        participants.add(msg['From'])
        msg.participants = mongo.get_thread_participants(list_name,
            msg['ThreadID'])
        msg.answers = mongo.get_thread_length(list_name,
            msg['ThreadID'])
        threads[cnt] = msg
        cnt = cnt + 1

    archives_length = mongo.get_archives_length(list_name)

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'month': month_string,
        'month_participants': len(participants),
        'month_discussions': len(threads),
        'threads': threads,
        'archives_length': archives_length,
    })
    return HttpResponse(t.render(c))

def list(request, mlist_fqdn=None):
    if not mlist_fqdn:
        return HttpResponseRedirect('/')
    t = loader.get_template('recent_activities.html')
    search_form = SearchForm(auto_id=False)
    list_name = mlist_fqdn.split('@')[0]

    # Get stats for last 30 days
    today = datetime.utcnow()
    end_date = datetime(today.year, today.month, today.day)
    begin_date = end_date - timedelta(days=32)

    threads = mongo.get_archives(table=list_name,start=begin_date,
        end=end_date)

    participants = set()
    cnt = 0
    for msg in threads:
        msg = Bunch(msg)
        # Statistics on how many participants and threads this month
        participants.add(msg['From'])
        msg.participants = mongo.get_thread_participants(list_name,
            msg['ThreadID'])
        msg.answers = mongo.get_thread_length(list_name,
            msg['ThreadID'])
        threads[cnt] = msg
        cnt = cnt + 1

    # top threads are the one with the most answers
    top_threads = sorted(threads, key=lambda entry: entry.answers, reverse=True)

    # active threads are the ones that have the most recent posting
    active_threads = sorted(threads, key=lambda entry: entry.Date, reverse=True)

    archives_length = mongo.get_archives_length(list_name)

    # top authors are the ones that have the most kudos.  How do we determine
    # that?  Most likes for their post?
    authors = generate_top_author()
    authors = sorted(authors, key=lambda author: author.kudos)
    authors.reverse()

    # threads per category is the top thread titles in each category
    threads_per_category = generate_thread_per_category()
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'month': 'Recent activity',
        'month_participants': len(participants),
        'month_discussions': len(threads),
        'top_threads': top_threads[:5],
        'most_active_threads': active_threads[:5],
        'top_author': authors,
        'threads_per_category': threads_per_category,
        'archives_length': archives_length,
    })
    return HttpResponse(t.render(c))

def message (request, mlist_fqdn, messageid):
    ''' Displays a single message identified by its messageid '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('message.html')
    message = Bunch(mongo.get_email(list_name, messageid))

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'message': message,
    })
    return HttpResponse(t.render(c))

def _search_results_page(request, mlist_fqdn, query_string, search_type, page=1, num_threads=25):
    search_form = SearchForm(auto_id=False)
    t = loader.get_template('search.html')
    list_name = mlist_fqdn.split('@')[0]
    threads = mongo.search_archives(list_name, query_string)
    res_num = len(threads)

    participants = set()
    for msg in threads:
        participants.add(msg['From'])

    paginator = Paginator(threads, num_threads)

    #If page request is out of range, deliver last page of results.
    try:
        threads = paginator.page(page)
    except (EmptyPage, InvalidPage):
        threads = paginator.page(paginator.num_pages)

    cnt = 0
    for msg in threads.object_list:
        msg = Bunch(msg)
        # Statistics on how many participants and threads this month
        participants.add(msg['From'])
        if 'ThreadID' in msg:
            msg.participants = mongo.get_thread_participants(list_name,
                msg['ThreadID'])
            msg.answers = mongo.get_thread_length(list_name,
                msg['ThreadID'])
        else:
            msg.participants = 0
            msg.answers = 0
        threads.object_list[cnt] = msg
        cnt = cnt + 1

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'month': search_type,
        'month_participants': len(participants),
        'month_discussions': res_num,
        'threads': threads,
    })
    return HttpResponse(t.render(c))


def search(request, mlist_fqdn):
    keyword = request.GET.get('keyword')
    target = request.GET.get('target')
    print request, target
    if keyword:
        url = '/search/%s/%s/%s/' % (mlist_fqdn, target, keyword)
    else:
        url = '/search/%s' % (mlist_fqdn)
    return HttpResponseRedirect(url)


def search_keyword(request, mlist_fqdn, target=None, keyword=None, page=1):
    print target, keyword, page
    if not keyword:
        keyword = request.GET.get('keyword')
    if not target:
        target = request.GET.get('target')
    if not target:
        target = 'Subject'
    regex = '.*%s.*' % keyword
    if target == 'SubjectContent':
        query_string = {'$or' : [
            {'Subject': re.compile(regex, re.IGNORECASE)},
            {'Content': re.compile(regex, re.IGNORECASE)}
            ]}
    else:
        query_string = {target.capitalize(): re.compile(regex, re.IGNORECASE)}
    return _search_results_page(request, mlist_fqdn, query_string, 'Search', page)


def search_tag(request, mlist_fqdn, tag=None):
    '''Searches both tag and topic'''
    if tag:
        query_string = {'Category': tag.capitalize()}
    else:
        query_string = None
    return _search_results_page(request, mlist_fqdn, query_string, 'Tag search')

def thread (request, mlist_fqdn, threadid):
    ''' Displays all the email for a given thread identifier '''
    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('thread.html')
    threads = mongo.get_thread_list(list_name, threadid)
    #prev_thread = mongo.get_thread_name(list_name, int(threadid) - 1)
    prev_thread = []
    if len(prev_thread) > 30:
        prev_thread = '%s...' % prev_thread[:31]
    #next_thread = mongo.get_thread_name(list_name, int(threadid) + 1)
    next_thread = []
    if len(next_thread) > 30:
        next_thread = '%s...' % next_thread[:31]

    participants = set()
    cnt = 0
    for msg in threads:
        msg = Bunch(msg)
        # Statistics on how many participants and threads this month
        participants.add(msg.email.From)
        cnt = cnt + 1

    archives_length = mongo.get_archives_length(list_name)

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form,
        'month': 'Thread',
        'participants': participants,
        'answers': cnt,
        'first_mail': threads[0],
        'threads': threads[1:],
        'next_thread': next_thread,
        'next_thread_id': 0,
        'prev_thread': prev_thread,
        'prev_thread_id': 0,
        'archives_length': archives_length,
    })
    return HttpResponse(t.render(c))
