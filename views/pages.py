#-*- coding: utf-8 -*-

from calendar import timegm
from datetime import datetime, timedelta
import json
import logging
import os
from urlparse import urljoin

from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
#import urlgrabber

from bunch import Bunch

from lib.mockup import generate_thread_per_category, generate_top_author

from lib import mongo

# Move this into settings.py
MONTH_PARTICIPANTS = 284
MONTH_DISCUSSIONS = 82
logger = logging.getLogger(__name__)


class SearchForm(forms.Form):
    keyword = forms.CharField(max_length=100,
                widget=forms.TextInput(
                    attrs={'placeholder': 'Search this list.'}
                    )
                )

def index(request):
    t = loader.get_template('index2.html')
    search_form = SearchForm(auto_id=False)
    base_url = settings.MAILMAN_API_URL % {
        'username': settings.MAILMAN_USER, 'password': settings.MAILMAN_PASS}
    #data = json.load(urlgrabber.urlopen(urljoin(base_url, 'lists')))
    #list_data = sorted(data['entries'], key=lambda elem: (elem['mail_host'], elem['list_name']))
    list_data = ['devel@fp.o', 'packaging@fp.o', 'fr-users@fp.o']
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'lists': list_data,
        'search_form': search_form['keyword'],
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
    t = loader.get_template('month_view2.html')
    threads = mongo.get_archives(list_name, start=begin_date,
        end=end_date)

    participants = set()
    cnt = 0
    for msg in threads:
        msg = Bunch(msg)
        # Statistics on how many participants and threads this month
        participants.add(msg['From'])
        msg.participants = mongo.get_thread_participants(list_name,
            msg['Thread-ID'])
        msg.answers = mongo.get_thread_length(list_name,
            msg['Thread-ID'])
        threads[cnt] = msg
        cnt = cnt + 1

    archives_length = mongo.get_archives_length(list_name)

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form['keyword'],
        'month': month_string,
        'month_participants': len(participants),
        'month_discussions': len(threads),
        'threads': threads,
        'archives_length': archives_length,
    })
    return HttpResponse(t.render(c))

def list(request, mlist_fqdn=None):
    if not mlist_fqdn:
        return HttpResponseRedirect('/2/')
    t = loader.get_template('recent_activities.html')
    search_form = SearchForm(auto_id=False)
    list_name = mlist_fqdn.split('@')[0]

    # Get stats for last 30 days
    today = datetime.utcnow()
    end_date = datetime(today.year, today.month, today.day)
    begin_date = end_date - timedelta(days=32)

    print begin_date, end_date
    threads = mongo.get_archives(table=list_name,start=begin_date,
        end=end_date)

    participants = set()
    cnt = 0
    for msg in threads:
        msg = Bunch(msg)
        # Statistics on how many participants and threads this month
        participants.add(msg['From'])
        msg.participants = mongo.get_thread_participants(list_name,
            msg['Thread-ID'])
        msg.answers = mongo.get_thread_length(list_name,
            msg['Thread-ID'])
        threads[cnt] = msg
        cnt = cnt + 1
    print len(threads)

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
        'search_form': search_form['keyword'],
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

def _search_results_page(request, mlist_fqdn, query_string, search_type):
    search_form = SearchForm(auto_id=False)
    t = loader.get_template('search2.html')

    list_name = mlist_fqdn.split('@')[0]

    try:
        db = get_ro_db(os.path.join(ARCHIVE_DIR, mlist_fqdn))
    except IOError:
        logger.error('No archive for mailing list %s' % mlist_fqdn)
        return

    # Note, can't use tuple() because of a bug in notmuch
    # Collect data about each thread
    threads = []
    participants = set()
    if query_string:
        for thread in db.create_query(query_string).search_threads():
            thread_info = get_thread_info(thread)
            participants.update(thread_info.participants)
            threads.append(thread_info)

        threads.sort(key=lambda entry: entry.most_recent, reverse=True)

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form['keyword'],
        'month': search_type,
        'month_participants': len(participants),
        'month_discussions': len(threads),
        'threads': threads,
    })
    return HttpResponse(t.render(c))


def search(request, mlist_fqdn):
    keyword = request.GET.get('keyword')
    if keyword:
        url = '/2/search/%s/%s' % (mlist_fqdn, keyword)
    else:
        url = '/2/search/%s' % (mlist_fqdn,)
    return HttpResponseRedirect(url)


def search_keyword(request, mlist_fqdn, keyword=None):
    if not keyword:
        keyword = request.GET.get('keyword')
    return _search_results_page(request, mlist_fqdn, keyword, 'Search')


def search_tag(request, mlist_fqdn, tag=None):
    '''Searches both tag and topic'''
    if tag:
        query_string = 'tag:%(tag)s or tag:=topic=%(tag)s' % {'tag': tag}
    else:
        query_string = None
    return _search_results_page(request, mlist_fqdn, query_string, 'Tag search')
