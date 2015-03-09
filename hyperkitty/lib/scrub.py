# Copyright (C) 2011-2012 by the Free Software Foundation, Inc.
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

"""Cleanse a message for archiving."""

from __future__ import absolute_import, unicode_literals

import os
import re
import binascii
from types import IntType
from mimetypes import guess_all_extensions
from email.header import decode_header, make_header
from email.errors import HeaderParseError

# Path characters for common platforms
pre = re.compile(r'[/\\:]')
# All other characters to strip out of Content-Disposition: filenames
# (essentially anything that isn't an alphanum, dot, dash, or underscore).
sre = re.compile(r'[^-\w.]')
# Regexp to strip out leading dots
dre = re.compile(r'^\.*')

BR = '<br>\n'

NEXT_PART = re.compile(r'--------------[ ]next[ ]part[ ]--------------\n')


def guess_extension(ctype, ext):
    # mimetypes maps multiple extensions to the same type, e.g. .doc, .dot,
    # and .wiz are all mapped to application/msword.  This sucks for finding
    # the best reverse mapping.  If the extension is one of the giving
    # mappings, we'll trust that, otherwise we'll just guess. :/
    all_exts = guess_all_extensions(ctype, strict=False)
    if ext in all_exts:
        return ext
    return all_exts and all_exts[0]


def get_charset(message, default="ascii", guess=False):
    """
    Get the message charset.
    From: http://ginstrom.com/scribbles/2007/11/19/parsing-multilingual-email-with-python/
    """
    if message.get_content_charset():
        return message.get_content_charset().decode("ascii")
    if message.get_charset():
        return message.get_charset().decode("ascii")
    charset = default
    if not guess:
        return charset
    # Try to guess the encoding (best effort mode)
    text = message.get_payload(decode=True)
    for encoding in ["ascii", "utf-8", "iso-8859-15"]:
        try:
            text.decode(encoding)
        except UnicodeDecodeError:
            continue
        else:
            charset = encoding
            break
    return charset


def oneline(s):
    """Inspired by mailman.utilities.string.oneline"""
    try:
        h = make_header(decode_header(s))
        ustr = h.__unicode__()
        return ''.join(ustr.splitlines())
    except (LookupError, UnicodeError, ValueError, HeaderParseError):
        # possibly charset problem. return with undecoded string in one line.
        return ''.join(s.splitlines())


class Scrubber(object):
    """
    Scrubs a single message, extracts attachments, and return the text and the
    attachments.
    See also: http://ginstrom.com/scribbles/2007/11/19/parsing-multilingual-email-with-python/
    """

    def __init__(self, mlist, msg):
        self.mlist = mlist
        self.msg = msg


    def scrub(self):
        attachments = []
        sanitize = 1 # TODO: implement other options
        #outer = True
        # Now walk over all subparts of this message and scrub out various types
        for part_num, part in enumerate(self.msg.walk()):
            ctype = part.get_content_type()
            if not isinstance(ctype, unicode):
                ctype = ctype.decode("ascii")
            # If the part is text/plain, we leave it alone
            if ctype == 'text/plain':
                disposition = part.get('content-disposition')
                if disposition and disposition.decode("ascii", "replace"
                        ).strip().startswith("attachment"):
                    # part is attached
                    attachments.append(self.parse_attachment(part, part_num))
                    part.set_payload('')
            elif ctype == 'text/html' and isinstance(sanitize, IntType):
#            if sanitize == 0:
#                if outer:
#                    raise DiscardMessage
#                replace_payload_by_text(part,
#                                 _('HTML attachment scrubbed and removed'),
#                                 # Adding charset arg and removing content-type
#                                 # sets content-type to text/plain
#                                 lcset)
#            elif sanitize == 2:
#                # By leaving it alone, Pipermail will automatically escape it
#                pass
#            elif sanitize == 3:
#                # Pull it out as an attachment but leave it unescaped.  This
#                # is dangerous, but perhaps useful for heavily moderated
#                # lists.
#                attachments.append(self.parse_attachment(part, part_num, filter_html=False))
#                replace_payload_by_text(part, _("""\
#An HTML attachment was scrubbed...
#URL: %(url)s
#"""), lcset)
#            else:
                if sanitize == 1:
                    # Don't HTML-escape it, this is the frontend's job
                    ## HTML-escape it and store it as an attachment, but make it
                    ## look a /little/ bit prettier. :(
                    #payload = websafe(part.get_payload(decode=True))
                    ## For whitespace in the margin, change spaces into
                    ## non-breaking spaces, and tabs into 8 of those.  Then use a
                    ## mono-space font.  Still looks hideous to me, but then I'd
                    ## just as soon discard them.
                    #def doreplace(s):
                    #    return s.expandtabs(8).replace(' ', '&nbsp;')
                    #lines = [doreplace(s) for s in payload.split('\n')]
                    #payload = '<tt>\n' + BR.join(lines) + '\n</tt>\n'
                    #part.set_payload(payload)
                    ## We're replacing the payload with the decoded payload so this
                    ## will just get in the way.
                    #del part['content-transfer-encoding']
                    attachments.append(self.parse_attachment(part, part_num, filter_html=False))
                    part.set_payload('')
            elif ctype == 'message/rfc822':
                # This part contains a submessage, so it too needs scrubbing
                attachments.append(self.parse_attachment(part, part_num))
                part.set_payload('')
            # If the message isn't a multipart, then we'll strip it out as an
            # attachment that would have to be separately downloaded.
            elif part.get_payload() and not part.is_multipart():
                payload = part.get_payload(decode=True)
                ctype = part.get_content_type()
                if not isinstance(ctype, unicode):
                    ctype.decode("ascii")
                # XXX Under email 2.5, it is possible that payload will be None.
                # This can happen when you have a Content-Type: multipart/* with
                # only one part and that part has two blank lines between the
                # first boundary and the end boundary.  In email 3.0 you end up
                # with a string in the payload.  I think in this case it's safe to
                # ignore the part.
                if payload is None:
                    continue
                attachments.append(self.parse_attachment(part, part_num))
            #outer = False
        # We still have to sanitize multipart messages to flat text because
        # Pipermail can't handle messages with list payloads.  This is a kludge;
        # def (n) clever hack ;).
        if self.msg.is_multipart():
            # We now want to concatenate all the parts which have been scrubbed to
            # text/plain, into a single text/plain payload.  We need to make sure
            # all the characters in the concatenated string are in the same
            # encoding, so we'll use the 'replace' key in the coercion call.
            # BAW: Martin's original patch suggested we might want to try
            # generalizing to utf-8, and that's probably a good idea (eventually).
            text = []
            for part in self.msg.walk():
                # TK: bug-id 1099138 and multipart
                # MAS test payload - if part may fail if there are no headers.
                if not part.get_payload() or part.is_multipart():
                    continue
                # All parts should be scrubbed to text/plain by now, except
                # if sanitize == 2, there could be text/html parts so keep them
                # but skip any other parts.
                partctype = part.get_content_type()
                if partctype != 'text/plain' and (partctype != 'text/html' or
                                                  sanitize != 2):
                    #text.append(_('Skipped content of type %(partctype)s\n'))
                    continue
                try:
                    t = part.get_payload(decode=True) or ''
                # MAS: TypeError exception can occur if payload is None. This
                # was observed with a message that contained an attached
                # message/delivery-status part. Because of the special parsing
                # of this type, this resulted in a text/plain sub-part with a
                # null body. See bug 1430236.
                except (binascii.Error, TypeError):
                    t = part.get_payload() or ''
                partcharset = get_charset(part, guess=True)
                try:
                    t = t.decode(partcharset, 'replace')
                except (UnicodeError, LookupError, ValueError,
                        AssertionError):
                    # We can get here if partcharset is bogus in some way.
                    # Replace funny characters.  We use errors='replace'
                    t = t.decode('ascii', 'replace')
                # Separation is useful
                if isinstance(t, basestring):
                    if not t.endswith('\n'):
                        t += '\n'
                    text.append(t)

            text = u"\n".join(text)
        else:
            text = self.msg.get_payload(decode=True)
            charset = get_charset(self.msg, guess=True)
            try:
                text = text.decode(charset, "replace")
            except (UnicodeError, LookupError, ValueError, AssertionError):
                text = text.decode('ascii', 'replace')

            next_part_match = NEXT_PART.search(text)
            if next_part_match:
                text = text[0:next_part_match.start(0)]

        return (text, attachments)


    def parse_attachment(self, part, counter, filter_html=True):
        # pylint: disable=unused-argument
        # Store name, content-type and size
        # Figure out the attachment type and get the decoded data
        decodedpayload = part.get_payload(decode=True)
        # BAW: mimetypes ought to handle non-standard, but commonly found types,
        # e.g. image/jpg (should be image/jpeg).  For now we just store such
        # things as application/octet-streams since that seems the safest.
        ctype = part.get_content_type()
        if not isinstance(ctype, unicode):
            ctype = ctype.decode("ascii")
        charset = get_charset(part, default=None, guess=False)
        # i18n file name is encoded
        try:
            filename = oneline(part.get_filename(''))
        except (TypeError, UnicodeDecodeError):
            # Workaround for https://bugs.launchpad.net/mailman/+bug/1060951
            # (accented filenames)
            filename = u"attachment.bin"
        filename, fnext = os.path.splitext(filename)
        # For safety, we should confirm this is valid ext for content-type
        # but we can use fnext if we introduce fnext filtering
        # TODO: re-implement this
        #if mm_cfg.SCRUBBER_USE_ATTACHMENT_FILENAME_EXTENSION:
        #    # HTML message doesn't have filename :-(
        #    ext = fnext or guess_extension(ctype, fnext)
        #else:
        #    ext = guess_extension(ctype, fnext)
        ext = fnext or guess_extension(ctype, fnext)
        if not ext:
            # We don't know what it is, so assume it's just a shapeless
            # application/octet-stream, unless the Content-Type: is
            # message/rfc822, in which case we know we'll coerce the type to
            # text/plain below.
            if ctype == 'message/rfc822':
                ext = '.txt'
            else:
                ext = '.bin'
        # Allow only alphanumerics, dash, underscore, and dot
        ext = sre.sub('', ext)
        # Now base the filename on what's in the attachment, uniquifying it if
        # necessary.
        if not filename:
            filebase = u'attachment'
        else:
            # Sanitize the filename given in the message headers
            parts = pre.split(filename)
            filename = parts[-1]
            # Strip off leading dots
            filename = dre.sub('', filename)
            # Allow only alphanumerics, dash, underscore, and dot
            # i18n filenames are not supported yet,
            # see https://bugs.launchpad.net/bugs/1060951
            filename = sre.sub('', filename)
            # If the filename's extension doesn't match the type we guessed,
            # which one should we go with?  For now, let's go with the one we
            # guessed so attachments can't lie about their type.  Also, if the
            # filename /has/ no extension, then tack on the one we guessed.
            # The extension was removed from the name above.
            filebase = filename
        # TODO: bring back the HTML sanitizer feature
        if ctype == 'message/rfc822':
            submsg = part.get_payload()
            # Don't HTML-escape it, this is the frontend's job
            ## BAW: I'm sure we can eventually do better than this. :(
            #decodedpayload = websafe(str(submsg))
            decodedpayload = str(submsg)
        return (counter, filebase+ext, ctype, charset, decodedpayload)
