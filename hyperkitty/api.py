#-*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#

import json
import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.exceptions import ParseError
from django.conf.urls import url
from django.conf import settings

from hyperkitty.lib import get_store
from kittystore.storm.model import Email, Thread


class ListSerializer(serializers.Serializer):
    name = serializers.CharField()
    display_name = serializers.CharField()
    subject_prefix = serializers.CharField()

class EmailSerializer(serializers.Serializer):
    list_name = serializers.EmailField()
    message_id = serializers.CharField()
    thread_id = serializers.CharField()
    sender_name = serializers.CharField()
    sender_email = serializers.EmailField()
    subject = serializers.CharField()
    in_reply_to = serializers.CharField()
    date = serializers.DateTimeField()

class EmailLinkSerializer(serializers.Serializer):
    list_name = serializers.EmailField()
    message_id = serializers.CharField()
    sender_name = serializers.CharField()
    sender_email = serializers.EmailField()
    date = serializers.DateTimeField()

class ThreadSerializer(serializers.Serializer):
    thread_id = serializers.CharField()
    list_name = serializers.EmailField()
    date_active = serializers.DateTimeField()
    subject = serializers.CharField()
    starting_email = EmailLinkSerializer()
    email_ids = serializers.CharField()
    participants = serializers.CharField()


class ListResource(APIView):
    """ Resource used to retrieve lists from the archives using the
    REST API.
    """

    def get(self, request):
        store = get_store(request)
        lists = store.get_lists()
        if not lists:
            return Response(status=404)
        else:
            return Response(ListSerializer(lists, many=True).data)

class EmailResource(APIView):
    """ Resource used to retrieve emails from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, messageid):
        store = get_store(request)
        email = store.get_message_by_id_from_list(mlist_fqdn, messageid)
        if not email:
            return Response(status=404)
        else:
            return Response(EmailSerializer(email).data)


class ThreadResource(APIView):
    """ Resource used to retrieve threads from the archives using the
    REST API.
    """

    def get(self, request, mlist_fqdn, threadid):
        store = get_store(request)
        thread = store.get_thread(mlist_fqdn, threadid)
        if not thread:
            return Response(status=404)
        else:
            return Response(ThreadSerializer(thread).data)


class SearchResource(APIView):
    """ Resource used to search the archives using the REST API.
    """

    def get(self, request, mlist_fqdn, field, keyword):
        fields = ['Subject', 'Content', 'SubjectContent', 'From']
        if field not in fields:
            raise ParseError(detail="Unknown field: " + field + ". Supported fields are " + ", ".join(fields))

        store = get_store(request)
        threads = None
        if field == 'Subject':
            threads = store.search_list_for_subject(mlist_fqdn, keyword)
        elif field == 'Content':
            threads = store.search_list_for_content(mlist_fqdn, keyword)
        elif field == 'SubjectContent':
            threads = store.search_list_for_content_subject(mlist_fqdn, keyword)
        elif field == 'From':
            threads = store.search_list_for_sender(mlist_fqdn, keyword)

        if not threads:
            return Response(status=404)
        else:
            return Response(EmailSerializer(threads, many=True).data)
