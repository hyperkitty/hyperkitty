# Copyright (C) 2008-2012 by the Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: Toshio Kuratomi <toshio@fedoraproject.org>
# Authors: Pierre-Yves Chibon <pingou@fedoraproject.org>
# 

"""Integration with HyperKitty Archiver."""

from __future__ import absolute_import, unicode_literals

__metaclass__ = type
__all__ = [
    'HyperKitty',
    ]


from base64 import b32encode
import hashlib
import pymongo
import datetime
import email.Utils
from urllib import quote
from urlparse import urljoin

from zope.interface import implements

from mailman.config import config
from mailman.interfaces.archiver import IArchiver
from mailman.interfaces.mailinglist import IMailingList


def convert_date(date_string):
    """ Convert the string of the date to a datetime object. """
    date_string = date_string.strip()
    time_tuple = email.Utils.parsedate(date_string)

    # convert time_tuple to datetime
    EpochSeconds = time.mktime(time_tuple)
    dt = datetime.datetime.fromtimestamp(EpochSeconds)
    return dt


class HyperKitty(object):
    """An archiver for mailman implementing tagging, rating, and a forum-ish interface

    Mailman proposes a draft specification for interoperability between list
    servers and archivers: <http://wiki.list.org/display/DEV/Stable+URLs>.
    """

    implements(IArchiver)

    name = 'hyperkitty'

    @staticmethod
    def list_url(mlist):
        """See `IArchiver`."""
        if mlist.archive_private:
            return None
        base_url = config.archiver.hyperkitty.base_url
        if not base_url:
            # Pick a default
            base_url = mlist.domain.base_url
        # TODO: I see that some lists use mlist.posting_address -- is there a
        # difference with fqdn_listname?
        return urljoin(base_url, quote(mlist.fqdn_listname))

    @staticmethod
    def stable_url_id(msg):
        # Should this be a method or attribute on mailman.email.message instead?
        message_id = msg.get('message-id')
        # It is not the archiver's job to ensure the message has a Message-ID.
        # If this header is missing, there is no permalink.
        if message_id is None:
            return None
        # The angle brackets are not part of the Message-ID.  See RFC 2822.
        if message_id.startswith('<') and message_id.endswith('>'):
            message_id = message_id[1:-1]
        else:
            message_id = message_id.strip()
        digest = hashlib.sha1(message_id).digest()
        message_id_hash = b32encode(digest)
        del msg['x-message-id-hash']
        msg['X-Message-ID-Hash'] = message_id_hash
        return message_id_hash

    @classmethod
    def permalink(cls, mlist, message):
        """See `IArchiver`."""
        base_url = cls.list_url(mlist)
        message_id_hash = cls.stable_url_id(message)
        if not base_url or not message_id_hash:
            return None
        return urljoin(base_url, 'messages/%s/%s' % (mlist.fqdn_listname,
            message_id_hash))

    @classmethod
    def archive_message(cls, mlist, message):
        """See `IArchiver`."""
        # Side effect: stable_id_hash is saved in msg['X-Message-ID-Hash'] -- used by
        # HyperKitty archiver
        cls.stable_url_id(message)
        connection = pymongo.Connection('localhost', 27017)
        #TODO: We have to adjust the client for this, use the full list
        # name (with domain name) as table instead of just the list name
        db = connection[mlist.fqdn_listname]
        db.mails.create_index('MessageID')
        db.mails.ensure_index('MessageID')
        db.mails.create_index('InReplyTo')
        db.mails.ensure_index('InReplyTo')
        db.mails.create_index('ThreadID')
        db.mails.ensure_index('ThreadID')
        infos = {}
        for it in message.keys():
            # Avoids problem when called in a template
            it2 = it.replace('-', '')
            infos[it2] = message[it]
        keys = infos.keys()
        ## There seem to be a problem to parse some messages
        if not keys:
            print '  Failed: %s keys: "%s"' % (mbfile, keys)
            # Will we still need this ?
            raise Exception ('Message could not be parsed correctly')
        # Will we still need this ?
        # TODO: Should we replace Message-ID by X-Message-ID-Hash ?
        if db.mails.find({'MessageID': infos['MessageID']}).count() == 0:
            # Do we need this conversion or has the module already done that?
            infos['Date'] = convert_date(infos['Date'])
            infos['Content'] = message.get_payload()
            if not 'References' in infos:
                infos['ThreadID'] = msg['MessageID']
            else:
                ref = infos['References'].split('\n')[0].strip()
                res = db.mails.find_one({'MessageID': ref})
                if res and 'ThreadID' in res:
                    infos['ThreadID'] = res['ThreadID']
                else:
                    infos['ThreadID'] = msg['MessageID']
            infos['Category'] = 'Question'
            if 'agenda' in infos['Subject'].lower():
                infos['Category'] = 'Agenda'
            if 'reminder' in infos['Subject'].lower():
                infos['Category'] = 'Agenda'
            db.mails.insert(infos)
        else:
            raise Exception (
                'MessageID %s already exists in the database' % \
                infos['MessageID'])
        ## TODO: Should we save the message on the hard-disk as well?
        return cls.permalink(mlist, message)
