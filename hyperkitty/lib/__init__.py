#-*- coding: utf-8 -*-

import urllib
from hashlib import md5
import threading
import datetime

from django.conf import settings

from hyperkitty.utils import log

import kittystore


class ThreadSafeStorePool(object):
    """
    http://unpythonic.blogspot.fr/2007/11/using-storm-and-sqlite-in-multithreaded.html
    """

    def __init__(self):
        self._local = threading.local()

    def get(self):
        try:
            return self._local.store
        except AttributeError:
            self._local.store = kittystore.get_store(settings.KITTYSTORE_URL, debug=False)
            return self._local.store


def gravatar_url(email):
    '''Return a gravatar url for an email address'''
    size = 64
    default = "http://fedoraproject.org/static/images/" + \
            "fedora_infinity_%ix%i.png" % (size, size)
    query_string = urllib.urlencode({'s': size, 'd': default})
    identifier = md5(email).hexdigest()
    return 'http://www.gravatar.com/avatar/%s?%s' % (identifier, query_string)


def get_months(store, list_name):
    """ Return a dictionnary of years, months for which there are
    potentially archives available for a given list (based on the
    oldest post on the list).

    :arg list_name, name of the mailing list in which this email
    should be searched.
    """
    date_first = store.get_start_date(list_name)
    if not date_first:
        return {}
    archives = {}
    now = datetime.datetime.now()
    year = date_first.year
    month = date_first.month
    while year < now.year:
        archives[year] = range(1, 13)[(month -1):]
        year = year + 1
        month = 1
    archives[now.year] = range(1, 13)[:now.month]
    return archives

