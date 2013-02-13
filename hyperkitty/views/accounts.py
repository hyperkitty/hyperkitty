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

import re
import sys
import logging
from urllib2 import HTTPError
from urlparse import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader, RequestContext
from django.utils.http import is_safe_url
from django.utils.translation import gettext as _

from hyperkitty.models import UserProfile, Rating, Favorite
from hyperkitty.views.forms import RegistrationForm
from hyperkitty.lib import get_store


logger = logging.getLogger(__name__)



@login_required
def user_profile(request, user_email=None):
    if not request.user.is_authenticated():
        return redirect('user_login')
    t = loader.get_template('user_profile.html')
    store = get_store(request)

    # try to render the user profile.
    try:
        user_profile = request.user.get_profile()
        # @TODO: Include the error name e.g, ProfileDoesNotExist?
    except:
        user_profile = UserProfile.objects.create(user=request.user)

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

    c = RequestContext(request, {
        'user_profile' : user_profile,
        'votes_up': votes_up,
        'votes_down': votes_down,
        'favorites': favorites,
        'use_mockups': settings.USE_MOCKUPS,
    })

    return HttpResponse(t.render(c))


def user_registration(request):
    redirect_to = request.REQUEST.get("next", reverse("root"))
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = settings.LOGIN_REDIRECT_URL


    if request.user.is_authenticated():
        # Already registered, redirect back to index page
        return HttpResponseRedirect(redirect_to)

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
                    return HttpResponseRedirect(redirect_to)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'next': redirect_to,
    }
    return render_to_response('register.html', context,
                              context_instance=RequestContext(request))

