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

"""
WSGI and Django middlewares for KittyStore

Inspired by http://pypi.python.org/pypi/middlestorm
"""

from threading import local

from django.conf import settings
import kittystore


class KittyStoreWSGIMiddleware(object):
    """WSGI middleware.
    Add KittyStore object in environ['kittystore.store']. Each thread contains
    own store.
    """

    def __init__(self, app):
        """Create WSGI middleware.
        :param app: top level application or middleware.
        :param database: instance of Database returned create_database.
        """
        self._app = app
        self._local = local()

    def __call__(self, environ, start_response):
        try:
            environ['kittystore.store']  = self._local.store
        except AttributeError:
            environ['kittystore.store']  = \
                    self._local.__dict__.setdefault('store',
                        kittystore.get_store(settings.KITTYSTORE_URL,
                                             settings.KITTYSTORE_DEBUG))
        try:
            return self._app(environ, start_response)
        finally:
            environ['kittystore.store'].rollback()
            #environ['kittystore.store'].close()


class KittyStoreDjangoMiddleware(object):
    """Django middleware.
    Add KittyStore object in environ['kittystore.store']. Each thread contains
    own store.
    """

    def __init__(self):
        """Create Django middleware."""
        self._local = local()

    def process_request(self, request):
        try:
            request.environ['kittystore.store']  = self._local.store
        except AttributeError:
            request.environ['kittystore.store']  = \
                    self._local.__dict__.setdefault('store',
                        kittystore.get_store(settings.KITTYSTORE_URL,
                                             settings.KITTYSTORE_DEBUG))

    #def process_response(self, request, response):
    #    request.environ['kittystore.store'].close()
    #    return response

    def process_exception(self, request, exception):
        request.environ['kittystore.store'].rollback()
