#-*- coding: utf-8 -*-

import pymongo
import re
from bunch import Bunch
from datetime import datetime

connection = pymongo.Connection('localhost', 27017)

def _build_thread(emails):
    thread = {}
    for email in emails:
        #print email['Date'], email['From'] #, email['Message-ID']
        email = Bunch(email)
        ref = []
        if 'References' in email:
            ref.extend(email['References'].split()[-1:])
        elif 'In-Reply-To' in email:
            ref.append(email['In-Reply-To'])
        if email['Message-ID'] not in thread:
            thread[email['Message-ID']] = Bunch(
                {'email': email, 'child': []})
        else:
            thread[email['Message-ID']].email = email
        for ref in set(ref):
            if ref in thread:
                thread[ref].child.append(email['Message-ID'])
            else:
                thread[ref] = Bunch(
                {'email': None, 'child': [email['Message-ID']]})
    return thread

def _tree_to_list(tree, mailid, level, thread_list):
    start = tree[mailid]
    start.level = level
    thread_list.append(start)
    for mail in start.child:
        mail = tree[mail]
        thread_list = _tree_to_list(tree, mail.email['Message-ID'],
            level + 1, thread_list)
    return thread_list

def get_thread_list(table, threadid):
    db = connection[table]
    thread = list(db.mails.find({'ThreadID': threadid},
        sort=[('Date', pymongo.ASCENDING)]))

    tree = _build_thread(thread)
    thread_list = []
    if thread:
        thread = _tree_to_list(tree, thread[0]['Message-ID'], 0, thread_list)
        return thread
    else:
        return []

def get_thread_name(table, threadid):
    db = connection[table]
    thread = list(db.mails.find({'ThreadID': threadid},
        sort=[('Date', pymongo.ASCENDING)]))[0]
    return thread['Subject']

def get_emails_thread(table, start_email, thread):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    db.mails.create_index('In-Reply-To')
    db.mails.ensure_index('In-Reply-To')
    db.mails.create_index('Message-ID')
    db.mails.ensure_index('Message-ID')
    regex = '.*%s.*' % start_email['Message-ID']
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
    for el in db.mails.find({'References': {'$exists':False},
            "Date": {"$gte": start, "$lt": end}}, 
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


def search_archives(table, query):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    for el in query:
        db.mails.create_index(str(el))
        db.mails.ensure_index(str(el))
    return list(db.mails.find(query, sort=[('Date',
        pymongo.DESCENDING)]))
    
