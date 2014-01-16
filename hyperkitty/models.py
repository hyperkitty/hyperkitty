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
from django.contrib import admin

import pytz
from paintstore.fields import ColorPickerField



class UserProfile(models.Model):
    # User Object
    user = models.OneToOneField(User)

    karma = models.IntegerField(default=1)
    TIMEZONES = [ (tz, tz) for tz in pytz.common_timezones ]
    timezone = models.CharField(max_length=100, choices=TIMEZONES, default=u"")

    def __unicode__(self):
        """Unicode representation"""
        return u'%s' % (unicode(self.user))


class Tag(models.Model):
    list_address = models.CharField(max_length=255, db_index=True)
    threadid = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User)
    tag = models.CharField(max_length=255)

    def __unicode__(self):
        """Unicode representation"""
        return u'Tag %s on thread %s in list %s' % (unicode(self.tag),
                unicode(self.threadid), unicode(self.list_address))

admin.site.register(Tag)


class Favorite(models.Model):
    list_address = models.CharField(max_length=255, db_index=True)
    threadid = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User)

    def __unicode__(self):
        """Unicode representation"""
        return u"Thread %s is a favorite of %s" % (unicode(self.threadid),
                unicode(self.user))

admin.site.register(Favorite)


class LastView(models.Model):
    list_address = models.CharField(max_length=255, db_index=True)
    threadid = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(User)
    view_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        """Unicode representation"""
        return u"Last view of %s by user %s was %s" % (unicode(self.threadid),
                unicode(self.user), self.view_date.isoformat())

admin.site.register(LastView)


class ThreadCategory(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    color = ColorPickerField()

    class Meta:
        verbose_name_plural = "Thread categories"

    def __unicode__(self):
        """Unicode representation"""
        return u'Category "%s"' % (unicode(self.name))

class ThreadCategoryAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.name = obj.name.lower()
        return super(ThreadCategoryAdmin, self).save_model(
                     request, obj, form, change)

admin.site.register(ThreadCategory, ThreadCategoryAdmin)
