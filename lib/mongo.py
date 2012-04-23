#-*- coding: utf-8 -*-

import pymongo
import re
from bunch import Bunch
from datetime import datetime

connection = pymongo.Connection('localhost', 27017)


def _build_thread(emails):
    thread = {}
    for email in emails:
        #print email['Date'], email['From'] , email['MessageID']
        email = Bunch(email)
        ref = []
        if 'References' in email:
            refs = email['References'].split()[-1:]
            refs = [item.replace('<', '').replace('>', '') for item in refs]
            ref.extend(refs)
        elif 'InReplyTo' in email:
            rep = email['InReplyTo'].replace('<', '').replace('>', '')
            ref.append(rep)

        if email['MessageID'] not in thread:
            thread[email['MessageID']] = Bunch(
                {'email': email, 'child': []})
        else:
            thread[email['MessageID']].email = email

        for ref in set(ref):
            if ref in thread:
                thread[ref].child.append(email['MessageID'])
            else:
                thread[ref] = Bunch(
                {'email': None, 'child': [email['MessageID']]})
    return thread


def _tree_to_list(tree, mailid, level, thread_list):
    start = tree[mailid]
    #print start.email.From, start.email.Date, start.child
    start.level = level
    thread_list.append(start)
    for mail in start.child:
        mail = tree[mail]
        thread_list = _tree_to_list(tree, mail.email['MessageID'],
            level + 1, thread_list)
    return thread_list


def get_thread_list(table, threadid):
    db = connection[table]
    db.mails.create_index('ThreadID')
    db.mails.ensure_index('ThreadID')
    db.mails.create_index('References')
    db.mails.ensure_index('References')
    db.mails.create_index('InReplyTo')
    db.mails.ensure_index('InReplyTo')

    thread = list(db.mails.find({'ThreadID': threadid}))
    start = db.mails.find_one({'ThreadID': threadid,
                            'References': {'$exists':False},
                            'InReplyTo': {'$exists':False}})

    tree = _build_thread(thread)
    thread_list = []
    if thread:
        thread = _tree_to_list(tree, start['MessageID'], 0, thread_list)
        return thread
    else:
        return []


def get_thread_name(table, threadid):
    db = connection[table]
    db.mails.create_index('ThreadID')
    db.mails.ensure_index('ThreadID')
    thread = list(db.mails.find({'ThreadID': int(threadid)},
        sort=[('Date', pymongo.ASCENDING)]))
    if thread:
        return thread[0]['Subject']
    else:
        return ''


def get_email(table, emailid):
    db = connection[table]
    db.mails.create_index('MessageID')
    db.mails.ensure_index('MessageID')
    return db.mails.find_one({'MessageID': emailid})


def get_emails_thread(table, start_email, thread):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    db.mails.create_index('InReplyTo')
    db.mails.ensure_index('InReplyTo')
    db.mails.create_index('MessageID')
    db.mails.ensure_index('MessageID')
    regex = '.*%s.*' % start_email['MessageID']
    for el in db.mails.find({'References': re.compile(regex, re.IGNORECASE)},
        sort=[('Date', pymongo.DESCENDING)]):
        thread.append(el)
        get_emails_thread(el, thread)
    return thread


def get_archives(table, start, end):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    db.mails.create_index('References')
    db.mails.ensure_index('References')
    # Beginning of thread == No 'References' header
    archives = []
    for el in db.mails.find(
            {'References': {'$exists':False},
            'InReplyTo': {'$exists':False},
            "Date": {"$gt": start, "$lt": end}}, 
            sort=[('Date', pymongo.DESCENDING)]):
        archives.append(el)
    return archives


def get_thread(table, start, end):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    db.mails.create_index('References')
    db.mails.ensure_index('References')
    # Beginning of thread == No 'References' header
    archives = Bunch()
    for el in db.mails.find({'References': {'$exists':False},
            "Date": {"$gte": start, "$lt": end}}, 
            sort=[('Date', pymongo.DESCENDING)]):
        thread = get_emails_thread(el, [el])
        #print el['Subject'], len(thread)
        archives[el['Subject']] = thread
    return archives


def get_thread_length(table, thread_id):
    db = connection[table]
    db.mails.create_index('ThreadID')
    db.mails.ensure_index('ThreadID')
    return db.mails.find({'ThreadID': thread_id}).count()


def get_thread_participants(table, thread_id):
    db = connection[table]
    db.mails.create_index('ThreadID')
    db.mails.ensure_index('ThreadID')
    authors = set()
    for mail in db.mails.find({'ThreadID': thread_id}):
        authors.add(mail['From'])
    return len(authors)


def get_archives_length(table):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    archives = {}
    entry = db.mails.find_one(sort=[('Date', pymongo.ASCENDING)])
    date = entry['Date']
    now = datetime.now()
    year = date.year
    month = date.month
    while year < now.year:
        archives[year] = range(1,13)[(month -1):]
        year = year + 1
        month = 1
    archives[now.year] = range(1,13)[:now.month]
    return archives


def search_archives(table, query, limit=None):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    for el in query:
        db.mails.create_index(str(el))
        db.mails.ensure_index(str(el))
    output = []
    if limit:
        try:
            limit = int(limit)
        except ValueError:
            limit = None
    if limit:
        output = list(db.mails.find(query, sort=[('Date',
        pymongo.DESCENDING)]).limit(limit))
    else:
        output = list(db.mails.find(query, sort=[('Date',
        pymongo.DESCENDING)]))
    return output

