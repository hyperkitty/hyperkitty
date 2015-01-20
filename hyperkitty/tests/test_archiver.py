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


import os
import json
import shutil
import tempfile
from StringIO import StringIO
from textwrap import dedent
from urllib import urlencode

from mock import Mock, patch
from pkg_resources import resource_string
from zope.configuration import xmlconfig
from django.conf import settings
from mailman.email.message import Message
from kittystore.test import FakeList

from hyperkitty.tests.utils import ViewTestCase
from hyperkitty.archiver import Archiver



class ArchiverTestCase(ViewTestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hyperkitty-testing-")
        conffile = os.path.join(self.tmpdir, "hyperkitty.cfg")
        test_config = dedent("""
        [archiver.hyperkitty]
        configuration: {}
        """.format(conffile))
        self.archiver = Archiver()
        self.archiver._base_url = "http://lists.example.com"
        self.archiver._auth = (settings.MAILMAN_ARCHIVER_API_USER,
                               settings.MAILMAN_ARCHIVER_API_PASS)
        # Patch requests
        self.requests_patcher = patch("hyperkitty.archiver.requests")
        requests = self.requests_patcher.start()
        def internal_req(func, url, *a, **kw):
            extra_args = {"data": {}}
            if "params" in kw:
                extra_args["data"].update(kw["params"])
                del kw["params"]
            if "data" in kw:
                extra_args["data"].update(kw["data"])
            if "files" in kw:
                for field, fdata in kw["files"].items():
                    extra_args["data"][field] = StringIO(fdata[1])
                    extra_args["data"][field].name = fdata[0]
            if "auth" in kw:
                extra_args['HTTP_AUTHORIZATION'] = \
                    'Basic ' + '{}:{}'.format(
                        settings.MAILMAN_ARCHIVER_API_USER,
                        settings.MAILMAN_ARCHIVER_API_PASS
                        ).encode("base64").strip()
            result = func(url, **extra_args)
            result.json = json.loads(result.content)
            return result
        requests.get.side_effect = lambda url, *a, **kw: \
            internal_req(self.client.get, url, *a, **kw)
        requests.post.side_effect = lambda url, *a, **kw: \
            internal_req(self.client.post, url, *a, **kw)

    def tearDown(self):
        self.requests_patcher.stop()
        shutil.rmtree(self.tmpdir)

    def _get_msg(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        return msg


    def test_list_url(self):
        self.assertEqual(self.archiver.list_url(
            FakeList("list@lists.example.com")),
            "http://lists.example.com/list/list@lists.example.com/"
            )

    def test_permalink(self):
        msg = self._get_msg()
        self.assertEqual(self.archiver.permalink(
            FakeList("list@lists.example.com"), msg),
            "http://lists.example.com/list/list@lists.example.com/message/QKODQBCADMDSP5YPOPKECXQWEQAMXZL3/"
            )

    def test_archive_message(self):
        msg = self._get_msg()
        with patch("hyperkitty.archiver.logger") as logger:
            url = self.archiver.archive_message(
                FakeList("list@lists.example.com"), msg)
            self.assertTrue(logger.info.called)
        self.assertEqual(url,
            "http://lists.example.com/list/list@lists.example.com/message/QKODQBCADMDSP5YPOPKECXQWEQAMXZL3/"
            )
        self.assertEqual(self.store.get_list_size(u"list@lists.example.com"), 1)
