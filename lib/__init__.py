#-*- coding: utf-8 -*-

from hashlib import md5
import urllib


def gravatar_url(email):
    '''Return a gravatar url for an email address'''
    size = 64
    default = "http://fedoraproject.org/static/images/" + \
            "fedora_infinity_%ix%i.png" % (size, size)
    query_string = urllib.urlencode({'s': size, 'd': default})
    identifier = md5(email).hexdigest()
    return 'http://www.gravatar.com/avatar/%s?%s' % (identifier, query_string)
