#-*- coding: utf-8 -*-
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

"""
Fedora OpenID support

No extra configurations are needed to make this work.
"""

from __future__ import absolute_import, unicode_literals

from social_auth.backends import OpenIDBackend, OpenIdAuth


FEDORA_OPENID_URL = 'https://id.fedoraproject.org'

# pylint: disable=too-few-public-methods

class FedoraBackend(OpenIDBackend):
    """Fedora OpenID authentication backend"""
    name = 'fedora'


class FedoraAuth(OpenIdAuth):
    """Fedora OpenID authentication"""
    AUTH_BACKEND = FedoraBackend

    def openid_url(self):
        """Return Fedora OpenID service url"""
        return FEDORA_OPENID_URL


# Backend definition
BACKENDS = {
    'fedora': FedoraAuth,
}
