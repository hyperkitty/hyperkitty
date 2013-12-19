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

"""
Class implementation of Mailman's IArchiver interface
"""
from __future__ import absolute_import, unicode_literals

import os
import sys
from urlparse import urljoin

from zope.interface import implements
from mailman.interfaces.archiver import IArchiver
from mailman.config import config
from mailman.config.config import external_configuration
from django.core.urlresolvers import reverse
from kittystore import get_store
from kittystore.utils import get_message_id_hash


class Archiver(object):

    implements(IArchiver)

    name = "hyperkitty"

    def __init__(self):
        self.store = None
        self.base_url = None
        self.settings = None # will be filled by _load_conf()
        self._load_conf()

    def _load_conf(self):
        """
        Find the location of the Django settings module from Mailman's
        configuration file, and load it to get the store's URL.
        """
        # Read our specific configuration file
        archiver_config = external_configuration(
                config.archiver.hyperkitty.configuration)
        self.base_url = archiver_config.get("general", "base_url")
        settings_path = archiver_config.get("general", "django_settings")
        if settings_path.endswith("/settings.py"):
            # we want the directory
            settings_path = os.path.dirname(settings_path)
        #path_added = False
        if settings_path not in sys.path:
            #path_added = True
            sys.path.append(settings_path)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
        try:
            from django.conf import settings
        except ImportError:
            raise ImportError("Could not import Django's settings from %s"
                              % settings_path)
        self.settings = settings
        #if path_added:
        #    sys.path.remove(settings_path)

    def list_url(self, mlist):
        """Return the url to the top of the list's archive.

        :param mlist: The IMailingList object.
        :returns: The url string.
        """
        return urljoin(self.base_url,
                       reverse('list_overview', args=[mlist.fqdn_listname]))

    def permalink(self, mlist, msg):
        """Return the url to the message in the archive.

        This url points directly to the message in the archive.  This method
        only calculates the url, it does not actually archive the message.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        msg_id = msg['Message-Id'].strip().strip("<>")
        msg_hash = get_message_id_hash(msg_id)
        return urljoin(self.base_url, reverse('message_index',
                    kwargs={"mlist_fqdn": mlist.fqdn_listname,
                            "message_id_hash": msg_hash}))

    def archive_message(self, mlist, msg):
        """Send the message to the archiver.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        if self.store is None:
            self.store = get_store(self.settings)
        msg.message_id_hash = self.store.add_to_list(mlist, msg)
        self.store.commit()
        # TODO: Update karma
        return msg.message_id_hash
