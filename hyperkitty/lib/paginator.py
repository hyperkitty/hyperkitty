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


from __future__ import absolute_import, unicode_literals, division

from django.http import Http404
from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger,
    InvalidPage)


def paginate(objects=None, page_num=1, max_page_range=10, paginator=None,
             results_per_page=10):
    if objects is None and paginator is None:
        raise TypeError("You must either provide an 'objects' argument "
                        "or a 'paginator' argument")
    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        page_num = 1
    if paginator is None:
        # else use the provided instance
        paginator = Paginator(objects, results_per_page)
    try:
        objects = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        objects = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        objects = paginator.page(paginator.num_pages)
    except InvalidPage:
        raise Http404("No such page of results!")
    # Calculate the displayed page range
    if paginator.num_pages > max_page_range:
        objects.page_range = [ 1 ]
        subrange_lower = page_num - int(max_page_range / 2 - 2)
        if subrange_lower > 3:
            objects.page_range.append("...")
        else:
            subrange_lower = 2
        objects.page_range.extend(range(subrange_lower, page_num))
        if page_num != 1 and page_num != 100:
            objects.page_range.append(page_num)
        subrange_upper = page_num + int(max_page_range / 2 - 2)
        if subrange_upper >= paginator.num_pages - 2:
            subrange_upper = paginator.num_pages - 1
        objects.page_range.extend(range(page_num+1, subrange_upper+1))
        if subrange_upper < paginator.num_pages - 2:
            objects.page_range.append("...")
        objects.page_range.append(paginator.num_pages)
    else:
        objects.page_range = [ p+1 for p in range(paginator.num_pages) ]
    return objects
