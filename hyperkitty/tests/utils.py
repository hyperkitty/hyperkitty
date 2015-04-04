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

from __future__ import absolute_import, print_function, unicode_literals

import os
import shutil
import tempfile
from unittest import SkipTest

import haystack
import mailmanclient
from mock import Mock, patch
#from django import VERSION as DJANGO_VERSION
from django.test import TestCase as DjangoTestCase
from django.conf import settings
from django.core.management import call_command
#from django.core.cache import get_cache

from hyperkitty.lib.cache import cache


class TestCase(DjangoTestCase):
    # pylint: disable=attribute-defined-outside-init

    override_settings = {
        "DEBUG": True,
        "TEMPLATE_DEBUG": True,
        "USE_SSL": False,
        "USE_MOCKUPS": False,
        "ROOT_URLCONF": "hyperkitty.urls",
        "LOGIN_URL": '/accounts/login/',
        "LOGIN_REDIRECT_URL": '/',
        "LOGIN_ERROR_URL": '/accounts/login/',
        "COMPRESS_ENABLED": False,
        "COMPRESS_PRECOMPILERS": (),
        #"CACHES": {
        #    'default': {
        #        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        #    },
        #},
    }


    def _pre_setup(self):
        super(TestCase, self)._pre_setup()
        # Override settings
        self._old_settings = {}
        for key, value in self.override_settings.items():
            self._old_settings[key] = getattr(settings, key, None)
            setattr(settings, key, value)
        #if DJANGO_VERSION[:2] < (1, 7):
        #    cache.backend = get_cache("default") # in 1.7 it's a proxy
        #else:
        #    from django.core.cache import caches
        #    #print("~"*40, caches.all())
        self.mailman_client = Mock()
        self.mailman_client.get_user.side_effect = mailmanclient.MailmanConnectionError()
        self.mailman_client.get_list.side_effect = mailmanclient.MailmanConnectionError()
        self._mm_client_patcher = patch("hyperkitty.lib.mailman.MailmanClient",
                                        lambda *a: self.mailman_client)
        self._mm_client_patcher.start()

    def _post_teardown(self):
        self._mm_client_patcher.stop()
        cache.clear()
        for key, value in self._old_settings.items():
            if value is None:
                delattr(settings, key)
            else:
                setattr(settings, key, value)
        #if DJANGO_VERSION[:2] < (1, 7):
        #    cache.backend = get_cache("default")
        super(TestCase, self)._post_teardown()


class SearchEnabledTestCase(TestCase):
    # pylint: disable=attribute-defined-outside-init

    def _pre_setup(self):
        try:
            import whoosh # pylint: disable=unused-variable
        except ImportError:
            raise SkipTest("The Whoosh library is not available")
        self.tmpdir = tempfile.mkdtemp(prefix="hyperkitty-testing-")
        self.override_settings["HAYSTACK_CONNECTIONS"] = {
            'default': {
                'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
                'PATH': os.path.join(self.tmpdir, 'fulltext_index'),
            },
        }
        #self.override_settings["HAYSTACK_SIGNAL_PROCESSOR"] = \
        #    'haystack.signals.RealtimeSignalProcessor'
        super(SearchEnabledTestCase, self)._pre_setup()
        # Connect to the backend using the new settings. Using the reload()
        # method is not enough, because the settings are cached in the class
        haystack.connections.connections_info = settings.HAYSTACK_CONNECTIONS
        haystack.connections.reload("default")
        haystack.signal_processor = haystack.signals.RealtimeSignalProcessor(
            haystack.connections, haystack.connection_router)
        call_command('rebuild_index', interactive=False, verbosity=0)

    def _post_teardown(self):
        haystack.signal_processor.teardown()
        shutil.rmtree(self.tmpdir)
        super(SearchEnabledTestCase, self)._post_teardown()




def get_test_file(*fileparts):
    return os.path.join(os.path.dirname(__file__), "testdata", *fileparts)
get_test_file.__test__ = False
