#!/usr/bin/python -tt

# Import a maildir into notmuch.
# Eventually we may also convert from mbox
# That will give us a full conversion from mailman2 to mailman3
#
# For now use mb2md -s devel.mbox -d /var/tmp/notmuch
# (The destination dir must be an absolute path)

from base64 import b32encode
import glob
import hashlib
import mailbox
import os
import sys

import notmuch


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


maildir = os.path.abspath(sys.argv[1])
actual_db_dir = os.path.join(maildir, '.notmuch')
m_box_dir = os.path.join(maildir, 'messages')
m_box = mailbox.Maildir(m_box_dir, factory=None)

try:
    if os.access(actual_db_dir, os.W_OK|os.X_OK) and os.path.isdir(actual_db_dir):
        db = notmuch.Database(maildir,
                mode=notmuch.Database.MODE.READ_WRITE)
    else:
        db = notmuch.Database(maildir, create=True)
    for message in glob.glob(os.path.abspath(
            os.path.join(maildir, 'messages', 'cur', '*'))):
        m_box_msg_key = os.path.basename(message).split(':', 1)[:-1][0]
        email_file = m_box.get_message(m_box_msg_key)
        msg, status = db.add_message(message)
        if status == notmuch.STATUS.SUCCESS:
            # Add the stable url hash as a tag.  This is one of the limitations of
            # notmuch.  In our own database we'd add this as a unique field so it
            # could be used as a secondary id
            msgid = stable_url_id(email_file)
            msg.add_tag('=msgid=%s' % msgid)
finally:
    # No db close for notmuch
    del db

