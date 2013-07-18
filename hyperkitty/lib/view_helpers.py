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


import datetime

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.timezone import utc

from hyperkitty.models import ThreadCategory, LastView
from hyperkitty.views.forms import CategoryForm


FLASH_MESSAGES = {
    "updated-ok": ("success", "The profile was successfully updated."),
    "sent-ok": ("success", "The message has been sent successfully."),
    "attached-ok": ("success", "Thread successfully re-attached."),
}


def get_months(store, list_name):
    """ Return a dictionnary of years, months for which there are
    potentially archives available for a given list (based on the
    oldest post on the list).

    :arg list_name, name of the mailing list in which this email
    should be searched.
    """
    date_first = store.get_start_date(list_name)
    if not date_first:
        return {}
    archives = {}
    now = datetime.datetime.now()
    year = date_first.year
    month = date_first.month
    while year < now.year:
        archives[year] = range(1, 13)[(month -1):]
        year = year + 1
        month = 1
    archives[now.year] = range(1, 13)[:now.month]
    return archives


def get_display_dates(year, month, day):
    if day is None:
        start_day = 1
    else:
        start_day = int(day)
    begin_date = datetime.datetime(int(year), int(month), start_day)

    if day is None:
        end_date = begin_date + datetime.timedelta(days=32)
        end_date = end_date.replace(day=1)
    else:
        end_date = begin_date + datetime.timedelta(days=1)

    return begin_date, end_date


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def paginate(objects, page_num, max_page_range=10, paginator=None):
    try:
        page_num = int(page_num)
    except (TypeError, ValueError):
        page_num = 1
    if paginator is None:
        paginator = Paginator(objects, 10) # else use the provided instance
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


def get_category_widget(request=None, current_category=None):
    """
    Returns the category form and the applicable category object (or None if no
    category is set for this thread).

    If current_category is not provided or None, try to deduce it from the POST
    request.
    if request is not provided or None, don't return the category form, return
    None instead.
    """
    categories = [ (c.name, c.name.upper())
                   for c in ThreadCategory.objects.all() ] \
                 + [("", "no category")]

    if request:
        if request.method == "POST":
            category_form = CategoryForm(request.POST)
        else:
            category_form = CategoryForm(initial={"category": current_category or ""})
        category_form["category"].field.choices = categories
    else:
        category_form = None
    if request and request.method == "POST" and category_form.is_valid():
        # is_valid() must be called after the choices have been set
        current_category = category_form.cleaned_data["category"]

    if not current_category:
        category = None
    else:
        try:
            category = ThreadCategory.objects.get(name=current_category)
        except ThreadCategory.DoesNotExist:
            category = None
    return category, category_form


def is_thread_unread(request, mlist_name, thread):
    """Returns True or False if the thread is unread or not."""
    unread = False
    if request.user.is_authenticated():
        try:
            last_view_obj = LastView.objects.get(
                    list_address=mlist_name,
                    threadid=thread.thread_id,
                    user=request.user)
        except LastView.DoesNotExist:
            unread = True
        else:
            if thread.date_active.replace(tzinfo=utc) \
                    > last_view_obj.view_date:
                unread = True
    return unread
