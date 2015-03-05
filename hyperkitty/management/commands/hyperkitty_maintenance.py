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
Do HyperKitty maintenance tasks
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from haystack.query import SearchQuerySet
from haystack.management.commands.update_index import \
    Command as UpdateIndexCommand

from hyperkitty.models import Thread
from hyperkitty.lib.mailman import sync_with_mailman
from hyperkitty.lib.analysis import compute_thread_order_and_depth


# TODO: add an exclusive lock to prevent concurrent runs

class Command(BaseCommand):
    help = "Do HyperKitty maintenance tasks"
    option_list = BaseCommand.option_list + (
        make_option('--long',
            action='store_true', default=False,
            help="Do long tasks"),
        )

    def handle(self, *args, **options):
        options["verbosity"] = int(options.get("verbosity", "1"))
        # logging
        if options["verbosity"] >= 3:
            debuglevel = logging.DEBUG
        else:
            debuglevel = logging.INFO
        logging.basicConfig(format='%(message)s', level=debuglevel)
        if args:
            raise CommandError("no arguments allowed")

        # Sync with mailman
        sync_with_mailman()

        # Remove orphan threads
        threads = Thread.objects.annotate(
            num_emails=Count("emails")).filter(num_emails=0)
        if options["verbosity"] >= 1:
            self.stdout.write("Deleting {} orphan thread(s)".format(
                threads.count()))
        threads.delete()

        # Update the fulltext index
        self.update_fulltext_index(options["verbosity"])

        # Compute thread order and depth for all threads (long)
        if options["long"]:
            for thread in Thread.objects.all():
                compute_thread_order_and_depth(thread)

    def update_fulltext_index(self, verbosity):
        update_cmd = UpdateIndexCommand()
        # Find the last email in the index:
        try:
            last_email = SearchQuerySet().latest('archived_date')
        except IndexError:
            update_cmd.start_date = None
        else:
            update_cmd.start_date = last_email.object.archived_date
        # set defaults
        update_cmd.verbosity = verbosity
        update_cmd.batchsize = None
        update_cmd.end_date = None
        update_cmd.remove = True
        update_cmd.workers = 0
        update_cmd.update_backend("hyperkitty", "default")
