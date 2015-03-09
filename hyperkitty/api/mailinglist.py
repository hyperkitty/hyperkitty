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

#from django.shortcuts import get_object_or_404
#from django.http import Http404
from django.core.exceptions import PermissionDenied
#from rest_framework.response import Response
from rest_framework import serializers, generics

from hyperkitty.models import MailingList, ArchivePolicy
from hyperkitty.api.utils import EnumField


class MailingListSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='hk_api_mailinglist_detail', lookup_field="name")
    threads = serializers.HyperlinkedIdentityField(
        view_name='hk_api_thread_list', lookup_field="name",
        lookup_url_kwarg="mlist_fqdn")
    emails = serializers.HyperlinkedIdentityField(
        view_name='hk_api_email_list', lookup_field="name",
        lookup_url_kwarg="mlist_fqdn")
    archive_policy = EnumField(enum=ArchivePolicy)
    class Meta:
        model = MailingList
        fields = ("url", "name", "display_name", "description", "subject_prefix",
                  "archive_policy", "created_at", "threads", "emails")
        lookup_field = "name"


class MailingListList(generics.ListAPIView):
    """List mailing-lists"""

    queryset = MailingList.objects.exclude(
        archive_policy=ArchivePolicy.private.value)
    lookup_field = "name"
    serializer_class = MailingListSerializer
#    def get(self, request):
#        lists = MailingList.objects.exclude(
#            archive_policy=ArchivePolicy.private.value)
#        serializer = MailingListSerializer(lists, many=True)
#        return Response(serializer.data)


class MailingListDetail(generics.RetrieveAPIView):
    """Show a mailing-list"""

    queryset = MailingList.objects.all()
    lookup_field = "name"
    serializer_class = MailingListSerializer

    def get_object(self):
        mlist = super(MailingListDetail, self).get_object()
        #mlist = get_object_or_404(MailingList, name=self.kwargs["name"])
        #try:
        #    mlist = MailingList.objects.get(name=self.kwargs["name"])
        #except MailingList.DoesNotExist:
        #    raise Http404
        if mlist.archive_policy == ArchivePolicy.private.value:
            raise PermissionDenied
        return mlist
#    def get(self, request, name):
#        try:
#            mlist = MailingList.objects.get(name=name)
#        except MailingList.DoesNotExist:
#            raise Http404
#        if mlist.archive_policy == ArchivePolicy.private.value:
#            raise PermissionDenied
#        serializer = MailingListSerializer(mlist)
#        return Response(serializer.data)
