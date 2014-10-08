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

from copy import deepcopy

import mailmanclient
from mock import Mock
from django.test import TestCase as DjangoTestCase
from django.conf import settings

import kittystore
from kittystore.test import SettingsModule

import hyperkitty.lib.mailman


OVERRIDE_SETTINGS = {
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
        # Make sure the mailman client always raises an exception
        hyperkitty.lib.mailman.MailmanClient = Mock() # the class
        self.set_mailman_client_mode("failing") # the instance

    def set_mailman_client_mode(self, mode):
        if mode == "failing":
            self.mailman_client = Mock()
            self.mailman_client.get_user.side_effect = mailmanclient.MailmanConnectionError()
        elif mode == "mocking":
            self.mailman_client = FakeMailmanClient()
        else:
            raise ValueError("Mailman client mode is either 'failing' or 'mocking'")
        hyperkitty.lib.mailman.MailmanClient.return_value = self.mailman_client

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()
        for key, value in self._old_settings.iteritems():
            setattr(settings, key, value)
        hyperkitty.lib.mailman.MailmanClient = mailmanclient.Client


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



#
# Fake mailman client
#

from urllib2 import HTTPError

class FakeConnection:
    """
    Looks for information inside a dict instead of making HTTP requests.
    Also, logs the called URLs as called_paths.
    Very incomplete at the moment.
    """

    def __init__(self):
        self.data = {}
        self.called_paths = []

    def call(self, path, data=None, method=None):
        self.called_paths.append(path)
        if data is not None: # serialize objects
            for key, val in data.iteritems():
                data[key] = unicode(val)
        splittedpath = path.split("/")
        result = deepcopy(self.data)
        while splittedpath:
            component = splittedpath.pop(0)
            #print "comp:", component, result
            if component == "find":
                try:
                    result = [result[data.values()[0]]]
                except KeyError:
                    result = []
            else:
                try:
                    result = result[component]
                except KeyError:
                    raise HTTPError(url=path, code=404, hdrs=None, fp=None,
                                    msg="No such path: %s" % path)
        if isinstance(result, list):
            result = {"entries": result}
        content = {"self_link": path}
        content.update(result)
        return None, content # response, content

class FakeMailmanClient(mailmanclient.Client):
    """
    Subclass of mailmanclient.Client to instantiate a FakeConnection object
    instead of the real connection
    """

    def __init__(self, *args, **kw):
        self._connection = FakeConnection()

    @property
    def data(self):
        return self._connection.data
    @data.setter
    def data(self, data):
        self._connection.data = data

    @property
    def called_paths(self):
        return self._connection.called_paths

    def add_fake_user(self, address):
        """Make it easier to create fake users"""
        user_id = address[:address.index("@")] + "_userid"
        if "users" not in self._connection.data:
            self._connection.data["users"] = {}
        self._connection.data["users"][address] = {"user_id": user_id}
        self._connection.data["users"][user_id] = {"addresses": [{
            "email": address, "self_link": "address/%s" % address}]}
        if "members" not in self._connection.data:
            self._connection.data["members"] = {}
