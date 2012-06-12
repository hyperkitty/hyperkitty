from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from api import EmailResource, ThreadResource, SearchResource

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Account
    url(r'^accounts/login/$', 'views.accounts.user_login', name='user_login'),
    url(r'^accounts/logout/$', 'views.accounts.user_logout', name='user_logout'),
    url(r'^accounts/profile/$', 'views.accounts.user_profile', name='user_profile'),

    # Index
    url(r'^/$', 'views.pages.index', name='index'),
    url(r'^$',  'views.pages.index', name='index'),

    # Archives
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        'views.pages.archives'),
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'views.pages.archives'),
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/$',
        'views.pages.archives'),

    # Threads
    url(r'^thread/(?P<mlist_fqdn>.*@.*)/(?P<threadid>.+)/$',
        'views.pages.thread'),


    # Lists
    url(r'^list/$', 'views.pages.index'),
    url(r'^list/(?P<mlist_fqdn>.*@.*)/$',
        'views.pages.list'),


    # Message
    url(r'^message/(?P<mlist_fqdn>.*@.*)/(?P<messageid>.+)/$',
        'views.pages.message'),


    # Search
    # If page number is present in URL
    url(r'^search/(?P<mlist_fqdn>.*@.*)\/(?P<target>.*)\/(?P<keyword>.*)\/(?P<page>\d+)/$',
        'views.pages.search_keyword'),
    # Show the first page as default when no page number is present in URL
    url(r'^search/(?P<mlist_fqdn>.*@.*)\/(?P<target>.*)\/(?P<keyword>.*)/$',
        'views.pages.search_keyword'),
    url(r'^search/(?P<mlist_fqdn>.*@.*)/$',
        'views.pages.search'),

    # Category
    url(r'^addcategory/(?P<mlist_fqdn>.*@.*)\/(?P<email_id>.*)/$',
        'views.pages.add_category'),


    # Tag
    url(r'^tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)\/(?P<page>\d+)/$',
        'views.pages.search_tag'),
    url(r'^tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)/$',
        'views.pages.search_tag'),
    url(r'^addtag/(?P<mlist_fqdn>.*@.*)\/(?P<email_id>.*)/$',
        'views.pages.add_tag'),

    # REST API
    url(r'^api/$', 'views.pages.api'),
    url(r'^api/email\/(?P<mlist_fqdn>.*@.*)\/(?P<messageid>.*)/',
        EmailResource.as_view()),
    url(r'^api/thread\/(?P<mlist_fqdn>.*@.*)\/(?P<threadid>.*)/',
        ThreadResource.as_view()),
    url(r'^api/search\/(?P<mlist_fqdn>.*@.*)\/(?P<field>.*)\/(?P<keyword>.*)/',
        SearchResource.as_view()),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Admin  
    url(r'^admin/', include(admin.site.urls)),

    # Social Auth
    url(r'', include('social_auth.urls')),

)
#) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()

