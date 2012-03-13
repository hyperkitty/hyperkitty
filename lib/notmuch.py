#-*- coding: utf-8 -*-

from __future__ import absolute_import

from calendar import timegm
from datetime import datetime, timedelta
import json
import os

import bunch
import notmuch

from hyperkitty.lib import gravatar_url

# Used to remove tags that notmuch added automatically that we don't want
IGNORED_TAGS = (u'inbox', u'unread', u'signed')

def get_ro_db(path):
    # Instead of throwing an exception, notmuch bindings tend to segfault if
    # the database path doesn't exist.

    # Does the notmuch db exist?
    actual_db_dir = os.path.join(path, '.notmuch')
    if os.access(actual_db_dir, os.W_OK|os.X_OK) and os.path.isdir(actual_db_dir):
        return notmuch.Database(path,
                mode=notmuch.Database.MODE.READ_ONLY)

    raise IOError('Notmuch database not present in %(path)s' %
            {'path': path})

def get_thread_info(thread):
    thread_info = bunch.Bunch()

    #
    # Get information about the first email of a thread
    #

    first_email = tuple(thread.get_toplevel_messages())[0]
    for tag in (tg for tg in first_email.get_tags() if tg.startswith('=msgid=')):
        thread_info.email_id = tag.split('=msgid=', 1)[-1]
        break
    first_email_data = json.loads(first_email.format_message_as_json())

    # Python-3.3 has ''.rsplit(maxsplit=1) (keyword arg).  Until then, we need
    # rsplit(None, 1) to get the desired behaviour
    author = first_email_data['headers']['From'].rsplit(None, 1)
    if author[-1].startswith('<'):
        author[-1] = author[-1][1:]
    if author[-1].endswith('>'):
        author[-1] = author[-1][:-1]
    # This accounts for From lines without a real name, just email address
    name = author[0]
    email = author[-1]
    thread_info.author = name
    thread_info.avatar = gravatar_url(email)

    for body_part in first_email_data['body']:
        try:
            # The body may have many parts.  We only want the part that we
            # can guess is the actual text of an email message.
            # For this prototype, that is defined as
            # has a content-type and content keys.  and the content-type
            # is text/plain.  When this is not a prototype, the heuristic
            # should be more advanced
            if body_part['content-type'] == u'text/plain':
                thread_info.body = body_part['content']
                break
        except KeyError:
            continue

    #
    # Get meta info about the thread itself
    #

    #  Used for sorting threads
    thread_info.most_recent = thread.get_newest_date()
    date_as_offset = timegm(datetime.utcnow().timetuple()) - thread_info.most_recent
    thread_info.age = str(timedelta(seconds=date_as_offset))
    thread_info.title = thread.get_subject()
    # Because notmuch doesn't allow us to extend the schema, everything is
    # in a tag.  Extract those tags that have special meaning to us
    thread_info.tags = []
    thread_info.answers = []
    thread_info.liked = 0
    for tag in thread.get_tags():
        if tag.startswith('=msgid='):
            msgid = tag.split('=msgid=', 1)[-1]
            # The first email doesn't count as a reply :-)
            if msgid != thread_info.email_id:
                thread_info.answers.append(tag.split('=msgid=', 1)[-1])
        elif tag.startswith('=threadlike='):
            thread_info.liked = int(tag.split('=threadlike=', 1)[-1])
        elif tag.startswith('=topic='):
            thread_info.category = tag.split('=topic=', 1)[-1]
            print thread_info.category
        elif tag in IGNORED_TAGS:
            continue
        else:
            thread_info.tags.append(tag)
    # notmuch has this nice method call to give us the info but it returns
    # it as a string instead of a list
    thread_info.participants = set(thread.get_authors().replace(u'| ', u', ', 1).split(u', '))


    return thread_info
