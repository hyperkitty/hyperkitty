# mongodb/api.py
from djangorestframework.views import View

from django.conf.urls.defaults import url
from django.http import HttpResponseNotModified, HttpResponse
from lib import mongo
import pymongo
import json

connection = pymongo.Connection('localhost', 27017)


class EmailResource(View):
    """ Resource used to retrieve emails from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, messageid):
        list_name = mlist_fqdn.split('@')[0]
        email = mongo.get_email(list_name, messageid)
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
        thread = mongo.get_thread_list(list_name, threadid)
        if not thread:
            return HttpResponse(status=404)
        else:
            return thread
