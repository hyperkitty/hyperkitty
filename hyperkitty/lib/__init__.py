#-*- coding: utf-8 -*-

import urllib
from hashlib import md5
import threading

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
