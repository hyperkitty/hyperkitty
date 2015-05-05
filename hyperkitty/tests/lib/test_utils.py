# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
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

import datetime
from email.message import Message
from email import message_from_file

from django.utils import timezone
try:
    from django.utils.timezone import get_fixed_timezone
except ImportError:
    # Django < 1.7
    from django.utils.tzinfo import FixedOffset as get_fixed_timezone

from hyperkitty.lib import utils
from hyperkitty.tests.utils import TestCase, get_test_file


class TestUtils(TestCase):

    def test_ref_parsing(self):
        with open(get_test_file("strange-in-reply-to-header.txt")) as email_file:
            msg = message_from_file(email_file)
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, "200704070053.46646.other.person@example.com")

    def test_wrong_reply_to_format(self):
        with open(get_test_file("wrong-in-reply-to-header.txt")) as email_file:
            msg = message_from_file(email_file)
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, None)

    def test_in_reply_to(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["In-Reply-To"] = " <ref-1> "
        msg.set_payload("Dummy message")
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, "ref-1")

    def test_in_reply_to_and_reference(self):
        """The In-Reply-To header should win over References"""
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["In-Reply-To"] = " <ref-1> "
        msg["References"] = " <ref-2> "
        msg.set_payload("Dummy message")
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, "ref-1")

    def test_single_reference(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["References"] = " <ref-1> "
        msg.set_payload("Dummy message")
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, "ref-1")

    def test_reference_no_brackets(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["References"] = "ref-1"
        msg.set_payload("Dummy message")
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, "ref-1")

    def test_multiple_reference(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["References"] = " <ref-1> <ref-2> "
        msg.set_payload("Dummy message")
        ref_id = utils.get_ref(msg)
        self.assertEqual(ref_id, "ref-2")

    def test_empty_reference(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["References"] = " "
        msg.set_payload("Dummy message")
        try:
            utils.get_ref(msg)
        except IndexError:
            self.fail("Empty 'References' tag should be handled")

    def test_non_ascii_headers(self):
        """utils.header_to_unicode must handle non-ascii headers"""
        testdata = [
                ("=?ISO-8859-2?Q?V=EDt_Ondruch?=", u'V\xedt Ondruch'),
                ("=?UTF-8?B?VsOtdCBPbmRydWNo?=", u'V\xedt Ondruch'),
                ("=?iso-8859-1?q?Bj=F6rn_Persson?=", u'Bj\xf6rn Persson'),
                ("=?UTF-8?B?TWFyY2VsYSBNYcWhbMOhxYhvdsOh?=", u'Marcela Ma\u0161l\xe1\u0148ov\xe1'),
                ("Dan =?ISO-8859-1?Q?Hor=E1k?=", u'Dan Hor\xe1k'),
                ("=?ISO-8859-1?Q?Bj=F6rn?= Persson", u'Bj\xf6rn Persson'),
                ("=?UTF-8?Q?Re=3A_=5BFedora=2Dfr=2Dlist=5D_Compte=2Drendu_de_la_r=C3=A9union_du_?= =?UTF-8?Q?1_novembre_2009?=", u"Re: [Fedora-fr-list] Compte-rendu de la r\xe9union du 1 novembre 2009"),
                ("=?iso-8859-1?q?Compte-rendu_de_la_r=E9union_du_?= =?iso-8859-1?q?1_novembre_2009?=", u"Compte-rendu de la r\xe9union du 1 novembre 2009"),
                ]
        for h_in, h_expected in testdata:
            h_out = utils.header_to_unicode(h_in)
            self.assertEqual(h_out, h_expected)
            self.assertTrue(isinstance(h_out, unicode))

    def test_bad_header(self):
        """
        utils.header_to_unicode must handle badly encoded non-ascii headers
        """
        testdata = [
            (b"Guillermo G\xf3mez", u"Guillermo G\ufffdmez"),
            ("=?gb2312?B?UmU6IFJlOl9bQW1iYXNzYWRvcnNdX01hdGVyaWFfc29icmVfb19DRVNvTF8oRGnhcmlvX2RlX2JvcmRvKQ==?=",
                u"Re: Re:_[Ambassadors]_Materia_sobre_o_CESoL_(Di\ufffdrio_de_bordo)"),
        ]
        for h_in, h_expected in testdata:
            try:
                h_out = utils.header_to_unicode(h_in)
            except UnicodeDecodeError, e:
                self.fail(e)
            self.assertEqual(h_out, h_expected)
            self.assertTrue(isinstance(h_out, unicode))

    def test_wrong_datestring(self):
        datestring = "Fri, 5 Dec 2003 11:41 +0000 (GMT Standard Time)"
        parsed = utils.parsedate(datestring)
        self.assertEqual(parsed, None)

    def test_very_large_timezone(self):
        """
        Timezone displacements must not be greater than 14 hours
        Or PostgreSQL won't accept them.
        """
        datestrings = [
            ("Wed, 1 Nov 2006 23:50:26 +1800",
            datetime.datetime(2006, 11, 1, 23, 50, 26,
                              tzinfo=get_fixed_timezone(18*60))),
            ("Wed, 1 Nov 2006 23:50:26 -1800",
            datetime.datetime(2006, 11, 1, 23, 50, 26,
                              tzinfo=get_fixed_timezone(-18*60))),
            ]
        for datestring, expected in datestrings:
            parsed = utils.parsedate(datestring)
            self.assertEqual(parsed, expected)
            self.assertTrue(parsed.utcoffset() <= datetime.timedelta(hours=13),
                            "UTC offset %s for datetime %s is too large"
                            % (parsed.utcoffset(), parsed))

    def test_datestring_no_timezone(self):
        datestring = "Sun, 12 Dec 2004 19:11:28"
        parsed = utils.parsedate(datestring)
        expected = datetime.datetime(2004, 12, 12, 19, 11, 28,
                                     tzinfo=timezone.utc)
        self.assertEqual(parsed, expected)

    def test_unknown_encoding(self):
        """Unknown encodings should just replace unknown characters"""
        header = "=?x-gbk?Q?Frank_B=A8=B9ttner?="
        decoded = utils.header_to_unicode(header)
        self.assertEqual(decoded, u'Frank B\ufffd\ufffdttner')

    def test_no_from(self):
        msg = Message()
        msg.set_payload("Dummy message")
        try:
            name, email = utils.parseaddr(msg["From"])
        except AttributeError, e:
            self.fail(e)
        self.assertEqual(name, '')
        self.assertEqual(email, '')

    def test_get_message_id_hash(self):
        msg_id = '<87myycy5eh.fsf@uwakimon.sk.tsukuba.ac.jp>'
        expected = 'JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP'
        self.assertEqual(utils.get_message_id_hash(msg_id), expected)

    def test_get_message_id(self):
        msg = Message()
        msg["Message-Id"] = '<%s>' % ('x' * 300)
        self.assertEqual(utils.get_message_id(msg), 'x' * 254)

    def test_non_ascii_ref(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["In-Reply-To"] = u"<ref-\xed>".encode('utf-8')
        msg.set_payload("Dummy message")
        try:
            ref_id = utils.get_ref(msg)
        except UnicodeEncodeError as e:
            self.fail(e)
        self.assertEqual(ref_id, "ref-")
