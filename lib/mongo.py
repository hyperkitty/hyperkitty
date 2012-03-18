#-*- coding: utf-8 -*-

import pymongo
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
    for el in db.mails.find({'In-Reply-To': start_email['Message-ID']},
        sort=[('Date', pymongo.DESCENDING)]):
        thread.append(el)
        get_emails_thread(el, thread)
    return thread


def get_archives(table, start, end):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    db.mails.create_index('In-Reply-To')
    db.mails.ensure_index('In-Reply-To')
    # Beginning of thread == No 'In-Reply-To' header
    archives = []
    for el in db.mails.find({'In-Reply-To': {'$exists':False},
            "Date": {"$gte": start, "$lt": end}}, 
            sort=[('Date', pymongo.DESCENDING)]):
        archives.append(el)
    return archives


def get_thread(table, start, end):
    db = connection[table]
    db.mails.create_index('Date')
    db.mails.ensure_index('Date')
    db.mails.create_index('In-Reply-To')
    db.mails.ensure_index('In-Reply-To')
    # Beginning of thread == No 'In-Reply-To' header
    archives = Bunch()
    for el in db.mails.find({'In-Reply-To': {'$exists':False},
            "Date": {"$gte": start, "$lt": end}}, 
            sort=[('Date', pymongo.DESCENDING)]):
        thread = get_emails_thread(el, [el])
        #print el['Subject'], len(thread)
        archives[el['Subject']] = thread
    return archives


def get_thread_length(table, thread_id):
    db = connection[table]
    db.mails.create_index('Thread-ID')
    db.mails.ensure_index('Thread-ID')
    return db.mails.find({'Thread-ID': thread_id}).count()


def get_thread_participants(table, thread_id):
    db = connection[table]
    db.mails.create_index('Thread-ID')
    db.mails.ensure_index('Thread-ID')
    authors = set()
    for mail in db.mails.find({'Thread-ID': thread_id}):
        authors.add(mail['From'])
    return len(authors)

def get_archives_length(table):
    db = connection[table]
    archives = {}
    for entry in db.mails.find():
        date = entry['Date']
        if date.year in archives:
            archives[date.year].add(date.month)
        else:
            archives[date.year] = set([date.month])
    for key in archives:
        archives[key] = list(archives[key])
    return archives
    
