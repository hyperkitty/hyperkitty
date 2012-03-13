#-*- coding: utf-8 -*-

from calendar import timegm
from datetime import date, datetime, timedelta
import json
import logging
import os
import string
from urlparse import urljoin

import bunch
from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.conf import settings
import notmuch
import urlgrabber

from hyperkitty.lib.mockup import generate_random_thread, generate_top_author, \
    generate_thread_per_category, get_email_tag

from hyperkitty.lib import gravatar_url
from lib.notmuch import get_ro_db

# Move this into settings.py
ARCHIVE_DIR = '/home/toshio/mm3/mailman/var/archives/hyperkitty/'
# Used to remove tags that notmuch added automatically that we don't want
IGNORED_TAGS = (u'inbox', u'unread', u'signed')

MAILING_LIST = 'Fedora Development'
MAILING_LIST_ADDRESS = 'devel@list.fedoraproject.org'
MONTH = 'January 2011'
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
    t = loader.get_template('index.html')
    search_form = SearchForm(auto_id=False)
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : MAILING_LIST,
        'list_address': MAILING_LIST_ADDRESS,
        'search_form': search_form['keyword'],
    })
    return HttpResponse(t.render(c))


def archives(request, year=None, month=None):
    if not year and not month:
        today = date.today()
    else:
        try:
            today = date(int(year), int(month), 1)
        except ValueError, err:
            logger.error('Wrong format given for the date')
    search_form = SearchForm(auto_id=False)
    t = loader.get_template('month_view.html')
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : MAILING_LIST,
        'list_address': MAILING_LIST_ADDRESS,
        'search_form': search_form['keyword'],
        'month': today.strftime("%B %Y"),
        'month_participants': MONTH_PARTICIPANTS,
        'month_discussions': MONTH_DISCUSSIONS,
        'threads': generate_random_thread(),
    })
    return HttpResponse(t.render(c))

def recent(request):
    t = loader.get_template('recent_activities.html')
    threads = generate_random_thread()
    threads2 = threads[:]
    threads2.reverse()
    authors = generate_top_author()
    authors = sorted(authors, key=lambda author: author.kudos)
    authors.reverse()
    threads_per_category = generate_thread_per_category()
    search_form = SearchForm(auto_id=False)
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : MAILING_LIST,
        'list_address': MAILING_LIST_ADDRESS,
        'search_form': search_form['keyword'],
        'month': 'Recent activity',
        'month_participants': MONTH_PARTICIPANTS,
        'month_discussions': MONTH_DISCUSSIONS,
        'top_threads': threads,
        'most_active_threads': threads2,
        'top_author': authors,
        'threads_per_category': threads_per_category,
    })
    return HttpResponse(t.render(c))


def search(request):
    keyword = request.GET.get('keyword')
    return HttpResponseRedirect('/search/%s' % keyword)


def search_keyword(request, keyword):
    search_form = SearchForm(auto_id=False)
    t = loader.get_template('search.html')
    if keyword:
        c = RequestContext(request, {
            'app_name': settings.APP_NAME,
            'list_name' : MAILING_LIST,
            'list_address': MAILING_LIST_ADDRESS,
            'search_form': search_form['keyword'],
            'month': 'Search',
            'month_participants': MONTH_PARTICIPANTS,
            'month_discussions': MONTH_DISCUSSIONS,
            'threads': generate_random_thread(),
        })
    else:
        c = RequestContext(request, {
            'app_name': settings.APP_NAME,
            'list_name' : MAILING_LIST,
            'list_address': MAILING_LIST_ADDRESS,
            'search_form': search_form['keyword'],
            'month': 'Search',
            'month_participants': MONTH_PARTICIPANTS,
            'month_discussions': MONTH_DISCUSSIONS,
            'threads': [],
        })
    return HttpResponse(t.render(c))

def search_tag(request, tag):
    search_form = SearchForm(auto_id=False)
    t = loader.get_template('search.html')
    c = RequestContext(request, {
        'app_name': settings.APP_NAME,
        'list_name' : MAILING_LIST,
        'list_address': MAILING_LIST_ADDRESS,
        'search_form': search_form['keyword'],
        'month': 'Tag search',
        'month_participants': MONTH_PARTICIPANTS,
        'month_discussions': MONTH_DISCUSSIONS,
        'threads': get_email_tag(tag),
    })
    return HttpResponse(t.render(c))
