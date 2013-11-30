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


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, Page
from django.utils import six
from storm.store import ResultSet


class StormPaginator(Paginator):

    def page(self, number):
        "Returns a Page object for the given 1-based page number."
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        #return StormPage(self.object_list[bottom:top], number, self)
        return Page(list(self.object_list[bottom:top]), number, self)

class StormPage(Page):

    def __len__(self):
        return self.paginator.per_page

    def __getitem__(self, index):
        if not isinstance(index, (slice,) + six.integer_types):
            raise TypeError
        # The object_list is converted to a list so that if it was a QuerySet
        # it won't be a database hit per __getitem__.
        return list(self.object_list)[index]
        #return self.object_list[index]

    def __iter__(self):
        for obj in self.object_list:
            yield obj

    def __contains__(self, item):
        return self.object_list.__contains__(item)


def paginate(objects, page_num, max_page_range=10, paginator=None):
    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        page_num = 1
    if paginator is None:
        # else use the provided instance
        if isinstance(objects, ResultSet):
            paginator = StormPaginator(objects, 10)
        else:
            paginator = Paginator(objects, 10)
    try:
        objects = paginator.page(page_num)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        objects = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        objects = paginator.page(paginator.num_pages)
    # Calculate the displayed page range
    if paginator.num_pages > max_page_range:
        objects.page_range = [ 1 ]
        subrange_lower = page_num - (max_page_range / 2 - 2)
        if subrange_lower > 3:
            objects.page_range.append("...")
        else:
            subrange_lower = 2
        objects.page_range.extend(range(subrange_lower, page_num))
        if page_num != 1 and page_num != 100:
            objects.page_range.append(page_num)
        subrange_upper = page_num + (max_page_range / 2 - 2)
        if subrange_upper >= paginator.num_pages - 2:
            subrange_upper = paginator.num_pages - 1
        objects.page_range.extend(range(page_num+1, subrange_upper+1))
        if subrange_upper < paginator.num_pages - 2:
            objects.page_range.append("...")
        objects.page_range.append(paginator.num_pages)
    else:
        objects.page_range = [ p+1 for p in range(paginator.num_pages) ]
    return objects

