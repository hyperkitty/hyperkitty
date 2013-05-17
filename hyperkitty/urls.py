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
from django.conf import settings
from django.views.generic.base import TemplateView
from api import ListResource, EmailResource, ThreadResource, SearchResource

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.views import login as login_view
from django.contrib.auth.views import logout as logout_view

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from hyperkitty.views import TextTemplateView



urlpatterns = patterns('hyperkitty.views',
    # Index
    url(r'^/$', 'pages.index', name='index'),
    url(r'^$', 'pages.index', name='root'),
    url(r'^lists-properties$', 'pages.list_properties', name='list_properties'),

    # Account
    #url(r'^accounts/login/$', login_view, {'template_name': 'login.html', 'SSL': True}, name='user_login'),
    url(r'^accounts/login/$', 'accounts.login_view', {'template_name': 'login.html', 'SSL': True}, name='user_login'),
    url(r'^accounts/logout/$', logout_view, {'next_page': '/'}, name='user_logout'),
    url(r'^accounts/profile/$', 'accounts.user_profile', name='user_profile'),
    url(r'^accounts/register/$', 'accounts.user_registration', {'SSL': True}, name='user_registration'),


    # List archives and overview
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        'list.archives', name='archives_with_day'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'list.archives', name='archives_with_month'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/latest$',
        'list.archives', name='archives_latest'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/$',
        'list.overview', name='list_overview'),

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
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/addtag$',
        'thread.add_tag', name='add_tag'),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/favorite$',
        'thread.favorite', name='favorite'),


    # Search Tag
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/tag/(?P<tag>.*)/$',
        'list.search_tag', name='search_tag'),

    # Search
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/search/(?P<target>.*)/(?P<keyword>.*)/$',
        'list.search_keyword', name="search_keyword"),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/search/$',
        'list.search', name="search_list"),


    # REST API
    url(r'^api/$', TemplateView.as_view(template_name="api.html")),
    url(r'^api/list\/',
        ListResource.as_view(), name="api_list"),
    url(r'^api/email\/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/(?P<messageid>.*)/',
        EmailResource.as_view(), name="api_email"),
    url(r'^api/thread\/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/(?P<threadid>.*)/',
        ThreadResource.as_view(), name="api_thread"),
    url(r'^api/search\/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/(?P<field>.*)\/(?P<keyword>.*)/',
        SearchResource.as_view(), name="api_search"),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Admin
    url(r'^admin/', include(admin.site.urls), {"SSL": True}),

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

