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

from __future__ import absolute_import, unicode_literals, print_function

import datetime
from collections import namedtuple
from urllib2 import HTTPError
from uuid import UUID

from django.conf import settings
from django.db import models, IntegrityError
from django.db.models.signals import (
    post_init, pre_save, pre_delete, post_delete)
from django.contrib import admin
from django.dispatch import receiver
from django.core.cache import cache
from django.utils.timezone import now, utc

import pytz
import dateutil.parser
from paintstore.fields import ColorPickerField
from enum import Enum
from mailmanclient import MailmanConnectionError


from hyperkitty.lib.mailman import get_mailman_client
from hyperkitty.lib.signals import new_email, new_thread
from hyperkitty.lib.analysis import compute_thread_order_and_depth

import logging
logger = logging.getLogger(__name__)


# TODO:
# - caching
# - simplify methods



class ArchivePolicy(Enum):
    """
    Copy from mailman.interfaces.archiver.ArchivePolicy since we can't import
    mailman (PY3-only).
    """
    never = 0
    private = 1
    public = 2



class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name="hyperkitty_profile")

    karma = models.IntegerField(default=1)
    TIMEZONES = [ (tz, tz) for tz in pytz.common_timezones ]
    timezone = models.CharField(max_length=100, choices=TIMEZONES, default=u"")

    def __unicode__(self):
        return u'%s' % (unicode(self.user))

    @property
    def emails(self):
        return Email.objects.filter(
            sender__address__in=self.addresses).order_by("date")

    @property
    def addresses(self):
        addresses = set(self.user.email)
        mm_user = self.get_mailman_user()
        if mm_user:
            # TODO: caching
            addresses.update(mm_user.addresses)
        return list(sorted(addresses))

    def get_votes_in_list(self, list_name):
        # TODO: Caching ?
        votes = self.user.votes.filter(email__mailinglist__name=list_name)
        likes = votes.filter(value=1).count()
        dislikes = votes.filter(value=-1).count()
        return likes, dislikes

    def get_mailman_user(self):
        # TODO: Caching: cache the mailman user id
        try:
            mm_client = get_mailman_client()
            return mm_client.get_user(self.user.email)
        except (HTTPError, MailmanConnectionError):
            return None

    def get_mailman_user_id(self):
        # TODO: Caching: cache the mailman user id
        mm_user = self.get_mailman_user()
        if mm_user is None:
            return None
        return mm_user.user_id

    def get_subscriptions(self):
        # TODO: Caching
        mm_client = get_mailman_client()
        mm_user = self.get_mailman_user()
        if mm_user is None:
            return []
        sub_names = set()
        for mlist_id in mm_user.subscription_list_ids:
            mlist_name = mm_client.get_list(mlist_id).fqdn_listname
            ## de-duplicate subscriptions
            #if mlist_name in [ s["list_name"] for s in sub_names ]:
            #    continue
            sub_names.add(mlist_name)
        return list(sorted(sub_names))

    def get_first_post(self, mlist):
        return self.emails.filter(mailinglist=mlist
            ).order_by("archived_date").first()

admin.site.register(Profile)


class MailingList(models.Model):
    """
    An archived mailing-list.
    """
    name = models.CharField(max_length=254, primary_key=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    subject_prefix = models.CharField(max_length=255)
    archive_policy = models.IntegerField(
        choices=[ (p.value, p.name) for p in ArchivePolicy ],
        default=ArchivePolicy.public.value)
    created_at = models.DateTimeField(default=now)

    @property
    def is_private(self):
        return self.archive_policy == ArchivePolicy.private.value

    @property
    def is_new(self):
        return self.created_at and \
                now() - self.created_at <= datetime.timedelta(days=30)

    def get_recent_dates(self):
        today = now()
        #today -= datetime.timedelta(days=400) #debug
        # the upper boundary is excluded in the search, add one day
        end_date = today + datetime.timedelta(days=1)
        begin_date = end_date - datetime.timedelta(days=32)
        return begin_date, end_date

    def get_participants_count_between(self, begin_date, end_date):
        # We filter on emails dates instead of threads dates because that would
        # also include last month's participants when threads carry from one
        # month to the next
        # TODO: caching
        return self.emails.filter(
                date__gte=begin_date, date__lt=end_date
            ).values("sender_id").distinct().count()
        #result = Email.objects.filter(mailinglist=self, date__gte=begin_date, date__lt=end_date).values("sender_id").distinct().count()

    def get_threads_between(self, begin_date, end_date):
        return self.threads.filter(
                date_active__gte=begin_date, date_active__lt=end_date
            ).order_by("-date_active")

    @property
    def recent_participants_count(self):
        begin_date, end_date = self.get_recent_dates()
        return self.get_participants_count_between(begin_date, end_date)
        #return session.cache.get_or_create(
        #    str("list:%s:recent_participants_count" % self.name),
        #    lambda: self.get_participants_count_between(begin_date, end_date),
        #    86400)

    @property
    def recent_threads(self):
        # CACHING
        begin_date, end_date = self.get_recent_dates()
        return self.get_threads_between(begin_date, end_date)

    def get_participants_count_for_month(self, year, month):
        # CACHING
        begin_date = datetime.datetime(year, month, 1, tzinfo=utc)
        end_date = begin_date + datetime.timedelta(days=32)
        end_date = end_date.replace(day=1)
        return self.get_participants_count_between(begin_date, end_date)

    def get_top_participants(self, start, end, limit=None):
        query = Sender.objects.filter(
            emails__mailinglist=self,
            emails__date__gte=start,
            emails__date__lt=end,
            ).annotate(count=models.Count("emails")
            ).order_by("-count")
        # Compatibility:
        #query = query.values_list("name", "address", "num_emails")
        #print(query.query)
        if limit is not None:
            return query[:limit]
        else:
            return query

    def update_from_mailman(self):
        try:
            client = get_mailman_client()
            mm_list = client.get_list(self.name)
        except MailmanConnectionError:
            return
        except HTTPError, err:
            return # can't update at this time
        if not mm_list:
            return
        converters = {
            "created_at": dateutil.parser.parse,
            "archive_policy": lambda p: getattr(ArchivePolicy, p).value,
        }
        for propname in ("display_name", "description", "subject_prefix",
                         "archive_policy", "created_at"):
            try:
                value = getattr(mm_list, propname)
            except AttributeError:
                value = mm_list.settings[propname]
            if propname in converters:
                value = converters[propname](value)
            setattr(self, propname, value)
        self.save()

@receiver(new_email)
def refresh_mailinglist_cache(sender, **kwargs):
    pass
    #cache = event.store.db.cache
    ## recent activity
    #begin_date = event.mlist.get_recent_dates()[0]
    #if event.message.date >= begin_date:
    #    cache.delete(str("list:%s:recent_participants_count" % event.mlist.name))
    #    event.mlist.recent_participants_count
    #    cache.delete(str("list:%s:recent_threads_count" % event.mlist.name))
    #    event.mlist.recent_threads_count
    ## month activity
    #year, month = event.message.date.year, event.message.date.month
    #cache.delete(str("list:%s:participants_count:%s:%s"
    #                 % (event.mlist.name, year, month)))
    #event.mlist.get_month_activity(year, month)



class Sender(models.Model):
    address = models.EmailField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    mailman_id = models.CharField(max_length=255, null=True)

    def set_mailman_id(self):
        try:
            client = get_mailman_client()
            mm_user = client.get_user(self.address)
        except HTTPError as e:
            raise MailmanConnectionError(e) # normalize all possible error types
        self.mailman_id = mm_user.user_id
        self.save()
        ## Go further and associate the user's other addresses?
        #Sender.objects.filter(address__in=mm_user.addresses
        #    ).update(mailman_id=mm_user.user_id)



class Email(models.Model):
    """
    An archived email, from a mailing-list. It is identified by both the list
    name and the message id.
    """
    mailinglist = models.ForeignKey("MailingList", related_name="emails")
    message_id = models.CharField(max_length=255, db_index=True)
    message_id_hash = models.CharField(max_length=255, db_index=True)
    sender = models.ForeignKey("Sender", related_name="emails")
    subject = models.CharField(max_length="512", db_index=True)
    content = models.TextField()
    date = models.DateTimeField()
    timezone = models.SmallIntegerField()
    in_reply_to = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey("self",
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name="children")
    thread = models.ForeignKey("Thread", related_name="emails")
    archived_date = models.DateTimeField(auto_now_add=True, db_index=True)
    thread_depth = models.IntegerField(default=0)
    thread_order = models.IntegerField(default=0, db_index=True)

    @property
    def likes(self):
        # TODO: caching
        return self.votes.filter(value=1).count()

    @property
    def dislikes(self):
        # TODO: caching
        return self.votes.filter(value=-1).count()

    @property
    def likestatus(self):
        likes, dislikes = self.likes, self.dislikes
        # TODO: use an Enum?
        if likes - dislikes >= 10:
            return "likealot"
        if likes - dislikes > 0:
            return "like"
        return "neutral"

    def vote(self, value, user):
        # Checks if the user has already voted for this message.
        existing = self.votes.filter(user=user).first()
        # TODO: make sure this is covered by unit tests
        if existing is not None and existing.value == value:
            return # Vote already recorded (should I raise an exception?)
        if value not in (0, 1, -1):
            raise ValueError("A vote can only be +1 or -1 (or 0 to cancel)")
        # The vote can be added, changed or cancelled. Keep it simple and
        # delete likes and dislikes cached values.
        # TODO: delete cached values
        if existing is not None:
            # vote changed or cancelled
            if value == 0:
                existing.delete()
            else:
                existing.value = value
        else:
            # new vote
            vote = Vote(email=self, user=user, value=value)
            vote.save()

@receiver([post_init, pre_save], sender=Email)
def Email_set_message_id_hash(sender, **kwargs):
    from hyperkitty.lib.utils import get_message_id_hash # circular import
    email = kwargs["instance"]
    if not email.message_id_hash:
        email.message_id_hash = get_message_id_hash(email.message_id)

@receiver(pre_save, sender=Email)
def Email_check_parent_id(sender, **kwargs):
    """Make sure there is only one email with parent_id == None in a thread"""
    instance = kwargs["instance"]
    if instance.parent_id != None:
        return
    starters = Email.objects.filter(
            thread=instance.thread, parent_id__isnull=True
        ).values_list("id", flat=True)
    if len(starters) > 0 and list(starters) != [instance.id]:
        raise IntegrityError("There can be only one email with "
                             "parent_id==None in the same thread")

@receiver(pre_delete, sender=Email)
def Email_reset_parent_id(sender, **kwargs):
    email = kwargs["instance"]
    if email.parent_id is None:
        # not sure this is really useful. Does email.thread return the same
        # instance each time?
        email.thread._starting_email_cache = None
    children = email.children.order_by("date")
    if not children:
        return
    if email.parent_id is None:
        # temporarily set the email's parent_id to not None, to allow the next
        # email to be the starting email (there's a check on_save for duplicate
        # thread starters)
        email.parent_id = email.id
        email.save(update_fields["parent_id"])
        starter = children[0]
        starter.parent_id = None
        starter.save()
        children.all().update(parent_id=starter.id)
    else:
        children.update(parent_id=email.parent_id)

@receiver(post_delete, sender=Email)
def Email_update_or_clean_thread(sender, **kwargs):
    email = kwargs["instance"]
    try:
        thread = Thread.objects.get(id=email.thread_id)
    except Thread.DoesNotExist:
        return
    if thread.emails.count() == 0:
        thread.delete()
    else:
        compute_thread_order_and_depth(thread)



class Attachment(models.Model):
    email = models.ForeignKey("Email", related_name="attachments")
    counter = models.SmallIntegerField()
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    encoding = models.CharField(max_length=255, null=True)
    size = models.IntegerField()
    content = models.BinaryField()

@receiver(pre_save, sender=Attachment)
def Attachment_set_size(sender, **kwargs):
    instance = kwargs["instance"]
    instance.size = len(instance.content)



class Thread(models.Model):
    """
    A thread of archived email, from a mailing-list. It is identified by both
    the list name and the thread id.
    """
    mailinglist = models.ForeignKey("MailingList", related_name="threads")
    thread_id = models.CharField(max_length=255, db_index=True)
    date_active = models.DateTimeField(db_index=True, default=now)
    category = models.ForeignKey("ThreadCategory", related_name="threads", null=True)
    _starting_email_cache = None

    @property
    def starting_email(self):
        if self._starting_email_cache is None:
            try:
                self._starting_email_cache = \
                    self.emails.get(parent_id__isnull=True)
            except Email.DoesNotExist:
                self._starting_email_cache = \
                    self.emails.order_by("date").first()
        return self._starting_email_cache

    @property
    def last_email(self):
        return self.emails.order_by("-date").first()

    @property
    def participants(self):
        """Set of email senders in this thread"""
        return Sender.objects.filter(emails__thread_id=self.id).distinct()

    @property
    def participants_count(self):
        # TODO: Cache this
        return self.participants.count()

    def replies_after(self, date):
        return self.emails.filter(date__gt=date)

    #def _get_category(self):
    #    if not self.category_id:
    #        return None
    #    return self.category_obj.name
    #def _set_category(self, name):
    #    if not name:
    #        self.category_id = None
    #        return
    #    session = object_session(self)
    #    try:
    #        category = session.query(Category).filter_by(name=name).one()
    #    except NoResultFound:
    #        category = Category(name=name)
    #        session.add(category)
    #    self.category_id = category.id
    #category = property(_get_category, _set_category)

    #@property
    #def emails_count(self):
    #    # TODO: Cache this
    #    return self.emails.count()

    @property
    def subject(self):
        # TODO: Cache this
        return self.starting_email.subject

    def _getvotes(self):
        return Vote.objects.filter(email__thread_id=self.id)

    @property
    def likes(self):
        # TODO: Cache this
        return self._getvotes().filter(value=1).count()

    @property
    def dislikes(self):
        # TODO: Cache this
        return self._getvotes().filter(value=-1).count()

    @property
    def likestatus(self):
        # TODO: deduplicate with the equivalent function in the Email class
        likes, dislikes = self.likes, self.dislikes
        # XXX: use an Enum?
        if likes - dislikes >= 10:
            return "likealot"
        if likes - dislikes > 0:
            return "like"
        return "neutral"

    @property
    def prev_thread(self): # TODO: Make it a relationship
        return Thread.objects.filter(
                mailinglist=self.mailinglist,
                date_active__lt=self.date_active
            ).order_by("-date_active").first()

    @property
    def next_thread(self): # TODO: Make it a relationship
        return Thread.objects.filter(
                mailinglist=self.mailinglist,
                date_active__gt=self.date_active
            ).order_by("date_active").first()

    def is_unread_by(self, user):
        if not user.is_authenticated():
            return False
        try:
            last_view = LastView.objects.get(thread=self, user=user)
        except LastView.DoesNotExist:
            return True
        return self.date_active.replace(tzinfo=utc) > last_view.view_date


@receiver(new_email)
def refresh_thread_cache(sender, **kwargs):
    pass
    #cache = event.store.db.cache
    #cache.delete(str("list:%s:thread:%s:emails_count"
    #                 % (event.message.list_name, event.message.thread_id)))
    #event.message.thread.emails_count
    #cache.delete(str("list:%s:thread:%s:participants_count"
    #                 % (event.message.list_name, event.message.thread_id)))
    #event.message.thread.participants_count

@receiver(new_thread)
def cache_thread_subject(sender, **kwargs):
    pass
    #event.store.db.cache.set(
    #        str("list:%s:thread:%s:subject"
    #            % (event.thread.list_name, event.thread.thread_id)),
    #        event.thread.starting_email.subject)



class Vote(models.Model):
    """
    A User's vote on a message
    """
    email = models.ForeignKey("Email", related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="votes")
    value = models.SmallIntegerField(db_index=True)

admin.site.register(Vote)


class Tagging(models.Model):

    thread = models.ForeignKey("Thread")
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    tag = models.ForeignKey("Tag")

    def __unicode__(self):
        return 'Tag %s on %s by %s' % (unicode(self.tag),
                unicode(self.thread), unicode(self.user))


class Tag(models.Model):

    name = models.CharField(max_length=255, db_index=True)
    threads = models.ManyToManyField("Thread",
        through="Tagging", related_name="tags")
    users = models.ManyToManyField(settings.AUTH_USER_MODEL,
        through="Tagging", related_name="tags")

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return 'Tag %s' % (unicode(self.name))


#class Tag(models.Model):
#    thread = models.ForeignKey("Thread", related_name="tags")
#    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="tags")
#    tag = models.CharField(max_length=255)
#
#    def __unicode__(self):
#        return u'Tag %s on thread %s in list %s' % (unicode(self.tag),
#                unicode(self.thread.thread_id), unicode(self.mailinglist_name))

admin.site.register(Tag)


class Favorite(models.Model):
    thread = models.ForeignKey("Thread", related_name="favorites")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="favorites")

    def __unicode__(self):
        return u"%s is a favorite of %s" % (
            unicode(self.thread), unicode(self.user))

admin.site.register(Favorite)


class LastView(models.Model):
    thread = models.ForeignKey("Thread", related_name="lastviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="lastviews")
    view_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        """Unicode representation"""
        return u"Last view of %s by %s was %s" % (
            unicode(self.thread), unicode(self.user),
            self.view_date.isoformat())

    def num_unread(self):
        if self.thread.date_active.replace(tzinfo=utc) <= self.view_date:
            return 0 # avoid the expensive query below
        else:
            return self.thread.emails.filter(date__gt=self.view_date).count()

admin.site.register(LastView)


class ThreadCategory(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    color = ColorPickerField()

    class Meta:
        verbose_name_plural = "Thread categories"

    def __unicode__(self):
        return u'Thread category "%s"' % (unicode(self.name))

class ThreadCategoryAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.name = obj.name.lower()
        return super(ThreadCategoryAdmin, self).save_model(
                     request, obj, form, change)

admin.site.register(ThreadCategory, ThreadCategoryAdmin)
