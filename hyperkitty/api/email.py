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

from hyperkitty.models import Email, ArchivePolicy
from .utils import MLChildHyperlinkedRelatedField
from .sender import SenderSerializer


class EmailShortSerializer(serializers.HyperlinkedModelSerializer):
    url = MLChildHyperlinkedRelatedField(
        view_name='hk_api_email_detail', read_only=True,
        lookup_field="message_id_hash", source="*")
    mailinglist = serializers.HyperlinkedRelatedField(
        view_name='hk_api_mailinglist_detail', read_only=True, lookup_field="name")
    thread = MLChildHyperlinkedRelatedField(
        view_name='hk_api_thread_detail', read_only=True,
        lookup_field="thread_id")
    parent = MLChildHyperlinkedRelatedField(
        view_name='hk_api_email_detail', read_only=True,
        lookup_field="message_id_hash")
    children = MLChildHyperlinkedRelatedField(
        view_name='hk_api_email_detail', read_only=True,
        lookup_field="message_id_hash", many=True)
    sender = SenderSerializer()
    likes = serializers.IntegerField(min_value=0)
    dislikes = serializers.IntegerField(min_value=0)

    class Meta:
        model = Email
        fields = ("url", "mailinglist", "message_id", "message_id_hash",
                  "thread", "sender", "subject", "date", "parent", "children",
                  "likes", "dislikes")


class EmailSerializer(EmailShortSerializer):
    class Meta:
        model = Email
        fields = EmailShortSerializer.Meta.fields + ("content",)#, "attachments")


class EmailList(generics.ListAPIView):
    """List emails"""

    serializer_class = EmailShortSerializer

    def get_queryset(self):
        query = Email.objects.filter(
                mailinglist__name=self.kwargs["mlist_fqdn"],
            ).exclude(mailinglist__archive_policy=ArchivePolicy.private.value)
        if "thread_id" in self.kwargs:
            query = query.filter(thread__thread_id=self.kwargs["thread_id"])
        return query.order_by("-archived_date")


class EmailListBySender(generics.ListAPIView):
    """List emails by sender"""

    serializer_class = EmailShortSerializer

    def get_queryset(self):
        return Email.objects.filter(
                sender__address=self.kwargs["address"],
            ).exclude(mailinglist__archive_policy=ArchivePolicy.private.value
            ).order_by("-archived_date")


class EmailDetail(generics.RetrieveAPIView):
    """Show an email"""

    serializer_class = EmailSerializer

    def get_object(self):
        email = get_object_or_404(Email,
            mailinglist__name=self.kwargs["mlist_fqdn"],
            message_id_hash=self.kwargs["message_id_hash"],
            )
        if email.mailinglist.archive_policy == ArchivePolicy.private.value:
            raise PermissionDenied
        return email
