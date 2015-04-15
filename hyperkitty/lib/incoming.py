#-*- coding: utf-8 -*-
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

from __future__ import absolute_import, unicode_literals, division


import re

from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from mailmanclient import MailmanConnectionError

from hyperkitty.lib.signals import new_email, new_thread
from hyperkitty.lib.utils import (get_ref, parseaddr, parsedate,
    header_to_unicode, get_message_id)
from hyperkitty.lib.scrub import Scrubber
from hyperkitty.lib.analysis import compute_thread_order_and_depth
from hyperkitty.models import (MailingList, Sender, Email, Attachment, Thread,
    ArchivePolicy)

import logging
logger = logging.getLogger(__name__)


class DuplicateMessage(Exception):
    """
    The database already contains an email with the same Message-ID header.
    """


def add_to_list(list_name, message):
    #timeit("1 start")
    mlist = MailingList.objects.get_or_create(name=list_name)[0]
    if not getattr(settings, "HYPERKITTY_BATCH_MODE", False):
        mlist.update_from_mailman()
    mlist.save()
    if mlist.archive_policy == ArchivePolicy.never.value:
        logger.info("Archiving disabled by list policy for %s", list_name)
        return
    if not message.has_key("Message-Id"):
        raise ValueError("No 'Message-Id' header in email", message)
    #timeit("2 after ml, before checking email & sender")
    msg_id = get_message_id(message)
    if Email.objects.filter(mailinglist=mlist, message_id=msg_id).exists():
        raise DuplicateMessage(msg_id)
    email = Email(mailinglist=mlist, message_id=msg_id)
    email.in_reply_to = get_ref(message) # Find thread id

    # Sender
    try:
        from_name, from_email = parseaddr(message['From'])
        from_name = header_to_unicode(from_name).strip()
        sender_address = from_email.decode("ascii").strip()
    except (UnicodeDecodeError, UnicodeEncodeError):
        raise ValueError("Non-ascii sender address", message)
    if not sender_address:
        if from_name:
            sender_address = re.sub("[^a-z0-9]", "", from_name.lower())
            if not sender_address:
                sender_address = "unknown"
            sender_address = "{}@example.com".format(sender_address)
        else:
            sender_address = "unknown@example.com"
    sender = Sender.objects.get_or_create(address=sender_address)[0]
    sender.name = from_name # update the name if needed
    sender.save()
    email.sender = sender
    if not getattr(settings, "HYPERKITTY_BATCH_MODE", False):
        set_sender_mailman_id(sender)
    #timeit("3 after sender, before email content")

    # Headers
    email.subject = header_to_unicode(message.get('Subject'))
    if email.subject is not None:
        # limit subject size to 512, it's a varchar field
        email.subject = email.subject[:512]
    msg_date = parsedate(message.get("Date"))
    if msg_date is None:
        # Absent or unparseable date
        msg_date = timezone.now()
    utcoffset = msg_date.utcoffset()
    if msg_date.tzinfo is not None:
        msg_date = msg_date.astimezone(timezone.utc) # store in UTC
    email.date = msg_date
    if utcoffset is None:
        email.timezone = 0
    else:
        # in minutes
        email.timezone = int(
            ((utcoffset.days * 24 * 60 * 60) + utcoffset.seconds) / 60 )

    # Content
    scrubber = Scrubber(list_name, message)
    # warning: scrubbing modifies the msg in-place
    email.content, attachments = scrubber.scrub()
    #timeit("4 after email content, before signals")

    # TODO: detect category?

    # Set or create the Thread
    if email.in_reply_to is not None:
        try:
            ref_msg = Email.objects.get(
                mailinglist=email.mailinglist,
                message_id=email.in_reply_to)
        except Email.DoesNotExist:
            # the parent may not be archived (on partial imports), create a new
            # thread for now.
            pass
        else:
            # re-use parent's thread-id
            email.parent = ref_msg
            email.thread_id = ref_msg.thread_id
            ref_msg.thread.date_active = email.date
            ref_msg.thread.save()

    thread_created = False
    if email.thread_id is None:
        # Create the thread if not found
        thread = Thread.objects.create(
            mailinglist=email.mailinglist,
            thread_id=email.message_id_hash,
            date_active=email.date)
        thread_created = True
        email.thread = thread

    email.save() # must save before setting the thread.starting_email

    if thread_created:
        thread.starting_email = email
        thread.save()
        new_thread.send("Mailman", thread=thread)
        #signal_results = new_thread.send_robust("Mailman", thread=thread)
        #for receiver, result in signal_results:
        #    if isinstance(result, Exception):
        #        logger.warning(
        #            "Signal 'new_thread' to {} raised an exception: {}".format(
        #            receiver.func_name, result))

    # Signals
    new_email.send("Mailman", email=email)
    #signal_results = new_email.send_robust("Mailman", email=email)
    #for receiver, result in signal_results:
    #    if isinstance(result, Exception):
    #        logger.warning(
    #            "Signal 'new_email' to {} raised an exception: {}".format(
    #            receiver.func_name, result))
    #        #logger.exception(result)
    #        #from traceback import print_exc; print_exc(result)
    #timeit("5 after signals, before save")
    #timeit("6 after save")
    # compute thread props here because email must have been saved before
    # (there will be DB queries in this function)
    if not getattr(settings, "HYPERKITTY_BATCH_MODE", False):
        compute_thread_order_and_depth(email.thread)

    # Attachments (email must have been saved before)
    for attachment in attachments:
        counter, name, content_type, encoding, content = attachment
        if Attachment.objects.filter(email=email, counter=counter).exists():
            continue
        Attachment.objects.create(
            email=email, counter=counter, name=name, content_type=content_type,
            encoding=encoding, content=content)

    return email.message_id_hash


def set_sender_mailman_id(sender):
    if sender.mailman_id is not None:
        return
    try:
        sender.set_mailman_id()
    except MailmanConnectionError:
        return


def set_or_create_thread(email):
    if email.in_reply_to is not None:
        try:
            ref_msg = Email.objects.get(
                mailinglist=email.mailinglist,
                message_id=email.in_reply_to)
        except Email.DoesNotExist:
            pass # the parent may not be archived (on partial imports)
        else:
            # re-use parent's thread-id
            email.parent = ref_msg
            email.thread_id = ref_msg.thread_id
            ref_msg.thread.date_active = email.date
            ref_msg.thread.save()
            return
    # Create the thread if not found
    thread = Thread.objects.create(
        mailinglist=email.mailinglist,
        thread_id=email.message_id_hash,
        date_active=email.date)
    #signal_results = new_thread.send_robust("Mailman", thread=thread)
    #for receiver, result in signal_results:
    #    if isinstance(result, Exception):
    #        logger.warning(
    #            "Signal 'new_thread' to {} raised an exception: {}".format(
    #            receiver.func_name, result))
    email.thread = thread


@receiver(new_email)
def check_orphans(sender, **kwargs):
    """
    When a reply is received before its original message, it must be
    re-attached when the original message arrives.
    """
    # pylint: disable=unused-argument
    if getattr(settings, "HYPERKITTY_BATCH_MODE", False):
        return # For batch imports, let the cron job do the work
    email = kwargs["email"]
    orphans = Email.objects.filter(
            mailinglist=email.mailinglist,
            in_reply_to=email.message_id,
            parent_id__isnull=True,
        ).exclude(
            # guard against emails with the in-reply-to header pointing to
            # themselves
            id=email.id
        )
    for orphan in orphans:
        if orphan.id == email.id:
            continue
        orphan.set_parent(email)
