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

from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.views.generic.simple import direct_to_template
from api import EmailResource, ThreadResource, SearchResource

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('hyperkitty.views',
    # Account
    url(r'^accounts/login/$', 'accounts.user_login', name='user_login'),
    url(r'^accounts/logout/$', 'accounts.user_logout', name='user_logout'),
    url(r'^accounts/profile/$', 'accounts.user_profile', name='user_profile'),
    url(r'^accounts/register/$', 'accounts.user_registration', name='user_registration'),


    # Index
    url(r'^/$', 'pages.index', name='index'),
    url(r'^$', 'pages.index', name='root'),

    # Archives
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        'list.archives', name='archives_with_day'),
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'list.archives', name='archives_with_month'),
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/$',
        'list.archives', name='archives'),

    # Threads
    url(r'^thread/(?P<mlist_fqdn>.*@.*)/(?P<threadid>.+)/$',
        'thread.thread_index', name='thread'),


    # Lists
    url(r'^list/$', 'pages.index'), # Can I remove this URL?
    url(r'^list/(?P<mlist_fqdn>.*@.*)/$',
        'list.list', name='list_overview'),

    # Search Tag
    url(r'^tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)\/(?P<page>\d+)/$',
        'list.search_tag'),
    url(r'^tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)/$',
        'list.search_tag', name='search_tag'),

    # Search
    # If page number is present in URL
    url(r'^search/(?P<mlist_fqdn>.*@.*)\/(?P<target>.*)\/(?P<keyword>.*)\/(?P<page>\d+)/$',
        'list.search_keyword'),
    # Show the first page as default when no page number is present in URL
    url(r'^search/(?P<mlist_fqdn>.*@.*)\/(?P<target>.*)\/(?P<keyword>.*)/$',
        'list.search_keyword', name="search_keyword"),
    url(r'^search/(?P<mlist_fqdn>.*@.*)/$',
        'list.search', name="search_list"),


    ### MESSAGE LEVEL VIEWS ###
    url(r'^message/(?P<mlist_fqdn>.*@.*)/(?P<hashid>\w+)/$',
        'message.index', name='message_index'),

    url(r'^message/(?P<mlist_fqdn>.*@.*)/(?P<hashid>\w+)/attachment/(?P<counter>\d+)/(?P<filename>.+)$',
        'message.attachment', name='message_attachment'),

    url(r'^vote/(?P<mlist_fqdn>.*@.*)/$',
        'message.vote', name='message_vote'),
    ### MESSAGE LEVEL VIEW ENDS ###



    ### THREAD LEVEL VIEWS ###
    # Thread view page
    url(r'^thread/(?P<mlist_fqdn>.*@.*)/(?P<threadid>.+)/$',
        'thread.thread_index', name='thread_index'),

    # Add Tag to a thread
    url(r'^addtag/(?P<mlist_fqdn>.*@.*)\/(?P<hashid>.*)/$',
        'thread.add_tag', name='add_tag'),
    ### THREAD LEVEL VIEW ENDS ###


    # REST API
    url(r'^api/$', 'api.api'),
    url(r'^api/email\/(?P<mlist_fqdn>.*@.*)\/(?P<hashid>.*)/',
        EmailResource.as_view(), name="api_email"),
    url(r'^api/thread\/(?P<mlist_fqdn>.*@.*)\/(?P<threadid>.*)/',
        ThreadResource.as_view(), name="api_thread"),
    url(r'^api/search\/(?P<mlist_fqdn>.*@.*)\/(?P<field>.*)\/(?P<keyword>.*)/',
        SearchResource.as_view(), name="api_search"),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Admin
    url(r'^admin/', include(admin.site.urls)),

    # Robots.txt
    url(r'^robots\.txt$', direct_to_template,
     {'template': 'robots.txt', 'mimetype': 'text/plain'}),

    # Social Auth
    url(r'', include('social_auth.urls')),

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

