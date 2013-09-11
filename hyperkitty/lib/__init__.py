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


def get_store(request):
    return request.environ["kittystore.store"]


def stripped_subject(mlist, subject):
    if mlist is None:
        return subject
    if not subject:
        return u"(no subject)"
    if not mlist.subject_prefix:
        return subject
    if subject.lower().startswith(mlist.subject_prefix.lower()):
        subject = subject[len(mlist.subject_prefix) : ]
    return subject
