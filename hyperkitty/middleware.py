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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#



class PaginationMiddleware(object):
    """
    Inserts a variable representing the current page onto the request object if
    it exists in either **GET** or **POST** portions of the request.
    """
    def process_request(self, request):
        try:
            request.page = int(request.REQUEST['page'])
        except (KeyError, ValueError, TypeError):
            request.page = 1



# http://stackoverflow.com/questions/2799450/django-https-for-just-login-page

from django.conf import settings
from django.http import HttpResponsePermanentRedirect

SSL = 'SSL'

class SSLRedirect(object):
    # pylint: disable=unused-argument

    def process_view(self, request, view_func, view_args, view_kwargs):
        want_secure = view_kwargs.pop(SSL, False)
        if not settings.USE_SSL: # User-disabled (e.g: development server)
            return # but after having removed the 'SSL' kwarg

        if self._is_secure(request):
            return # Already in HTTPS, never redirect back to HTTP

        if request.user.is_authenticated():
            want_secure = True

        if want_secure:
            return self._redirect(request, want_secure)

    def _is_secure(self, request):
        if request.is_secure():
            return True

        #Handle the Webfaction case until this gets resolved in the request.is_secure()
        if 'HTTP_X_FORWARDED_SSL' in request.META:
            return request.META['HTTP_X_FORWARDED_SSL'] == 'on'

        return False

    def _redirect(self, request, secure):
        # Note: this method is also capable of redirecting to HTTP, but we
        # don't use this feature.
        protocol = secure and "https" or "http"
        newurl = "%s://%s%s" % (protocol, request.get_host(), request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError(
                "Django can't perform a SSL redirect while maintaining "
                "POST data. Please structure your views so that redirects "
                "only occur during GETs.")
        return HttpResponsePermanentRedirect(newurl)



# https://docs.djangoproject.com/en/dev/topics/i18n/timezones/

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

class TimezoneMiddleware(object):

    def process_request(self, request):
        if not request.user.is_authenticated():
            return
        try:
            profile = request.user.hyperkitty_profile
        except ObjectDoesNotExist:
            return
        if profile.timezone:
            timezone.activate(profile.timezone)
