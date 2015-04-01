# -*- coding: utf-8 -*-
# pylint: skip-file

from __future__ import absolute_import, print_function, unicode_literals

import unittest
import datetime
import uuid
from urllib2 import HTTPError

from mock import Mock
from mailman.email.message import Message
from mailman.interfaces.archiver import ArchivePolicy

#import kittystore.utils
#from kittystore import get_store
#from kittystore.caching import mailman_user
#from kittystore.test import FakeList, SettingsModule


class ListCacheTestCase(unittest.TestCase):

    def setUp(self):
        self.store = get_store(SettingsModule(), auto_create=True)
        kittystore.utils.MM_CLIENT = Mock()

    def tearDown(self):
        self.store.close()
        kittystore.utils.MM_CLIENT = None

    def test_properties_on_new_message(self):
        ml = FakeList("example-list")
        ml.display_name = u"name 1"
        ml.subject_prefix = u"[prefix 1]"
        ml.description = u"desc 1"
        kittystore.utils.MM_CLIENT.get_list.side_effect = lambda n: ml
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        self.store.add_to_list("example-list", msg)
        ml_db = self.store.get_lists()[0]
        self.assertEqual(ml_db.display_name, "name 1")
        self.assertEqual(ml_db.subject_prefix, "[prefix 1]")
        ml.display_name = u"name 2"
        ml.subject_prefix = u"[prefix 2]"
        ml.description = u"desc 2"
        ml.archive_policy = "private"
        msg.replace_header("Message-ID", "<dummy2>")
        self.store.add_to_list("example-list", msg)
        ml_db = self.store.get_lists()[0]
        #ml_db = self.store.db.find(List).one()
        self.assertEqual(ml_db.display_name, "name 2")
        self.assertEqual(ml_db.subject_prefix, "[prefix 2]")
        self.assertEqual(ml_db.description, "desc 2")
        self.assertEqual(ml_db.archive_policy, ArchivePolicy.private)

    def test_on_old_message(self):
        kittystore.utils.MM_CLIENT = None
        olddate = datetime.datetime.utcnow() - datetime.timedelta(days=40)
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["Date"] = olddate.isoformat()
        msg.set_payload("Dummy message")
        self.store.add_to_list("example-list", msg)
        ml_db = self.store.get_lists()[0]
        self.assertEqual(ml_db.recent_participants_count, 0)
        self.assertEqual(ml_db.recent_threads_count, 0)



class FakeMMUser(object):
    user_id = None

class UserIdCacheTestCase(unittest.TestCase):

    def setUp(self):
        self.store = get_store(SettingsModule(), auto_create=True)#, debug=True)
        self.mm_client = Mock()
        mailman_user._MAILMAN_CLIENT = self.mm_client
        self.mm_client.get_user.side_effect = HTTPError(
                None, 404, "dummy", {}, None)

    def tearDown(self):
        self.store.close()
        mailman_user._MAILMAN_CLIENT = None

    def test_on_new_message_userid(self):
        # Check that the user_id is set on a new message
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        # setup Mailman's reply
        new_user_id = FakeMMUser()
        uid = uuid.uuid1()
        new_user_id.user_id = uid.int
        self.mm_client.get_user.side_effect = lambda addr: new_user_id
        # check the User does not exist yet
        self.assertEqual(0,
                self.store.get_message_count_by_user_id(uid))
        # do the test and check
        self.store.add_to_list("example-list", msg)
        dbmsg = self.store.get_message_by_id_from_list(
                "example-list", "dummy")
        self.assertEqual(dbmsg.sender.user_id, uid)
        self.assertTrue(dbmsg.sender.user is not None,
                "A 'User' instance was not created")
        self.assertEqual(dbmsg.sender.user.id, uid)
        self.assertEqual(1,
                self.store.get_message_count_by_user_id(uid))
        self.assertEqual(self.store.get_users_count(), 1)

    def test_on_new_message_no_reply_from_mailman(self):
        # Check that the user_id is set on a new message
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        self.store.add_to_list("example-list", msg)
        dbmsg = self.store.get_message_by_id_from_list(
                "example-list", "dummy")
        self.assertEqual(dbmsg.sender.user_id, None)

    def test_sync_mailman_user(self):
        # Check that the user_id is set when sync_mailman_user is run
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        self.store.add_to_list("example-list", msg)
        dbmsg = self.store.get_message_by_id_from_list(
                "example-list", "dummy")
        self.assertEqual(dbmsg.sender.user_id, None)
        # setup Mailman's reply
        uid = uuid.uuid1()
        new_user_id = FakeMMUser()
        new_user_id.user_id = uid.int
        self.mm_client.get_user.side_effect = lambda addr: new_user_id
        # do the test and check
        mailman_user.sync_mailman_user(self.store)
        #dbmsg = self.store.get_message_by_id_from_list(
        #        "example-list", "dummy")
        self.assertEqual(dbmsg.sender.user_id, uid)
        self.assertTrue(dbmsg.sender.user is not None,
                "A 'User' instance was not created")
        self.assertEqual(dbmsg.sender.user.id, uid)
        self.assertEqual(1,
                self.store.get_message_count_by_user_id(uid))

    def test_on_new_message_bad_reply_from_mailman(self):
        # Check that errors from mailmanclient are handled gracefully
        self.mm_client.get_user.side_effect = ValueError
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        try:
            self.store.add_to_list("example-list", msg)
        except ValueError, e:
            self.fail("Errors from mailmanclient should be handled gracefully")
        dbmsg = self.store.get_message_by_id_from_list(
                "example-list", "dummy")
        self.assertEqual(dbmsg.sender.user_id, None)


class TestNotifyStore(unittest.TestCase):
    def setUp(self):
        self.store = get_sa_store(SettingsModule(), auto_create=True)
        self.store.db.cache.get_or_create = Mock()
        self.store.db.cache.get_or_create.side_effect = lambda *a, **kw: a[1]()
        self.store.db.cache.set = Mock()
        # cache.delete() will be called if the cache is invalidated
        self.store.db.cache.delete = Mock()

    def tearDown(self):
        self.store.close()

    def test_on_new_message_invalidate(self):
        # Check that the cache is invalidated on new message
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        today = datetime.datetime.utcnow().date() # don't use datetime.date.today(), we need UTC
        self.store.add_to_list("example-list", msg)
        # calls to cache.delete() -- invalidation
        delete_args = [ call[0][0] for call in
                        self.store.db.cache.delete.call_args_list ]
        #from pprint import pprint; pprint(delete_args)
        self.assertEqual(set(delete_args), set([
            u'list:example-list:recent_participants_count',
            u'list:example-list:recent_threads_count',
            u'list:example-list:participants_count:%d:%d' % (today.year, today.month),
            u'list:example-list:thread:QKODQBCADMDSP5YPOPKECXQWEQAMXZL3:emails_count',
            u'list:example-list:thread:QKODQBCADMDSP5YPOPKECXQWEQAMXZL3:participants_count'
            ]))
        # calls to cache.get_or_create() -- repopulation
        goc_args = [ call[0][0] for call in
                     self.store.db.cache.get_or_create.call_args_list ]
        #from pprint import pprint; pprint(goc_args)
        self.assertEqual(set(goc_args), set([
            u'list:example-list:recent_participants_count',
            u'list:example-list:recent_threads_count',
            u'list:example-list:participants_count:%d:%d' % (today.year, today.month),
            u'list:example-list:threads_count:%d:%d' % (today.year, today.month),
            u'list:example-list:thread:QKODQBCADMDSP5YPOPKECXQWEQAMXZL3:emails_count',
            u'list:example-list:thread:QKODQBCADMDSP5YPOPKECXQWEQAMXZL3:participants_count',
            u'list:example-list:thread:QKODQBCADMDSP5YPOPKECXQWEQAMXZL3:starting_email_id',
            ]))
        #self.assertEqual(l.recent_participants_count, 1)
        #self.assertEqual(l.recent_threads_count, 1)
        #msg.replace_header("Message-ID", "<dummy2>")
        #self.store.add_to_list("example-list", msg)
        #self.assertEqual(l.recent_participants_count, 1)
        #self.assertEqual(l.recent_threads_count, 2)

    def test_on_new_thread_invalidate(self):
        # Check that the cache is invalidated on new message
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg.set_payload("Dummy message")
        self.store.add_to_list("example-list", msg)
        msg.replace_header("Message-ID", "<dummy2>")
        msg["In-Reply-To"] = "<dummy>"
        self.store.add_to_list("example-list", msg)
        call_args = [ call[0][0] for call in self.store.db.cache.set.call_args_list ]
        # we have duplicates because both the Storm and the SQLAlchemy model
        # subscribe to the event, so we must deduplicate
        call_args = set(call_args)
        #from pprint import pprint; pprint(call_args)
        #print(repr(call_args))
        self.assertEqual(call_args, set([
            u'list:example-list:thread:QKODQBCADMDSP5YPOPKECXQWEQAMXZL3:subject'
            ]))
