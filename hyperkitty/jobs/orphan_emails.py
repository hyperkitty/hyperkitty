# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>

"""
Find the parents of orphan emails.

When an email has an in-reply-to header pointing to no known email, it
is set to start a new thread. This job runs later on and tries to find the
missing email in the database, in case it was added in the meantime.

This can happen if HK receives the reply before the original message (when a
mail server in the chain has an issue, or in case of greylisting for example).
"""

from __future__ import absolute_import, print_function, unicode_literals

from django_extensions.management.jobs import BaseJob
from hyperkitty.models import Email


class Job(BaseJob):
    help = "Reattach orphan emails"
    when = "daily"

    def execute(self):
        orphan_starters = Email.objects.filter(
            parent_id__isnull=True, in_reply_to__isnull=False)
        for orphan_starter in orphan_starters:
            parent = Email.objects.filter(
                mailinglist=orphan_starter.mailinglist,
                message_id=orphan_starter.in_reply_to).first()
            if parent is None:
                continue
            if orphan_starter.id == parent.id:
                # an email with the in-reply-to header pointing to itself,
                # that's just bogus, ignore it.
                continue
            orphan_starter.set_parent(parent)
