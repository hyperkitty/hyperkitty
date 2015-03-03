# -*- coding: utf-8 -*-
# pylint: disable=R0904,C0103

from __future__ import absolute_import, print_function, unicode_literals

from email.message import Message
from textwrap import dedent

from django.test import TestCase

from hyperkitty.management.commands.hyperkitty_import import DbImporter


class DbImporterTestCase(TestCase):

    def setUp(self):
        options = {
            "no_download": True,
            "verbosity": 0,
            "since": None,
        }
        self.importer = DbImporter("example-list", options)

    def test_empty_attachment(self):
        # Make sure the content of an attachment is not unicode when it hasn't
        # been downloaded
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload(dedent("""
        Dummy message
        -------------- next part --------------
        A non-text attachment was scrubbed...
        Name: signature
        Type: application/pgp-signature
        Size: 189 bytes
        Desc: digital signature
        Url : /some/place/in/the/archives/attachment.bin
        
        ------------------------------
        """))
        attachments = self.importer.extract_attachments(msg)
        self.assertEqual(len(attachments), 1)
        self.assertFalse(isinstance(attachments[0]["content"], unicode))
