# -*- coding: utf-8 -*-
"""
Class implementation of Mailman's IArchiver interface
"""


from mailman.interfaces.archiver import IArchiver
from django.core.urlresolvers import reverse
from hyperkitty.lib import ThreadSafeStorePool


class Archiver(object):

    implements(IArchiver)

    name = "hyperkitty"

    def __init__(self):
        self.store = None

    def list_url(self, mlist):
        """Return the url to the top of the list's archive.

        :param mlist: The IMailingList object.
        :returns: The url string.
        """
        return reverse('archives', mlist_fqdn=mlist)

    def permalink(self, mlist, msg):
        """Return the url to the message in the archive.

        This url points directly to the message in the archive.  This method
        only calculates the url, it does not actually archive the message.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        return reverse('message_index', mlist_fqdn=mlist, hashid=msg.message_id_hash)

    def archive_message(self, mlist, msg):
        """Send the message to the archiver.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        if self.store is None:
            self.store = ThreadSafeStorePool().get()
        msg.message_id_hash = self.store.add_to_list(mlist.list_name, msg)
        # Update karma
