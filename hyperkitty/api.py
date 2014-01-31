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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from hyperkitty.models import Tag
from hyperkitty.lib import get_store


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
    likes = serializers.IntegerField()
    dislikes = serializers.IntegerField()

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

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("list_address", "threadid", "tag")


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
        email = store.get_message_by_hash_from_list(mlist_fqdn, messageid)
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


class TagResource(APIView):
    """
    Resource used to retrieve tags from the database using the REST API.
    """

    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)
