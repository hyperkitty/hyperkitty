# -*- coding: utf-8 -*-
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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
#

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth import logout, authenticate, login, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login_view
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _
from social_auth.backends import SocialAuthBackend

from hyperkitty.models import UserProfile, Rating, Favorite
from hyperkitty.views.forms import RegistrationForm, UserProfileForm
from hyperkitty.lib import get_store, FLASH_MESSAGES


logger = logging.getLogger(__name__)


def login_view(request, *args, **kwargs):
    if "extra_context" not in kwargs:
        kwargs["extra_context"] = {}
    if "backends" not in kwargs["extra_context"]:
        kwargs["extra_context"]["backends"] = []
    # Note: sorry but I really find the .setdefault() method non-obvious and
    # harder to re-read that the lines above.
    for backend in get_backends():
        if not isinstance(backend, SocialAuthBackend):
            continue # It should be checked using duck-typing instead
        kwargs["extra_context"]["backends"].append(backend.name)
    return django_login_view(request, *args, **kwargs)


@login_required
def user_profile(request, user_email=None):
    if not request.user.is_authenticated():
        return redirect('user_login')

    store = get_store(request)

    # try to render the user profile.
    try:
        user_profile = request.user.get_profile()
        # @TODO: Include the error name e.g, ProfileDoesNotExist?
    except:
        user_profile = UserProfile.objects.create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.save()
            redirect_url = reverse('user_profile')
            redirect_url += "?msg=updated-ok"
            return redirect(redirect_url)
    else:
        form = UserProfileForm(initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                })

    # Votes
    try:
        votes = Rating.objects.filter(user=request.user)
    except Rating.DoesNotExist:
        votes = []
    votes_up = []
    votes_down = []
    for vote in votes:
        message = store.get_message_by_hash_from_list(
                vote.list_address, vote.messageid)
        vote_data = {"list_address": vote.list_address,
                     "messageid": vote.messageid,
                     "message": message,
                    }
        if vote.vote == 1:
            votes_up.append(vote_data)
        elif vote.vote == -1:
            votes_down.append(vote_data)

    # Favorites
    try:
        favorites = Favorite.objects.filter(user=request.user)
    except Favorite.DoesNotExist:
        favorites = []
    for fav in favorites:
        thread = store.get_thread(fav.list_address, fav.threadid)
        fav.thread = thread

    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

    context = {
        'user_profile' : user_profile,
        'form': form,
        'votes_up': votes_up,
        'votes_down': votes_down,
        'favorites': favorites,
        'flash_messages': flash_messages,
    }
    return render(request, "user_profile.html", context)


def user_registration(request):
    if not settings.USE_INTERNAL_AUTH:
        raise SuspiciousOperation
    redirect_to = request.REQUEST.get("next", reverse("root"))
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = settings.LOGIN_REDIRECT_URL


    if request.user.is_authenticated():
        # Already registered, redirect back to index page
        return redirect(redirect_to)

    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            u = User.objects.create_user(form.cleaned_data['username'],
                                         form.cleaned_data['email'],
                                         form.cleaned_data['password1'])
            u.is_active = True
            u.save()
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password1'])

            if user is not None:
                logger.debug(user)
                if user.is_active:
                    login(request, user)
                    return redirect(redirect_to)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'next': redirect_to,
    }
    return render(request, 'register.html', context)
