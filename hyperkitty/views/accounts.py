# -*- coding: utf-8 -*-
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
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

from urllib2 import HTTPError

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation
from django.contrib.auth import login, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as django_login_view
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url
from django.utils.timezone import get_current_timezone
from django.http import Http404, HttpResponse
#from django.utils.translation import gettext as _
from social.backends.base import BaseAuth as SocialAuthBackend
import dateutil.parser
import mailmanclient

from hyperkitty.models import (Favorite, LastView, MailingList, Sender,
    Email, Vote, Profile)
from hyperkitty.views.forms import (InternalAuthenticationForm,
    RegistrationForm, UserProfileForm)
from hyperkitty.lib.view_helpers import FLASH_MESSAGES, is_mlist_authorized
from hyperkitty.lib.paginator import paginate
from hyperkitty.lib.mailman import get_mailman_client


import logging
logger = logging.getLogger(__name__)


def login_view(request, *args, **kwargs):
    if "extra_context" not in kwargs:
        kwargs["extra_context"] = {}
    if "backends" not in kwargs["extra_context"]:
        kwargs["extra_context"]["social_backends"] = []
    # Note: sorry but I really find the .setdefault() method non-obvious and
    # harder to re-read that the lines above.
    for backend in get_backends():
        if not isinstance(backend, SocialAuthBackend):
            continue # It should be checked using duck-typing instead
        kwargs["extra_context"]["social_backends"].append(backend.name)
    kwargs["authentication_form"] = InternalAuthenticationForm
    return django_login_view(request, *args, **kwargs)


@login_required
def user_profile(request):
    if not request.user.is_authenticated():
        return redirect('hk_user_login')
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Create the profile if it does not exist. There's a signal receiver
        # that creates it for new users, but HyperKitty may be added to an
        # existing Django project with existing users.
        profile = Profile.objects.create(user=request.user)
    mm_user = profile.get_mailman_user()

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            profile.timezone = form.cleaned_data["timezone"]
            request.user.save()
            profile.save()
            # Now update the display name in Mailman
            if mm_user is not None:
                mm_user.display_name = "%s %s" % (
                        request.user.first_name, request.user.last_name)
                mm_user.save()
            redirect_url = reverse('hk_user_profile')
            redirect_url += "?msg=updated-ok"
            return redirect(redirect_url)
    else:
        form = UserProfileForm(initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "timezone": get_current_timezone(),
                })

    # Favorites
    favorites = Favorite.objects.filter(user=request.user)

    # Emails
    other_addresses = profile.addresses[:]
    other_addresses.remove(request.user.email)

    # Flash messages
    flash_messages = []
    flash_msg = request.GET.get("msg")
    if flash_msg:
        flash_msg = { "type": FLASH_MESSAGES[flash_msg][0],
                      "msg": FLASH_MESSAGES[flash_msg][1] }
        flash_messages.append(flash_msg)

    # Extract the gravatar_url used by django_gravatar2.  The site
    # administrator could alternatively set this to http://cdn.libravatar.org/
    gravatar_url = getattr(settings, 'GRAVATAR_URL', 'http://www.gravatar.com')
    gravatar_shortname = '.'.join(gravatar_url.split('.')[-2:]).strip('/')

    context = {
        'user_profile' : profile,
        'form': form,
        'other_addresses': other_addresses,
        'favorites': favorites,
        'flash_messages': flash_messages,
        'gravatar_url': gravatar_url,
        'gravatar_shortname': gravatar_shortname,
    }
    return render(request, "hyperkitty/user_profile.html", context)


def user_registration(request):
    if not settings.USE_INTERNAL_AUTH:
        raise SuspiciousOperation
    try:
        redirect_to = request.GET["next"]
    except KeyError:
        try:
            redirect_to = request.POST["next"]
        except KeyError:
            redirect_to = reverse("hk_root")
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = settings.LOGIN_REDIRECT_URL
    if request.user.is_authenticated():
        # Already registered, redirect back to index page
        return redirect(redirect_to)

    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info("New registered user: %s", user.username)
            if user.is_active:
                login(request, user)
                return redirect(redirect_to)
    else:
        form = RegistrationForm()

    context = {
        'form': form,
        'next': redirect_to,
    }
    return render(request, 'hyperkitty/register.html', context)


@login_required
def last_views(request):
    # Last viewed threads
    lviews = LastView.objects.filter(user=request.user
        ).order_by("-view_date")
    lviews = paginate(lviews, request.GET.get('lvpage'))
    return render(request, 'hyperkitty/ajax/last_views.html', {
                "last_views": lviews,
            })


@login_required
def votes(request):
    all_votes = paginate(request.user.votes.all(),
                     request.GET.get('vpage'))
    return render(request, 'hyperkitty/ajax/votes.html', {
                "votes": all_votes,
            })


@login_required
def subscriptions(request):
    #if "user_id" not in request.session:
    #    return HttpResponse("Could not find or create your user ID in Mailman",
    #                        content_type="text/plain", status=500)
    profile = request.user.hyperkitty_profile
    mm_user_id = profile.get_mailman_user_id()
    subs = []
    for mlist_name in profile.get_subscriptions():
        try:
            mlist = MailingList.objects.get(name=mlist_name)
        except MailingList.DoesNotExist:
            mlist = None # no archived email yet
        posts_count = likes = dislikes = 0
        first_post = all_posts_url = None
        if mlist is not None:
            posts_count = profile.emails.filter(mailinglist__name=mlist_name).count()
            likes, dislikes = profile.get_votes_in_list(mlist_name)
            first_post = profile.get_first_post(mlist)
            if mm_user_id is not None:
                all_posts_url = "%s?list=%s" % (
                    reverse("hk_user_posts", args=[mm_user_id]),
                    mlist_name)
        likestatus = "neutral"
        if likes - dislikes >= 10:
            likestatus = "likealot"
        elif likes - dislikes > 0:
            likestatus = "like"
        subs.append({
            "list_name": mlist_name,
            "mlist": mlist,
            "posts_count": posts_count,
            "first_post": first_post,
            "likes": likes,
            "dislikes": dislikes,
            "likestatus": likestatus,
            "all_posts_url": all_posts_url,
        })
    return render(request, 'hyperkitty/fragments/user_subscriptions.html', {
                "subscriptions": subs,
            })


def public_profile(request, user_id):
    class FakeMailmanUser(object):
        display_name = None
        created_on = None
        addresses = []
        subscription_list_ids = []
        user_id = None
    try:
        client = get_mailman_client()
        mm_user = client.get_user(user_id)
    except HTTPError:
        raise Http404("No user with this ID: %s" % user_id)
    except mailmanclient.MailmanConnectionError:
        #if db_user is None:
        #    return HttpResponse("Can't connect to Mailman",
        #                        content_type="text/plain", status=500)
        mm_user = FakeMailmanUser()
        mm_user.user_id = user_id
        #mm_user.addresses = db_user.addresses
    #XXX: don't list subscriptions, there's a privacy issue here.
    # # Subscriptions
    # subscriptions = get_subscriptions(mm_user, db_user)
    all_votes = Vote.objects.filter(email__sender__mailman_id=user_id)
    likes = all_votes.filter(value=1).count()
    dislikes = all_votes.filter(value=-1).count()
    likestatus = "neutral"
    if likes - dislikes >= 10:
        likestatus = "likealot"
    elif likes - dislikes > 0:
        likestatus = "like"
    # No email display on the public profile, we have enough spam
    # as it is, thank you very much
    #try:
    #    email = unicode(mm_user.addresses[0])
    #except KeyError:
    #    email = None
    fullname = mm_user.display_name
    if not fullname:
        fullname = Sender.objects.filter(mailman_id=user_id).exclude(name=""
            ).values_list("name", flat=True).first()
    if mm_user.created_on is not None:
        creation = dateutil.parser.parse(mm_user.created_on)
    else:
        creation = None
    posts_count = Email.objects.filter(sender__mailman_id=user_id).count()
    context = {
        "fullname": fullname,
        "creation": creation,
        "posts_count": posts_count,
        "likes": likes,
        "dislikes": dislikes,
        "likestatus": likestatus,
    }
    return render(request, "hyperkitty/user_public_profile.html", context)


def posts(request, user_id):
    mlist_fqdn = request.GET.get("list")
    if mlist_fqdn is None:
        mlist = None
        return HttpResponse("Not implemented yet", status=500)
    else:
        try:
            mlist = MailingList.objects.get(name=mlist_fqdn)
        except MailingList.DoesNotExist:
            raise Http404("No archived mailing-list by that name.")
        if not is_mlist_authorized(request, mlist):
            return render(request, "hyperkitty/errors/private.html", {
                            "mlist": mlist,
                          }, status=403)

    fullname = Sender.objects.filter(mailman_id=user_id).exclude(name=""
        ).values_list("name", flat=True).first()
    # Get the messages and paginate them
    messages = Email.objects.filter(
        mailinglist=mlist, sender__mailman_id=user_id)
    try:
        page_num = int(request.GET.get('page', "1"))
    except ValueError:
        page_num = 1
    messages = paginate(messages, page_num)

    for message in messages:
        message.myvote = message.votes.filter(
            user=request.user).first()

    context = {
        'user_id': user_id,
        'mlist' : mlist,
        'messages': messages,
        'fullname': fullname,
    }
    return render(request, "hyperkitty/user_posts.html", context)
