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

# pylint: disable=unused-argument

from django.conf import settings
from hyperkitty import VERSION

def export_settings(request):
    exports = ["APP_NAME", "USE_MOCKUPS", "USE_INTERNAL_AUTH"]
    extra_context = dict(
        (name.lower(), getattr(settings, name)) for name in exports)
    extra_context["HYPERKITTY_VERSION"] = VERSION
    return extra_context


from django.core.urlresolvers import reverse, NoReverseMatch

def postorius_info(request):
    postorius_url = False
    if "postorius" in settings.INSTALLED_APPS:
        try:
            postorius_url = reverse("postorius.views.list_index")
        except NoReverseMatch:
            pass
    return {"postorius_installed": postorius_url }
