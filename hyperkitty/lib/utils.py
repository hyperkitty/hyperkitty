# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>


from __future__ import absolute_import, print_function, unicode_literals

import re
import email.utils
from base64 import b32encode
from hashlib import sha1
from email.header import decode_header
from datetime import timedelta

import dateutil.parser, dateutil.tz
from django.utils import timezone



def get_message_id_hash(msg_id):
    """
    Returns the X-Message-ID-Hash header for the provided Message-ID header.

    See <http://wiki.list.org/display/DEV/Stable+URLs#StableURLs-Headers> for
    details. Example:
    """
    msg_id = email.utils.unquote(msg_id)
    return unicode(b32encode(sha1(msg_id).digest()))


def get_message_id(message):
    msg_id = email.utils.unquote(message['Message-Id']).decode("ascii")
    # Protect against extremely long Message-Ids (there is no limit in the
    # email spec), it's set to VARCHAR(255) in the database
    if len(msg_id) >= 255:
        msg_id = msg_id[:254]
    return msg_id


IN_BRACKETS_RE = re.compile("[^<]*<([^>]+)>.*")
def get_ref(message):
    """
    Returns the message-id of the reference email for a given message.
    """
    if (not message.has_key("References")
            and not message.has_key("In-Reply-To")):
        return None
    ref_id = message.get("In-Reply-To")
    if ref_id is not None:
        ref_id = ref_id.decode('ascii', 'ignore')
    if ref_id is None or not ref_id.strip():
        ref_id = message.get("References")
        if ref_id is not None and ref_id.strip():
            # There can be multiple references, use the last one
            ref_id = ref_id.split()[-1].strip()
    if ref_id is not None:
        if "<" in ref_id or ">" in ref_id:
            ref_id = IN_BRACKETS_RE.match(ref_id)
            if ref_id:
                ref_id = ref_id.group(1)
    if ref_id is not None:
        ref_id = ref_id[:254].decode("ascii")
    return ref_id


def parseaddr(address):
    """
    Wrapper around email.utils.parseaddr to also handle Mailman's generated
    mbox archives.
    """
    if address is None:
        return "", ""
    address = address.replace(" at ", "@")
    from_name, from_email = email.utils.parseaddr(address)
    if not from_name:
        from_name = from_email
    return from_name, from_email


def parsedate(datestring):
    if datestring is None:
        return None
    try:
        parsed = dateutil.parser.parse(datestring)
    except ValueError:
        return None
    if parsed.utcoffset() is not None and \
            abs(parsed.utcoffset()) > timedelta(hours=13):
        parsed = parsed.astimezone(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc) # make it aware
    return parsed


def header_to_unicode(header):
    """
    See also: http://ginstrom.com/scribbles/2007/11/19/parsing-multilingual-email-with-python/
    """
    h_decoded = []
    for text, charset in decode_header(header):
        if charset is None:
            try:
                h_decoded.append(unicode(text))
            except UnicodeDecodeError:
                h_decoded.append(unicode(text, "ascii", "replace"))
        else:
            try:
                h_decoded.append(text.decode(charset))
            except (LookupError, UnicodeDecodeError):
                # Unknown encoding or decoding failed
                h_decoded.append(text.decode("ascii", "replace"))
    return " ".join(h_decoded)


def stripped_subject(mlist, subject):
    if mlist is None:
        return subject
    if not subject:
        return u"(no subject)"
    if not mlist.subject_prefix:
        return subject
    if subject.lower().startswith(mlist.subject_prefix.lower()):
        subject = subject[len(mlist.subject_prefix) : ]
    return subject



import time
from collections import defaultdict
LASTTIME = None
TIMES = defaultdict(list)
def timeit(name):
    global LASTTIME#, TIMES # pylint: disable=global-statement
    now = time.time()
    if LASTTIME is not None:
        spent = now - LASTTIME
        TIMES[name].append(spent)
        print("{}: {}".format(name, spent))
    LASTTIME = now
