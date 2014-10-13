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


from django.core.urlresolvers import reverse
from mailman.email.message import Message
from mailman.interfaces.archiver import ArchivePolicy

from hyperkitty.tests.utils import ViewTestCase

import kittystore
from kittystore.test import FakeList


class PrivateListTestCase(ViewTestCase):

    def setUp(self):
        ml = FakeList("list@example.com")
        ml.archive_policy = ArchivePolicy.private
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msgid>"
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy message")
        msg["Message-ID-Hash"] = self.msgid = self.store.add_to_list(ml, msg)

    def _do_test(self, sort_mode):
        response = self.client.get(reverse("hk_root"), {"sort": sort_mode})
        self.assertNotContains(response, "list@example.com", status_code=200)

    def test_sort_active(self):
        self._do_test("active")
    def test_sort_popular(self):
        self._do_test("popular")
