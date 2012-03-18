#-*- coding: utf-8 -*-

import pymongo
import re
from bunch import Bunch

connection = pymongo.Connection('localhost', 27017)

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
    for date in db.mails.distinct('Date'):
        if date.year in archives:
            archives[date.year].add(date.month)
        else:
            archives[date.year] = set([date.month])
    for key in archives:
        archives[key] = list(archives[key])
    return archives


def search_archives(table, query):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    for el in query:
        db.mails.create_index(str(el))
        db.mails.ensure_index(str(el))
    return db.mails.find(query,
        sort=[('Date', pymongo.DESCENDING)]).limit(50)
