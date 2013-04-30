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

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib import admin



class Rating(models.Model):
    # @TODO: instead of list_address, user list model from kittystore?
    list_address = models.CharField(max_length=255)

    # @TODO: instead of messsageid, use message model from kittystore?
    messageid = models.CharField(max_length=100)

    user = models.ForeignKey(User)

    vote = models.SmallIntegerField()

    def __unicode__(self):
        """Unicode representation"""
        if self.vote == 1:
            return u'%s liked message %s' % (unicode(self.user),
                    unicode(self.messageid))
        else:
            return u'%s disliked message %s' % (unicode(self.user),
                    unicode(self.messageid))

admin.site.register(Rating)


class UserProfile(models.Model):
    # User Object
    user = models.OneToOneField(User)

    karma = models.IntegerField(default=1)

    def __unicode__(self):
        """Unicode representation"""
        return u'%s' % (unicode(self.user))


class Tag(models.Model):
    # @TODO: instead of list_address, user list model from kittystore?
    list_address = models.CharField(max_length=255)

    # @TODO: instead of threadid, use thread model from kittystore?
    threadid = models.CharField(max_length=100)

    tag = models.CharField(max_length=255)

    def __unicode__(self):
        """Unicode representation"""
        return u'Tag %s on thread %s in list %s' % (unicode(self.tag),
                unicode(self.threadid), unicode(self.list_address))

admin.site.register(Tag)


class Favorite(models.Model):
    list_address = models.CharField(max_length=255)
    threadid = models.CharField(max_length=100)
    user = models.ForeignKey(User)

    def __unicode__(self):
        """Unicode representation"""
        return u"Thread %s is a favorite of %s" % (unicode(self.threadid),
                unicode(self.user))

admin.site.register(Favorite)
