from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'hyperkitty.views.home', name='home'),
    # url(r'^hyperkitty/', include('hyperkitty.foo.urls')),
    # This will be the new index page
    url(r'^2$', 'views.pages.index'),
    url(r'^2/$', 'views.pages.index'),
    # This will be the new archives page
    url(r'^2/archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)/$', 'views.pages.archives'),
    url(r'^2/archives/(?P<mlist_fqdn>.*@.*)/(?P<year>\d{4})/(?P<month>\d\d?)$', 'views.pages.archives'),
    url(r'^2/archives/(?P<mlist_fqdn>.*@.*)/$', 'views.pages.archives'),
    url(r'^2/archives/(?P<mlist_fqdn>.*@.*)$', 'views.pages.archives'),
    # This will be the new recent page
    url(r'^2/list$', 'views.pages.index'),
    url(r'^2/list/$', 'views.pages.index'),
    url(r'^2/list/(?P<mlist_fqdn>.*@.*)/$', 'views.pages.list'),
    url(r'^2/list/(?P<mlist_fqdn>.*@.*)$', 'views.pages.list'),
    # Search
    #url(r'^2/search$', 'views.pages.search'),
    url(r'^2/search/(?P<mlist_fqdn>.*@.*)$', 'views.pages.search_keyword'),
    url(r'^2/search/(?P<mlist_fqdn>.*@.*)/$', 'views.pages.search_keyword'),
    url(r'^2/search/(?P<mlist_fqdn>.*@.*)\/(?P<keyword>.*)$', 'views.pages.search_keyword'),
    url(r'^2/tag/(?P<mlist_fqdn>.*@.*)\/(?P<tag>.*)$', 'views.pages.search_tag'),
    # mockups:
    url(r'^$', 'views.mockup.index'),
    url(r'^archives$', 'views.mockup.archives'),
    url(r'^archives/(?P<year>\d{4})/(?P<month>\d{2})/$', 'views.mockup.archives'),
    url(r'^recent$', 'views.mockup.recent'),
    url(r'^search$', 'views.mockup.search'),
    url(r'^search\/(?P<keyword>.*)$', 'views.mockup.search_keyword'),
    url(r'^tag\/(?P<tag>.*)$', 'views.mockup.search_tag'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
#) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()

