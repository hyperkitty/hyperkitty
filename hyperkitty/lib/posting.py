#-*- coding: utf-8 -*-
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


from django.core.exceptions import SuspiciousOperation
from django.core.mail import EmailMessage
from mailmanclient import MailmanConnectionError

from hyperkitty.lib import mailman


class PostingFailed(Exception):
    pass


def post_to_list(request, mlist, subject, message, headers={},
                 attachments=None):
    if not mlist:
        # Make sure the list exists to avoid posting to any email addess
        raise SuspiciousOperation("I don't know this mailing-list")
    # Check that the user is subscribed
    try:
        mailman.subscribe(mlist.name, request.user)
    except MailmanConnectionError:
        raise PostingFailed("Can't connect to Mailman's REST server, "
                            "your message has not been sent.")
    # send the message
    headers["User-Agent"] = "HyperKitty on %s" % request.build_absolute_uri("/")
    if not request.user.first_name and not request.user.last_name:
        from_email = request.user.email
    else:
        from_email = '"%s %s" <%s>' % (request.user.first_name,
                                       request.user.last_name,
                                       request.user.email)
    msg = EmailMessage(
               subject=subject,
               body=message,
               from_email=from_email,
               to=[mlist.name],
               headers=headers,
               )
    # Attachments
    if attachments:
        if not isinstance(attachments, list):
            attachments = [attachments]
        for attach in attachments:
            msg.attach(attach.name, attach.read())
    msg.send()
