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

from __future__ import absolute_import, unicode_literals

import datetime
from functools import wraps

from django.http import Http404
from django.utils.timezone import utc
from django.utils.decorators import available_attrs
from django.shortcuts import render

from hyperkitty.models import ThreadCategory, MailingList, Profile
from hyperkitty.views.forms import CategoryForm
from hyperkitty.lib.cache import cache


FLASH_MESSAGES = {
    "updated-ok": ("success", "The profile was successfully updated."),
    "sent-ok": ("success", "The message has been sent successfully."),
    "attached-ok": ("success", "Thread successfully re-attached."),
}


def get_months(mlist):
    """ Return a dictionnary of years, months for which there are
    potentially archives available for a given list (based on the
    oldest post on the list).

    :arg list_name, name of the mailing list in which this email
    should be searched.
    """
    date_first = cache.get_or_set(
        "MailingList:%s:first_date" % mlist.name,
        lambda: mlist.emails.order_by("date"
            ).values_list("date", flat=True).first(),
        None)
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
    begin_date = datetime.datetime(
        int(year), int(month), start_day, tzinfo=utc)

    if day is None:
        end_date = begin_date + datetime.timedelta(days=32)
        end_date = end_date.replace(day=1)
    else:
        end_date = begin_date + datetime.timedelta(days=1)

    return begin_date, end_date


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def get_category_widget(request=None, current_category=None, categories=()):
    """
    Returns the category form and the applicable category object (or None if no
    category is set for this thread).

    If current_category is not provided or None, try to deduce it from the POST
    request.
    if request is not provided or None, don't return the category form, return
    None instead.
    """

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


def show_mlist(mlist, request):
    def get_domain(host):
        return ".".join(host.split(".")[-2:])
    return (get_domain(mlist.name.partition("@")[2])
            == get_domain(request.get_host()))


# View decorator: check that the list is authorized
def check_mlist_private(func):
    @wraps(func, assigned=available_attrs(func))
    def inner(request, *args, **kwargs):
        if "mlist_fqdn" in kwargs:
            mlist_fqdn = kwargs["mlist_fqdn"]
        else:
            mlist_fqdn = args[0]
        try:
            mlist = MailingList.objects.get(name=mlist_fqdn)
        except MailingList.DoesNotExist:
            raise Http404("No archived mailing-list by that name.")
        if not is_mlist_authorized(request, mlist):
            return render(request, "hyperkitty/errors/private.html", {
                            "mlist": mlist,
                          }, status=403)
        return func(request, *args, **kwargs)
    return inner


def is_mlist_authorized(request, mlist):
    if not mlist.is_private:
        return True
    if not request.user.is_authenticated():
        return False
    # Private list and logged-in user: check subscriptions
    try:
        profile = Profile.objects.get(user_id=request.user.id)
    except Profile.DoesNotExist:
        # Create the profile if it does not exist. There's a signal receiver
        # that creates it for new users, but HyperKitty may be added to an
        # existing Django project with existing users.
        profile = Profile.objects.create(user=request.user)
    if mlist.name in profile.get_subscriptions():
        return True
    else:
        return False
