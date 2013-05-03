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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from django.conf import settings
from mailmanclient import Client, MailmanConnectionError


def subscribe(list_address, user):
    client = Client('%s/3.0' % settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER, settings.MAILMAN_API_PASS)
    rest_list = client.get_list(list_address)
    try:
        member = rest_list.get_member(user.email)
    except ValueError:
        # not subscribed yet, subscribe the user without email delivery
        member = rest_list.subscribe(user.email,
                "%s %s" % (user.first_name, user.last_name))
        member.preferences["delivery_status"] = "by_user"
        member.preferences.save()
