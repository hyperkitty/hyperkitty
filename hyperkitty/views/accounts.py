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

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.forms import AuthenticationForm
from hyperkitty.models import UserProfile, Rating
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader, RequestContext
from django.utils.translation import gettext as _
from urllib2 import HTTPError
from urlparse import urlparse

from forms import RegistrationForm
from hyperkitty.lib import get_store


logger = logging.getLogger(__name__)


def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_login(request, template='login.html'):

    user = None
    parse_r = urlparse(request.META.get('HTTP_REFERER', 'index'))
    previous = '%s%s' % (parse_r.path, parse_r.query)

    next_var = request.POST.get('next', request.GET.get('next', previous))

    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        user = authenticate(username=request.POST.get('username'),
                            password=request.POST.get('password'))

    if user is not None:
        logger.debug(user)
        if user.is_active:
            login(request, user)
            return redirect(next_var)

    else:
        form = AuthenticationForm()
    return render_to_response(template, {'form': form, 'next' : next_var},
                              context_instance=RequestContext(request))

@login_required
def user_profile(request, user_email=None):
    if not request.user.is_authenticated():
        return redirect('user_login')
    t = loader.get_template('user_profile.html')

    # try to render the user profile.
    try:
        user_profile = request.user.get_profile()
        # @TODO: Include the error name e.g, ProfileDoesNotExist?
    except:
        user_profile = UserProfile.objects.create(user=request.user)

    try:
        votes = Rating.objects.filter(user=request.user)
    except Rating.DoesNotExist:
        votes = {}
    store = get_store(request)
    votes_up = []
    votes_down = []
    for vote in votes:
        message = store.get_message_by_id_from_list(
                vote.list_address, vote.message_id)
        vote_data = {"list_address": vote.list_address,
                     "message_id": vote.message_id,
                     "message": message,
                    }
        if vote.vote == 1:
            votes_up.append(vote_data)
        elif vote.vote == -1:
            votes_down.append(vote_data)

    c = RequestContext(request, {
        'user_profile' : user_profile,
        'votes_up': votes_up,
        'votes_down': votes_down,
        'use_mockups': settings.USE_MOCKUPS,
    })

    return HttpResponse(t.render(c))


def user_registration(request):
    if request.user.is_authenticated():
        # Already registered, redirect back to index page
        return redirect('index')

    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Save the user data.
            form.save(form.cleaned_data)
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password1'])

            if user is not None:
                logger.debug(user)
                if user.is_active:
                    login(request, user)
                    return redirect('index')
    else:
        form = RegistrationForm()

    return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))

