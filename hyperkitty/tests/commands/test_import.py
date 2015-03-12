# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os.path
import mailbox
import tempfile
from email.message import Message
from shutil import rmtree
from StringIO import StringIO
from textwrap import dedent

from mock import patch
from django.conf import settings

from hyperkitty.management.commands.hyperkitty_import import DbImporter
from hyperkitty.management.commands.hyperkitty_import import Command
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.tests.utils import TestCase


class DbImporterTestCase(TestCase):

    def setUp(self):
        options = {
            "no_download": True,
            "verbosity": 0,
            "since": None,
        }
        self.output = StringIO()
        self.importer = DbImporter(
            "example-list", options, self.output, self.output)

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



class CommandTestCase(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="hyperkitty-testing-")
        self.command = Command()

    def tearDown(self):
        rmtree(self.tmpdir)
        settings.HYPERKITTY_BATCH_MODE = False

    def test_impacted_threads(self):
        # existing message
        msg1 = Message()
        msg1["From"] = "dummy@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-01-01 12:00:00"
        msg1.set_payload("msg1")
        add_to_list("list@example.com", msg1)
        # new message in the imported mbox
        msg2 = Message()
        msg2["From"] = "dummy@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["Date"] = "2015-02-01 12:00:00"
        msg2.set_payload("msg1")
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        mbox.add(msg2)
        # do the import
        output = StringIO()
        with patch("hyperkitty.management.commands.hyperkitty_import.compute_thread_order_and_depth") as mock_compute:
            self.command.execute(os.path.join(self.tmpdir, "test.mbox"),
                verbosity=2, stdout=output, stderr=output,
                list_address="list@example.com",
                since=None, no_download=True, no_sync_mailman=True,
            )
        #print(mock_compute.call_args_list)
        self.assertEqual(mock_compute.call_count, 1)
        thread = mock_compute.call_args[0][0]
        self.assertEqual(thread.emails.count(), 1)
        self.assertEqual(thread.starting_email.message_id, "msg2")
        #print(output.getvalue())
