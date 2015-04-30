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
from tempfile import gettempdir

from django.conf import settings
from django_extensions.management.jobs import BaseJob
from lockfile import LockFile, AlreadyLocked, LockFailed
from hyperkitty.search_indexes import update_index

import logging
logger = logging.getLogger(__name__)


class Job(BaseJob):
    help = "Update the full-text index"
    when = "minutely"

    def execute(self):
        lock = LockFile(getattr(
            settings, "HYPERKITTY_JOBS_UPDATE_INDEX_LOCKFILE",
            os.path.join(gettempdir(), "hyperkitty-jobs-update-index.lock")))
        try:
            lock.acquire(timeout=0)
        except AlreadyLocked:
            logger.warning("The job 'update_index' is already running")
            return
        except LockFailed as e:
            logger.warning("Could not obtain a lock for the 'update_index' "
                           "job (%s)", e)
            return
        try:
            update_index()
        except Exception as e: # pylint: disable-msg=broad-except
            logger.exception("Failed to update the fulltext index: %s", e)
        finally:
            lock.release()
