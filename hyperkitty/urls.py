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

from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from hyperkitty.api import ListResource, EmailResource, ThreadResource
from hyperkitty.api import TagResource

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import logout as logout_view

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from hyperkitty.views import TextTemplateView



urlpatterns = patterns('hyperkitty.views',
    # Index
    url(r'^/?$', 'index.index', name='root'),

    # Account
    url(r'^accounts/login/$', 'accounts.login_view', {'template_name': 'login.html', 'SSL': True}, name='user_login'),
    url(r'^accounts/logout/$', logout_view, {'next_page': '/'}, name='user_logout'),
    url(r'^accounts/profile/$', 'accounts.user_profile', name='user_profile'),
    url(r'^accounts/profile/last_views$', 'accounts.last_views', name='user_last_views'),
    url(r'^accounts/profile/votes$', 'accounts.votes', name='user_votes'),
    url(r'^accounts/profile/subscriptions$', 'accounts.subscriptions', name='user_subscriptions'),
    url(r'^accounts/register/$', 'accounts.user_registration', {'SSL': True}, name='user_registration'),

    # Users
    url(r'^user/(?P<user_id>[^/]+)/$', 'accounts.public_profile', name='public_user_profile'),
    url(r'^user/(?P<user_id>[^/]+)/posts$', 'accounts.posts', name='user_posts'),

    # List archives and overview
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        'list.archives', name='archives_with_day'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'list.archives', name='archives_with_month'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/latest$',
        'list.archives', name='archives_latest'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/$',
        'list.overview', name='list_overview'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/recent-activity$',
        'list.recent_activity', name='list_recent_activity'),

    # Message
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/$',
        'message.index', name='message_index'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/attachment/(?P<counter>\d+)/(?P<filename>.+)$',
        'message.attachment', name='message_attachment'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/vote$',
        'message.vote', name='message_vote'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/(?P<message_id_hash>\w+)/reply$',
        'message.reply', name='message_reply'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/new$',
        'message.new_message', name='message_new'),

    # Thread
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/$',
        'thread.thread_index', name='thread'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/replies$',
        'thread.replies', name='thread_replies'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/tags$',
        'thread.tags', name='tags'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/suggest-tags$',
        'thread.suggest_tags', name='suggest_tags'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/favorite$',
        'thread.favorite', name='favorite'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/category$',
        'thread.set_category', name='thread_set_category'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/reattach$',
        'thread.reattach', name='thread_reattach'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/reattach-suggest$',
        'thread.reattach_suggest', name='thread_reattach_suggest'),


    # Search
    url(r'^search$', 'search.search', name='search'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/tag/(?P<tag>.*)/$',
        'search.search_tag', name='search_tag'),


    # REST API
    url(r'^api/$', TemplateView.as_view(template_name="api.html")),
    url(r'^api/list\/',
        ListResource.as_view(), name="api_list"),
    url(r'^api/email\/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/(?P<messageid>.*)/',
        EmailResource.as_view(), name="api_email"),
    url(r'^api/thread\/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/(?P<threadid>.*)/',
        ThreadResource.as_view(), name="api_thread"),
    url(r'^api/tag\/', TagResource.as_view(), name="api_tag"),

    # Errors
    url(r'^error/schemaupgrade$',
        TemplateView.as_view(template_name="errors/schemaupgrade.html"),
        name="error_schemaupgrade"),

    # Admin
    url(r'^admin/', include(admin.site.urls), {"SSL": True}),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Robots.txt
    url(r'^robots\.txt$', TextTemplateView.as_view(template_name="robots.txt")),

    # Social Auth
    url(r'', include('social_auth.urls'), {"SSL": True}),

    # Mailman 2.X compatibility
    url(r'^listinfo/?$', 'compat.summary'),
    url(r'^listinfo/(?P<list_name>[^/]+)/?$', 'compat.summary'),
    url(r'^pipermail/(?P<list_name>[^/]+)/?$', 'compat.summary'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/?$', 'compat.arch_month'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<summary_type>[a-z]+)\.html$', 'compat.arch_month'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)\.txt.gz', 'compat.arch_month_mbox'),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<msg_num>\d+)\.html$', 'compat.message'),

)
#) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()

