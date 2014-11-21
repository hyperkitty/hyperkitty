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
import shutil
import tempfile
from textwrap import dedent

from mock import Mock, patch
from pkg_resources import resource_string
from zope.configuration import xmlconfig
from mailman.config import config
from mailman.email.message import Message
from kittystore.test import FakeList

from hyperkitty.tests.utils import TestCase
from hyperkitty.archiver import Archiver



class ArchiverTestCase(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hyperkitty-testing-")
        conffile = os.path.join(self.tmpdir, "hyperkitty.cfg")
        test_config = dedent("""
        [archiver.hyperkitty]
        configuration: {}
        """.format(conffile))
        # Mailman's config has been initialized by the FakeMailmanClient
        config.push('ArchiverTestCase config', test_config)
        with open(conffile, 'w') as hkcfg:
            hkcfg.write(dedent("""
        [general]
        base_url: http://lists.example.com
        django_settings: {}/settings.py
        """.format(self.tmpdir)))
        self.archiver = Archiver()

    def tearDown(self):
        config.pop('ArchiverTestCase config')
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

    @patch("hyperkitty.archiver.get_store")
    def test_archive_message(self, get_store):
        store = Mock()
        get_store.return_value = store
        msg = self._get_msg()
        with patch("hyperkitty.archiver.logger") as logger:
            url = self.archiver.archive_message(
                FakeList("list@lists.example.com"), msg)
            self.assertTrue(logger.info.called)
        self.assertEqual(url,
            "http://lists.example.com/list/list@lists.example.com/message/QKODQBCADMDSP5YPOPKECXQWEQAMXZL3/"
            )
        self.assertTrue(store.add_to_list.called)
        self.assertTrue(store.commit.called)
