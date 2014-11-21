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

import uuid
from copy import deepcopy

import mailmanclient
from mock import Mock, patch
from django.test import TestCase as DjangoTestCase
from django.conf import settings

import kittystore
from kittystore.test import SettingsModule
from mailmanclient.tests.utils import FakeMailmanClient

import hyperkitty.lib.mailman


OVERRIDE_SETTINGS = {
    "DEBUG": True,
    "TEMPLATE_DEBUG": True,
    "USE_SSL": False,
    "KITTYSTORE_URL": 'sqlite:',
    "KITTYSTORE_SEARCH_INDEX": None,
    "KITTYSTORE_DEBUG": False,
    "USE_MOCKUPS": False,
    "ROOT_URLCONF": "hyperkitty.urls",
    "LOGIN_URL": '/accounts/login/',
    "LOGIN_REDIRECT_URL": '/',
    "LOGIN_ERROR_URL": '/accounts/login/',
    "COMPRESS_ENABLED": False,
    "COMPRESS_PRECOMPILERS": (),
    "CACHES": {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
    },
}


class TestCase(DjangoTestCase):

    def _pre_setup(self):
        super(TestCase, self)._pre_setup()
        # Override settings
        self._old_settings = {}
        for key, value in OVERRIDE_SETTINGS.iteritems():
            self._old_settings[key] = getattr(settings, key)
            setattr(settings, key, value)
        # Use the mocking mailman client
        FakeMailmanClient.setUp()
        self.set_mailman_client_mode("failing")
        self._mm_client_patcher = patch("hyperkitty.lib.mailman.MailmanClient",
                                        lambda *a: self.mailman_client)
        self._mm_client_patcher.start()

    def set_mailman_client_mode(self, mode):
        if mode == "failing":
            self.mailman_client = Mock()
            self.mailman_client.get_user.side_effect = mailmanclient.MailmanConnectionError()
        elif mode == "mocking":
           self.mailman_client = FakeMailmanClient('%s/3.0' %
                   settings.MAILMAN_REST_SERVER,
                   settings.MAILMAN_API_USER,
                   settings.MAILMAN_API_PASS)
        else:
            raise ValueError("Mailman client mode is either 'failing' or 'mocking'")

    def _post_teardown(self):
        self._mm_client_patcher.stop()
        FakeMailmanClient.tearDown()
        for key, value in self._old_settings.iteritems():
            setattr(settings, key, value)
        super(TestCase, self)._post_teardown()


class ViewTestCase(TestCase):
    """A testcase class that sets up kittystore to make the web client work"""

    def _pre_setup(self):
        super(ViewTestCase, self)._pre_setup()
        self.store = kittystore.get_store(SettingsModule(),
                                     debug=False, auto_create=True)
        self.client.defaults = {"kittystore.store": self.store,
                                "HTTP_USER_AGENT": "testbot",
                                }

    def _post_teardown(self):
        super(ViewTestCase, self)._post_teardown()
