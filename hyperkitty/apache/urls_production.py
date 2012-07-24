from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from gsoc.api import EmailResource, ThreadResource, SearchResource

urlpatterns = patterns('',
    # Account
    url(r'^accounts/login/$', 'views.accounts.user_login', name='user_login'),
    url(r'^accounts/logout/$', 'views.accounts.user_logout', name='user_logout'),
    url(r'^accounts/profile/$', 'views.accounts.user_profile', name='user_profile'),
    url(r'^accounts/register/$', 'views.accounts.user_registration', name='user_registration'),


    # Index
    url(r'^/$', 'views.pages.index', name='index'),
    url(r'^$', 'views.pages.index', name='index'),

    # Archives
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        'views.list.archives'),
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/$',
        'views.list.archives'),
    url(r'^archives/(?P<mlist_fqdn>.*@.*)/$',
        'views.list.archives'),

    # Threads
    url(r'^thread/(?P<mlist_fqdn>.*@.*)/(?P<threadid>.+)/$',
        'views.thread.thread_index'),


    # Lists
    url(r'^list/$', 'views.pages.index'), # Can I remove this URL?
    url(r'^list/(?P<mlist_fqdn>.*@.*)/$',
        'views.list.list'),

    # Search Tag
    url(r'^tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)\/(?P<page>\d+)/$',
        'views.list.search_tag'),
    url(r'^tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)/$',
        'views.list.search_tag'),

    # Search
    # If page number is present in URL
    url(r'^search/(?P<mlist_fqdn>.*@.*)\/(?P<target>.*)\/(?P<keyword>.*)\/(?P<page>\d+)/$',
        'views.list.search_keyword'),
    # Show the first page as default when no page number is present in URL
    url(r'^search/(?P<mlist_fqdn>.*@.*)\/(?P<target>.*)\/(?P<keyword>.*)/$',
        'views.list.search_keyword'),
    url(r'^search/(?P<mlist_fqdn>.*@.*)/$',
        'views.list.search'),


    ### MESSAGE LEVEL VIEWS ###
    # Vote a message
    url(r'^message/(?P<mlist_fqdn>.*@.*)/(?P<messageid>.+)/$',
        'views.message.index'),

    url(r'^vote/(?P<mlist_fqdn>.*@.*)/$',
        'views.message.vote'),
    ### MESSAGE LEVEL VIEW ENDS ###

 

    ### THREAD LEVEL VIEWS ###
    # Thread view page
    url(r'^thread/(?P<mlist_fqdn>.*@.*)/(?P<threadid>.+)/$',
        'views.thread.thread_index'),

    # Add Tag to a thread
    url(r'^addtag/(?P<mlist_fqdn>.*@.*)\/(?P<email_id>.*)/$',
        'views.thread.add_tag'),
    ### THREAD LEVEL VIEW ENDS ###

 
    # REST API
    url(r'^api/$', 'views.api.api'),
    url(r'^api/email\/(?P<mlist_fqdn>.*@.*)\/(?P<messageid>.*)/',
        EmailResource.as_view()),
    url(r'^api/thread\/(?P<mlist_fqdn>.*@.*)\/(?P<threadid>.*)/',
        ThreadResource.as_view()),
    url(r'^api/search\/(?P<mlist_fqdn>.*@.*)\/(?P<field>.*)\/(?P<keyword>.*)/',
        SearchResource.as_view()),


    # Social Auth
    url(r'', include('social_auth.urls')),

)
