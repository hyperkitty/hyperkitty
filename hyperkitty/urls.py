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

from django import VERSION as DJANGO_VERSION
from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import logout as logout_view

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
if DJANGO_VERSION[:2] < (1, 7):
    admin.autodiscover()

from hyperkitty import api


# pylint: disable=invalid-name
urlpatterns = patterns('hyperkitty.views',
    # Index
    url(r'^/?$', 'index.index', name='hk_root'),

    # Account (logged-in user)
    url(r'^accounts/login/$', 'accounts.login_view', {'template_name': 'hyperkitty/login.html', 'SSL': True}, name='hk_user_login'),
    url(r'^accounts/logout/$', logout_view, {'next_page': '/'}, name='hk_user_logout'),
    url(r'^accounts/profile/$', 'accounts.user_profile', name='hk_user_profile'),
    url(r'^accounts/profile/last_views$', 'accounts.last_views', name='hk_user_last_views'),
    url(r'^accounts/profile/votes$', 'accounts.votes', name='hk_user_votes'),
    url(r'^accounts/profile/subscriptions$', 'accounts.subscriptions', name='hk_user_subscriptions'),
    url(r'^accounts/register/$', 'accounts.user_registration', {'SSL': True}, name='hk_user_registration'),

    # Users
    url(r'^users/$', 'users.users', name='hk_users_overview'),
    url(r'^users/(?P<user_id>[^/]+)/$', 'accounts.public_profile', name='hk_public_user_profile'),
    url(r'^users/(?P<user_id>[^/]+)/posts$', 'accounts.posts', name='hk_user_posts'),

    # List archives and overview
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        'mlist.archives', name='hk_archives_with_day'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'mlist.archives', name='hk_archives_with_month'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/latest$',
        'mlist.archives', name='hk_archives_latest'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/$',
        'mlist.overview', name='hk_list_overview'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/recent-activity$',
        'mlist.recent_activity', name='hk_list_recent_activity'),

    # Message
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/$',
        'message.index', name='hk_message_index'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/attachment/(?P<counter>\d+)/(?P<filename>.+)$',
        'message.attachment', name='hk_message_attachment'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/vote$',
        'message.vote', name='hk_message_vote'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/reply$',
        'message.reply', name='hk_message_reply'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/new$',
        'message.new_message', name='hk_message_new'),

    # Thread
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/$',
        'thread.thread_index', name='hk_thread'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/replies$',
        'thread.replies', name='hk_thread_replies'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/tags$',
        'thread.tags', name='hk_tags'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/suggest-tags$',
        'thread.suggest_tags', name='hk_suggest_tags'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/favorite$',
        'thread.favorite', name='hk_favorite'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/category$',
        'thread.set_category', name='hk_thread_set_category'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/reattach$',
        'thread.reattach', name='hk_thread_reattach'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/reattach-suggest$',
        'thread.reattach_suggest', name='hk_thread_reattach_suggest'),


    # Search
    url(r'^search$', 'search.search', name='hk_search'),


    # Categories and Tags
    url(r'^categories/$', 'categories.categories', name='hk_categories_overview'),
    url(r'^tags/$', 'tags.tags', name='hk_tags_overview'),

    # Mailman archiver API
    url(r'^api/mailman/urls$', 'mailman.urls', name='hk_mailman_urls'),
    url(r'^api/mailman/archive$', 'mailman.archive', name='hk_mailman_archive'),

    # REST API
    url(r'^api/$', TemplateView.as_view(template_name="hyperkitty/api.html")),
    url(r'^api/lists/$',
        api.MailingListList.as_view(), name="hk_api_mailinglist_list"),
    url(r'^api/list/(?P<name>[^/@]+@[^/@]+)/$',
        api.MailingListDetail.as_view(), name="hk_api_mailinglist_detail"),
    url(r'^api/list/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/threads/$',
        api.ThreadList.as_view(), name="hk_api_thread_list"),
    url(r'^api/list/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/thread/(?P<thread_id>[^/]+)/$',
        api.ThreadDetail.as_view(), name="hk_api_thread_detail"),
    url(r'^api/list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/emails/$',
        api.EmailList.as_view(), name="hk_api_email_list"),
    url(r'^api/list/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/email/(?P<message_id_hash>.*)/$',
        api.EmailDetail.as_view(), name="hk_api_email_detail"),
    url(r'^api/list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<thread_id>[^/]+)/emails/$',
        api.EmailList.as_view(), name="hk_api_thread_email_list"),
    #url(r'^api/sender/(?P<address>[^/@]+@[^/@]+)/$',
    #    api.SenderDetail.as_view(), name="hk_api_sender_detail"),
    url(r'^api/sender/(?P<mailman_id>[^/]+)/emails/$',
        api.EmailListBySender.as_view(), name="hk_api_sender_email_list"),
    url(r'^api/tags/$', api.TagList.as_view(), name="hk_api_tag_list"),
    #url(r'^', include(restrouter.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Errors
    url(r'^error/schemaupgrade$',
        TemplateView.as_view(template_name="hyperkitty/errors/schemaupgrade.html"),
        name="hk_error_schemaupgrade"),

    # Admin
    url(r'^admin/', include(admin.site.urls), {"SSL": True}),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Robots.txt
    url(r'^robots\.txt$', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),

    # Mailman 2.X compatibility
    url(r'^listinfo/?$', 'compat.summary'),
    url(r'^listinfo/(?P<list_name>[^/]+)/?$', 'compat.summary'),
    url(r'^pipermail/(?P<list_name>[^/]+)/?$', 'compat.summary'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/?$', 'compat.arch_month'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<summary_type>[a-z]+)\.html$', 'compat.arch_month'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)\.txt.gz', 'compat.arch_month_mbox'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<msg_num>\d+)\.html$', 'compat.message'),
    url(r'^list/(?P<list_name>[^@]+)@[^/]+/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/?$', 'compat.arch_month'),
    url(r'^list/(?P<list_name>[^@]+)@[^/]+/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<msg_num>\d+)\.html$', 'compat.message'),

)
#) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
