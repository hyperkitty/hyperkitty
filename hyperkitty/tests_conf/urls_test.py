# -*- coding: utf-8 -*-

import hyperkitty

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    #url(r'^$', 'hyperkitty.views.pages.index'),
    (r'^hyperkitty/', include('hyperkitty.urls')),
	#url(r'', include('social_auth.urls')),
)
