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


from __future__ import absolute_import, print_function, unicode_literals

from django.core.cache import cache as django_cache


MISSING = object()

class CacheProxy:

    def __init__(self):
        self.backend = django_cache

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def get_or_set(self, key, fn, timeout=MISSING):
        value = self.backend.get(key)
        if value is None:
            value = fn()
            if timeout is MISSING:
                self.backend.set(key, value)
            else:
                self.backend.set(key, value, timeout)
        return value

cache = CacheProxy()

