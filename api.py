#-*- coding: utf-8 -*-

from djangorestframework.views import View
from django.conf.urls.defaults import url
from django.conf import settings
from django.http import HttpResponseNotModified, HttpResponse
from kittystore.kittysastore import KittySAStore
import json
import re

STORE = KittySAStore(settings.KITTYSTORE_URL)


class EmailResource(View):
    """ Resource used to retrieve emails from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, messageid):
        list_name = mlist_fqdn.split('@')[0]
        email = STORE.get_email(list_name, messageid)
        if not email:
            return HttpResponse(status=404)
        else:
            return email


class ThreadResource(View):
    """ Resource used to retrieve threads from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, threadid):
        list_name = mlist_fqdn.split('@')[0]
        thread = STORE.get_thread(list_name, threadid)
        if not thread:
            return HttpResponse(status=404)
        else:
            return thread


class SearchResource(View):
    """ Resource used to search the archives using the REST API.
    """

    def get(self, request, mlist_fqdn, field, keyword):
        list_name = mlist_fqdn.split('@')[0]

        if field not in ['Subject', 'Content', 'SubjectContent', 'From']:
            return HttpResponse(status=404)

        regex = '.*%s.*' % keyword
        if field == 'SubjectContent':
            query_string = {'$or' : [
                {'Subject': re.compile(regex, re.IGNORECASE)},
                {'Content': re.compile(regex, re.IGNORECASE)}
                ]}
        else:
            query_string = {field.capitalize(): 
                re.compile(regex, re.IGNORECASE)}

        print query_string, field, keyword
        threads = STORE.search_archives(list_name, query_string)
        if not threads:
            return HttpResponse(status=404)
        else:
            return threads
