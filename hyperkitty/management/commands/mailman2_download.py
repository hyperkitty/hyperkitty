# -*- coding: utf-8 -*-

# Copyright (C) 2011-2015 by the Free Software Foundation, Inc.
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
Download archives from Mailman 2.1
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import urllib2
import gzip
import itertools
import logging
from multiprocessing import Pool
from datetime import date
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def _archive_downloader(args):
    options, year, month = args
    if not year or not month:
        return
    basename = "{0}-{1}.txt.gz".format(year, month)
    filepath = os.path.join(options["destination"], basename)
    if os.path.exists(filepath):
        if options["verbosity"] >= 2:
            print("{0} already downloaded, skipping".format(basename))
        return
    url = "{0}/pipermail/{1}/{2}".format(
            options["url"], options["list_address"], basename)
    if options["verbosity"] >= 2:
        print("Downloading from {0}".format(url))
    try:
        request = urllib2.urlopen(url)
        with open(filepath, "w") as f:
            f.write(request.read())
    except urllib2.URLError, e:
        if isinstance(e, urllib2.HTTPError) and e.code == 404:
            print("This archive hasn't been created on the server yet: %s"
                  % basename)
        else:
            print("Error: %s" % e.reason)
        return
    pos = str(MONTHS.index(month) + 1).rjust(2, "0")
    newname = '{0}-{1}-{2}-{3}.txt'.format(
        options["list_address"], year, pos, month)
    with open(os.path.join(options["destination"], newname), "w") as f:
        f.write(gzip.open(filepath).read())
    print("Downloaded archive for {0} {1} from {2}".format(month, year, url))


class Command(BaseCommand):
    args = "-u <url> -l <list_address> [-d destination]"
    help = "Download Mailman 2.1 archives"
    option_list = BaseCommand.option_list + (
        make_option('-u', '--url',
            help="URL of the Mailman server"),
        make_option('-l', '--list-address',
            help="the full list address the mailbox will be imported to"),
        make_option('-d', '--destination', default=os.getcwd(),
            help="directory to download the archives to. Defaults "
                 "to the current directory (%default)"),
        make_option("-s", "--start", default="2000",
            help="first year to start looking for archives")
        )

    def _check_options(self, args, options): # pylint: disable-msg=unused-argument
        if not options.get("url"):
            raise CommandError("an URL must be provided")
        if not options.get("list_address"):
            raise CommandError(
                "The list address must be provided.")
        if "@" not in options["list_address"]:
            raise CommandError(
                "The list name must be fully-qualified, including "
                "the '@' symbol and the domain name.")
        try:
            options["start"] = range(1980, int(options["start"]), date.today().year + 1)
        except ValueError, e:
            raise CommandError("invalid value for '--start': %s" % e)
        options["verbosity"] = int(options.get("verbosity", "1"))

    def handle(self, *args, **options):
        self._check_options(args, options)
        # logging
        if options["verbosity"] >= 3:
            debuglevel = logging.DEBUG
        else:
            debuglevel = logging.INFO
        logging.basicConfig(format='%(message)s', level=debuglevel)

        p = Pool(5)
        p.map(_archive_downloader, itertools.product([options], options["start"], MONTHS))
