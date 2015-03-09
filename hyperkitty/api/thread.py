#-*- coding: utf-8 -*-
# Copyright (C) 2012-2015 by the Free Software Foundation, Inc.
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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

# pylint: disable=no-init

from __future__ import absolute_import, unicode_literals

from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework import serializers, generics

from hyperkitty.models import Thread, ArchivePolicy
from hyperkitty.api.utils import MLChildHyperlinkedRelatedField


class ThreadSerializer(serializers.HyperlinkedModelSerializer):
    url = MLChildHyperlinkedRelatedField(
        view_name='hk_api_thread_detail', read_only=True,
        lookup_field="thread_id", source="*")
    mailinglist = serializers.HyperlinkedRelatedField(
        view_name='hk_api_mailinglist_detail', read_only=True, lookup_field="name")
    starting_email = MLChildHyperlinkedRelatedField(
        view_name='hk_api_email_detail', read_only=True,
        lookup_field="message_id_hash")
    likes = serializers.IntegerField(min_value=0)
    dislikes = serializers.IntegerField(min_value=0)
    emails = MLChildHyperlinkedRelatedField(
        view_name='hk_api_thread_email_list', read_only=True,
        lookup_field="thread_id", source="*")
    replies_count = serializers.SerializerMethodField()
    next_thread = MLChildHyperlinkedRelatedField(
        view_name='hk_api_thread_detail', read_only=True,
        lookup_field="thread_id")
    prev_thread = MLChildHyperlinkedRelatedField(
        view_name='hk_api_thread_detail', read_only=True,
        lookup_field="thread_id")
    class Meta:
        model = Thread
        fields = ("url", "mailinglist", "thread_id", "subject", "date_active",
                  "category", "starting_email", "emails", "likes", "dislikes",
                  "replies_count", "next_thread", "prev_thread")

    def get_replies_count(self, obj):
        return obj.emails_count - 1


class ThreadList(generics.ListAPIView):
    """List threads"""

    serializer_class = ThreadSerializer

    def get_queryset(self):
        return Thread.objects.filter(
                mailinglist__name=self.kwargs["mlist_fqdn"],
            ).exclude(mailinglist__archive_policy=ArchivePolicy.private.value
            ).order_by("-date_active")


class ThreadDetail(generics.RetrieveAPIView):
    """Show a thread"""

    serializer_class = ThreadSerializer

    def get_object(self):
        thread = get_object_or_404(Thread,
            mailinglist__name=self.kwargs["mlist_fqdn"],
            thread_id=self.kwargs["thread_id"],
            )
        if thread.mailinglist.archive_policy == ArchivePolicy.private.value:
            raise PermissionDenied
        return thread
