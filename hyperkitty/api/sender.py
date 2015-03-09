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

from __future__ import absolute_import, unicode_literals, print_function

from rest_framework import serializers
from hyperkitty.models import Sender


class OptionalHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):
    def to_representation(self, obj):
        value = getattr(obj, self.lookup_field)
        if value is None:
            return None
        return super(OptionalHyperlinkedRelatedField, self).to_representation(obj)


class SenderSerializer(serializers.HyperlinkedModelSerializer):
    emails = OptionalHyperlinkedRelatedField(
        view_name='hk_api_sender_email_list', read_only=True,
        lookup_field="mailman_id", source="*", required=False)
    # emails is None if mailmain_id is None
    class Meta:
        model = Sender
        fields = ("name", "mailman_id", "emails")
        lookup_field = "address"
