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

from .mailinglist import MailingListList, MailingListDetail
from .thread import ThreadList, ThreadDetail
from .email import EmailList, EmailDetail, EmailListBySender
from .tag import TagList

#from rest_framework.views import APIView
#from rest_framework.response import Response
#from rest_framework.reverse import reverse

#from hyperkitty.models import MailingList, Email, Thread, Tag, ArchivePolicy, Sender


#class EmailResource(APIView):
#    """ Resource used to retrieve emails from the archives using the
#    REST API.
#    """
#
#    def get(self, request, mlist_fqdn, messageid):
#        email = Email.objects.filter(
#            mailinglist__name=mlist_fqdn,
#            message_id_hash=messageid
#            ).exclude(
#            mailinglist__archive_policy=ArchivePolicy.private.value)
#        return Response(EmailSerializer(email).data)
#
#
#class ThreadResource(APIView):
#    """ Resource used to retrieve threads from the archives using the
#    REST API.
#    """
#
#    def get(self, request, mlist_fqdn, threadid):
#        thread = Thread.objects.filter(
#            mailinglist__name=mlist_fqdn,
#            thread_id=threadid,
#            ).exclude(
#            mailinglist__archive_policy=ArchivePolicy.private.value)
#        return Response(ThreadSerializer(thread).data)
#
#class TagResource(APIView):
#    """
#    Resource used to retrieve tags from the database using the REST API.
#    """
#
#    def get(self, request):
#        tags = Tag.objects.all()
#        return Response(TagSerializer(tags, many=True).data)


#class MailingListViewSet(viewsets.ModelViewSet):
#    queryset = MailingList.objects.exclude(
#        archive_policy=ArchivePolicy.private.value)
#    serializer_class = MailingListSerializer
#
#
#class EmailViewSet(viewsets.ModelViewSet):
#
#    queryset = Email.objects.filter(
#            mailinglist__name=mlist_fqdn, message_id_hash=messageid
#        ).exclude(
#            mailinglist__archive_policy=ArchivePolicy.private.value
#        )
#    serializer_class = EmailSerializer
#
#
#class ThreadViewSet(viewsets.ModelViewSet):
#
#    queryset = Thread.objects.filter(
#            mailinglist__name=mlist_fqdn, thread_id=threadid,
#        ).exclude(
#            mailinglist__archive_policy=ArchivePolicy.private.value
#        )
#    serializer_class = ThreadSerializer
#
#
#class TagViewSet(viewsets.ModelViewSet):
#
#    queryset = Tag.objects.all()
#    serializer_class = TagSerializer
