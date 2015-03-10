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
Update the full-text index
"""

from __future__ import absolute_import, print_function, unicode_literals

import os.path
import sys
from tempfile import gettempdir

from django.conf import settings
from django_extensions.management.jobs import BaseJob
from lockfile import LockFile, AlreadyLocked, LockFailed
from haystack.query import SearchQuerySet
from haystack.management.commands.update_index import \
    Command as UpdateIndexCommand


def _do_update():
    update_cmd = UpdateIndexCommand()
    # Find the last email in the index:
    try:
        last_email = SearchQuerySet().latest('archived_date')
    except IndexError:
        update_cmd.start_date = None
    else:
        update_cmd.start_date = last_email.object.archived_date
    # set defaults
    update_cmd.verbosity = 0
    update_cmd.batchsize = None
    update_cmd.end_date = None
    update_cmd.workers = 0
    # Setting remove to True is extremely slow, it needs to scan the entire
    # index and database. About 15 minutes on Fedora's lists, so not for a
    # frequent operation.
    update_cmd.remove = False
    update_cmd.update_backend("hyperkitty", "default")


class Job(BaseJob):
    help = "Update the full-text index"
    when = "hourly"

    def execute(self):
        lock = LockFile(getattr(
            settings, "HYPERKITTY_JOBS_UPDATE_INDEX_LOCKFILE",
            os.path.join(gettempdir(), "hyperkitty-jobs-update-index.lock")))
        try:
            lock.acquire(timeout=0)
        except AlreadyLocked:
            print("The job 'update_index' is already running", file=sys.stderr)
            return
        except LockFailed as e:
            print("Could not obtain a lock for the 'update_index' job "
                  "({})".format(e), file=sys.stderr)
            return
        try:
            _do_update()
        finally:
            lock.release()
