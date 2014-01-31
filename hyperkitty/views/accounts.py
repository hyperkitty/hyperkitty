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
from urllib2 import HTTPError

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation, ObjectDoesNotExist
from django.contrib.auth import authenticate, login, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login_view
from django.shortcuts import render, redirect
from django.utils.http import is_safe_url
from django.utils.timezone import utc, get_current_timezone
from django.http import Http404, HttpResponse
#from django.utils.translation import gettext as _
from social_auth.backends import SocialAuthBackend
import dateutil.parser
import mailmanclient

from hyperkitty.models import UserProfile, Favorite, LastView
from hyperkitty.views.forms import RegistrationForm, UserProfileForm
from hyperkitty.lib import get_store
from hyperkitty.lib.view_helpers import FLASH_MESSAGES
from hyperkitty.lib.paginator import paginate
from hyperkitty.lib.mailman import get_subscriptions, is_mlist_authorized


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
def user_profile(request):
    if not request.user.is_authenticated():
        return redirect('user_login')

    store = get_store(request)

    # try to render the user profile.
    try:
        user_profile = request.user.get_profile()
    except ObjectDoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    # get the Mailman user
    try:
        mm_client = mailmanclient.Client('%s/3.0' %
                    settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER,
                    settings.MAILMAN_API_PASS)
        mm_user = mm_client.get_user(request.user.email)
    except (HTTPError, mailmanclient.MailmanConnectionError):
        mm_client = mm_user = None

    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            user_profile.timezone = form.cleaned_data["timezone"]
            request.user.save()
            user_profile.save()
            # Now update the display name in Mailman
            if mm_user is not None:
                mm_user.display_name = "%s %s" % (
                        request.user.first_name, request.user.last_name)
                mm_user.save()
            redirect_url = reverse('user_profile')
            redirect_url += "?msg=updated-ok"
            return redirect(redirect_url)
    else:
        form = UserProfileForm(initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "timezone": get_current_timezone(),
                })

    # Favorites
    try:
        favorites = Favorite.objects.filter(user=request.user)
    except Favorite.DoesNotExist:
        favorites = []
    for fav in favorites:
        thread = store.get_thread(fav.list_address, fav.threadid)
        fav.thread = thread
        if thread is None:
            fav.delete() # thread has gone away?
    favorites = [ f for f in favorites if f.thread is not None ]

    # Emails
    emails = []
    if mm_user is not None:
        for addr in mm_user.addresses:
            addr = unicode(addr)
            if addr != request.user.email:
                emails.append(addr)

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
        'user_profile' : user_profile,
        'form': form,
        'emails': emails,
        'favorites': favorites,
        'flash_messages': flash_messages,
        'gravatar_url': gravatar_url,
        'gravatar_shortname': gravatar_shortname,
    }
    return render(request, "user_profile.html", context)


def user_registration(request):
    if not settings.USE_INTERNAL_AUTH and \
            request.META["SERVER_NAME"] != "testserver": # work with unit tests
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


@login_required
def last_views(request):
    store = get_store(request)
    # Last viewed threads
    try:
        last_views = LastView.objects.filter(user=request.user
                                            ).order_by("view_date")
    except Favorite.DoesNotExist:
        last_views = []
    last_views = paginate(last_views, request.GET.get('lvpage'))
    for last_view in last_views:
        thread = store.get_thread(last_view.list_address, last_view.threadid)
        last_view.thread = thread
        if thread is None:
            last_view.delete()
            continue
        if thread.date_active.replace(tzinfo=utc) > last_view.view_date:
            # small optimization: only query the replies if necessary
            # XXX: Storm-specific (count method)
            thread.unread = thread.replies_after(last_view.view_date).count()
        else:
            thread.unread = 0
    last_views = [ lv for lv in last_views if lv.thread is not None ]

    return render(request, 'ajax/last_views.html', {
                "last_views": last_views,
            })


@login_required
def votes(request):
    store = get_store(request)
    if "user_id" not in request.session:
        return HttpResponse("Could not find or create your user ID in Mailman",
                            content_type="text/plain", status=500)
    user = store.get_user(request.session["user_id"])
    votes = paginate(user.votes, request.GET.get('vpage'))
    return render(request, 'ajax/votes.html', {
                "votes": votes,
            })


@login_required
def subscriptions(request):
    store = get_store(request)
    # get the Mailman user
    try:
        mm_client = mailmanclient.Client('%s/3.0' %
                    settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER,
                    settings.MAILMAN_API_PASS)
        mm_user = mm_client.get_user(request.user.email)
    except (HTTPError, mailmanclient.MailmanConnectionError):
        mm_client = mm_user = None
    # Subscriptions
    subscriptions = get_subscriptions(store, mm_client, mm_user)
    return render(request, 'fragments/user_subscriptions.html', {
                "subscriptions": subscriptions,
            })


def public_profile(request, user_id):
    class FakeMailmanUser(object):
        display_name = None
        created_on = None
        addresses = []
        subscription_list_ids = []
    store = get_store(request)
    try:
        client = mailmanclient.Client('%s/3.0' %
                    settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER,
                    settings.MAILMAN_API_PASS)
        mm_user = client.get_user(user_id)
    except HTTPError:
        raise Http404("No user with this ID: %s" % user_id)
    except mailmanclient.MailmanConnectionError:
        db_user = store.get_user(user_id)
        if db_user is None:
            return HttpResponse("Can't connect to Mailman",
                                content_type="text/plain", status=500)
        mm_user = FakeMailmanUser()
        mm_user.display_name = list(db_user.senders)[0].name
        mm_user.addresses = db_user.addresses
    fullname = mm_user.display_name
    if not fullname:
        fullname = store.get_sender_name(user_id)
    # Subscriptions
    subscriptions = get_subscriptions(store, client, mm_user)
    likes = sum([s["likes"] for s in subscriptions])
    dislikes = sum([s["dislikes"] for s in subscriptions])
    likestatus = "neutral"
    if likes - dislikes >= 10:
        likestatus = "likealot"
    elif likes - dislikes > 0:
        likestatus = "like"
    try:
        email = unicode(mm_user.addresses[0])
    except KeyError:
        email = None
    if mm_user.created_on is not None:
        creation = dateutil.parser.parse(mm_user.created_on)
    else:
        creation = None
    context = {
        "fullname": fullname,
        "mm_user": mm_user,
        "email": email,
        "creation": creation,
        "subscriptions": subscriptions,
        "posts_count": sum([s["posts_count"] for s in subscriptions]),
        "likes": likes,
        "dislikes": dislikes,
        "likestatus": likestatus,
    }
    return render(request, "user_public_profile.html", context)


def posts(request, user_id):
    store = get_store(request)
    mlist_fqdn = request.GET.get("list")
    if mlist_fqdn is None:
        mlist = None
        return HttpResponse("Not implemented yet", status=500)
    else:
        mlist = store.get_list(mlist_fqdn)
        if mlist is None:
            raise Http404("No archived mailing-list by that name.")
        if not is_mlist_authorized(request, mlist):
            return render(request, "errors/private.html", {
                            "mlist": mlist,
                          }, status=403)

    # Get the user's full name
    try:
        client = mailmanclient.Client('%s/3.0' %
                    settings.MAILMAN_REST_SERVER,
                    settings.MAILMAN_API_USER,
                    settings.MAILMAN_API_PASS)
        mm_user = client.get_user(user_id)
    except HTTPError:
        raise Http404("No user with this ID: %s" % user_id)
    except mailmanclient.MailmanConnectionError:
        fullname = None
    else:
        fullname = mm_user.display_name
    if not fullname:
        fullname = store.get_sender_name(user_id)

    # Get the messages and paginate them
    messages = store.get_messages_by_user_id(user_id, mlist_fqdn)
    try:
        page_num = int(request.GET.get('page', "1"))
    except ValueError:
        page_num = 1
    messages = paginate(messages, page_num)

    for message in messages:
        message.myvote = message.get_vote_by_user_id(
                request.session.get("user_id"))

    context = {
        'user_id': user_id,
        'mlist' : mlist,
        'messages': messages,
        'fullname': fullname,
    }
    return render(request, "user_posts.html", context)
