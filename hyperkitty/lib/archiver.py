# -*- coding: utf-8 -*-
"""
Class implementation of Mailman's IArchiver interface
"""

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
        self.store_url = None
        self._load_conf()

    def _load_conf(self):
        """
        Find the location of the Django settings module from Mailman's
        configuration file, and load it to get the store's URL.
        """
        # Read our specific configuration file
        archiver_config = external_configuration(
                config.archiver.hyperkitty.configuration)
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
        self.store_url = settings.KITTYSTORE_URL
        #if path_added:
        #    sys.path.remove(settings_path)

    def list_url(self, mlist):
        """Return the url to the top of the list's archive.

        :param mlist: The IMailingList object.
        :returns: The url string.
        """
        return urljoin(self.store_url,
                       reverse('archives', args=[mlist.fqdn_listname]))

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
        return urljoin(self.store_url, reverse('message_index',
                    kwargs={"mlist_fqdn": mlist.fqdn_listname,
                            "hashid": msg_hash}))

    def archive_message(self, mlist, msg):
        """Send the message to the archiver.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        if self.store is None:
            self.store = get_store(self.store_url)
        msg.message_id_hash = self.store.add_to_list(mlist, msg)
        self.store.commit()
        # TODO: Update karma
        return msg.message_id_hash
