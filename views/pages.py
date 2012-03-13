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
import urlgrabber

from lib.mockup import generate_thread_per_category, generate_top_author

from lib.notmuch import get_thread_info, get_ro_db

# Move this into settings.py
ARCHIVE_DIR = '/home/toshio/mm3/mailman/var/archives/hyperkitty/'

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
    data = json.load(urlgrabber.urlopen(urljoin(base_url, 'lists')))
    list_data = sorted(data['entries'], key=lambda elem: (elem['mail_host'], elem['list_name']))
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
            end_date = begin_date + timedelta(days=32)
            month_string = begin_date.strftime('%B %Y')
        except ValueError, err:
            logger.error('Wrong format given for the date')

    if not end_date:
        end_date = datetime.utcnow()
        begin_date = end_date - timedelta(days=32)
        month_string = 'Past thirty days'
    begin_timestamp = timegm(begin_date.timetuple())
    end_timestamp = timegm(end_date.timetuple())

    list_name = mlist_fqdn.split('@')[0]

    search_form = SearchForm(auto_id=False)
    t = loader.get_template('month_view2.html')

    try:
        db = get_ro_db(os.path.join(ARCHIVE_DIR, mlist_fqdn))
    except IOError:
        logger.error('No archive for mailing list %s' % mlist_fqdn)
        return

    msgs = db.create_query('%s..%s' % (begin_timestamp, end_timestamp)).search_messages()
    participants = set()
    discussions = set()
    for msg in msgs:
        message = json.loads(msg.format_message_as_json())
        # Statistics on how many participants and threads this month
        participants.add(message['headers']['From'])
        discussions.add(msg.get_thread_id())

    # Collect data about each thread
    threads = []
    for thread_id in discussions:
        # Note: can't use tuple() due to a bug in notmuch
        thread = [thread for thread in db.create_query('thread:%s' % thread_id).search_threads()]
        if len(thread) != 1:
            logger.warning('Unknown thread_id %(thread)s from %(mlist)s:'
                    ' %(start)s-%(end)s' % {
                        'thread': thread_id, 'mlist': mlist_fqdn,
                        'start': begin_timestamp, 'end': end_timestamp})
            continue
        thread = thread[0]
        thread_info = get_thread_info(thread)
        threads.append(thread_info)

    # For threads, we need to have threads ordered by
    # youngest to oldest with the oldest message within thread
    threads.sort(key=lambda entry: entry.most_recent, reverse=True)

    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : list_name,
        'list_address': mlist_fqdn,
        'search_form': search_form['keyword'],
        'month': month_string,
        'month_participants': len(participants),
        'month_discussions': len(discussions),
        'threads': threads,
    })
    return HttpResponse(t.render(c))

def recent(request, mlist_fqdn):
    t = loader.get_template('recent_activities.html')
    search_form = SearchForm(auto_id=False)
    list_name = mlist_fqdn.split('@')[0]

    # Get stats for last 30 days
    end_date = datetime.utcnow()
    begin_date = end_date - timedelta(days=32)
    begin_timestamp = timegm(begin_date.timetuple())
    end_timestamp = timegm(end_date.timetuple())

    try:
        db = get_ro_db(os.path.join(ARCHIVE_DIR, mlist_fqdn))
    except IOError:
        logger.error('No archive for mailing list %s' % mlist_fqdn)
        return

    msgs = db.create_query('%s..%s' % (begin_timestamp, end_timestamp)).search_messages()
    participants = set()
    discussions = set()
    for msg in msgs:
        message = json.loads(msg.format_message_as_json())
        # Statistics on how many participants and threads this month
        participants.add(message['headers']['From'])
        discussions.add(msg.get_thread_id())

    thread_query = db.create_query('%s..%s' % (begin_timestamp, end_timestamp)).search_threads()
    top_threads = []
    for thread in thread_query:
        thread_info = get_thread_info(thread)
        top_threads.append(thread_info)
    # top threads are the ones with the most posts
    top_threads.sort(key=lambda entry: len(entry.answers), reverse=True)

    # active threads are the ones that have the most recent posting
    active_threads = sorted(top_threads, key=lambda entry: entry.most_recent, reverse=True)

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
        'month_discussions': len(discussions),
        'top_threads': top_threads,
        'most_active_threads': active_threads,
        'top_author': authors,
        'threads_per_category': threads_per_category,
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
