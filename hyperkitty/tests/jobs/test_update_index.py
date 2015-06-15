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

# pylint: disable=unnecessary-lambda,protected-access

from __future__ import absolute_import, print_function, unicode_literals

import os
import os.path
from tempfile import gettempdir

from mock import Mock, patch

from hyperkitty.jobs.update_index import Job
from hyperkitty.tests.utils import TestCase


def get_lockfile_path():
    return os.path.join(gettempdir(), "hyperkitty-jobs-update-index.lock")


class UpdateIndexTestCase(TestCase):

    def setUp(self):
        self.job = Job()
        self.fnmock = Mock()
        self.patcher = patch("hyperkitty.jobs.update_index.update_index",
                             self.fnmock)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()


    def test_ok(self):
        self.job.execute()
        self.assertTrue(self.fnmock.called)

    def test_lock(self):
        lfp = get_lockfile_path()
        with open(lfp, "w") as lfph:
            lfph.write("%d\n" % os.getpid())
        try:
            self.job.execute()
            self.assertTrue(os.path.exists(lfp))
        finally:
            os.remove(lfp)
        self.assertFalse(self.fnmock.called)

    def test_lock_break(self):
        lfp = get_lockfile_path()
        with open(lfp, "w") as lfph:
            lfph.write("123456789\n")
        try:
            self.job.execute()
            self.assertFalse(os.path.exists(lfp))
        finally:
            try:
                os.remove(lfp)
            except OSError:
                pass # was removed properly
        self.assertTrue(self.fnmock.called)
