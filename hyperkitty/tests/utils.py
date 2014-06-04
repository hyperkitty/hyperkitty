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


from django.test import TestCase as DjangoTestCase
from django.conf import settings

import kittystore
from kittystore.test import SettingsModule


OVERRIDE_SETTINGS = {
    "TEMPLATE_DEBUG": True,
    "ASSETS_DEBUG": True,
    "USE_SSL": False,
    "KITTYSTORE_URL": 'sqlite:',
    "KITTYSTORE_SEARCH_INDEX": None,
    "KITTYSTORE_DEBUG": False,
    "USE_MOCKUPS": False,
    "ROOT_URLCONF": "hyperkitty.urls",
    "LOGIN_URL": '/accounts/login/',
    "LOGIN_REDIRECT_URL": '/',
    "LOGIN_ERROR_URL": '/accounts/login/',
    "CACHES": {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
    },
}


class TestCase(DjangoTestCase):

    def _pre_setup(self):
        super(TestCase, self)._pre_setup()
        self._old_settings = {}
        for key, value in OVERRIDE_SETTINGS.iteritems():
            self._old_settings[key] = getattr(settings, key)
            setattr(settings, key, value)

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        for key, value in self._old_settings.iteritems():
            setattr(settings, key, value)


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
